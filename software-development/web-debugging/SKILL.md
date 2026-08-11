---
name: web-debugging
description: "Debug web UI issues: CSS conflicts, layout problems, missing content, visual bugs."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, web, css, ui, frontend, visual-bugs]
    related_skills: [systematic-debugging, test-driven-development]
---

# Web Debugging

## Overview

Web UI bugs often look like "missing content" but are actually CSS conflicts, specificity issues, or layout problems. Jumping to complex solutions (adding new content, restructuring HTML) without diagnosing WHY existing content isn't visible is the #1 mistake.

**Core principle:** Diagnose visibility BEFORE adding content. Check CSS conflicts BEFORE assuming the DOM is wrong.

## When to Use

Use for ANY web UI issue:
- Content appears "missing" or blank
- Layout looks wrong
- Styles don't apply as expected
- Visual bugs in browsers
- Responsive design issues
- CSS not loading or applying

**Use this ESPECIALLY when:**
- User says "content is missing" or "page is blank"
- Elements exist in DOM but aren't visible
- Styles seem to be overridden
- Layout breaks on certain screen sizes

## The Debugging Sequence

### Phase 1: Verify Content Exists

**BEFORE assuming content is missing:**

1. **Check the DOM** — Does the element exist in the HTML?
   ```bash
   curl -s http://example.com/page | grep "element-class"
   ```

2. **Check for CSS conflicts** — Search the ENTIRE CSS file for the class:
   ```bash
   grep -n "element-class" styles.css
   ```

3. **Look for later rules that override** — CSS specificity wins. A rule at line 2000 can override a rule at line 100.

4. **Inspect computed styles** — Use browser dev tools to see what actually applies.

### Phase 2: Identify the Conflict

**Common CSS conflict patterns:**

1. **Later rule overrides earlier rule:**
   ```css
   /* Line 100 */
   .hero { background: #242128; color: #fff; }
   
   /* Line 2000 */
   .page-header, .hero { background: #fff; }  /* ← This wins */
   ```

2. **Higher specificity wins:**
   ```css
   .hero { background: #242128; }  /* specificity: 0,1,0 */
   body .hero { background: #fff; }  /* specificity: 0,1,1 — wins */
   ```

3. **!important overrides everything:**
   ```css
   .hero { background: #242128; }
   .other { background: #fff !important; }  /* ← This wins */
   ```

### Phase 3: Fix the Root Cause

**Fix patterns (in order of preference):**

1. **Remove the conflicting selector** from the later rule:
   ```css
   /* Before */
   .page-header, .hero { background: #fff; }
   
   /* After */
   .page-header { background: #fff; }
   ```

2. **Increase specificity** of the intended rule:
   ```css
   /* Before */
   .hero { background: #242128; }
   
   /* After */
   body .hero { background: #242128; }
   ```

3. **Move the rule later** in the CSS file (last rule wins at same specificity).

4. **Use !important** (last resort — indicates a specificity war):
   ```css
   .hero { background: #242128 !important; }
   ```

## Common Mistakes

| Mistake | Reality |
|---------|---------|
| "Content is missing, let me add it" | Content exists but is hidden by CSS. Check visibility first. |
| "Let me restructure the HTML" | HTML is fine. CSS conflict is hiding it. |
| "Let me add a background image" | Background is fine. Text color conflicts with background. |
| "Let me add overlay layers" | Overcomplicating. The bug is a one-line CSS conflict. |
| "Let me change the layout" | Layout is fine. Specificity issue is overriding styles. |

## Real-World Example

**Symptom:** Agent page hero section appears blank (white background, white text invisible).

**Wrong approach:** Generate an image, add overlay layers, restructure HTML.

**Right approach:**
1. Check DOM: `<section class="agent-hero">` exists ✓
2. Search CSS: `grep -n "agent-hero" styles.css`
3. Find conflict: Line 2000 has `.agent-hero { background: #fff; }`
4. Fix: Remove `.agent-hero` from that selector.

**Result:** One-line fix instead of 50-line complex solution.

## Diagnostic Commands

```bash
# Check if element exists in DOM
curl -s http://example.com/page | grep "element-class"

# Find all CSS rules for a class
grep -n "element-class" styles.css

# Check for background conflicts
grep -n "background.*#fff" styles.css | grep "element-class"

# Check computed styles (browser dev tools)
# Right-click element → Inspect → Computed tab
```

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Verify** | Check DOM, search CSS, inspect computed styles | Content exists, conflict identified |
| **2. Identify** | Find the conflicting rule, understand specificity | Know which rule wins and why |
| **3. Fix** | Remove conflict, increase specificity, or move rule | Styles apply as intended |

## Red Flags — STOP and Diagnose

If you catch yourself thinking:
- "The content is missing, let me add it"
- "Let me generate an image for this"
- "Let me restructure the HTML"
- "Let me add overlay layers"
- "Let me change the layout"

**STOP.** Check the DOM first. Check CSS conflicts first. The content is probably there but hidden.

**Remember:** A one-line CSS conflict is more likely than a missing feature. Diagnose before building.
