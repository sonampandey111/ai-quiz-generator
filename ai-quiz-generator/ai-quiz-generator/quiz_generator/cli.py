"""Command-line interface for the quiz generator."""

from __future__ import annotations

import argparse
import json
import sys

from .generator import DIFFICULTIES, Quiz, QuizError, QuizGenerator

LETTERS = "ABCD"


def take_quiz(quiz: Quiz) -> int:
    """Run the quiz interactively and return the number of correct answers."""
    print(f"\n=== {quiz.title} ===")
    score = 0

    for number, q in enumerate(quiz.questions, start=1):
        print(f"\nQ{number}. {q.question}")
        for letter, option in zip(LETTERS, q.options):
            print(f"  {letter}) {option}")

        while True:
            choice = input("Your answer (A-D, or q to quit): ").strip().upper()
            if choice == "Q":
                print(f"\nQuit early. Score so far: {score}/{number - 1}")
                return score
            if choice in LETTERS:
                break
            print("Please enter A, B, C, or D.")

        if LETTERS.index(choice) == q.answer_index:
            score += 1
            print("Correct!")
        else:
            correct = LETTERS[q.answer_index]
            print(f"Incorrect. The answer is {correct}) {q.options[q.answer_index]}")

        if q.explanation:
            print(f"Why: {q.explanation}")

    print(f"\nFinal score: {score}/{len(quiz.questions)}")
    return score


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a multiple-choice quiz on any topic using AI."
    )
    parser.add_argument("topic", help="Subject of the quiz")
    parser.add_argument(
        "-n", "--num", type=int, default=5, help="Number of questions (default: 5)"
    )
    parser.add_argument(
        "-d",
        "--difficulty",
        choices=DIFFICULTIES,
        default="medium",
        help="Difficulty level (default: medium)",
    )
    parser.add_argument(
        "--export", metavar="FILE", help="Save the generated quiz to a JSON file"
    )
    parser.add_argument(
        "--no-take",
        action="store_true",
        help="Generate and export only; don't start the interactive quiz",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        generator = QuizGenerator()
        print(f"Generating a {args.difficulty} quiz on '{args.topic}'...")
        quiz = generator.generate(
            args.topic, num_questions=args.num, difficulty=args.difficulty
        )
    except QuizError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # network, auth, rate-limit errors from the SDK
        print(f"API error: {exc}", file=sys.stderr)
        print("Check that ANTHROPIC_API_KEY is set correctly.", file=sys.stderr)
        return 1

    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(quiz.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"Quiz saved to {args.export}")

    if not args.no_take:
        try:
            take_quiz(quiz)
        except (KeyboardInterrupt, EOFError):
            print("\nQuiz cancelled.")
            return 130

    return 0
