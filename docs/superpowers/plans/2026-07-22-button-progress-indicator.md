# Indikatif Progress Indicator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace spinning-only spinners on the 4 pipeline Run buttons (research/discover/generate/score) with an indikatif progress bar that shows shimmer animation, elapsed time, and phase label — purely client-side, no backend changes.

**Architecture:** Single reusable Jinja partial `_progress.html` rendered in each of the 4 phase partials. One global HTMX lifecycle hook in `base.html` drives show/tick/fade via `htmx:beforeRequest` / `afterRequest` / `responseError`. CSS uses the existing `.progress-shine` keyframe plus a new `transition: width` for completion jump. Counter & fill width are computed from a monotonic tick bound to the request start time.

**Tech Stack:** FastAPI + Jinja2 + Tailwind (CDN) + HTMX 2.0.4 + vanilla JS (ES2020). No new dependencies.

## Global Constraints

- Python 3.11+, FastAPI ≥ 0.115.0, Jinja2 ≥ 3.1.0, HTMX 2.0.4 (already loaded).
- No new npm/pip dependencies.
- No backend route changes; only template + inline JS/CSS edits.
- Project package data rule (`pyproject.toml`): `"fp.web" = ["templates/**/*.html"]` — new partial is auto-included in build.
- Stay inside the dark slate color palette used in `base.html` (slate-700/800/900, blue-600 accents).
- Export phase excluded — it uses `<a href>` download links, not HTMX forms.
- Spinner fallback `.htmx-indicator` must remain visible if JS fails to load (backwards compat).

---

## File Structure

| File | Status | Responsibility |
|------|--------|---------------|
| `fp/web/templates/partials/_progress.html` | **Create** | Self-contained progress widget (label + elapsed + fill bar). |
| `fp/web/templates/base.html` | Modify | Add `.run-progress` CSS rules (hidden/error/done) + global HTMX hook to drive the widget. |
| `fp/web/templates/partials/research.html` | Modify | Include `_progress` below Run button; set `data-phase="research"`. |
| `fp/web/templates/partials/discover.html` | Modify | Include `_progress` below Run button; set `data-phase="discover"`. |
| `fp/web/templates/partials/generate.html` | Modify | Include `_progress` below Run button; set `data-phase="generate"`. |
| `fp/web/templates/partials/score.html` | Modify | Include `_progress` below Run button; set `data-phase="score"`. |
| `tests/web/test_progress_partial.py` | **Create** | Assert partial renders with correct phase label & required DOM hooks. |
| `tests/web/test_pipeline.py` | Modify (add tests) | Assert partials include `#*-progress` element when state requires action. |

---

## Task 1: Create the progress partial

**Files:**
- Create: `fp/web/templates/partials/_progress.html`

**Interfaces:**
- Consumed by: Tasks 2–5 (one include per phase partial).
- Produces: A `<div class="run-progress hidden" data-phase="..." id="...-progress">...</div>` subtree with `.run-progress-fill`, `.run-progress-status`, `.run-progress-elapsed` descendants.

- [ ] **Step 1: Write the partial**

```html
{# Reusable indeterminate progress indicator. Expects 'phase_id' and 'phase_label' vars. #}
<div id="{{ phase_id }}-progress"
     class="run-progress hidden mt-3 rounded-lg border border-slate-700/50 bg-slate-800/60 p-3"
     data-phase="{{ phase_id }}"
     role="status"
     aria-live="polite">
  <div class="flex items-center justify-between text-xs mb-2">
    <span class="run-progress-label flex items-center gap-2 text-slate-300">
      <svg class="run-progress-spinner animate-spin h-3 w-3 text-blue-400"
           fill="none" viewBox="0 0 24 24" aria-hidden="true">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
        </path>
      </svg>
      <span class="run-progress-status">{{ phase_label }}</span>
    </span>
    <span class="run-progress-elapsed font-mono text-slate-400">0:00</span>
  </div>
  <div class="h-2 bg-slate-900/80 rounded-full overflow-hidden">
    <div class="run-progress-fill h-full progress-shine" style="width: 0%"></div>
  </div>
</div>
```

- [ ] **Step 2: Verify partial is auto-bundled (build sanity)**

