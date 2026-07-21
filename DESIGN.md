---
name: Focus Prompt
description: AI Brand Visibility Research Tool — Unbranded Prompt Discovery
colors:
  midnight-navy: "#0f172a"
  deep-slate: "#1e293b"
  steel-gray: "#334155"
  muted-slate: "#475569"
  slate-border: "#47556980"
  bright-blue: "#2563eb"
  light-blue: "#60a5fa"
  blue-glow: "#3b82f633"
  pure-white: "#ffffff"
  cloud-white: "#e2e8f0"
  silver-text: "#94a3b8"
  ash-text: "#64748b"
  emerald-success: "#10b981"
  amber-warning: "#f59e0b"
  red-error: "#ef4444"
  yellow-review: "#facc15"
typography:
  display:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.2
  headline:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.3
  title:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    maxWidth: "75ch"
  label:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.05em"
    textTransform: uppercase
  mono:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: "0.375rem"
  md: "0.5rem"
  lg: "0.75rem"
  xl: "0.75rem"
  full: "9999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "1.5rem"
  "2xl": "2rem"
components:
  button-primary:
    backgroundColor: "{colors.bright-blue}"
    textColor: "{colors.pure-white}"
    rounded: "{rounded.lg}"
    padding: "0.5rem 1rem"
  button-primary-hover:
    backgroundColor: "#3b82f6"
    textColor: "{colors.pure-white}"
  card:
    backgroundColor: "{colors.deep-slate}"
    textColor: "{colors.cloud-white}"
    rounded: "{rounded.xl}"
    padding: "1.5rem"
  input:
    backgroundColor: "{colors.steel-gray}"
    textColor: "{colors.pure-white}"
    rounded: "{rounded.lg}"
    padding: "0.5rem 0.75rem"
  badge:
    backgroundColor: "{colors.blue-glow}"
    textColor: "{colors.light-blue}"
    rounded: "{rounded.full}"
    padding: "0.25rem 0.75rem"
  nav-link:
    backgroundColor: "transparent"
    textColor: "{colors.silver-text}"
    rounded: "{rounded.md}"
    padding: "0.375rem 0.75rem"
---

# Design System: Focus Prompt

## 1. Overview

**Creative North Star: "The Research Lab"**

Focus Prompt's design system embodies the precision and analytical rigor of a research laboratory. Every interface element serves a clear purpose — to surface data, guide analysis, and enable decisive action. The system rejects frivolous decoration in favor of functional clarity, treating every pixel as a tool in the researcher's workflow.

The midnight navy foundation creates a focused, distraction-free environment where data stands out against the darkness. Blue accents serve as beacons of action and status, drawing the eye to interactive elements and key metrics. The overall density is intentional — information is layered but never cluttered, with clear visual hierarchy guiding the user through complex multi-step workflows.

**Key Characteristics:**
- **Analytical precision**: Every element has a clear data role
- **Controlled density**: Information-rich without overwhelming
- **Action-oriented**: Clear affordances for every interactive element
- **Status-driven**: Color-coded feedback for pipeline progress and data quality

## 2. Colors

The palette is built on a midnight navy foundation with strategic blue accents for action and status feedback.

