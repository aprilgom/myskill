#!/usr/bin/env python3
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_fixture(root):
    (root / "src").mkdir()
    (root / "src" / "App.jsx").write_text(
        """
export default function App() {
  return (
    <main className="brand-shell">
      <section className="hero">
        <img src="/studio.webp" alt="Studio product context" />
        <p className="brand">Northline Studio</p>
        <h1>Northline Studio</h1>
        <p>Editorial tools for calm production teams.</p>
        <a className="cta">Start</a>
      </section>
      <section><h2>One workflow</h2><p>One focused section.</p></section>
    </main>
  )
}
""",
        encoding="utf-8",
    )
    (root / "src" / "style.css").write_text(
        """
:root { --ink: #1d1c18; --paper: #f6f2ea; --accent: #0d6b68; }
@font-face { font-family: "Editorial"; src: url("/editorial.woff2"); }
body { margin: 0; font-family: "Editorial", Georgia, serif; background: linear-gradient(120deg, #f6f2ea, #eef3ec); color: var(--ink); }
.hero { min-height: 100dvh; display: grid; place-items: center; background-image: url('/studio.webp'); background-size: cover; }
.cta { transition: transform .2s ease, opacity .2s ease; }
@keyframes enter { from { opacity: 0; transform: translateY(12px); } }
@media (max-width: 760px) { .hero { min-height: 92dvh; padding: 24px; } }
@media (prefers-reduced-motion: reduce) { * { animation: none; transition: none; } }
""",
        encoding="utf-8",
    )
    (root / "public-image.png").write_bytes(b"\x89PNG\r\n")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp) / "fixture"
        fixture.mkdir()
        write_fixture(fixture)
        score_path = Path(tmp) / "score.json"
        html_path = Path(tmp) / "map.html"

        subprocess.run([
            "python3", str(ROOT / "scripts" / "score.py"), str(fixture),
            "--json", str(score_path), "--markdown"
        ], check=True)
        data = json.loads(score_path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert 0 <= data["score"] <= 100
        assert len(data["categories"]) == 9
        assert data["actions"]
        assert any("manual" in gap["reason"] for gap in data["extraction_gaps"])

        subprocess.run([
            "python3", str(ROOT / "scripts" / "render_dashboard.py"), str(score_path),
            "--template", str(ROOT / "assets" / "template.html"),
            "--out", str(html_path)
        ], check=True)
        html = html_path.read_text(encoding="utf-8")
        assert "Frontend Design Cartography" in html
        assert "{{" not in html and "}}" not in html
        assert html_path.stat().st_size > 1000
    print("self_test passed")


if __name__ == "__main__":
    main()
