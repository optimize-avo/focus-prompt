# Design: Indikatif Progress Indicator untuk Tombol Pipeline

## Problem

Tombol Run di setiap phase pipeline (research, discover, generate, score, export) saat ini hanya menampilkan spinner SVG `animate-spin` yang berputar tanpa henti. Untuk operasi LLM yang memakan waktu 30-90 detik, user tidak punya gambaran progress — terasa menggantung dan tidak jelas apakah masih jalan atau sudah stuck.

## Goal

Ganti spinner statis dengan progress bar indikatif (animated shimmer + elapsed time + fase label) sehingga:
- User mendapat feedback visual yang jelas tentang "loading ini masih jalan, dan sudah berjalan selama X detik"
- Tampilan loading konsisten di seluruh pipeline (semua phase button pakai komponen yang sama)
- Tidak membutuhkan perubahan backend (indeterminate, bukan true percentage dari server)

## Scope

**In scope:**
- Komponen progress bar reusable di 5 partial pipeline (research, discover, generate, score, export)
- JavaScript hook global di `base.html` yang auto-attach ke setiap form dengan `run-btn`
- CSS shimmer animation yang sudah ada (`.progress-shine`) diperluas dengan fill-width animation

**Out of scope:**
- Backend changes (no SSE refactor, no real percentage tracking)
- Perubahan tombol visual itu sendiri
- Real-time server-pushed progress

## Decisions

- **Tipe progress:** Indeterminate shimmer (animated linear-gradient sweep) — bukan persentase pasti
- **Behavior cap:** Bar berhenti di 92% (tidak pernah menyentuh 100% saat loading), loncat ke 100% saat response diterima
- **Elapsed counter:** Format `M:SS` (mono font), update tiap detik
- **Fase label:** Setiap tombol punya `phase` attribute sendiri (research|discover|generate|score|export), label berubah halus berdasarkan fase yang sedang jalan
- **No fake percentages:** Tidak menampilkan angka persen — user sudah paham ini loading yang belum selesai
- **Graceful error:** Saat `htmx:responseError`, bar jadi warna amber
- **Komponen reusable:** Single partial `_progress.html` yang di-include di 5 tempat, DRY

---

## Komponen UI

### `_progress.html` (partial baru)

```html
<div id="__PROGRESS_ID__-indicator"
     class="run-progress hidden mt-3 rounded-lg border border-slate-700/50 bg-slate-800/60 p-3"
     data-phase="__PHASE__"
     role="status"
     aria-live="polite">
  <div class="flex items-center justify-between text-xs mb-2">
    <span class="run-progress-label flex items-center gap-2 text-slate-300">
      <svg class="animate-spin h-3 w-3 text-blue-400" fill="none" viewBox="0 0 24 24" aria-hidden="true">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      <span class="run-progress-status">Working...</span>
    </span>
    <span class="run-progress-elapsed font-mono text-slate-400">0:00</span>
  </div>
  <div class="h-2 bg-slate-900/80 rounded-full overflow-hidden">
    <div class="run-progress-fill h-full progress-shine" style="width: 0%"></div>
  </div>
</div>
```

### Visual states

| State | Container | Fill width | Label | Elapsed |
|-------|-----------|------------|-------|---------|
| Idle | hidden | — | — | — |
| Loading | visible | 0% → 92% over ~150s | `Running {phase}...` | `0:00` → `M:SS` |
| Success | visible, then fade | jumps to 100% (200ms) | `Done` | frozen |
| Error | visible, amber border | frozen at last width | `Error occurred` | frozen |

---

## Behavior Spec

### JS lifecycle (di `base.html`)

Pasang listener sekali di body, handle semua form yang punya `run-btn`:

```
htmx:beforeRequest
  ├── show progress container (remove .hidden)
  ├── start setInterval(tick, 1000) → update elapsed & width
  └── setTimeout(freezeLabel, 2500) → swap status text

htmx:afterRequest
  ├── kill intervals/timeouts
  ├── fill width → 100% (CSS transition 200ms)
  ├── status label → "Done" (green)
  └── setTimeout(hideProgress, 800) → add .hidden back

htmx:responseError / htmx:timeout / htmx:sendError
  ├── kill intervals/timeouts
  ├── border → amber/red
  └── status label → "Error occurred"

htmx:beforeSend (cancel guard)
  └── if already loading for this form, htmx abort sends second request
```

### Tick function