### Primary
- **Bright Blue** (#2563eb): Primary action color for buttons, active states, and key interactive elements. Used sparingly to maintain impact — reserved for "do this now" affordances.

### Secondary
- **Light Blue** (#60a5fa): Secondary accent for badges, highlights, and informational emphasis. Softer than primary, used for "note this" rather than "do this."

### Neutral
- **Midnight Navy** (#0f172a): Root background color. Creates the deep, focused environment where data takes center stage.
- **Deep Slate** (#1e293b): Card and panel backgrounds. Elevated from root to create subtle layering without shadows.
- **Steel Gray** (#334155): Input fields and interactive surfaces. One level above cards, indicating "you can interact with this."
- **Muted Slate** (#475569): Borders and dividers. Subtle structural elements that define space without competing with content.
- **Pure White** (#ffffff): Primary headings and high-emphasis text. Maximum contrast for scanability.
- **Cloud White** (#e2e8f0): Body text and secondary content. Comfortable reading contrast without the harshness of pure white.
- **Silver Text** (#94a3b8): Navigation links and tertiary content. Present but receded, supporting the hierarchy.
- **Ash Text** (#64748b): Muted labels and placeholder text. Lowest emphasis, still readable against backgrounds.

### Status
- **Emerald** (#10b981): Success states, completed actions, positive metrics.
- **Amber** (#f59e0b): Warning states, items needing attention, partial progress.
- **Red** (#ef4444): Error states, failed actions, critical issues.
- **Yellow** (#facc15): Review-needed states, items requiring human judgment.

### Named Rules

**The Beacon Rule.** Blue is reserved exclusively for actionable elements — buttons, active tabs, clickable badges. Never use blue for decorative purposes or static content. Its scarcity is the point.

**The Layering Rule.** Background depth follows a strict scale: root (navy) → cards (deep slate) → inputs (steel gray). Never invert this hierarchy. Shadows are not used; depth is conveyed through color alone.

## 3. Typography

**Display Font:** Inter (with system-ui fallback)
**Body Font:** Inter (with system-ui fallback)
**Mono Font:** JetBrains Mono (with monospace fallback)

**Character:** Clean, professional, and highly legible at all sizes. Inter's humanist design provides warmth without sacrificing the analytical precision the interface demands. The single-family approach maintains visual consistency across dense data displays.

### Hierarchy
- **Display** (700, 1.5rem, line-height 1.2): Page titles and primary headings. Used once per view to establish the screen's purpose.
- **Headline** (600, 1.25rem, line-height 1.3): Section headers and card titles. Groups related content and establishes scannable landmarks.
- **Title** (600, 1.125rem, line-height 1.4): Component-level headings. Labels for distinct UI regions within a section.
- **Body** (400, 0.875rem, line-height 1.5): Primary content text. Max line length 75ch for comfortable reading.
- **Label** (500, 0.75rem, letter-spacing 0.05em, uppercase): Field labels, column headers, and category markers. The uppercase treatment creates clear visual separation from content.
- **Mono** (400, 0.875rem, line-height 1.5): Code snippets, technical values, and data identifiers. Used sparingly for technical precision.

### Named Rules

**The Hierarchy Rule.** Every screen must have exactly one Display heading. All other text defers to the hierarchy — no skipping levels, no using bold body text as a substitute for proper headings.

## 4. Elevation

This system uses **tonal layering** instead of shadows. Depth is conveyed through progressively lighter background colors at each elevation level: root (midnight navy) → cards (deep slate) → inputs (steel gray). This approach maintains the flat, analytical aesthetic while providing clear spatial hierarchy.

### Named Rules

**The Flat-By-Default Rule.** No element has a shadow at rest. Hover states may use subtle background lightening (one step up the slate scale) to indicate interactivity. The absence of shadows reinforces the "research lab" aesthetic — clean, precise, no unnecessary visual noise.

## 5. Components

### Buttons
- **Shape:** Gently curved edges (0.75rem radius)
- **Primary:** Bright blue background (#2563eb), white text, 0.5rem 1rem padding. Used for primary actions — "Run", "Continue", "Submit".
- **Hover / Focus:** Lightens to #3b82f6 with subtle transition (200ms ease). Focus ring: 2px blue outline with 2px offset.
- **Secondary:** Steel gray background, white text. Used for secondary actions — "Cancel", "Back", "Skip".
- **Ghost:** Transparent background, silver text. Used for tertiary actions — "Learn more", "View details".

### Cards
- **Corner Style:** Sharp but friendly (0.75rem radius)
- **Background:** Deep slate (#1e293b) — elevated from root
- **Border:** Subtle muted slate border (1px, 47556980) — barely visible, just enough to define edges
- **Internal Padding:** 1.5rem — comfortable spacing for content
- **Shadow Strategy:** None. Depth via color layering only.

### Inputs
- **Style:** Steel gray background (#334155), muted slate border (1px solid #475569)
- **Focus:** Border shifts to bright blue, subtle blue ring appears (2px, #3b82f633)
- **Error:** Border shifts to red, error text appears below in red
- **Disabled:** Background darkens to deep slate, text mutes to ash

### Badges
- **Style:** Pill-shaped (9999px radius), blue glow background (#3b82f633), light blue text (#60a5fa)
- **State:** Static — no hover or active states. Pure informational.
- **Use:** Status indicators, count displays, category labels

### Navigation
- **Style:** Horizontal bar, deep slate background with subtle bottom border
- **Default:** Silver text (#94a3b8), transparent background
- **Hover:** White text, subtle slate-700 background
- **Active:** White text, subtle blue underline or left accent

### Pipeline Stepper (Signature Component)
- **Purpose:** Visual progress indicator for the 5-phase pipeline workflow
- **Shape:** Connected circles with horizontal lines between them
- **States:** Locked (muted), Ready (steel), Loading (blue pulse), Complete (emerald), Failed (red)
- **Behavior:** Current step highlighted, completed steps show checkmark, future steps dimmed

## 6. Do's and Don'ts

### Do:
- **Do** use blue exclusively for actionable elements — buttons, active states, clickable badges. Its restraint is the system's strength.
- **Do** maintain the layering hierarchy: root → cards → inputs. Never invert the depth scale.
- **Do** use uppercase labels with letter-spacing for field labels and category markers — they create clear visual separation from content.
- **Do** keep information density intentional — every element earns its space through data value or action affordance.
- **Do** use status colors (emerald, amber, red, yellow) consistently across all pipeline states and metrics.
- **Do** ensure body text hits 4.5:1 contrast against its background (cloud white on deep slate achieves this).

### Don't:
- **Don't** use shadows for elevation — the system is flat by design. Depth comes from color layering only.
- **Don't** use blue for decorative purposes, static content, or non-interactive elements. Blue means "you can do something with this."
- **Don't** invert the background hierarchy. Never put a lighter background inside a darker container.
- **Don't** use playful or gamified elements — no badges, achievements, confetti, or game-like interactions. This is a research tool, not a game.
- **Don't** use overly colorful or saturated accent schemes. The palette is intentionally muted to keep focus on data.
- **Don't** add gratuitous animations or transitions. Motion should be functional — indicating state changes, not decorating them.
- **Don't** use glassmorphism, gradient text, or other decorative effects. The aesthetic is clean, flat, and analytical.
