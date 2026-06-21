#!/usr/bin/env python3
"""Local web app for DevAssist."""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import devassist


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DevAssist</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #667085;
      --line: #d8dee8;
      --accent: #176b87;
      --accent-strong: #0e536a;
      --danger: #b42318;
      --code: #111827;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }
    header {
      height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }
    h1 {
      margin: 0;
      font-size: 24px;
      letter-spacing: 0;
    }
    .status {
      min-width: 190px;
      text-align: right;
      color: var(--muted);
      font-size: 14px;
    }
    main {
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      gap: 18px;
      padding: 18px;
      min-height: 0;
    }
    aside, section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 0;
    }
    aside {
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    section {
      display: grid;
      grid-template-rows: auto minmax(190px, 1fr) auto minmax(160px, 0.65fr) auto minmax(110px, 0.38fr);
    }
    label {
      display: block;
      margin-bottom: 7px;
      font-size: 13px;
      font-weight: 700;
      color: #344054;
    }
    input, select, button, textarea {
      font: inherit;
    }
    input[type="password"], input[type="text"], select {
      width: 100%;
      height: 42px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 12px;
      background: #fff;
      color: var(--text);
    }
    input[type="file"] {
      width: 100%;
      padding: 12px;
      border: 1px dashed #aab4c2;
      border-radius: 8px;
      background: #f8fafc;
    }
    button {
      height: 44px;
      border: 1px solid transparent;
      border-radius: 6px;
      background: var(--accent);
      color: white;
      font-weight: 700;
      cursor: pointer;
    }
    button:hover { background: var(--accent-strong); }
    button:disabled {
      cursor: not-allowed;
      opacity: 0.62;
    }
    .secondary {
      background: white;
      color: var(--accent);
      border-color: var(--line);
    }
    .secondary:hover {
      background: #f8fafc;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .file-list {
      min-height: 96px;
      max-height: 150px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      background: #fbfdff;
    }
    .output-head {
      min-height: 60px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
    }
    .solution-head {
      border-top: 1px solid var(--line);
    }
    .output-title {
      font-weight: 800;
      color: #344054;
    }
    pre {
      margin: 0;
      padding: 18px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--code);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 14px;
      line-height: 1.55;
    }
    .error { color: var(--danger); }
    .hint {
      margin-top: -8px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }
    @media (max-width: 820px) {
      header {
        height: auto;
        align-items: flex-start;
        gap: 6px;
        flex-direction: column;
        padding: 18px;
      }
      .status { text-align: left; }
      main {
        grid-template-columns: 1fr;
      }
      aside { order: 1; }
      section { order: 2; min-height: 420px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <h1>DevAssist</h1>
      <div id="status" class="status">Ready</div>
    </header>
    <main>
      <aside>
        <div>
          <label for="files">Files</label>
          <input id="files" type="file" multiple>
        </div>
        <div id="fileList" class="file-list">No files selected</div>
        <div class="row">
          <div>
            <label for="language">Language</label>
            <select id="language">
              <option value="">Auto detect</option>
              <option>Python</option>
              <option>JavaScript</option>
              <option>Java</option>
              <option>C</option>
              <option>C++</option>
              <option>HTML</option>
              <option>CSS</option>
            </select>
          </div>
          <div>
            <label for="model">Model</label>
            <input id="model" type="text" value="gemini-3.5-flash">
          </div>
        </div>
        <div class="hint">Gemini access is loaded from the local .env file or GEMINI_API_KEY.</div>
        <button id="review">Review Code</button>
      </aside>
      <section>
        <div class="output-head">
          <div class="output-title">Review</div>
          <button id="copy" class="secondary">Copy</button>
        </div>
        <pre id="output">Choose one or more files, then run a review.</pre>
        <div class="output-head solution-head">
          <div class="output-title">Correct Code</div>
          <button id="copySolution" class="secondary">Copy Code</button>
        </div>
        <pre id="solution">Corrected code will appear here.</pre>
        <div class="output-head solution-head">
          <div class="output-title">Where To Paste</div>
          <button id="copyPasteGuide" class="secondary">Copy Steps</button>
        </div>
        <pre id="pasteGuide">Paste instructions will appear here.</pre>
      </section>
    </main>
  </div>
  <script>
    const filesInput = document.querySelector("#files");
    const fileList = document.querySelector("#fileList");
    const output = document.querySelector("#output");
    const statusEl = document.querySelector("#status");
    const reviewButton = document.querySelector("#review");
    const copyButton = document.querySelector("#copy");
    const solution = document.querySelector("#solution");
    const pasteGuide = document.querySelector("#pasteGuide");
    const copySolutionButton = document.querySelector("#copySolution");
    const copyPasteGuideButton = document.querySelector("#copyPasteGuide");

    filesInput.addEventListener("change", () => {
      const files = Array.from(filesInput.files);
      fileList.textContent = files.length ? files.map(file => file.name).join("\\n") : "No files selected";
      statusEl.textContent = files.length ? `${files.length} file(s) selected` : "Ready";
    });

    copyButton.addEventListener("click", async () => {
      await navigator.clipboard.writeText(output.textContent);
      statusEl.textContent = "Copied";
    });

    copySolutionButton.addEventListener("click", async () => {
      await navigator.clipboard.writeText(solution.textContent);
      statusEl.textContent = "Code copied";
    });

    copyPasteGuideButton.addEventListener("click", async () => {
      await navigator.clipboard.writeText(pasteGuide.textContent);
      statusEl.textContent = "Steps copied";
    });

    reviewButton.addEventListener("click", async () => {
      const files = Array.from(filesInput.files);
      if (!files.length) {
        output.textContent = "Choose at least one file.";
        output.className = "error";
        return;
      }

      reviewButton.disabled = true;
      statusEl.textContent = "Reviewing";
      output.className = "";
      output.textContent = "";
      solution.className = "";
      solution.textContent = "";
      pasteGuide.textContent = "";

      try {
        const payloadFiles = await Promise.all(files.map(async file => ({
          name: file.name,
          content: await file.text()
        })));

        const response = await fetch("/api/review", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            language: document.querySelector("#language").value,
            model: document.querySelector("#model").value,
            files: payloadFiles
          })
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "Review failed");
        }

        output.textContent = data.review || "No review returned.";
        solution.textContent = data.solution || "No corrected code needed.";
        pasteGuide.textContent = data.pasteGuide || "Replace the original file contents with the corrected code.";
        statusEl.textContent = "Done";
      } catch (error) {
        output.className = "error";
        output.textContent = error.message;
        solution.textContent = "Corrected code will appear here.";
        pasteGuide.textContent = "Paste instructions will appear here.";
        statusEl.textContent = "Failed";
      } finally {
        reviewButton.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


class DevAssistHandler(BaseHTTPRequestHandler):
    server_version = "DevAssist/1.0"

    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._send_bytes(HTML.encode("utf-8"), "text/html; charset=utf-8")

    def do_HEAD(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = HTML.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/api/review":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = self._review(payload)
            self._send_json(result)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args) -> None:
        return

    def _review(self, payload: dict) -> dict[str, str]:
        if devassist.genai is None or devassist.types is None:
            raise ValueError("google-genai is not installed.")

        api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing.")

        files = payload.get("files") or []
        if not files:
            raise ValueError("Choose at least one file.")

        model = (payload.get("model") or devassist.DEFAULT_MODEL).strip()
        language = (payload.get("language") or "").strip() or None
        client = devassist.genai.Client(api_key=api_key)
        review_sections: list[str] = []
        solution_sections: list[str] = []
        paste_sections: list[str] = []

        for file_item in files:
            name = str(file_item.get("name") or "untitled")
            content = str(file_item.get("content") or "")
            if not content.strip():
                review_sections.append(f"Review for {name}\n{'-' * min(len(name) + 11, 72)}\nError: empty file.")
                paste_sections.append(f"{name}\nOpen this file and add your code there. The uploaded file is empty.")
                continue

            review_text = self._generate_review(client, model, name, content, language)
            solution = self._extract_solution(client, model, name, content, language)
            heading = f"Review for {name}\n{'-' * min(len(name) + 11, 72)}"
            review_sections.append(f"{heading}\n{review_text.strip()}")
            solution_sections.append(solution.strip())
            paste_sections.append(self._paste_instructions(name))

        return {
            "review": "\n\n".join(review_sections).strip(),
            "solution": "\n\n".join(solution_sections).strip(),
            "pasteGuide": "\n\n".join(paste_sections).strip(),
        }

    def _paste_instructions(self, file_name: str) -> str:
        return (
            f"{file_name}\n"
            f"{'-' * min(len(file_name), 72)}\n"
            "1. Open this same file in your code editor.\n"
            "2. Select all existing code in that file.\n"
            "3. Copy the code from the Correct Code box.\n"
            "4. Paste it over the old code.\n"
            "5. Save the file and run it again."
        )

    def _generate_with_retries(self, client, model: str, message: str) -> str:
        last_error: Exception | None = None

        for candidate in devassist.candidate_models(model):
            for attempt in range(3):
                try:
                    response = client.models.generate_content_stream(
                        model=candidate,
                        contents=message,
                        config=devassist.types.GenerateContentConfig(
                            system_instruction=devassist.PROMPT,
                            max_output_tokens=1200,
                        ),
                    )
                    return "".join(chunk.text or "" for chunk in response)
                except Exception as exc:
                    last_error = exc
                    if not devassist.is_retryable_error(exc):
                        raise
                    time.sleep(1.5 * (attempt + 1))

        raise RuntimeError(
            "Gemini is temporarily unavailable after retrying fallback models. "
            f"Last error: {last_error}"
        )

    def _generate_json_with_retries(self, client, model: str, message: str, schema: dict) -> str:
        last_error: Exception | None = None

        for candidate in devassist.candidate_models(model):
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=candidate,
                        contents=message,
                        config=devassist.types.GenerateContentConfig(
                            temperature=0,
                            response_mime_type="application/json",
                            response_json_schema=schema,
                            max_output_tokens=3000,
                        ),
                    )
                    return response.text or ""
                except Exception as exc:
                    last_error = exc
                    if not devassist.is_retryable_error(exc):
                        raise
                    time.sleep(1.5 * (attempt + 1))

        raise RuntimeError(
            "Gemini is temporarily unavailable after retrying fallback models. "
            f"Last error: {last_error}"
        )

    def _generate_review(self, client, model: str, file_name: str, code: str, language: str | None) -> str:
        message = self._make_web_review_message(file_name, code, language)
        return self._generate_with_retries(client, model, message)

    def _make_web_review_message(self, file_name: str, code: str, language: str | None) -> str:
        language_line = f"Language: {language}" if language else "Language: infer from the file name and code"
        return (
            "Review this code for a beginner. Explain errors, bugs, and improvements in concise plain English. "
            "Do not include corrected code in this review; corrected code is generated separately.\n\n"
            f"File: {file_name}\n"
            f"{language_line}\n\n"
            "Code:\n"
            "```text\n"
            f"{code}\n"
            "```"
        )

    def _parse_model_json(self, text: str) -> dict[str, str]:
        stripped = self._clean_json_text(text)

        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return {
                "review": text.strip(),
                "solution": "",
                "needs_solution_extraction": "true",
            }

        return {
            "review": str(parsed.get("review") or "No review returned."),
            "solution": str(
                parsed.get("corrected_code")
                or parsed.get("solution")
                or parsed.get("code")
                or ""
            ),
            "needs_solution_extraction": "",
        }

    def _clean_json_text(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()

        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            stripped = stripped[start : end + 1]

        return stripped

    def _extract_solution(
        self,
        client,
        model: str,
        file_name: str,
        code: str,
        language: str | None,
    ) -> str:
        language_line = f"Language: {language}" if language else "Language: infer from the file name and code"
        message = (
            "Fix the following code. Return the complete corrected source file. "
            "Do not explain anything. Do not add markdown fences. Do not add headings. "
            "The output must be only code inside the corrected_code JSON field.\n\n"
            f"File: {file_name}\n"
            f"{language_line}\n\n"
            f"{code}"
        )
        schema = {
            "type": "object",
            "properties": {
                "corrected_code": {
                    "type": "string",
                    "description": "The complete corrected source code only, with no prose.",
                }
            },
            "required": ["corrected_code"],
            "additionalProperties": False,
        }
        solution = self._generate_json_with_retries(client, model, message, schema).strip()
        parsed = self._parse_solution_json(solution)
        if parsed and self._looks_like_code(parsed):
            return parsed

        fenced = self._extract_first_code_block(solution)
        if fenced and self._looks_like_code(fenced):
            return fenced

        stripped = self._strip_code_fence(solution)
        if self._looks_like_code(stripped):
            return stripped

        return (
            "Could not safely extract corrected code only. "
            "Run the review again, or copy the code block from the Review box."
        )

    def _parse_solution_json(self, text: str) -> str:
        try:
            parsed = json.loads(self._clean_json_text(text))
        except json.JSONDecodeError:
            return ""
        return str(
            parsed.get("corrected_code")
            or parsed.get("solution")
            or parsed.get("code")
            or ""
        ).strip()

    def _extract_first_code_block(self, text: str) -> str:
        lines = text.splitlines()
        start_index = -1
        for index, line in enumerate(lines):
            if line.strip().startswith("```"):
                start_index = index + 1
                break
        if start_index == -1:
            return ""

        code_lines: list[str] = []
        for line in lines[start_index:]:
            if line.strip() == "```":
                break
            code_lines.append(line)
        return "\n".join(code_lines).strip()

    def _looks_like_code(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False

        prose_markers = (
            "here is",
            "here's",
            "the bug",
            "the issue",
            "review",
            "explanation",
            "you should",
            "you need",
        )
        first_words = stripped[:220].lower()
        if any(marker in first_words for marker in prose_markers):
            return False

        code_markers = (
            "def ",
            "class ",
            "import ",
            "from ",
            "app.",
            "@app.",
            "function ",
            "const ",
            "let ",
            "var ",
            "#include",
            "public class",
            "{",
            ";",
            "</",
        )
        return "\n" in stripped and any(marker in stripped for marker in code_markers)

    def _strip_code_fence(self, text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped

        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._send_bytes(
            json.dumps(payload).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def _send_bytes(
        self,
        body: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    devassist.load_env_file()
    parser = argparse.ArgumentParser(description="Run the DevAssist local web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser automatically.")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), DevAssistHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"DevAssist app running at {url}")
    print("Press Ctrl+C to stop.")

    if not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DevAssist app.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
