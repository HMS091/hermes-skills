# Hermes Browser Console Data Extraction Patterns

When `browser_snapshot` truncates (>8000 chars) or the accessibility tree doesn't show rich content, use `browser_console` with JavaScript expressions to extract data directly from the rendered DOM.

## URL & Page Structure

```javascript
// Current page URL
window.location.href

// Page title
document.title

// All heading hierarchy (great for page structure overview)
[...document.querySelectorAll('h1,h2,h3,h4')].map(h => h.textContent.trim()).join('\n')

// All visible links on page
[...document.querySelectorAll('a[href]')].map(a => ({text: a.textContent.trim().slice(0,60), href: a.href}))
```

## Text Search & Extraction

```javascript
// Check if keyword exists in page
document.body.innerText.includes('keyword')

// Get text around a specific keyword
const body = document.body.innerText;
const idx = body.indexOf('keyword');
body.substring(Math.max(0, idx-200), idx+1000)

// Search for multiple keywords in order
['revenue', 'users', 'growth'].forEach(kw => {
  const pos = body.indexOf(kw);
  if (pos > -1) console.log(kw + ':', body.substring(Math.max(0,pos-100), pos+200));
});

// Get all text matching a pattern (e.g. dollar amounts)
body.match(/\$\d[\d,.]*[BMK]?/g)

// Extract all sentences mentioning a company/product
body.match(/[^.]*?Saily[^.]*\./g)
```

## Link & Element Discovery

```javascript
// Find link by partial text
const links = [...document.querySelectorAll('a')];
links.filter(l => l.textContent.includes('Impact Report')).map(l => l.href)

// Find link by href pattern
links.filter(l => l.href.includes('transparency') || l.href.includes('impact')).map(l => l.href)

// Find specific element by content
[...document.querySelectorAll('button, [role="button"], summary')]
  .filter(el => el.textContent.includes('commission'))

// Check if SPA content loaded (page may look empty but JS has rendered content)
document.querySelector('#content, [data-loaded], [class*="content"]')?.textContent?.length
```

## Page State Inspection

```javascript
// Check if a disclosure/accordion element was expanded
document.querySelector('[aria-expanded="true"]')?.textContent?.slice(0, 100)

// See what's currently visible (not display:none)
[...document.querySelectorAll('*')].filter(el => {
  const style = getComputedStyle(el);
  return style.display !== 'none' && style.visibility !== 'hidden';
}).length

// Check for iframes on the page
[...document.querySelectorAll('iframe')].map(f => f.src || f.id)
```

## Single-Line Extraction (for terminal piping)

For quick one-liners that return a JSON string:

```javascript
JSON.stringify([...document.querySelectorAll('h2')].map(h => h.textContent.trim()))
```

## Limitations

- `console.log()` output is captured only if the expression returns a value AND the tool result shows it
- For multi-line debugging, return a single concatenated string at the end
- Very long strings (>50KB) may be silently truncated
- The browser console does NOT have access to tool functions — only standard DOM/browser APIs
