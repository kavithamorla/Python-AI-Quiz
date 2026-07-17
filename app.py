import os
import json
import re
import random
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Model to use for generation. Change if Groq deprecates this model.
MODEL_NAME = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Fixed quiz configuration
TOPIC = "Python"
DIFFICULTY = "hard"
NUM_QUESTIONS = 20

# Pool of Python subtopics used to vary question focus between participants
SUBTOPIC_POOL = [
    "decorators and closures",
    "generators and iterators",
    "the Global Interpreter Lock (GIL) and concurrency",
    "context managers and the `with` statement",
    "metaclasses and descriptors",
    "memory management, reference counting, and garbage collection",
    "exception handling and custom exceptions",
    "list/dict/set comprehensions and generator expressions",
    "the `itertools` and `functools` modules",
    "asyncio and coroutines",
    "type hints, `typing`, and static analysis",
    "object-oriented design: MRO, multiple inheritance, `super()`",
    "mutable vs immutable types and object identity",
    "scoping rules (LEGB) and namespaces",
    "magic/dunder methods and operator overloading",
    "string formatting, encoding, and Unicode handling",
    "file I/O, serialization, and the `pickle`/`json` modules",
    "performance: time/space complexity of built-in operations",
    "the standard library: `collections`, `heapq`, `bisect`",
    "packaging, virtual environments, and imports",
    "slicing, unpacking, and argument passing (*args/**kwargs)",
    "properties, class methods, static methods",
    "error-prone Python gotchas (mutable default args, late binding closures)",
    "regular expressions with the `re` module",
]


def build_prompt(seed_subtopics, variation_token):
    """Builds the instruction prompt sent to the Groq LLM for a hard, unique Python quiz."""
    subtopics_str = ", ".join(seed_subtopics)
    return f"""You are an expert Python instructor and quiz generation engine writing a
CHALLENGING, HARD-DIFFICULTY multiple-choice quiz for advanced/intermediate-to-advanced
Python programmers. Generate the quiz strictly as JSON.

Topic: Python (general language + standard library, hard difficulty)
Number of questions: {NUM_QUESTIONS}
Question type: multiple_choice (exactly 4 options each, exactly 1 correct)
Emphasize these subtopics across the questions (spread them out, don't repeat the same
subtopic too many times): {subtopics_str}
Variation seed (use only to encourage a unique, non-repeating set of questions — do not
mention it anywhere in the output): {variation_token}

Rules for question quality:
- Every question must require real understanding, careful reasoning, or knowledge of subtle
  Python behavior — not something answerable by guessing or surface-level recall.
- Favor "what does this code output", "what is the correct behavior", "which statement is
  true", and precise conceptual questions over trivia.
- All 4 options must be plausible to someone who half-knows the topic (strong distractors);
  avoid options that are obviously wrong or silly.
- Do not repeat the same question or the same underlying concept twice in this quiz.
- Keep each question self-contained (include any code snippet directly in the "question"
  field, using \\n for newlines).
- The explanation must be concise (1-3 sentences) and must clearly justify why the correct
  answer is correct.

Rules for output format:
- Return ONLY valid JSON, no markdown fences, no extra commentary, no text outside the JSON.
- JSON must follow this exact schema:

{{
  "quiz_title": "string",
  "questions": [
    {{
      "question": "string",
      "options": ["option A text", "option B text", "option C text", "option D text"],
      "correct_answer": "must exactly match one of the 4 option strings",
      "explanation": "short explanation of why the correct answer is correct"
    }}
  ]
}}

- There must be exactly {NUM_QUESTIONS} questions, each with exactly 4 options.
- correct_answer must exactly match one of that question's options (character-for-character).
"""


def extract_json(text):
    """Extracts a JSON object from the model's raw text response."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def validate_quiz(quiz_json):
    """Basic structural validation so malformed model output doesn't reach the client."""
    if not isinstance(quiz_json, dict):
        raise ValueError("Quiz payload is not an object.")
    questions = quiz_json.get("questions")
    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("Quiz has no questions.")
    for q in questions:
        if not isinstance(q, dict):
            raise ValueError("Malformed question entry.")
        if not q.get("question") or not isinstance(q.get("options"), list):
            raise ValueError("Question missing text or options.")
        if len(q["options"]) != 4:
            raise ValueError("Question does not have exactly 4 options.")
        if q.get("correct_answer") not in q["options"]:
            raise ValueError("correct_answer does not match any option.")
    return quiz_json


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate-quiz", methods=["POST"])
def generate_quiz():
    if client is None:
        return jsonify({
            "error": "GROQ_API_KEY is not configured on the server. "
                     "Set it in a .env file or as an environment variable."
        }), 500

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "Name is required."}), 400

    seed_subtopics = random.sample(SUBTOPIC_POOL, k=min(10, len(SUBTOPIC_POOL)))
    variation_token = f"{name}-{random.randint(100000, 999999)}"

    prompt = build_prompt(seed_subtopics, variation_token)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You output strict JSON only, matching the requested schema."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=6000,
        )
        raw_text = completion.choices[0].message.content
        quiz_json = extract_json(raw_text)
        quiz_json = validate_quiz(quiz_json)
        quiz_json.setdefault("quiz_title", f"Python Quiz (Hard) — {name}")
        return jsonify(quiz_json)

    except json.JSONDecodeError:
        return jsonify({
            "error": "The AI response could not be parsed as JSON. Please try again."
        }), 502
    except ValueError as e:
        return jsonify({"error": f"The AI response was malformed: {str(e)}. Please try again."}), 502
    except Exception as e:
        return jsonify({"error": f"Groq API error: {str(e)}"}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
