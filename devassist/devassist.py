#!/usr/bin/env python3
"""DevAssist: beginner-friendly Gemini-powered code review CLI."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - exercised before dependencies exist
    genai = None
    types = None


PROMPT = (
    "You are a coding mentor. Review the following code and explain any errors, "
    "bugs, or improvements in simple plain English. Be concise and beginner-friendly. "
    "Avoid motivational filler or long introductions. If you find a bug or error, "
    "include a 'Solution' section with corrected code and a short explanation of what changed."
)

DEFAULT_MODEL = "gemini-3.5-flash"
FALLBACK_MODELS = ("gemini-2.5-flash", "gemini-2.0-flash")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


class Colors:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def colorize(text: str, color: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{color}{text}{Colors.RESET}"


def load_env_file() -> None:
    for env_path in (PROJECT_DIR / ".env", SCRIPT_DIR / ".env"):
        if not env_path.exists():
            continue

        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue

            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="devassist.py",
        description="Review code files with Gemini and explain problems in plain English.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more code files to review.",
    )
    parser.add_argument(
        "--language",
        "-l",
        help="Optional language hint, such as python, java, c, or javascript.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("DEVASSIST_MODEL", DEFAULT_MODEL),
        help=f"Gemini model to use. Defaults to DEVASSIST_MODEL or {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colour-coded terminal output.",
    )
    return parser


def read_code_file(file_path: str) -> tuple[str | None, str | None]:
    path = Path(file_path)

    if not path.exists():
        return None, f"File not found: {file_path}"
    if not path.is_file():
        return None, f"Not a file: {file_path}"

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, f"Could not read {file_path}. Please use a UTF-8 text file."
    except OSError as exc:
        return None, f"Could not read {file_path}: {exc}"

    if not content.strip():
        return None, f"Empty file: {file_path}"

    return content, None


def make_user_message(file_path: str, code: str, language: str | None) -> str:
    language_line = f"Language: {language}" if language else "Language: infer from the file name and code"
    return (
        f"{PROMPT}\n\n"
        f"File: {file_path}\n"
        f"{language_line}\n\n"
        "Code:\n"
        "```text\n"
        f"{code}\n"
        "```"
    )


def stream_review(
    client,
    file_path: str,
    code: str,
    language: str | None,
    model: str,
) -> None:
    message = make_user_message(file_path, code, language)
    last_error: Exception | None = None

    for candidate in candidate_models(model):
        for attempt in range(3):
            try:
                response = client.models.generate_content_stream(
                    model=candidate,
                    contents=message,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT,
                        max_output_tokens=1200,
                    ),
                )
                for chunk in response:
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                return
            except Exception as exc:
                last_error = exc
                if not is_retryable_error(exc):
                    raise
                time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"Gemini is temporarily unavailable after retries: {last_error}")


def candidate_models(model: str) -> list[str]:
    models = [model]
    for fallback in FALLBACK_MODELS:
        if fallback not in models:
            models.append(fallback)
    return models


def is_retryable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "503",
            "unavailable",
            "high demand",
            "temporarily",
            "timeout",
            "rate limit",
            "429",
        )
    )


def main() -> int:
    load_env_file()
    parser = build_parser()
    args = parser.parse_args()
    use_color = not args.no_color and sys.stdout.isatty()

    if genai is None or types is None:
        print(
            colorize("Error: google-genai is not installed.", Colors.RED, use_color),
            file=sys.stderr,
        )
        print("Install it with: pip install google-genai", file=sys.stderr)
        return 1

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(
            colorize("Error: GEMINI_API_KEY is missing.", Colors.RED, use_color),
            file=sys.stderr,
        )
        print("Set it first, for example: export GEMINI_API_KEY='your-api-key'", file=sys.stderr)
        return 1

    client = genai.Client(api_key=api_key)
    had_error = False

    for index, file_path in enumerate(args.files, start=1):
        code, error = read_code_file(file_path)
        if error:
            had_error = True
            print(colorize(f"Error: {error}", Colors.RED, use_color), file=sys.stderr)
            continue

        if len(args.files) > 1:
            heading = f"\n[{index}/{len(args.files)}] Review for {file_path}"
        else:
            heading = f"Review for {file_path}"

        print(colorize(heading, Colors.BOLD + Colors.CYAN, use_color))
        print(colorize("-" * len(heading.strip()), Colors.BLUE, use_color))

        try:
            stream_review(client, file_path, code or "", args.language, args.model)
            print()
        except Exception as exc:  # The SDK exposes several API/network exceptions.
            had_error = True
            print(colorize(f"\nError while reviewing {file_path}: {exc}", Colors.RED, use_color), file=sys.stderr)

    if had_error:
        return 1

    print(colorize("\nDone.", Colors.GREEN, use_color))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
