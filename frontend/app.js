// Same-origin by default (FastAPI serves this file itself). If you split
// frontend/backend across two hosts later (e.g. frontend on Vercel, backend
// on Render), set this to the deployed backend URL instead.
const API_BASE_URL = "";

const SUGGESTIONS = [
  "5 mistakes beginners make when learning Python",
  "I tried the 75 Hard challenge for 30 days",
  "Why your phone battery dies so fast",
  "How I save money living in a small apartment",
  "Productivity tips that actually changed my life",
];

const STEP_ORDER = ["script", "titles", "description", "tags", "thumbnail"];

const form = document.getElementById("generate-form");
const topicInput = document.getElementById("topic");
const providerSelect = document.getElementById("provider");
const providerHint = document.getElementById("provider-hint");
const submitBtn = document.getElementById("submit-btn");
const outputEl = document.getElementById("output");
const outputEmpty = document.getElementById("output-empty");
const suggestionsEl = document.getElementById("suggestions");

// ---------------- Suggestion chips ----------------
SUGGESTIONS.forEach((text) => {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "chip";
  chip.textContent = text.length > 38 ? text.slice(0, 38) + "…" : text;
  chip.title = text;
  chip.addEventListener("click", () => {
    topicInput.value = text;
    topicInput.focus();
  });
  suggestionsEl.appendChild(chip);
});

// ---------------- Load available providers ----------------
const PROVIDER_LABELS = { openai: "OpenAI", gemini: "Google Gemini", groq: "Groq" };

