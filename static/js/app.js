const modeButtons = document.querySelectorAll(".mode");
const forms = {
  debug: document.querySelector("#debugForm"),
  leetcode: document.querySelector("#leetcodeForm"),
  fullstack: document.querySelector("#fullstackForm"),
  ml: document.querySelector("#mlForm"),
};

const analyzeBtn = document.querySelector("#analyzeBtn");
const output = document.querySelector("#output");
const statusText = document.querySelector("#status");
const englishToggle = document.querySelector("#englishToggle");
const hindiToggle = document.querySelector("#hindiToggle");

let activeMode = "debug";
let latestPayload = {};
let latestResult = {
  english: "### Start Here\nChoose a mode, fill the inputs, then analyze.\n\n### Visual Explanation\nYour visual dry run or diagram will appear here after analysis.",
  hindi: "### Start Here\nMode choose karo, inputs bharo, phir analyze karo.\n\n### Visual Explanation\nAnalysis ke baad yahan visual dry run ya diagram dikhega.",
};
let activeLanguage = "english";

function setMode(mode) {
  activeMode = mode;
  modeButtons.forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
  Object.entries(forms).forEach(([key, form]) => form.classList.toggle("active", key === mode));
  statusText.textContent = "Ready";
}

function setLanguage(language) {
  activeLanguage = language;
  englishToggle.classList.toggle("active", language === "english");
  hindiToggle.classList.toggle("active", language === "hindi");
  renderResult(latestResult[language] || "No result yet.");
}

function formDataToObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderResult(text) {
  const normalized = (text || "").trim();
  if (!normalized) {
    output.innerHTML = '<article class="result-card"><h3>No Result</h3><p>Nothing was returned.</p></article>';
    return;
  }

  const blocks = normalized.split(/```/);
  const html = [];
  const visualAid = buildVisualAid(latestPayload, normalized);
  if (visualAid) {
    html.push(visualAid);
  }

  blocks.forEach((block, index) => {
    if (index % 2 === 1) {
      const lines = block.split("\n");
      const first = lines[0].trim();
      const hasLanguage = /^[a-zA-Z+#]+$/.test(first) && lines.length > 1;
      const code = hasLanguage ? lines.slice(1).join("\n") : block;
      html.push(`
        <article class="result-card code-card">
          <h3>Code</h3>
          <pre>${escapeHtml(code.trim())}</pre>
        </article>
      `);
      return;
    }

    const sectionHtml = renderTextSections(block);
    if (sectionHtml) {
      html.push(sectionHtml);
    }
  });

  output.innerHTML = html.join("");
}

function buildVisualAid(payload, answerText) {
  const sourceText = [
    payload.mode,
    payload.problemStatement,
    payload.brokenCode,
    payload.workingCode,
    payload.leetcodeProblem,
    payload.mlGoal,
    payload.mlCode,
    payload.datasetInfo,
    payload.mlIssue,
    payload.bugDescription,
    payload.frontendIssue,
    payload.backendIssue,
    payload.databaseIssue,
    payload.techStack,
    answerText,
  ].filter(Boolean).join("\n");

  const array = extractArray(sourceText);
  if (array.length >= 2) {
    return renderArrayFingerVisual(array, sourceText);
  }

  if (payload.mode === "ml" || /machine learning|dataset|train|test|accuracy|loss|epoch|feature|label|target|scaler|preprocess|fit\(|predict\(|model/i.test(sourceText)) {
    return renderMlPipelineVisual(sourceText);
  }

  if (/frontend|backend|database|api|route|request/i.test(sourceText)) {
    return renderFullStackVisual(sourceText);
  }

  if (/recursion|recursive|call stack|stack overflow|base case/i.test(sourceText)) {
    return renderStackVisual(sourceText);
  }

  return renderCodeFlowVisual(sourceText);
}

function extractArray(text) {
  const match = text.match(/\[([^\[\]]{1,160})\]/);
  if (!match) return [];
  const values = match[1]
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length && item.length <= 12);
  if (values.length < 2 || values.length > 12) return [];
  return values;
}

function renderArrayFingerVisual(array, sourceText) {
  const targetMatch = sourceText.match(/target\s*=?\s*(-?\d+)/i);
  const target = targetMatch ? targetMatch[1] : "";
  const leftIndex = inferPointerIndex(sourceText, ["left", "l", "i"], 0, array.length);
  const rightIndex = inferPointerIndex(sourceText, ["right", "r", "j"], Math.min(1, array.length - 1), array.length);

  const boxes = array.map((value, index) => `
    <div class="array-slot ${index === leftIndex || index === rightIndex ? "active" : ""}">
      <span class="array-index">${index}</span>
      <strong>${escapeHtml(value)}</strong>
      <span class="finger-row">
        ${index === leftIndex ? '<span class="finger">☝️ i</span>' : ""}
        ${index === rightIndex && rightIndex !== leftIndex ? '<span class="finger alt">☝️ j</span>' : ""}
      </span>
    </div>
  `).join("");

  return `
    <article class="result-card visual-card child-visual">
      <h3>Visual Explanation</h3>
      <p>Array ko boxes ki line samjho. Finger jis box par hai, wahi value abhi check ho rahi hai.</p>
      <div class="array-visual">${boxes}</div>
      <div class="kid-steps">
        <div><b>Step 1:</b> Finger <b>i</b> pehli value par rakho.</div>
        <div><b>Step 2:</b> Dusri finger <b>j</b> next useful value par rakho.</div>
        <div><b>Step 3:</b> Dono boxes ki value compare/add/check karo${target ? ` target <b>${escapeHtml(target)}</b> ke saath` : ""}.</div>
      </div>
    </article>
  `;
}

function renderFullStackVisual(sourceText) {
  const activeLayer = inferActiveLayer(sourceText);
  const layers = [
    ["frontend", "Screen", "Button, form, UI state"],
    ["backend", "Server", "Route, API, validation"],
    ["database", "Data", "Query, table, schema"],
  ];

  const nodes = layers.map(([key, title, detail], index) => `
    <div class="pipeline-node ${activeLayer === key ? "danger-node" : ""}">
      <span class="node-step">0${index + 1}</span>
      <strong>${title}</strong>
      <small>${detail}</small>
      ${activeLayer === key ? '<b class="bug-marker">check here</b>' : ""}
    </div>
  `).join('<strong class="arrow">→</strong>');

  return `
    <article class="result-card visual-card child-visual">
      <h3>Visual Explanation</h3>
      <p>Bug ko request journey ki tarah dekho. Pehle dekho request kis box me toot rahi hai.</p>
      <div class="flow-visual">${nodes}</div>
      <div class="kid-steps compact-steps">
        <div><b>Step 1:</b> Frontend se kya data ja raha hai, console/network me check karo.</div>
        <div><b>Step 2:</b> Backend route same data receive kar raha hai ya nahi.</div>
        <div><b>Step 3:</b> Database query/table expected format me hai ya nahi.</div>
      </div>
    </article>
  `;
}

function renderMlPipelineVisual(sourceText) {
  const issue = inferMlIssue(sourceText);
  const metricChart = renderMlMetricChart(sourceText);
  const steps = [
    ["data", "Dataset", "rows + columns"],
    ["clean", "Clean", "missing values"],
    ["split", "Split", "train / test"],
    ["train", "Train", "model.fit()"],
    ["check", "Evaluate", "accuracy / loss"],
    ["predict", "Predict", "new input"],
  ];

  const nodes = steps.map(([key, title, detail], index) => `
    <div class="pipeline-node ${issue === key ? "danger-node" : ""}">
      <span class="node-step">0${index + 1}</span>
      <strong>${title}</strong>
      <small>${detail}</small>
      ${issue === key ? '<b class="bug-marker">bug likely here</b>' : ""}
    </div>
  `).join('<strong class="arrow">→</strong>');

  return `
    <article class="result-card visual-card child-visual">
      <h3>Visual Explanation</h3>
      <p>ML code ko factory line samjho. Data ek station se next station tak jaata hai.</p>
      <div class="ml-pipeline">${nodes}</div>
      ${metricChart}
      <div class="kid-steps compact-steps">
        <div><b>Rule:</b> Pehle train/test split, phir scaler ya preprocessing sirf train data par fit karo.</div>
        <div><b>Watch:</b> Agar accuracy weird high/low hai, leakage, imbalance, metric, ya split check karo.</div>
      </div>
    </article>
  `;
}

function renderMlMetricChart(sourceText) {
  const series = extractMlMetrics(sourceText);
  if (series.length) {
    return `
      <div class="ml-chart">
        <div class="chart-title">Metric Plot</div>
        ${renderLineChart(series)}
        <div class="chart-legend">${series.map((point) => `<span><b style="background:${point.color}"></b>${escapeHtml(point.label)}</span>`).join("")}</div>
      </div>
    `;
  }

  return `
    <div class="ml-chart">
      <div class="chart-title">What to Plot</div>
      <div class="bar-chart">
        <div style="height:78%"><span>Train</span></div>
        <div class="warn-bar" style="height:36%"><span>Test</span></div>
        <div style="height:58%"><span>Loss</span></div>
      </div>
      <p>Agar train high aur test low hai, model overfit ho raha hai. Agar dono low hain, model underfit ho sakta hai.</p>
    </div>
  `;
}

function extractMlMetrics(text) {
  const patterns = [
    ["train acc", /train(?:ing)?\s*(?:accuracy|acc)\s*[:=]\s*(0?\.\d+|\d+(?:\.\d+)?%?)/ig, "#4ea77f"],
    ["test acc", /(?:test|val|validation)\s*(?:accuracy|acc)\s*[:=]\s*(0?\.\d+|\d+(?:\.\d+)?%?)/ig, "#ed6c2f"],
    ["accuracy", /(?<!train\s)(?<!test\s)(?<!validation\s)(?:accuracy|acc)\s*[:=]\s*(0?\.\d+|\d+(?:\.\d+)?%?)/ig, "#df8bd1"],
    ["loss", /loss\s*[:=]\s*(0?\.\d+|\d+(?:\.\d+)?%?)/ig, "#050505"],
  ];

  return patterns.flatMap(([label, regex, color]) => {
    const values = [];
    let match = regex.exec(text);
    while (match && values.length < 8) {
      values.push(parseMetricValue(match[1]));
      match = regex.exec(text);
    }
    return values.map((value, index) => ({ label, value, index, color }));
  }).filter((point) => Number.isFinite(point.value));
}

function parseMetricValue(raw) {
  const isPercent = raw.includes("%");
  const value = Number(raw.replace("%", ""));
  if (!Number.isFinite(value)) return NaN;
  if (isPercent) return value / 100;
  return value > 1 ? value / 100 : value;
}

function renderLineChart(points) {
  const maxIndex = Math.max(...points.map((point) => point.index), 1);
  const width = 520;
  const height = 220;
  const pad = 34;
  const grouped = points.reduce((acc, point) => {
    acc[point.label] = acc[point.label] || [];
    acc[point.label].push(point);
    return acc;
  }, {});

  const lines = Object.entries(grouped).map(([label, group]) => {
    const sorted = group.sort((a, b) => a.index - b.index);
    const coords = sorted.map((point) => {
      const x = pad + (point.index / maxIndex) * (width - pad * 2);
      const y = height - pad - Math.max(0, Math.min(point.value, 1)) * (height - pad * 2);
      return { ...point, x, y };
    });
    const path = coords.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
    const dots = coords.map((point) => `<circle cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="5" fill="${point.color}"><title>${escapeHtml(label)} ${(point.value * 100).toFixed(1)}%</title></circle>`).join("");
    return `<path d="${path}" fill="none" stroke="${coords[0].color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>${dots}`;
  }).join("");

  return `
    <svg class="metric-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="ML metric chart">
      <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" />
      <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" />
      <text x="6" y="${pad + 6}">100%</text>
      <text x="10" y="${height - pad}">0%</text>
      ${lines}
    </svg>
  `;
}

