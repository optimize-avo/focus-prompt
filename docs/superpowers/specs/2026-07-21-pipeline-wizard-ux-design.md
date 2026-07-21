# Pipeline Wizard UX Redesign

## Problem Statement

The current pipeline flow is confusing for non-technical digital marketers:

1. **"Seed" terminology** - Users don't understand what "seed queries" means
2. **Results not showing** - After running research, users must refresh to see results
3. **Confusing output** - "Generated 112 queries" doesn't match the 10-item checklist
4. **No review capability** - Users can't review and filter items before proceeding

## Design Goals

- Make pipeline flow understandable for non-technical users
- Allow review and curation at each step
- Auto-show results after each step (no refresh needed)
- Replace technical jargon with clear, descriptive language

## Approach

**UI + New API Endpoints** - Refactor wizard UI with step-by-step flow + add API endpoints for review/selection per step.

---

## Section 1: Wizard Layout

### Structure

Each step occupies its own page/view with:

- **Progress bar** at top showing: 1️⃣ → 2️⃣ → 3️⃣ → 4️⃣ → 5️⃣
- **Step title** - Clear, descriptive (e.g., "Langkah 1: Riset Query Real")
- **Step description** - Brief explanation of what this step does
- **Action buttons** - Back/Next navigation at bottom

### Navigation

```
[Back] ← → [Next/Lanjut]
```

- Back button returns to previous step (saves current state)
- Next button advances to next step (only enabled when step is complete)

---

## Section 2: Research Step

### Header

- **Title:** "Langkah 1: Riset Query Real"
- **Description:** "Kami akan mencari query real yang diketik orang di Google tentang layananmu."

### Pre-Run UI

Show auto-generated queries from brand info:

```
Query yang akan dicari:
• jasa desain murah
• platform desain terbaik
• Sribu review
• alternatif Sribu
• ... (generated from brand services + competitors)

[+ Tambah Query]  → Opens input field for manual query
[🔍 Mulai Riset]  → Starts research
```

### Post-Run UI (Auto-Show)

After research completes, automatically show results:

```
✓ Riset selesai!

📊 112 queries ditemukan dari Google
✅ 10 queries siap di-review (top picks)

[Review Semua Queries]  → Opens modal with all 112 queries
[Lanjut ke Discover →]
```

### Review Modal

Modal popup for reviewing all queries:

```
┌─────────────────────────────────────────────────────┐
│ Review Queries (112)                    [✕ Close]  │
├─────────────────────────────────────────────────────┤
│ 🔍 Search queries...                    [Select All]│
├─────────────────────────────────────────────────────┤
│ ☑ jasa desain murah                    [Relevant]  │
│ ☑ platform desain terbaik              [Relevant]  │
│ ☐ desain logo mahal                    [Relevant]  │
│ ☑ Sribu review                         [Relevant]  │
│ ... (scrollable list)                               │
├─────────────────────────────────────────────────────┤
│ Selected: 85 / 112                     [Simpan Pilihan] │
└─────────────────────────────────────────────────────┘
```

Features:
- Checkbox per query for select/deselect
- Search filter to find specific queries
- "Relevant" mark button to highlight important ones
- "Select All" / "Deselect All" toggle
- Count display: "Selected: X / Total"
- "Simpan Pilihan" saves selection and closes modal

---

## Section 3: Discover Step

### Header

- **Title:** "Langkah 2: Temukan Focus Areas"
- **Description:** "Kami akan menganalisis query dan menemukan topik-topik utama yang relevan dengan bisnismu."

### Pre-Run UI

```
Menggunakan 85 queries dari langkah sebelumnya.

[💡 Temukan Focus Areas]
```

### Post-Run UI (Auto-Show)

```
✓ Focus areas ditemukan!

📊 6 focus areas ditemukan

□ Desain Grafis (12 signals)
□ Programming (8 signals)
□ Copywriting (15 signals)
...

[Review Semua Focus]  → Opens modal
[Lanjut ke Generate →]
```

### Review Modal

Same pattern as Research modal - checkbox, search, select/deselect.

---

## Section 4: Generate Step

### Header

- **Title:** "Langkah 3: Generate Prompts"
- **Description:** "Kami akan membuat berbagai variasi prompt untuk setiap focus area."

### Pre-Run UI

```
Menggunakan 6 focus areas dari langkah sebelumnya.
Mode: Unbranded

[✨ Generate Prompts]
```

