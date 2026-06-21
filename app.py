from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
import google.generativeai as genai
from twilio.rest import Client


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-1.5-flash"
FALLBACK_MODELS = ("gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-pro")

app = Flask(__name__)


VISUAL_INSTRUCTIONS = (
    "Always include a markdown section exactly titled 'Visual Explanation'. "
    "This section is mandatory for every answer. If the problem has arrays, strings, "
    "linked lists, pointers, indexes, recursion, stacks, queues, trees, graphs, API flow, "
    "database flow, or state changes, use simple ASCII diagrams. Examples: "
    "array indexes like index: 0 1 2 and arr: [2][7][11], pointers like L -> and R ->, "
    "step tables, recursion call stack, or Frontend -> Backend -> Database flow. "
    "Explain pointers like a child: say 'finger i is pointing here' or 'left finger moves'. "
    "For arrays, show boxes and where each finger/pointer is looking at each step. "
    "For ML problems, show Dataset -> Clean -> Split -> Train -> Evaluate -> Predict and mark the weak step. "
    "For normal code, show Input -> Logic -> Output and mark where the value first becomes wrong. "
    "If there is no data structure, draw a simple step-by-step flow. Keep diagrams compact "
    "and beginner friendly."
)


def load_env_file() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()
app.secret_key = os.getenv("SECRET_KEY", "dev-debugiq-change-this-secret")


PROMPTS = {
    "debug": (
        "You are a coding mentor for Indian CS students. User gives problem statement, "
        "broken code, and optionally working code. Do: 1) Explain why logic failed in "
        "simple English. 2) If working code provided, explain every difference between "
        "broken and working code. 3) Identify what CS concept they are missing. "
        "4) Repeat full explanation in simple Hinglish, written in Roman script, not Devanagari. "
        "Use common English CS terms like loop, function, array, API, database. Keep everything beginner friendly. "
        "Use short sections with markdown headings. "
        f"{VISUAL_INSTRUCTIONS}"
    ),
    "leetcode": (
        "You are a competitive programming mentor for Indian CS students. User gives a "
        "LeetCode problem. Do in order: 1) Identify algorithmic pattern this tests. "
        "2) Explain step by step how to think through it before writing code. "
        "3) Write clean well commented solution in specified language. "
        "4) Explain every important line in simple English. "
        "5) Give time and space complexity with simple explanation of why. "
        "6) Repeat everything in simple Hinglish, written in Roman script, not Devanagari. "
        "Use common English CS terms like loop, array, recursion, complexity. Be beginner friendly throughout. "
        "Use short sections with markdown headings. Keep the final solution inside a fenced code block. "
        f"{VISUAL_INSTRUCTIONS}"
    ),
    "fullstack": (
        "You are a full-stack debugging expert for Indian CS students. User gives a bug "
        "description and optionally frontend code, backend code, database query, and their "
        "tech stack. Do: 1) Identify which layer the bug is in — frontend, backend, "
        "database, or connection issue. 2) Explain exact cause in simple English. "
        "3) Give step by step fix. 4) Tell them what to watch for next time to avoid this bug. "
        "5) Repeat full explanation in simple Hinglish, written in Roman script, not Devanagari. "
        "Use common English CS terms like frontend, backend, database, API, route, request. Be specific and beginner friendly. "
        "Use short sections with markdown headings. Include a Visual Debug Map section showing "
        "Frontend -> Backend -> Database -> Connection and where the bug likely sits. "
        f"{VISUAL_INSTRUCTIONS}"
    ),
    "ml": (
        "You are an ML debugging mentor for Indian CS students. User gives ML goal, code, "
        "dataset info, metrics/errors, and expected behavior. Do: 1) Explain what the ML code is doing. "
        "2) Find syntax/runtime errors and logical ML errors. 3) Check data leakage, wrong train/test split, "
        "bad preprocessing order, missing values, target/feature mixups, shape mismatch, wrong metric choice, "
        "overfitting/underfitting, class imbalance, and prediction pipeline mistakes. 4) Explain exact fix step by step. "
        "5) Include a section titled 'Corrected ML Code' with one complete corrected code block when code is provided. "
        "6) Explain the missing ML concept in simple words. 7) Repeat in simple Hinglish, Roman script only. "
        "Use common ML terms like feature, label, train, test, accuracy, loss, epoch, model, scaler. "
        "Use short sections with markdown headings. Keep explanations concise but do not cut off corrected code. "
        f"{VISUAL_INSTRUCTIONS}"
    ),
}