function renderStackVisual(sourceText) {
  const mentionsBaseCase = /base case|stopping condition|stop/i.test(sourceText);
  return `
    <article class="result-card visual-card child-visual">
      <h3>Visual Explanation</h3>
      <p>Recursion ko plates ke stack jaisa samjho. Har function call ek new plate banata hai.</p>
      <div class="stack-visual">
        <div class="stack-frame">call 3<br><small>smallest problem</small></div>
        <div class="stack-frame">call 2<br><small>middle problem</small></div>
        <div class="stack-frame danger-node">call 1<br><small>${mentionsBaseCase ? "base case check" : "missing stop?"}</small></div>
      </div>
      <div class="kid-steps compact-steps">
        <div><b>Finger rule:</b> Top call finish hoti hai, phir answer neeche wali call ko return hota hai.</div>
        <div><b>Check:</b> Base case nahi hua to function rukega nahi.</div>
      </div>
    </article>
  `;
}

function renderCodeFlowVisual(sourceText) {
  const likelyBug = /loop|condition|if|else|logic|wrong output|expected|actual/i.test(sourceText) ? "Logic" : "Middle Step";
  return `
    <article class="result-card visual-card child-visual">
      <h3>Visual Explanation</h3>
      <p>Code ko 3 boxes me todo. Input andar aata hai, logic process karta hai, output bahar aata hai.</p>
      <div class="code-flow">
        <div class="flow-node">
          <span class="node-step">01</span>
          <strong>Input</strong>
          <small>given values</small>
        </div>
        <strong class="arrow">→</strong>
        <div class="flow-node danger-node">
          <span class="node-step">02</span>
          <strong>${likelyBug}</strong>
          <small>condition / loop / formula</small>
          <b class="bug-marker">check slowly</b>
        </div>
        <strong class="arrow">→</strong>
        <div class="flow-node">
          <span class="node-step">03</span>
          <strong>Output</strong>
          <small>expected answer</small>
        </div>
      </div>
      <div class="kid-steps compact-steps">
        <div><b>Step 1:</b> One small input manually run karo.</div>
        <div><b>Step 2:</b> Har loop/condition ke baad value likho.</div>
        <div><b>Step 3:</b> Jahan value expected se alag ho, bug wahi hai.</div>
      </div>
    </article>
  `;
}

