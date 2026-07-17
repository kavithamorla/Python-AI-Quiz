# Python Quiz (Flask + Groq API)

A hard-difficulty, 20-question Python quiz app. Each participant enters their name,
gets a fresh AI-generated set of questions (via Groq), and has 20 minutes to finish.

## Features
- Fixed topic (Python) and difficulty (Hard) — no setup needed beyond entering a name
- 20 multiple-choice questions, 4 options each, generated live by a Groq-hosted LLM
- Each participant gets a different question set (randomized subtopic focus + seed)
- 20-minute countdown timer with auto-submit when time runs out
- Automatic scoring: score, percentage, correct/wrong counts
- Leaderboard at `/leaderboard` with name and marks table
- Full review for every wrong answer: your answer, the correct answer, and an explanation
- Scores stored in `leaderboard.json` (file-based, no database required)

## Project Structure
```
quiz-app/
├── app.py                 # Flask backend + Groq API integration
├── requirements.txt       # Python dependencies
├── vercel.json             # Vercel deployment config
├── .env.example            # Copy to .env and add your Groq API key
├── templates/
│   └── index.html          # Main page
└── static/
    ├── style.css            # Styling
    └── script.js            # Frontend logic (timer, fetch, render, grade)
```

## Setup

### 1. Enter the project folder
```bash
cd quiz-app
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key
```bash
cp .env.example .env
```
Then edit `.env` and paste your key (get a free one at https://console.groq.com/keys):
```
GROQ_API_KEY=your_actual_key_here
```

### 5. Run the app
```bash
python app.py
```
Visit **http://localhost:5000** in your browser.

## How It Works
1. The participant enters their name and starts the quiz.
2. The frontend sends the name to `POST /api/generate-quiz`.
3. The backend builds a hard-difficulty Python prompt — randomly emphasizing a subset
   of subtopics (decorators, GIL, generators, asyncio, etc.) and a per-attempt random
   seed — and calls the Groq API asking for strict JSON output.
4. The backend validates the JSON shape (20 questions, 4 options each, correct answer
   present) before returning it to the frontend.
5. The frontend renders the quiz and starts a 20-minute countdown.
6. On submit (manual or automatic on timeout), answers are graded client-side and a
   results screen shows the score, percentage, and a full breakdown of wrong answers.

## Configuration
Override the model or port in `.env`:
```
GROQ_MODEL=llama-3.3-70b-versatile
PORT=5000
```

## Deploying to Vercel
This repo includes a `vercel.json` that routes all requests to the Flask app via
`@vercel/python` and serves `/static/*` directly.

1. Push this project to a GitHub repository.
2. Import the repo in Vercel.
3. In the Vercel project's Environment Variables, add `GROQ_API_KEY` (and optionally
   `GROQ_MODEL`).
4. Deploy.

Note: Vercel's Python runtime is serverless — each request is a fresh function
invocation, so keep the app stateless (this app already is, since quizzes are generated
and graded per-request/client-side).

## Notes
- If the model occasionally returns malformed JSON or an unexpected shape, the backend
  returns a 502 error asking to retry — the frontend surfaces this on the name screen.
- Quizzes and scores are not persisted; refreshing clears state.