Run: `python -c "from fp.web.app import app; print('ok')"`
Expected: prints `ok` (proves Jinja loader can read the template tree — if the file path is invalid, app startup fails).

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/partials/_progress.html
git commit -m "feat(web): add _progress partial for indeterminate loading"
```

---

## Task 2: Wire the global HTMX hook + CSS in base.html

**Files:**
- Modify: `fp/web/templates/base.html:27-62` (CSS), `:89-107` (JS)

**Interfaces:**
- Required DOM hooks the hook looks for: `.run-progress[data-phase=X]` somewhere inside the request's triggered element. Task 1 ensures the partial exposes both `data-phase` and a parent form relation (HTMX fires from forms, finds descendant by attribute match).
- Same hook is consumed by all 4 phase partials from Tasks 3–6.

- [ ] **Step 1: Extend CSS in `<style>` (append after line 57)**

```css
        /* Run progress widget (indeterminate shimmer + elapsed counter) */
        .run-progress.hidden { display: none; }
        .run-progress-fill {
            transition: width 200ms ease-out;
        }
        .run-progress.is-error {
            border-color: rgb(245 158 11 / 0.6);
            background-color: rgb(120 53 15 / 0.2);
        }
        .run-progress .run-progress-status.is-done { color: rgb(74 222 128); }
        .run-progress .run-progress-status.is-error { color: rgb(251 191 36); }
```

- [ ] **Step 2: Replace the existing `htmx:afterRequest` block (lines 99–106) with the full lifecycle hook**

```html
    <script>
        // Disable run buttons while their HTMX request is in flight.
        // Prevents double-submit and gives explicit visual feedback beyond the spinner.
        (function () {
            const PROGRESS_CAP_MS = 150000;     // 150s → 92% cap
            const PROGRESS_MAX_PCT = 92;

            function formatElapsed(ms) {
                const total = Math.floor(ms / 1000);
                const m = Math.floor(total / 60);
                const s = total % 60;
                return `${m}:${String(s).padStart(2, '0')}`;
            }

            function tick(progressEl, startedAt) {
                const elapsed = Date.now() - startedAt;
                const fill = progressEl.querySelector('.run-progress-fill');
                const elapsedEl = progressEl.querySelector('.run-progress-elapsed');
                const pct = Math.min(PROGRESS_MAX_PCT, (elapsed / PROGRESS_CAP_MS) * PROGRESS_MAX_PCT);
                if (fill) fill.style.width = `${pct}%`;
                if (elapsedEl) elapsedEl.textContent = formatElapsed(elapsed);
            }

            function findProgress(target) {
                // The form is the request source; the partial is rendered next to (or inside) the form.
                return target.querySelector('.run-progress[data-phase]')
                    || document.querySelector('.run-progress[data-phase]');
            }

            document.body.addEventListener('htmx:beforeRequest', (e) => {
                const btn = e.target.querySelector && e.target.querySelector('button.run-btn');
                if (btn) {
                    btn.disabled = true;
                    btn.setAttribute('aria-busy', 'true');
                }

                const progressEl = findProgress(e.target);
                if (!progressEl) return;
                progressEl.classList.remove('hidden', 'is-error');
                const statusEl = progressEl.querySelector('.run-progress-status');
                if (statusEl) statusEl.classList.remove('is-done', 'is-error');

                const startedAt = Date.now();
                progressEl.dataset.startedAt = String(startedAt);
                if (progressEl._tickInterval) clearInterval(progressEl._tickInterval);
                progressEl._tickInterval = setInterval(() => tick(progressEl, startedAt), 250);
                tick(progressEl, startedAt);
            });

            function finishProgress(progressEl, ok, label) {
                if (!progressEl) return;
                if (progressEl._tickInterval) {
                    clearInterval(progressEl._tickInterval);
                    progressEl._tickInterval = null;
                }
                const fill = progressEl.querySelector('.run-progress-fill');
                const statusEl = progressEl.querySelector('.run-progress-status');
                if (fill) {
                    if (ok) {
                        fill.style.width = '100%';
                    }
                }
                if (statusEl) {
                    statusEl.textContent = label;
                    statusEl.classList.remove('is-done', 'is-error');
                    statusEl.classList.add(ok ? 'is-done' : 'is-error');
                }
                if (!ok) progressEl.classList.add('is-error');
                if (ok) {
                    setTimeout(() => progressEl.classList.add('hidden'), 800);
                }
            }

            document.body.addEventListener('htmx:afterRequest', (e) => {
                const btn = e.target.querySelector && e.target.querySelector('button.run-btn');
                if (btn) {
                    btn.disabled = false;
                    btn.removeAttribute('aria-busy');
                }
                finishProgress(findProgress(e.target), e.detail.successful, e.detail.successful ? 'Done' : 'Error');
            });

            document.body.addEventListener('htmx:responseError', (e) => {
                finishProgress(findProgress(e.target), false, 'Server error');
            });
            document.body.addEventListener('htmx:sendError', (e) => {
                finishProgress(findProgress(e.target), false, 'Connection error');
            });
            document.body.addEventListener('htmx:timeout', (e) => {
                finishProgress(findProgress(e.target), false, 'Timed out');
            });
        })();
    </script>