def clip_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return (
        text[:limit]
        + "\n\n[DebugIQ note: input was very long, so only the first "
        + str(limit)
        + " characters were sent for faster analysis.]"
    )


def build_prompt(mode: str, payload: dict, language: str = "both") -> str:
    if mode == "debug":
        body = f"""
Problem statement:
{clip_text(payload.get("problemStatement", ""), 2500)}

Broken code:
{clip_text(payload.get("brokenCode", ""), 9000)}

Working code, optional:
{clip_text(payload.get("workingCode", ""), 9000) or "Not provided"}
"""
    elif mode == "leetcode":
        selected_language = payload.get("language", "Auto Detect")
        selected_difficulty = payload.get("difficulty", "Auto Detect")
        language_line = (
            "Auto detect from problem/code. First state the detected language before writing solution."
            if selected_language == "Auto Detect"
            else selected_language
        )
        difficulty_line = (
            "Auto detect from the problem. First state the detected difficulty and why."
            if selected_difficulty == "Auto Detect"
            else selected_difficulty
        )
        body = f"""
Problem statement:
{clip_text(payload.get("leetcodeProblem", ""), 5000)}

Difficulty:
{difficulty_line}

Language:
{language_line}
"""
    elif mode == "fullstack":
        body = f"""
Bug description:
{clip_text(payload.get("bugDescription", ""), 2500)}

Tech stack:
{clip_text(payload.get("techStack", ""), 800) or "Not specified"}

Frontend code/error:
{clip_text(payload.get("frontendIssue", ""), 6000) or "Not provided"}

Backend code/error:
{clip_text(payload.get("backendIssue", ""), 6000) or "Not provided"}

Database query/error:
{clip_text(payload.get("databaseIssue", ""), 4000) or "Not provided"}
"""
    elif mode == "ml":
        body = f"""
ML goal:
{clip_text(payload.get("mlGoal", ""), 2000)}

ML code:
{clip_text(payload.get("mlCode", ""), 9000)}

Dataset info:
{clip_text(payload.get("datasetInfo", ""), 3000) or "Not provided"}

Error, metrics, or weird behavior:
{clip_text(payload.get("mlIssue", ""), 3000) or "Not provided"}

Expected behavior:
{clip_text(payload.get("expectedMlBehavior", ""), 2000) or "Not provided"}
"""
    else:
        raise ValueError("Invalid mode.")

    if language == "english":
        language_instruction = "Write the answer only in simple English."
        format_instruction = "Format the answer directly in markdown. Do not return JSON."
    elif language == "hinglish":
        language_instruction = (
            "Write the answer only in Hinglish using Roman script. Do not use Devanagari. "
            "Use natural words like samjho, yahan, kyun, kaise, but keep CS terms in English."
        )
        format_instruction = "Format the answer directly in markdown. Do not return JSON."
    else:
        language_instruction = (
            "Return both versions in one response: simple English and simple Hinglish. "
            "Hinglish must use Roman script only, not Devanagari. Use common English CS terms."
            " If corrected code is needed, include the complete corrected code in the English part only; "
            "the Hinglish part should explain the same fix without repeating the full code block."
        )
        format_instruction = (
            "Use this exact format, with no text before or after it:\n"
            "<<<ENGLISH>>>\n"
            "English markdown answer here\n"
            "<<<HINGLISH>>>\n"
            "Hinglish markdown answer here"
        )

    return f"""
{PROMPTS[mode]}

{language_instruction}

{format_instruction}
Use clear markdown headings. Keep each line easy to scan.
Use fenced code blocks only for actual code.
You must include a section with this exact heading: ## Visual Explanation

User input:
{body}
"""


def parse_combined_response(text: str) -> dict:
    cleaned = text.strip()

    marker_match = cleaned.split("<<<HINGLISH>>>", 1)
    if len(marker_match) == 2:
        english = marker_match[0].replace("<<<ENGLISH>>>", "").strip()
        hinglish = marker_match[1].strip()
        return {
            "english": english or "No English explanation returned.",
            "hindi": hinglish or english or "No Hinglish explanation returned.",
        }

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        heading_split = split_markdown_languages(text)
        if heading_split:
            return heading_split
        return {
            "english": text.strip(),
            "hindi": text.strip(),
        }

    return {
        "english": str(parsed.get("english") or "No English explanation returned.").strip(),
        "hindi": str(parsed.get("hindi") or "Hindi explanation not returned.").strip(),
    }


