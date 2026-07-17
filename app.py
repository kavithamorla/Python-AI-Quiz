from __future__ import annotations

import json
import random
from pathlib import Path

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
LEADERBOARD_FILE = DATA_DIR / "leaderboard.json"

app = Flask(__name__)


QUESTION_BANK = [
    {
        "question": "What is the output of this code?\n\nx = 5\nprint(x * 3)",
        "options": ["8", "10", "15", "53"],
        "correct_answer": "15",
        "explanation": "The value of x is multiplied by 3, so 5 * 3 = 15.",
    },
    {
        "question": "What does len(['a', 'b', 'c']) return?",
        "options": ["2", "3", "4", "'a', 'b', 'c'"],
        "correct_answer": "3",
        "explanation": "len() returns the number of items in the list.",
    },
    {
        "question": "Which keyword is used to define a function in Python?",
        "options": ["func", "define", "def", "lambda"],
        "correct_answer": "def",
        "explanation": "Python functions are defined with the def keyword.",
    },
    {
        "question": "What is the output?\n\nprint(type([]))",
        "options": ["<class 'tuple'>", "<class 'list'>", "<class 'set'>", "<class 'dict'>"],
        "correct_answer": "<class 'list'>",
        "explanation": "Square brackets create a list.",
    },
    {
        "question": "What is the result of 10 // 3?",
        "options": ["3.33", "3", "4", "Error"],
        "correct_answer": "3",
        "explanation": "// performs floor division and returns the integer quotient.",
    },
    {
        "question": "Which collection type is unordered and mutable?",
        "options": ["tuple", "list", "set", "str"],
        "correct_answer": "set",
        "explanation": "Sets are mutable and do not preserve order.",
    },
    {
        "question": "What is printed?\n\nprint('Py' + 'thon')",
        "options": ["Py thon", "Python", "Py+thon", "Error"],
        "correct_answer": "Python",
        "explanation": "The + operator concatenates strings.",
    },
    {
        "question": "What is the output?\n\nnums = [1, 2, 3]\nnums.append(4)\nprint(nums)",
        "options": ["[1, 2, 3]", "[1, 2, 3, 4]", "(1, 2, 3, 4)", "[4, 1, 2, 3]"],
        "correct_answer": "[1, 2, 3, 4]",
        "explanation": "append() adds an element to the end of the list.",
    },
    {
        "question": "Which statement is used to handle exceptions?",
        "options": ["catch", "try/except", "handle/error", "throw/catch"],
        "correct_answer": "try/except",
        "explanation": "Python uses try/except blocks for exception handling.",
    },
    {
        "question": "What is the output?\n\nprint(bool(''))",
        "options": ["True", "False", "None", "Error"],
        "correct_answer": "False",
        "explanation": "An empty string is falsy in Python.",
    },
    {
        "question": "What does range(3) generate?",
        "options": ["1, 2, 3", "0, 1, 2", "0, 1, 2, 3", "3, 4, 5"],
        "correct_answer": "0, 1, 2",
        "explanation": "range(3) starts at 0 and ends before 3.",
    },
    {
        "question": "What is the output?\n\nprint(2 ** 4)",
        "options": ["6", "8", "16", "24"],
        "correct_answer": "16",
        "explanation": "** is the exponent operator.",
    },
    {
        "question": "Which data type uses key-value pairs?",
        "options": ["list", "tuple", "dict", "set"],
        "correct_answer": "dict",
        "explanation": "Dictionaries store values with associated keys.",
    },
    {
        "question": "What is the output?\n\ns = 'hello'\nprint(s[1])",
        "options": ["h", "e", "l", "o"],
        "correct_answer": "e",
        "explanation": "Python strings are zero-indexed.",
    },
    {
        "question": "Which method removes and returns the last item from a list?",
        "options": ["delete()", "remove()", "pop()", "clear()"],
        "correct_answer": "pop()",
        "explanation": "pop() removes the last item by default and returns it.",
    },
    {
        "question": "What is the output?\n\nprint('5' * 2)",
        "options": ["10", "55", "5 5", "Error"],
        "correct_answer": "55",
        "explanation": "Strings repeat when multiplied by an integer.",
    },
    {
        "question": "What does this return?\n\nsorted([3, 1, 2])",
        "options": ["[3, 1, 2]", "[1, 2, 3]", "(1, 2, 3)", "Error"],
        "correct_answer": "[1, 2, 3]",
        "explanation": "sorted() returns a new sorted list.",
    },
    {
        "question": "What is the output?\n\nprint(7 % 3)",
        "options": ["1", "2", "3", "4"],
        "correct_answer": "1",
        "explanation": "% returns the remainder.",
    },
    {
        "question": "Which loop is best when you know the number of iterations?",
        "options": ["while", "for", "do/while", "repeat"],
        "correct_answer": "for",
        "explanation": "for loops are commonly used when the number of iterations is known.",
    },
    {
        "question": "What is the output?\n\nprint('Python'.lower())",
        "options": ["python", "PYTHON", "Python", "Error"],
        "correct_answer": "python",
        "explanation": "lower() converts a string to lowercase.",
    },
]


def load_leaderboard() -> list[dict]:
    if not LEADERBOARD_FILE.exists():
        return []
    try:
        return json.loads(LEADERBOARD_FILE.read_text())
    except json.JSONDecodeError:
        return []


def save_leaderboard(entries: list[dict]) -> None:
    LEADERBOARD_FILE.write_text(json.dumps(entries, indent=2))


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/leaderboard")
def leaderboard():
    entries = sorted(load_leaderboard(), key=lambda item: (item.get("score", 0), item.get("percentage", 0)), reverse=True)
    return render_template("leaderboard.html", entries=entries)


@app.post("/api/generate-quiz")
def generate_quiz():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "Player").strip() or "Player"
    questions = random.sample(QUESTION_BANK, k=10)
    return jsonify(
        {
            "quiz_title": "Premium Python Quiz",
            "name": name,
            "questions": questions,
        }
    )


@app.post("/api/leaderboard")
def update_leaderboard():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "Anonymous").strip() or "Anonymous"
    score = int(payload.get("score") or 0)
    total = max(1, int(payload.get("total") or 1))
    percentage = float(payload.get("percentage") or 0)

    entries = load_leaderboard()
    entries.append(
        {
            "name": name,
            "score": score,
            "total": total,
            "percentage": percentage,
        }
    )
    entries = sorted(entries, key=lambda item: (item.get("score", 0), item.get("percentage", 0)), reverse=True)[:50]
    save_leaderboard(entries)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
