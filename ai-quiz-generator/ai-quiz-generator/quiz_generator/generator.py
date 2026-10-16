"""Quiz generation logic: calls the Anthropic API and validates the result."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field

from anthropic import Anthropic

DEFAULT_MODEL = os.getenv("QUIZ_MODEL", "claude-haiku-5-5")
OPTIONS_PER_QUESTION = 4
DIFFICULTIES = ("easy", "medium", "hard")

SYSTEM_PROMPT = """You are an expert quiz writer.
Respond ONLY with valid JSON. No commentary, no markdown code fences.

Use exactly this schema:
{
  "title": "string",
  "questions": [
    {
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "answer_index": 0,
      "explanation": "string"
    }
  ]
}

Rules:
- Each question has exactly 4 options.
- Exactly one option is correct. answer_index is its 0-based position.
- Distractors must be plausible and similar in length to the correct answer.
- Vary the position of the correct answer across questions.
- explanation is one or two sentences saying why the answer is correct."""


class QuizError(Exception):
    """Raised when a quiz cannot be generated or parsed."""


@dataclass
class Question:
    question: str
    options: list[str]
    answer_index: int
    explanation: str = ""

    def validate(self) -> None:
        if not self.question.strip():
            raise QuizError("Question text is empty.")
        if len(self.options) != OPTIONS_PER_QUESTION:
            raise QuizError(
                f"Expected {OPTIONS_PER_QUESTION} options, got {len(self.options)}."
            )
        if not all(isinstance(o, str) and o.strip() for o in self.options):
            raise QuizError("Every option must be non-empty text.")
        if not 0 <= self.answer_index < OPTIONS_PER_QUESTION:
            raise QuizError(f"answer_index {self.answer_index} is out of range.")


@dataclass
class Quiz:
    title: str
    questions: list[Question] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_json(raw: str) -> dict:
    """Parse JSON, tolerating accidental code fences or surrounding text."""
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise QuizError("Model response was not valid JSON.") from None


def parse_quiz(raw: str) -> Quiz:
    """Convert a raw model response into a validated Quiz."""
    data = _extract_json(raw)

    title = data.get("title")
    questions_data = data.get("questions")
    if not isinstance(title, str) or not title.strip():
        raise QuizError("Quiz is missing a title.")
    if not isinstance(questions_data, list) or not questions_data:
        raise QuizError("Quiz contains no questions.")

    questions = []
    for item in questions_data:
        try:
            q = Question(
                question=item["question"],
                options=list(item["options"]),
                answer_index=int(item["answer_index"]),
                explanation=str(item.get("explanation", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise QuizError(f"Malformed question: {exc}") from exc
        q.validate()
        questions.append(q)

    return Quiz(title=title.strip(), questions=questions)


class QuizGenerator:
    """Generates quizzes using the Anthropic Messages API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        client: Anthropic | None = None,
    ):
        self.model = model
        self.client = client or Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )

    def generate(
        self,
        topic: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        retries: int = 1,
    ) -> Quiz:
        if not topic.strip():
            raise QuizError("Topic must not be empty.")
        if num_questions < 1:
            raise QuizError("Number of questions must be at least 1.")
        if difficulty not in DIFFICULTIES:
            raise QuizError(f"Difficulty must be one of {DIFFICULTIES}.")

        prompt = (
            f"Create a {difficulty} multiple-choice quiz with exactly "
            f"{num_questions} questions about: {topic.strip()}"
        )

        last_error: QuizError | None = None
        for _ in range(retries + 1):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = "".join(b.text for b in response.content if b.type == "text")
            try:
                return parse_quiz(raw)
            except QuizError as exc:
                last_error = exc  # retry on malformed output

        raise QuizError(f"Failed to generate a valid quiz: {last_error}")