async function loadProviders() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/providers`);
    const data = await res.json();
    const available = data.available || [];

    providerSelect.innerHTML = "";

    if (available.length === 0) {
      providerSelect.innerHTML = `<option value="" disabled selected>No provider configured</option>`;
      providerHint.textContent =
        "No API key found on the server. Add OPENAI_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY to backend/.env and restart.";
      providerHint.classList.add("provider-hint--warn");
      submitBtn.disabled = true;
      return;
    }

    available.forEach((name, i) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = PROVIDER_LABELS[name] || name;
      if (i === 0) opt.selected = true;
      providerSelect.appendChild(opt);
    });
    providerHint.textContent = `${available.length} provider(s) ready: ${available
      .map((p) => PROVIDER_LABELS[p] || p)
      .join(", ")}.`;
  } catch (err) {
    providerHint.textContent = "Could not reach the backend. Is it running on this port?";
    providerHint.classList.add("provider-hint--warn");
    submitBtn.disabled = true;
  }
}
loadProviders();

// ---------------- Rail state helpers ----------------
function setStepState(step, state, statusText) {
  const li = document.querySelector(`.rail__step[data-step="${step}"]`);
  if (!li) return;
  li.dataset.state = state;
  const statusEl = li.querySelector(".rail__status");
  if (statusText) statusEl.textContent = statusText;
}

function resetRail() {
  STEP_ORDER.forEach((s) => setStepState(s, "pending", "waiting"));
}

// ---------------- Output card renderers ----------------
function clearOutput() {
  outputEl.innerHTML = "";
}

function addCard(html) {
  if (outputEmpty) outputEmpty.remove();
  const wrapper = document.createElement("div");
  wrapper.innerHTML = html;
  outputEl.appendChild(wrapper.firstElementChild);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function copyButton(targetText) {
  return `<button class="card__copy" onclick="navigator.clipboard.writeText(this.dataset.text); this.textContent='Copied'; setTimeout(()=>this.textContent='Copy',1200)" data-text="${escapeHtml(
    targetText
  ).replace(/"/g, "&quot;")}">Copy</button>`;
}

function renderScript(script) {
  addCard(`
    <div class="card" id="card-script">
      <div class="card__head">
        <span class="card__title">📝 Script</span>
        ${copyButton(script)}
      </div>
      <div class="card__body">${escapeHtml(script)}</div>
    </div>
  `);
}

function renderTitles(titles) {
  const rows = titles
    .map(
      (t, i) =>
        `<div class="title-option"><span><span class="title-option__rank">${String(
          i + 1
        ).padStart(2, "0")}</span>${escapeHtml(t)}</span></div>`
    )
    .join("");
  addCard(`
    <div class="card" id="card-titles">
      <div class="card__head">
        <span class="card__title">🎯 Title options</span>
        ${copyButton(titles.join("\n"))}
      </div>
      <div class="card__body">${rows}</div>
    </div>
  `);
}

function renderDescription(description) {
  addCard(`
    <div class="card" id="card-description">
      <div class="card__head">
        <span class="card__title">🔍 Description</span>
        ${copyButton(description)}
      </div>
      <div class="card__body">${escapeHtml(description)}</div>
    </div>
  `);
}

function renderTags(tags) {
  const pills = tags.map((t) => `<span class="tag-pill">${escapeHtml(t)}</span>`).join("");
  addCard(`
    <div class="card" id="card-tags">
      <div class="card__head">
        <span class="card__title">🏷️ Tags</span>
        ${copyButton(tags.join(", "))}
      </div>
      <div class="card__body"><div class="tag-list">${pills}</div></div>
    </div>
  `);
}

function renderThumbnail(concept, text) {
  addCard(`
    <div class="card" id="card-thumbnail">
      <div class="card__head">
        <span class="card__title">🖼️ Thumbnail concept</span>
        ${copyButton(concept + "\nOverlay text: " + text)}
      </div>
      <div class="card__body thumb-card">
        <div>${escapeHtml(concept)}</div>
        <div class="thumb-overlay">${escapeHtml(text)}</div>
      </div>
    </div>
  `);
}

function renderError(message) {
  addCard(`<div class="card error-banner">⚠️ ${escapeHtml(message)}</div>`);
}

// ---------------- Submit + SSE streaming ----------------
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    topic: topicInput.value.trim(),
    provider: providerSelect.value,
    niche: document.getElementById("niche").value.trim() || null,
    audience: document.getElementById("audience").value.trim() || null,
    tone: document.getElementById("tone").value.trim() || null,
    length: document.getElementById("length").value,
    language: document.getElementById("language").value.trim() || "English",
  };

  resetRail();
  clearOutput();
  outputEl.innerHTML = `<p class="output__empty" id="output-empty">Running…</p>`;

  submitBtn.disabled = true;
  submitBtn.querySelector(".btn-run__label").textContent = "Running…";
  submitBtn.querySelector(".btn-run__spinner").hidden = false;

  try {
    const res = await fetch(`${API_BASE_URL}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok || !res.body) {
      throw new Error(`Server responded with ${res.status}`);
    }

    document.getElementById("output-empty")?.remove();

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop(); // last chunk may be incomplete, keep for next read

      for (const evt of events) {
        const line = evt.trim();
        if (!line.startsWith("data:")) continue;
        const jsonStr = line.slice(5).trim();
        if (!jsonStr) continue;

        let parsed;
        try {
          parsed = JSON.parse(jsonStr);
        } catch {
          continue;
        }
        handleEvent(parsed);
      }
    }
  } catch (err) {
    renderError(`Something went wrong: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector(".btn-run__label").textContent = "Run agent";
    submitBtn.querySelector(".btn-run__spinner").hidden = true;
  }
});

function handleEvent(evt) {
  if (evt.type === "step_start") {
    setStepState(evt.step, "active", evt.label || "running…");
  } else if (evt.type === "step_done") {
    setStepState(evt.step, "done", "done");
    const data = evt.data || {};
    if (evt.step === "script") renderScript(data.script);
    if (evt.step === "titles") renderTitles(data.titles || []);
    if (evt.step === "description") renderDescription(data.description);
    if (evt.step === "tags") renderTags(data.tags || []);
    if (evt.step === "thumbnail") renderThumbnail(data.thumbnail_concept, data.thumbnail_text);
  } else if (evt.type === "error") {
    // Mark whichever step was mid-flight as errored
    const activeStep = document.querySelector('.rail__step[data-state="active"]');
    if (activeStep) setStepState(activeStep.dataset.step, "error", "failed");
    renderError(evt.message);
  } else if (evt.type === "complete") {
    // All steps already rendered incrementally; nothing else to do.
  }
}