```

- [ ] **Step 3: Sanity-render (server side still parses)**

Run: `python -c "from fp.web.app import app; print('ok')"`
Expected: prints `ok` (HTML errors would surface via Jinja at import time only if static — the JS runs in browser, so we just confirm server still loads).

- [ ] **Step 4: Commit**

```bash
git add fp/web/templates/base.html
git commit -m "feat(web): add indeterminate progress hook to global HTMX lifecycle"
```

---

## Task 3: Use the partial in research.html

**Files:**
- Modify: `fp/web/templates/partials/research.html` (around the submit button around line 60–80)

**Interfaces:**
- Calls into the partial from Task 1 with `phase_id="research"` and `phase_label="Researching queries…"`.
- The existing `.htmx-indicator` spinner block stays as a JS-disabled fallback.

- [ ] **Step 1: Read current state** of `fp/web/templates/partials/research.html` to locate the `<form … hx-post="/api/research">` and its `<button type="submit">`.

- [ ] **Step 2: Insert the include immediately after the `</form>` closing tag in the pre-run branch**

Find the existing spinner block (the `<span id="research-spinner" class="htmx-indicator …">`) and add right after the `</form>` of the pre-run section:

```html
        {% include 'partials/_progress.html' %}
```

Replace that single line with:

```html
        {% set phase_id = 'research' %}
        {% set phase_label = 'Researching queries…' %}
        {% include 'partials/_progress.html' %}
```

- [ ] **Step 3: Verify with TestClient**

Run: `python -c "
from fastapi.testclient import TestClient
from fp.web.app import app
c = TestClient(app)
r = c.get('/pipeline/research')
assert r.status_code == 200
assert 'id=\"research-progress\"' in r.text, 'progress partial missing'
assert 'data-phase=\"research\"' in r.text
print('ok')
"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add fp/web/templates/partials/research.html
git commit -m "feat(web): show indeterminate progress on research Run button"
```

---

## Task 4: Use the partial in discover.html

**Files:**
- Modify: `fp/web/templates/partials/discover.html`

**Interfaces:** Same pattern as Task 3 with `phase_id="discover"`, `phase_label="Discovering problems…"`.

- [ ] **Step 1: Locate** the `</form>` of the pre-run section in `discover.html` (search for `hx-indicator="#discover-spinner"`).

- [ ] **Step 2: Add the include after `</form>`**

```html
        {% set phase_id = 'discover' %}
        {% set phase_label = 'Discovering problems…' %}
        {% include 'partials/_progress.html' %}
```

- [ ] **Step 3: Verify**

Run: `python -c "
from fastapi.testclient import TestClient
from fp.web.app import app
c = TestClient(app)
r = c.get('/pipeline/discover')
assert r.status_code == 200
assert 'id=\"discover-progress\"' in r.text
assert 'data-phase=\"discover\"' in r.text
print('ok')
"`
Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
git add fp/web/templates/partials/discover.html
git commit -m "feat(web): show indeterminate progress on discover Run button"
```

---

## Task 5: Use the partial in generate.html

**Files:**
- Modify: `fp/web/templates/partials/generate.html`

**Interfaces:** Same pattern with `phase_id="generate"`, `phase_label="Generating prompts…"`.

- [ ] **Step 1: Locate** the `</form>` in `generate.html` (search for `hx-indicator="#generate-spinner"`).

- [ ] **Step 2: Add the include after `</form>`**

```html
        {% set phase_id = 'generate' %}
        {% set phase_label = 'Generating prompts…' %}
        {% include 'partials/_progress.html' %}
```

- [ ] **Step 3: Verify**

Run: `python -c "
from fastapi.testclient import TestClient
from fp.web.app import app
c = TestClient(app)
r = c.get('/pipeline/generate')
assert r.status_code == 200
assert 'id=\"generate-progress\"' in r.text
assert 'data-phase=\"generate\"' in r.text
print('ok')
"`
Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
git add fp/web/templates/partials/generate.html
git commit -m "feat(web): show indeterminate progress on generate Run button"
```

---

## Task 6: Use the partial in score.html

**Files:**
- Modify: `fp/web/templates/partials/score.html`

**Interfaces:** Same pattern with `phase_id="score"`, `phase_label="Scoring prompts…"`.

- [ ] **Step 1: Locate** `</form>` in `score.html`.

- [ ] **Step 2: Add the include after `</form>`**

```html
        {% set phase_id = 'score' %}
        {% set phase_label = 'Scoring prompts…' %}
        {% include 'partials/_progress.html' %}