def split_markdown_languages(text: str) -> dict | None:
    english_match = text.lower().find("english")
    hinglish_match = text.lower().find("hinglish")
    hindi_match = text.lower().find("hindi")
    second_index = hinglish_match if hinglish_match != -1 else hindi_match

    if english_match == -1 or second_index == -1 or second_index <= english_match:
        return None

    english = text[english_match:second_index].strip()
    hinglish = text[second_index:].strip()
    return {
        "english": english or text.strip(),
        "hindi": hinglish or text.strip(),
    }


def candidate_models() -> list[str]:
    configured = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    models = [configured]
    for fallback in FALLBACK_MODELS:
        if fallback not in models:
            models.append(fallback)
    return models


def generate_with_fallback(prompt: str) -> tuple[str, str]:
    last_error: Exception | None = None
    for model_name in candidate_models():
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.35,
                    "max_output_tokens": 8192,
                },
            )
            return response.text or "", model_name
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            retryable = any(marker in message for marker in ("not found", "unavailable", "503", "429", "quota"))
            if not retryable:
                raise
    raise RuntimeError(f"Gemini request failed for all fallback models. Last error: {last_error}")


def twilio_client() -> Client:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    missing = []
    if not account_sid:
        missing.append("TWILIO_ACCOUNT_SID")
    if not auth_token:
        missing.append("TWILIO_AUTH_TOKEN")
    if missing:
        raise RuntimeError(f"Missing Twilio config: {', '.join(missing)}")
    return Client(account_sid, auth_token)


def verify_service_sid() -> str:
    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")
    if not service_sid:
        raise RuntimeError("Missing Twilio config: TWILIO_VERIFY_SERVICE_SID")
    return service_sid


def normalize_phone(country_code: str, phone: str) -> str:
    country_code = (country_code or "+91").strip().replace(" ", "")
    if country_code and not country_code.startswith("+"):
        country_code = f"+{country_code}"
    phone = (phone or "").strip().replace(" ", "").replace("-", "")

    if phone.startswith("+"):
        return phone

    if phone.startswith("0"):
        phone = phone[1:]

    return f"{country_code}{phone}"


def is_logged_in() -> bool:
    return bool(session.get("verified_phone"))


@app.get("/login")
def login():
    if is_logged_in():
        return redirect(url_for("index"))
    return render_template("login.html")


@app.post("/send-otp")
def send_otp():
    country_code = (request.form.get("country_code") or "+91").strip()
    raw_phone = (request.form.get("phone") or "").strip()
    phone = normalize_phone(country_code, raw_phone)
    if not phone.startswith("+") or len(phone) < 8:
        return render_template(
            "login.html",
            error="Enter a valid phone number.",
            phone=raw_phone,
            country_code=country_code,
        ), 400

    try:
        twilio_client().verify.v2.services(verify_service_sid()).verifications.create(
            to=phone,
            channel="sms",
        )
    except Exception as exc:
        return render_template(
            "login.html",
            error=f"Could not send OTP. {exc}",
            phone=raw_phone,
            country_code=country_code,
        ), 502

    session["pending_phone"] = phone
    return render_template("verify.html", phone=phone)


@app.post("/verify-otp")
def verify_otp():
    phone = session.get("pending_phone")
    code = (request.form.get("code") or "").strip()
    if not phone:
        return redirect(url_for("login"))
    if not code:
        return render_template("verify.html", phone=phone, error="Enter the OTP."), 400

    try:
        check = twilio_client().verify.v2.services(verify_service_sid()).verification_checks.create(
            to=phone,
            code=code,
        )
    except Exception as exc:
        return render_template("verify.html", phone=phone, error=f"Could not verify OTP: {exc}"), 502

    if check.status != "approved":
        return render_template("verify.html", phone=phone, error="Invalid OTP. Try again."), 401

    session.pop("pending_phone", None)
    session["verified_phone"] = phone
    return redirect(url_for("index"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def index():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    if not is_logged_in():
        return jsonify({"error": "Login required."}), 401

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY is missing. Add it to .env or Render environment variables."}), 400

    payload = request.get_json(silent=True) or {}
    mode = payload.get("mode", "debug")

    genai.configure(api_key=api_key)
    try:
        combined_text, model_name = generate_with_fallback(build_prompt(mode, payload))
        parsed = parse_combined_response(combined_text)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify(
        {
            "english": parsed["english"],
            "hindi": parsed["hindi"],
            "model": model_name,
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)