```js
const CAP_MS = 150_000;     // 150 dtk → 92%
const MAX_PCT = 92;

function tick(elapsedMs) {
  const pct = Math.min(MAX_PCT, (elapsedMs / CAP_MS) * MAX_PCT);
  fill.style.width = `${pct}%`;
}
```

### Label cycling per fase

Setiap progress container punya `data-phase`. Label statis per fase:
- `research` → `Researching queries...`
- `discover` → `Discovering problems...`
- `generate` → `Generating prompts...`
- `score` → `Scoring prompts...`
- `export` → `Exporting results...`

(Cukup satu label per fase, tidak perlu multi-step rotation — tidak akurat, dan fase individual biasanya ≤ 60 detik.)

---

## File Changes

### New file
- `fp/web/templates/partials/_progress.html` — komponen progress reusable

### Modified files
- `fp/web/templates/base.html`
  - Tambah CSS: `.run-progress.hidden { display: none; }`, `.run-progress-fill { transition: width 200ms ease-out; }`, error state styling
  - Tambah JS hook: listener `htmx:beforeRequest`/`afterRequest`/`responseError` yang auto-manage komponen progress
- `fp/web/templates/partials/research.html` — replace spinner dengan include `_progress.html` + ganti spinner block jadi fallback (dipakai sebelum JS load)
- `fp/web/templates/partials/discover.html` — sama
- `fp/web/templates/partials/generate.html` — sama
- `fp/web/templates/partials/score.html` — sama
- `fp/web/templates/partials/export.html` — sama (cek dulu apakah exist)

### Optional helper
- `fp/web/static/js/progress.js` — extracted module jika base.html sudah terlalu besar (cek setelah edit)

---

## Architecture & Isolation

- **Komponen `_progress.html`** adalah single source of truth — ID auto-generated per form via Jinja loop counter atau hardcoded suffix per form (e.g., `#research-progress`, `#generate-progress`)
- **JS hook** di base.html tidak tahu tentang phase spesifik — baca dari `data-phase` attribute. Loose coupling between hook & component.
- **CSS animation** `.progress-shine` sudah ada di base.html (line 48-57), tidak perlu tambahan keyframe baru
- **No backend changes** — semua kontrol ada di client side

---

## Error Handling

| Trigger | Handling |
|---------|----------|
| Network error | `htmx:sendError` → label amber "Connection error", border amber |
| Server 500 | `htmx:responseError` → label "Server error", border red |
| Timeout (none configured, opsional bisa ditambah via `hx-trigger="..."`) | sama dengan responseError |
| JS disabled | Spinner fallback di HTML tetap muncul via `.htmx-indicator` (backwards compat) |
| Double submit | Sudah di-block via `run-btn.disabled = true` di base.html line 92-106 |

---

## Testing

### Unit (Jest/Vitest — optional, jika ada infra)
- `computeWidth(elapsedMs)` returns correct capped percentage
- `formatElapsed(ms)` returns `M:SS`

### Manual verification
1. Buka `/pipeline` di Web UI
2. Klik tombol Run di tiap phase (research, discover, generate, score)
3. Verifikasi:
   - Progress bar muncul di bawah tombol dalam 100ms
   - Elapsed counter update tiap detik
   - Bar shimmer animasi terlihat
   - Bar berhenti di ~92% sebelum response
   - Saat response, bar loncat ke 100% lalu fade
   - Label ganti ke "Done" / "Error occurred" sesuai status
4. Test pada phase `discover` saat tidak ada `state.web_data` (loading lebih cepat)
5. Resize browser ke mobile width — pastikan layout tidak overflow
6. Test rapid double-click — submit kedua ter-block (sudah ada)

### Accessibility
- `role="status"` + `aria-live="polite"` — screen reader mengumumkan perubahan
- Visible focus ring pada tombol (sudah ada di Tailwind default)
- Counter text dengan monospace font tidak membuat layout shift

---

## YAGNI Check

- ❌ Tidak tambah persentase pasti (fake-accurate)
- ❌ Tidak tambah fase rotation animation (overkill)
- ❌ Tidak ubah backend
- ❌ Tidak tambah SSE endpoint untuk real progress
- ❌ Tidak redesign tombol
- ❌ Tidak tambah cancel button (htmx cancel via ESC, opsional)

Yang dipakai: komponen minimal yang langsung menyelesaikan masalah user — "loading yang muter-muter doang" jadi "loading yang kasih gambaran waktu".