### Post-Run UI (Auto-Show)

```
✓ Prompts dihasilkan!

📊 85 prompts dihasilkan di 6 focus areas

Desain Grafis (15 prompts)
• Buat desain logo profesional...
• Cari desainer grafis terbaik...
...

Programming (12 prompts)
• ...

[Review Semua Prompts]  → Opens modal
[Lanjut ke Score →]
```

### Review Modal

Grouped by focus area:

```
┌─────────────────────────────────────────────────────┐
│ Review Prompts (85)                     [✕ Close]  │
├─────────────────────────────────────────────────────┤
│ 🔍 Search prompts...          [Expand All] [Collapse All]│
├─────────────────────────────────────────────────────┤
│ ▼ Desain Grafis (15)                               │
│   ☑ Buat desain logo profesional...                │
│   ☑ Cari desainer grafis terbaik...                │
│   ☐ Desain poster acara...                         │
│                                                    │
│ ▼ Programming (12)                                 │
│   ☑ Jasa pembuatan website...                      │
│   ...                                              │
├─────────────────────────────────────────────────────┤
│ Selected: 72 / 85                     [Simpan Pilihan] │
└─────────────────────────────────────────────────────┘
```

---

## Section 5: Score Step

### Header

- **Title:** "Langkah 4: Skor Relevansi"
- **Description:** "Kami akan menilai setiap prompt untuk relevansi dengan brand Anda."

### Pre-Run UI

```
Menggunakan 72 prompts dari langkah sebelumnya.

[📊 Mulai Scoring]
```

### Post-Run UI (Auto-Show)

```
✓ Scoring selesai!

📊 72 prompts scored
📈 Average score: 0.65
⚠️ 8 prompts need review

[Review Hasil Skor]  → Opens modal
[Lanjut ke Export →]
```

### Review Modal

Shows scored prompts with color-coded scores:

```
┌─────────────────────────────────────────────────────┐
│ Review Scores (72)                      [✕ Close]  │
├─────────────────────────────────────────────────────┤
│ 🔍 Search...              [Sort: Score ▼]          │
├─────────────────────────────────────────────────────┤
│ 🟢 0.85  Buat desain logo profesional...           │
│ 🟢 0.82  Cari desainer grafis terbaik...           │
│ 🟡 0.65  Jasa pembuatan website...                 │
│ 🔴 0.23  Desain poster acara...                    │
│ ...                                                │
└─────────────────────────────────────────────────────┘
```

---

## Section 6: Export Step

### Header

- **Title:** "Langkah 5: Export Hasil"
- **Description:** "Unduh hasil riset Anda dalam format yang diinginkan."

### UI

```
Ringkasan:
• 6 focus areas
• 72 prompts (8 need review)

[📥 Download CSV]  [📥 Download JSON]  [📋 Copy Markdown]
```

---

## API Endpoints (New)

### `POST /api/pipeline/step/{step}/selection`

Save user's selection for a step.

**Request:**
```json
{
  "selected_ids": ["query1", "query2", ...]
}
```

**Response:**
```json
{
  "status": "ok",
  "selected": 85,
  "total": 112
}
```

### `GET /api/pipeline/step/{step}/items`

Get all items for review modal.

**Response:**
```json
{
  "step": "research",
  "items": [
    {"id": "q1", "text": "jasa desain murah", "selected": true, "relevant": false},
    ...
  ],
  "total": 112,
  "selected_count": 85
}
```

### `PATCH /api/pipeline/step/{step}/items/{id}`

Update single item (toggle selection/relevant).

---

## Files to Modify

| File | Changes |
|------|---------|
| `fp/web/templates/pipeline.html` | Refactor to wizard step-by-step layout |
| `fp/web/routes/pipeline.py` | Add selection API endpoints, fix HTMX responses |
| `fp/web/static/js/wizard.js` | Add modal logic, selection management |
| `fp/web/templates/partials/*.html` | Update each step partial |
| `fp/web/static/css/custom.css` | Add modal styles if needed |

---

## Success Criteria

1. ✅ User can complete pipeline without confusion
2. ✅ Results auto-show after each step (no refresh)
3. ✅ User can review and filter items at each step
4. ✅ No technical jargon ("seed", "queries count mismatch")
5. ✅ Non-technical digital marketer can use without help
