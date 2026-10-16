"""Offline tests for quiz parsing and validation (no API key required)."""

import json
import unittest

from quiz_generator.generator import QuizError, parse_quiz

VALID_QUIZ = {
    "title": "Basics",
    "questions": [
        {
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "answer_index": 1,
            "explanation": "2 + 2 equals 4.",
        }
    ],
}


class ParseQuizTests(unittest.TestCase):
    def test_parses_valid_json(self):
        quiz = parse_quiz(json.dumps(VALID_QUIZ))
        self.assertEqual(quiz.title, "Basics")
        self.assertEqual(len(quiz.questions), 1)
        self.assertEqual(quiz.questions[0].answer_index, 1)

    def test_strips_code_fences(self):
        raw = "```json\n" + json.dumps(VALID_QUIZ) + "\n```"
        self.assertEqual(len(parse_quiz(raw).questions), 1)

    def test_extracts_json_from_surrounding_text(self):
        raw = "Here is your quiz: " + json.dumps(VALID_QUIZ) + " Enjoy!"
        self.assertEqual(parse_quiz(raw).title, "Basics")

    def test_rejects_non_json(self):
        with self.assertRaises(QuizError):
            parse_quiz("this is not json")

    def test_rejects_wrong_option_count(self):
        bad = json.loads(json.dumps(VALID_QUIZ))
        bad["questions"][0]["options"] = ["3", "4"]
        with self.assertRaises(QuizError):
            parse_quiz(json.dumps(bad))

    def test_rejects_out_of_range_answer(self):
        bad = json.loads(json.dumps(VALID_QUIZ))
        bad["questions"][0]["answer_index"] = 7
        with self.assertRaises(QuizError):
            parse_quiz(json.dumps(bad))

    def test_rejects_missing_title(self):
        bad = {"questions": VALID_QUIZ["questions"]}
        with self.assertRaises(QuizError):
            parse_quiz(json.dumps(bad))

    def test_rejects_empty_questions(self):
        with self.assertRaises(QuizError):
            parse_quiz(json.dumps({"title": "Empty", "questions": []}))


if __name__ == "__main__":
    unittest.main()
