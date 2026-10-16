# AI Quiz Generator

Generate multiple-choice quizzes on any topic using the Anthropic API, then take them in your terminal and get your score.

## Features

- Generate quizzes on any topic with a chosen number of questions and difficulty
- Structured JSON output, validated before use
- Interactive quiz mode with instant feedback and explanations
- Export quizzes to JSON for reuse
- Unit tests for parsing and validation (no API key needed)

## Project structure

```
ai-quiz-generator/
├── main.py                    # Entry point
├── quiz_generator/
│   ├── __init__.py
│   ├── generator.py           # API calls, parsing, validation
│   └── cli.py                 # Command-line interface
├── tests/
│   └── test_parsing.py        # Offline tests
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Get an API key from https://console.anthropic.com/

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set your API key:

   ```bash
   export ANTHROPIC_API_KEY="your_key_here"    # Windows PowerShell: $env:ANTHROPIC_API_KEY="..."
   ```

   Optionally choose a model with `QUIZ_MODEL` (defaults to `claude-haiku-5-5`).

## Usage

Take a quiz on a topic:

```bash
python main.py "World War II"
```

Options:

```bash
python main.py "Python decorators" -n 10 -d hard
python main.py "Photosynthesis" --export photosynthesis_quiz.json
```

| Flag | Description | Default |
|------|-------------|---------|
| `topic` | Subject of the quiz | required |
| `-n, --num` | Number of questions | 5 |
| `-d, --difficulty` | `easy`, `medium`, or `hard` | medium |
| `--export FILE` | Save the generated quiz as JSON | none |

## Running tests

```bash
python -m unittest discover tests
```

## How it works

1. `QuizGenerator.generate()` sends a system prompt that requires JSON output matching a fixed schema.
2. The response is parsed and validated (4 options per question, a valid answer index, non-empty text).
3. If the model returns malformed output, the generator raises a clear error instead of failing silently.
4. The CLI runs the quiz interactively and reports the final score.

## Extending

- **Web UI:** wrap `QuizGenerator` in a Flask or FastAPI endpoint and return `quiz.to_dict()`.
- **Other question types:** extend `Question` and the JSON schema in `SYSTEM_PROMPT`.
- **Caching:** save exported JSON files and reload them instead of calling the API again.
