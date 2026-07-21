# Pipeline Wizard UI Design

## Overview

Redesign the pipeline page from a tab-based interface to a unified vertical wizard flow. Each step (Research → Discover → Generate → Score → Export) appears as a sequential card with clear status indicators, data summaries, and keep/discard/ regenerate functionality.

## Current State

- **File**: `fp/web/templates/pipeline.html`
- **Partials**: `fp/web/templates/partials/*.html`
- **Routes**: `fp/web/routes/pipeline.py`
- **Tech**: FastAPI + Jinja2 + HTMX + Tailwind CSS (dark slate theme)

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Approach | Full HTMX Wizard | Consistent with existing stack, server-side rendering |
| Layout | Vertical (scroll) | Simple, mobile-friendly, clear progression |
| Theme | Keep existing dark slate | No disruption, PRODUCT.md says "professional restraint" |
| Keep/Discard | Checkbox mode | User confirmed: must keep ≥1 item to continue |
| Regenerate | Per focus level | Not per individual prompt |
| Data display | Summary view | Count + highlights, not full data dump |

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [1] Research  →  [2] Discover  →  [3] Generate    │
│       ✓              ⏳              🔒              │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Research Queries                                 ✓  │
│ ─────────────────────────────────────────────────── │
│ Generated 12 queries for brand analysis            │
│                                                    │
│ ☑ "What is [Brand]?"                               │
│ ☑ "[Brand] vs competitors"                         │
│ ☑ "[Brand] pricing"                                │
│ ☐ "[Brand] reviews 2024"                           │
│                                                    │
│ [Regenerate Selected] [Continue to Discover →]     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Discover Focus Areas                            🔒  │
│ (locked until Research completes)                  │
└─────────────────────────────────────────────────────┘
```

## Status Indicators

| Status | Icon | Badge Class | Description |
|--------|------|-------------|-------------|
| Locked | 🔒 | `bg-slate-700 text-slate-400` | Cannot run yet |
| Ready | ○ | `bg-blue-500/20 text-blue-400` | Can run now |
| Loading | ⏳ | `bg-blue-500 text-white status-pulse` | Currently running |
| Complete | ✓ | `bg-emerald-500/20 text-emerald-400` | Done, data available |
| Failed | ✗ | `bg-red-500/20 text-red-400` | Error, retry needed |

## Step Content Template

Each step card follows this structure:

```html
<div class="bg-slate-800 rounded-xl border border-slate-700/50 p-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-white">Step Name</h3>
    <span class="badge">Status</span>
  </div>
  
  <!-- Summary -->
  <p class="text-sm text-slate-400 mb-4">Summary text here</p>
  
  <!-- Item List (when complete) -->
  <div class="space-y-2">
    <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30">
      <input type="checkbox" class="rounded" />
      <span class="text-slate-200">Item text</span>
    </label>
  </div>
  
  <!-- Actions -->
  <div class="flex gap-3 mt-4">
    <button class="px-4 py-2 bg-blue-600 text-white rounded-lg">Run</button>
    <button class="px-4 py-2 bg-slate-600 text-white rounded-lg">Continue →</button>
  </div>
</div>
```

## Backend Changes

### New Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/pipeline/wizard` | Full wizard page (replaces tabs) |
| GET | `/api/pipeline/step/{step}` | Step partial with items |
| POST | `/api/pipeline/step/{step}/keep` | Keep selected items |
| POST | `/api/pipeline/step/{step}/regenerate` | Regenerate selected items |
| GET | `/api/pipeline/step/{step}/status` | Step status check |

### Step Data Flow

1. **Research**: Queries → checkbox → keep → advance
2. **Discover**: Focus areas → checkbox → keep → advance
3. **Generate**: Prompts per focus → checkbox → keep → advance
4. **Score**: Scored prompts → checkbox → keep → advance
5. **Export**: Download report

### Keep/Regenerate Logic

```python
# Keep items
@app.post("/api/pipeline/step/{step}/keep")
async def keep_items(step: str, item_ids: List[int]):
    # Mark kept items in database
    # Discard unchecked items
    return {"status": "ok", "kept": len(item_ids)}

# Regenerate per focus
@app.post("/api/pipeline/step/{step}/regenerate")  
async def regenerate(step: str, focus_id: int):
    # Delete existing items for this focus
    # Re-run generation for this focus only
    return {"status": "ok", "regenerated": focus_id}
```

## JavaScript Interactions

### Checkbox State Management

```javascript
// Enable/disable Continue button based on selections
document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
  cb.addEventListener('change', updateContinueButton);
});

function updateContinueButton() {
  const checked = document.querySelectorAll('input[type="checkbox"]:checked').length;
  const continueBtn = document.getElementById('continue-btn');
  continueBtn.disabled = checked === 0;
}
```

### Step Navigation

```javascript
// Auto-scroll to next step after Continue
function continueToNext(currentStep) {
  const nextStep = getNextStep(currentStep);
  // Scroll to next step
  document.getElementById(`step-${nextStep}`).scrollIntoView({ behavior: 'smooth' });
  // Load step content via HTMX
  htmx.trigger(`#step-${nextStep}`, 'loadStep');
}
```

## File Changes

### Modified Files

1. `fp/web/templates/pipeline.html` - Complete rewrite to wizard layout
2. `fp/web/routes/pipeline.py` - Add keep/regenerate endpoints

### New Files

1. `fp/web/templates/partials/wizard-step.html` - Reusable step component
2. `fp/web/static/js/wizard.js` - Wizard-specific interactions (optional, can inline)

## Acceptance Criteria

- [ ] Vertical wizard layout with 5 sequential steps
- [ ] Clear status indicators (locked, ready, loading, complete, failed)
- [ ] Summary data displayed after each step completes
- [ ] Checkbox-based keep/discard mechanism
- [ ] Continue button disabled when nothing selected
- [ ] Regenerate per focus level
- [ ] Smooth scroll to next step on Continue
- [ ] Responsive design (mobile-friendly)
- [ ] Uses existing dark slate theme and components

## Implementation Order

1. Create wizard-step.html partial template
2. Rewrite pipeline.html with vertical wizard layout
3. Add keep/regenerate backend routes
4. Implement checkbox state management
5. Add step navigation logic
6. Test full workflow end-to-end
