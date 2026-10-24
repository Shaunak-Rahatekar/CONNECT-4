# Real-Time Python-Powered Connect-4
## AI Game & Algorithm Analysis Platform

A browser-based Connect-4 game with Python AI opponents and an interactive
algorithm performance dashboard.  Built for the **Design and Analysis of
Algorithms (DAA)** course.

---

## Current Status

**Milestone 1 — Project Initialization** ✅

- Flask web application running
- 6×7 game board with responsive dark-theme UI
- Python game engine (`Board`, `Rules`) fully tested
- 64 pytest tests — all passing

---

## Features (planned across milestones)

- ♟ Human vs Human and Human vs AI gameplay
- 🤖 Greedy, Minimax, Alpha-Beta, and Memoized AI strategies
- 🔢 Configurable search depth (1–7)
- 📊 Real-time AI decision information panel
- 📈 Algorithm performance comparison dashboard
- 🧪 Complete pytest suite

---

## Setup

```powershell
# Clone
git clone https://github.com/Shaunak-Rahatekar/CONNECT-4.git
cd CONNECT-4

# Virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows PowerShell

# Dependencies
pip install -r requirements.txt
```

## Run

```powershell
python app.py
# then open http://127.0.0.1:5000
```

## Test

```powershell
pytest tests/ -v
```

---

## Project Structure

```
CONNECT-4/
├── app.py              Flask entry point and API routes
├── game/               Game engine (Flask-independent)
│   ├── board.py        Board state, gravity, undo
│   └── rules.py        Win detection, move application
├── algorithms/         AI modules (added in Prompts 3-6)
├── benchmarks/         Performance runner (added in Prompt 7)
├── tests/              pytest test suite
├── templates/          Jinja2 HTML templates
├── static/             CSS and JavaScript
└── docs/               Technical documentation
```

---

## Documentation

Full technical documentation, DAA concept mapping, complexity analysis,
and development logs:

📄 [`docs/PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md)

---

## Tech Stack

Python 3.13 · Flask 3.1 · HTML5 · CSS3 · JavaScript · pytest · Chart.js (Prompt 7)