function inferActiveLayer(text) {
  const lower = text.toLowerCase();
  if (/sql|query|table|schema|database|mysql|mongodb|postgres|sqlite/.test(lower)) return "database";
  if (/route|server|backend|flask|django|node|express|api|status|500|validation/.test(lower)) return "backend";
  if (/react|frontend|button|form|state|props|component|browser|css|html/.test(lower)) return "frontend";
  return "";
}

function inferMlIssue(text) {
  const lower = text.toLowerCase();
  if (/missing|null|nan|duplicate|dirty|clean/.test(lower)) return "clean";
  if (/split|train\/test|test split|data leakage|leakage/.test(lower)) return "split";
  if (/fit|train|overfit|underfit|epoch|model/.test(lower)) return "train";
  if (/accuracy|loss|metric|precision|recall|f1|evaluate/.test(lower)) return "check";
  if (/predict|prediction|inference|new input/.test(lower)) return "predict";
  return "split";
}

function inferPointerIndex(text, names, fallback, length) {
  for (const name of names) {
    const regex = new RegExp(`\\b${name}\\b\\s*(?:=|at|index|->|points? to)?\\s*(\\d+)`, "i");
    const match = text.match(regex);
    if (match) {
      const value = Number(match[1]);
      if (Number.isInteger(value) && value >= 0 && value < length) return value;
    }
  }
  return Math.max(0, Math.min(fallback, length - 1));
}

