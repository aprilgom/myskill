#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REFERENCE = """# Acme — Style Reference
> Clean dark orange product system.

**Theme:** dark

## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Night | `#101010` | `--color-night` | Page background |
| Cream | `#fff4e8` | `--color-cream` | Primary text |
| Orange | `#ff6a00` | `--color-orange` | Primary calls to action |

## Tokens — Typography

### Acme Sans — Primary text. · `--font-acme-sans`
- **Substitute:** Inter
- **Weights:** 400, 700
- **Sizes:** 16px, 32px, 72px
- **Line height:** 1.00, 1.20
- **Letter spacing:** -0.02em at large sizes
- **Role:** Primary text.

### Type Scale

| Role | Size | Line Height | Letter Spacing | Token |
|------|------|-------------|----------------|-------|
| body | 16px | 1.2 | — | `--text-body` |
| display | 72px | 1 | -0.02px | `--text-display` |

## Tokens — Spacing & Shapes

**Base unit:** 4px

**Density:** comfortable

### Spacing Scale

| Name | Value | Token |
|------|-------|-------|
| 16 | 16px | `--spacing-16` |
| 32 | 32px | `--spacing-32` |

### Border Radius

| Element | Value |
|---------|-------|
| buttons | 24px |
| cards | 12px |

### Layout

- **Section gap:** 32px
- **Card padding:** 16px
- **Element gap:** 16px

## Components

### Primary Action Button
**Role:** Main CTA.

Background: Orange (#ff6a00), Text: Night (#101010), Border Radius: 24px.

## Do's and Don'ts

### Do
- Use Orange (#ff6a00) for primary actions.

### Don't
- Do not introduce complex gradients or shadows.

## Imagery

Use product screenshots and restrained icons.

## Layout

Use a dark full-bleed hero with compact centered sections.

## Agent Prompt Guide

Quick Color Reference:
text: #fff4e8
background: #101010
accent: #ff6a00
primary action: #ff6a00 (filled action)

## Quick Start

### CSS Custom Properties

```css
:root {
  --color-night: #101010;
  --color-cream: #fff4e8;
  --color-orange: #ff6a00;
  --font-acme-sans: 'Acme Sans', Inter, sans-serif;
}
```
"""


CSS = """:root {
  --color-night: #101010;
  --color-cream: #fff4e8;
  --color-orange: #ff6a00;
  --font-acme-sans: 'Acme Sans', Inter, sans-serif;
  --text-body: 16px;
  --text-display: 72px;
  --spacing-16: 16px;
  --spacing-32: 32px;
}
body { background: var(--color-night); color: var(--color-cream); font-family: var(--font-acme-sans); }
.hero { padding: 32px; }
.button { background: #ff6a00; color: #101010; border-radius: 24px; padding: 16px 32px; letter-spacing: -0.02em; }
.card { border-radius: 12px; padding: 16px; }
"""


def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ref = root / "design.md"
        app = root / "app"
        app.mkdir()
        ref.write_text(REFERENCE, encoding="utf-8")
        (app / "globals.css").write_text(CSS, encoding="utf-8")
        (app / "page.tsx").write_text("export default function Page(){return <button className='button'>Start</button>}", encoding="utf-8")
        score_json = root / "score.json"
        out_html = root / "map.html"
        run(sys.executable, str(ROOT / "scripts" / "score.py"), str(app), "--reference", str(ref), "--json", str(score_json), "--markdown")
        result = json.loads(score_json.read_text(encoding="utf-8"))
        assert result["score"] >= 65, result["score"]
        assert result["reference"]["brand"] == "Acme"
        assert result["categories"]
        assert result["actions"]
        assert result["manual_review_gaps"]
        run(sys.executable, str(ROOT / "scripts" / "render_dashboard.py"), str(score_json), "--template", str(ROOT / "assets" / "template.html"), "--out", str(out_html))
        html = out_html.read_text(encoding="utf-8")
        assert "Refero Design Adherence Map" in html
        assert "{{" not in html and "}}" not in html
    print("self_test passed")


if __name__ == "__main__":
    main()
