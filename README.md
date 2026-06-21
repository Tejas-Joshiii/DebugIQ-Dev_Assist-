# DebugIQ

The complete learning and debugging tool for Indian CS students: debug code, learn LeetCode approaches, or diagnose full-stack bugs with English and Hinglish explanations.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web_App-000000?logo=flask&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-Flash-4285F4?logo=google&logoColor=white)
![Twilio](https://img.shields.io/badge/Twilio-OTP_Login-F22F46?logo=twilio&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=black)

## Live Demo

Render URL: `Add your Render live URL here after deployment`

## What Problem It Solves

Most beginners know their code is wrong, but they do not know why. DebugIQ explains the actual mistake, the missing CS concept, the right approach, and the fix in simple English and Hinglish.

## Modes

### 1. Debug My Code

Inputs:
- Problem statement
- Broken code
- Working code optional

Outputs:
- Why your logic failed
- Code diff explained when working code is provided
- Missing CS concept
- Visual walkthrough with simple arrows, array indexes, and pointer-style diagrams
- Dedicated Visual Explanation section in every answer
- Hinglish explanation toggle

![Debug mode](docs/screenshots/debug-mode.svg)

### 2. Teach Me LeetCode

Inputs:
- Problem statement
- Difficulty, with Auto Detect support
- Language, with Auto Detect support

Outputs:
- Pattern or concept tested
- Step-by-step thinking before code
- Visual approach with dry-run tables, array diagrams, pointer/index movement, or recursion stack
- Dedicated Visual Explanation section in every answer
- Clean commented solution
- Line-by-line explanation
- Time and space complexity
- Full Hinglish explanation

![LeetCode mode](docs/screenshots/leetcode-mode.svg)

### 3. FullStack Debugger

Inputs:
- Bug description
- Frontend code/error optional
- Backend code/error optional
- Database query/error optional
- Tech stack

Outputs:
- Which layer has the bug: frontend, backend, database, or connection
- Exact cause
- Step-by-step fix
- Visual debug map across frontend, backend, database, and connection
- Dedicated Visual Explanation section in every answer
- What to check next time
- Hinglish explanation toggle

![FullStack mode](docs/screenshots/fullstack-mode.svg)

### 4. ML Debugger

Inputs:
- ML goal
- ML code
- Dataset info
- Error, metrics, or weird behavior
- Expected behavior optional

Outputs:
- What the ML code is doing
- Runtime and logical ML mistakes
- Data leakage, preprocessing, split, shape, metric, overfitting, and imbalance checks
- Step-by-step fix
- Missing ML concept
- Visual Explanation for data/model pipeline
- Hinglish explanation

## Why DebugIQ Is Different

| Feature | ChatGPT | DebugIQ |
|---|---:|---:|
| Knows what code should do | No | Yes |
| Teaches approach first | No | Yes |
| Explains code diff | No | Yes |
| Identifies which layer bug is in | No | Yes |
| Hinglish explanation | No | Yes |
| Powered by Google Gemini | No | Yes |
| Built for Indian CS students | No | Yes |

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Flask
- AI: Gemini Flash via `google-generativeai`
- Authentication: Twilio Verify OTP
- Deployment: Render

## Run Locally

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Create `.env`:

```text
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
SECRET_KEY=replace-with-a-long-random-secret
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_VERIFY_SERVICE_SID=your_twilio_verify_service_sid
```

DebugIQ defaults to `gemini-1.5-flash` for faster responses and can fall back to other configured Gemini models.

Run:

```bash
.venv/bin/python app.py
```

Open:

```text
http://127.0.0.1:8000
```

## Deploy on Render

1. Push this repo to GitHub.
2. Create a new Render Web Service.
3. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Add environment variables:
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL=gemini-1.5-flash`
   - `SECRET_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_VERIFY_SERVICE_SID`
5. Deploy and paste the live URL in this README.

## Twilio OTP Setup

1. Create a Twilio account.
2. Open Twilio Verify.
3. Create a Verify Service.
4. Copy the Verify Service SID.
5. Add the Account SID, Auth Token, and Verify Service SID to `.env` locally and Render environment variables in production.

## Resume Bullet

Built DebugIQ, a Flask web app with 4 modes: code debugger, LeetCode approach teacher, full-stack bug diagnoser, and ML debugger, powered by Gemini with English and Hinglish explanations; deployed live on Render.