function renderTextSections(text) {
  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
  if (!lines.length) return "";

  const sections = [];
  let current = { title: "Explanation", body: [] };

  lines.forEach((line) => {
    const heading = line.match(/^#{1,4}\s+(.+)$/) || line.match(/^\*\*(.+)\*\*$/);
    if (heading) {
      if (current.body.length) sections.push(current);
      current = { title: heading[1].replaceAll("*", "").trim(), body: [] };
    } else {
      current.body.push(line);
    }
  });

  if (current.body.length) sections.push(current);

  return sections.map((section) => {
    const isVisual = /visual|flow|diagram|dry run|walkthrough/i.test(section.title);
    const body = section.body.map(renderLine).join("");
    return `
      <article class="result-card ${isVisual ? "visual-card" : ""}">
        <h3>${escapeHtml(section.title)}</h3>
        ${body}
      </article>
    `;
  }).join("");
}

function renderLine(line) {
  const cleaned = line.replace(/^[-*]\s+/, "");
  if (isTableRow(line)) {
    return renderTableLine(line);
  }
  if (/^\d+[.)]\s+/.test(line) || /^[-*]\s+/.test(line)) {
    return `<ul><li>${escapeHtml(cleaned.replace(/^\d+[.)]\s+/, ""))}</li></ul>`;
  }
  if (looksLikeDiagram(line)) {
    return `<pre class="diagram">${escapeHtml(line)}</pre>`;
  }
  return `<p>${escapeHtml(line)}</p>`;
}

function looksLikeDiagram(line) {
  return (
    (/->|→|<-|=>|\[[^\]]+\]|\bL\s*=|\bR\s*=|\bi\s*=|\bj\s*=|\^\s*/.test(line) && line.length < 180) ||
    /^index\s*[:|]/i.test(line) ||
    /^arr\s*[:|]/i.test(line) ||
    /^step\s*[:|]/i.test(line)
  );
}

function isTableRow(line) {
  return line.includes("|") && line.split("|").length >= 3;
}

function renderTableLine(line) {
  const cells = line.split("|").map((cell) => cell.trim()).filter(Boolean);
  if (!cells.length || cells.every((cell) => /^-+$/.test(cell))) {
    return "";
  }
  return `<table class="dry-run-table"><tbody><tr>${cells.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr></tbody></table>`;
}

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

englishToggle.addEventListener("click", () => setLanguage("english"));
hindiToggle.addEventListener("click", () => setLanguage("hindi"));

analyzeBtn.addEventListener("click", async () => {
  analyzeBtn.disabled = true;
  statusText.textContent = "Analyzing...";
  renderResult("### Thinking\nDebugIQ is analyzing your input. Results will appear below in separated sections.");

  try {
    const payload = {
      mode: activeMode,
      ...formDataToObject(forms[activeMode]),
    };
    latestPayload = payload;

    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Analysis failed.");
    }

    latestResult = {
      english: data.english || "No English explanation returned.",
      hindi: data.hindi || "Hindi explanation not returned.",
    };
    setLanguage(activeLanguage);
    statusText.textContent = "Done";
  } catch (error) {
    const message = error.message === "Failed to fetch"
      ? "Could not reach the local DebugIQ server. Make sure Flask is running, then refresh and try again."
      : error.message;
    latestResult = {
      english: message,
      hindi: message,
    };
    renderResult(`### Error\n${message}`);
    statusText.textContent = "Failed";
  } finally {
    analyzeBtn.disabled = false;
  }
});