```

- [ ] **Step 3: Verify**

Run: `python -c "
from fastapi.testclient import TestClient
from fp.web.app import app
c = TestClient(app)
r = c.get('/pipeline/score')
assert r.status_code == 200
assert 'id=\"score-progress\"' in r.text
assert 'data-phase=\"score\"' in r.text
print('ok')
"`
Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
git add fp/web/templates/partials/score.html
git commit -m "feat(web): show indeterminate progress on score Run button"
```

---

## Task 7: Add regression tests for the partial in template responses

**Files:**
- Create: `tests/web/test_progress_partial.py`

**Interfaces:**
- Imports `TestClient` and `app` from `fp.web.app`.
- Tests the 4 GET endpoints that render partials containing the progress widget.

- [ ] **Step 1: Write the test file**

```python
"""Regression tests for the indeterminate progress widget rendered by pipeline partials."""
import pytest
from fastapi.testclient import TestClient

from fp.web.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_research_partial_contains_progress_widget(client):
    """Research pre-run partial must include the progress widget."""
    r = client.get("/pipeline/research")
    assert r.status_code == 200
    body = r.text
    assert 'id="research-progress"' in body
    assert 'data-phase="research"' in body
    assert "Researching queries" in body
    assert "run-progress-fill" in body
    assert "run-progress-elapsed" in body


@pytest.mark.parametrize(
    "phase,label",
    [
        ("discover", "Discovering problems"),
        ("generate", "Generating prompts"),
        ("score", "Scoring prompts"),
    ],
)
def test_pipeline_partials_contain_progress_widget(client, phase, label):
    """Discover/Generate/Score partials each include the progress widget with their own phase id."""
    r = client.get(f"/pipeline/{phase}")
    assert r.status_code == 200
    body = r.text
    assert f'id="{phase}-progress"' in body
    assert f'data-phase="{phase}"' in body
    assert label in body
    assert "run-progress-fill" in body


def test_progress_widget_is_initially_hidden(client):
    """The progress widget must start hidden so it doesn't appear before a request."""
    r = client.get("/pipeline/research")
    assert r.status_code == 200
    # Find the progress container and verify it carries the `hidden` class.
    assert 'class="run-progress hidden' in r.text
```

- [ ] **Step 2: Run the tests**

Run: `pytest tests/web/test_progress_partial.py -v`
Expected: `4 passed` (or 1+3 parametrized = 4 total).

- [ ] **Step 3: Run the full web test suite to confirm no regressions**

Run: `pytest tests/web/ -v`
Expected: all previously passing tests still pass, plus the 4 new ones.

- [ ] **Step 4: Commit**

```bash
git add tests/web/test_progress_partial.py
git commit -m "test(web): assert progress widget renders on every pipeline partial"
```

---

## Self-Review Checklist (run after writing plan, before handoff)

- [x] **Spec coverage:**
  - Reusable partial → Task 1 ✓
  - Global HTMX hook → Task 2 ✓
  - Applied to 4 partials (research/discover/generate/score) → Tasks 3–6 ✓
  - Elapsed counter + cap at 92% → Task 2 (PROGRESS_MAX_PCT) ✓
  - Show on beforeRequest, fade after 800ms on success → Task 2 (`setTimeout(... , 800)`) ✓
  - Error states (responseError / sendError / timeout) → Task 2 (3 listeners) ✓
  - Spinner fallback preserved (no removal of `.htmx-indicator`) → Tasks 3–6 only add include, don't remove existing spinner span ✓
  - 150s cap with shimmer — spec said "30-60s typically", 150s gives comfortable buffer ✓
  - No backend changes — Tasks 1–7 only touch templates + tests ✓

- [x] **Placeholder scan:** No TBD, no "similar to Task N", no vague "handle edge cases". Every step has concrete code.

- [x] **Type/name consistency:** `progressEl._tickInterval` used in Task 2 in two places (set/clear). Verify commands in Steps reference exact `id="...-progress"` strings that match `phase_id` var names.

- [x] **YAGNI:** No fake percent display, no multi-label rotation, no cancel button, no extracted `progress.js` (kept inline in `base.html` since it's ~60 lines, not worth its own file).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-22-button-progress-indicator.md`.
