const setupSection = document.getElementById("setup-section");
const loadingSection = document.getElementById("loading-section");
const quizSection = document.getElementById("quiz-section");
const resultsSection = document.getElementById("results-section");

const startForm = document.getElementById("start-form");
const answersForm = document.getElementById("answers-form");
const quizTitleEl = document.getElementById("quiz-title");
const quizTakerNameEl = document.getElementById("quiz-taker-name");
const errorMsg = document.getElementById("error-msg");
const timerEl = document.getElementById("timer");
const progressFillEl = document.getElementById("progress-bar-fill");

const submitQuizBtn = document.getElementById("submit-quiz-btn");
const retryBtn = document.getElementById("retry-btn");

const QUIZ_DURATION_SECONDS = 20 * 60; // 20 minutes

let currentQuiz = null;
let currentName = "";
let timerInterval = null;
let secondsRemaining = QUIZ_DURATION_SECONDS;
let hasSubmitted = false;

function showSection(section) {
  [setupSection, loadingSection, quizSection, resultsSection].forEach(s => s.classList.add("hidden"));
  section.classList.remove("hidden");
}

function showError(message) {
  errorMsg.textContent = message;
  errorMsg.classList.remove("hidden");
}

function clearError() {
  errorMsg.classList.add("hidden");
  errorMsg.textContent = "";
}

startForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();

  const name = document.getElementById("name").value.trim();
  if (!name) {
    showError("Please enter your name.");
    return;
  }
  currentName = name;

  showSection(loadingSection);

  try {
    const res = await fetch("/api/generate-quiz", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Something went wrong generating the quiz.");
    }

    currentQuiz = data;
    hasSubmitted = false;
    renderQuiz(data);
    showSection(quizSection);
    startTimer();
  } catch (err) {
    showSection(setupSection);
    showError(err.message);
  }
});

function renderQuiz(quiz) {
  quizTitleEl.textContent = quiz.quiz_title || "Python Quiz (Hard)";
  quizTakerNameEl.textContent = `Good luck, ${currentName}!`;
  answersForm.innerHTML = "";

  quiz.questions.forEach((q, index) => {
    const block = document.createElement("div");
    block.className = "question-block";

    const qText = document.createElement("div");
    qText.className = "question-text";
    qText.textContent = `${index + 1}. ${q.question}`;
    block.appendChild(qText);

    q.options.forEach((opt, optIndex) => {
      const label = document.createElement("label");
      label.className = "option-label";

      const input = document.createElement("input");
      input.type = "radio";
      input.name = `question-${index}`;
      input.value = opt;
      input.id = `q${index}-opt${optIndex}`;

      label.appendChild(input);
      label.appendChild(document.createTextNode(opt));
      block.appendChild(label);
    });

    answersForm.appendChild(block);
  });
}

function startTimer() {
  secondsRemaining = QUIZ_DURATION_SECONDS;
  updateTimerDisplay();
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    secondsRemaining--;
    updateTimerDisplay();
    if (secondsRemaining <= 0) {
      clearInterval(timerInterval);
      if (!hasSubmitted) {
        gradeQuiz(currentQuiz, true);
      }
    }
  }, 1000);
}

function updateTimerDisplay() {
  const clamped = Math.max(0, secondsRemaining);
  const mins = Math.floor(clamped / 60).toString().padStart(2, "0");
  const secs = (clamped % 60).toString().padStart(2, "0");
  timerEl.textContent = `${mins}:${secs}`;

  const pctElapsed = 1 - clamped / QUIZ_DURATION_SECONDS;
  progressFillEl.style.width = `${Math.min(100, Math.max(0, pctElapsed * 100))}%`;

  timerEl.classList.toggle("timer-warning", clamped <= 120 && clamped > 0);
  timerEl.classList.toggle("timer-expired", clamped <= 0);
}

submitQuizBtn.addEventListener("click", () => {
  if (!currentQuiz || hasSubmitted) return;
  gradeQuiz(currentQuiz, false);
});

function gradeQuiz(quiz, timeExpired) {
  hasSubmitted = true;
  clearInterval(timerInterval);

  const resultsBreakdown = document.getElementById("results-breakdown");
  resultsBreakdown.innerHTML = "";

  let correctCount = 0;
  let wrongCount = 0;

  quiz.questions.forEach((q, index) => {
    const checked = answersForm.querySelector(`[name="question-${index}"]:checked`);
    const userAnswer = checked ? checked.value : "";
    const isCorrect = userAnswer !== "" && userAnswer === q.correct_answer;

    if (isCorrect) {
      correctCount++;
    } else {
      wrongCount++;
    }

    const item = document.createElement("div");
    item.className = `result-item ${isCorrect ? "correct" : "incorrect"}`;

    const status = document.createElement("div");
    status.className = "status";
    status.textContent = isCorrect ? "✔ Correct" : "✘ Incorrect";
    item.appendChild(status);

    const qText = document.createElement("div");
    qText.className = "result-question";
    qText.textContent = `${index + 1}. ${q.question}`;
    item.appendChild(qText);

    if (!isCorrect) {
      const yourAns = document.createElement("div");
      yourAns.className = "your-answer";
      yourAns.textContent = `Your answer: ${userAnswer || "(no answer)"}`;
      item.appendChild(yourAns);

      const correctAns = document.createElement("div");
      correctAns.className = "correct-answer";
      correctAns.textContent = `Correct answer: ${q.correct_answer}`;
      item.appendChild(correctAns);

      if (q.explanation) {
        const expl = document.createElement("div");
        expl.className = "explanation";
        expl.textContent = `Explanation: ${q.explanation}`;
        item.appendChild(expl);
      }
    }

    resultsBreakdown.appendChild(item);
  });

  const total = quiz.questions.length;
  const percentage = Math.round((correctCount / total) * 1000) / 10;

  document.getElementById("results-name").textContent = timeExpired
    ? `${currentName} — time's up! Here's how you did:`
    : `${currentName}, here's how you did:`;
  document.getElementById("stat-score").textContent = `${correctCount}/${total}`;
  document.getElementById("stat-percentage").textContent = `${percentage}%`;
  document.getElementById("stat-correct").textContent = correctCount;
  document.getElementById("stat-wrong").textContent = wrongCount;

  showSection(resultsSection);
}

retryBtn.addEventListener("click", () => {
  currentQuiz = null;
  hasSubmitted = false;
  startForm.reset();
  clearInterval(timerInterval);
  showSection(setupSection);
});
