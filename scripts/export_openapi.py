"""Export the FastAPI OpenAPI schema and generate a static Swagger UI page.

Usage:
    uv run python scripts/export_openapi.py [--out-dir <dir>]

Output:
    <out-dir>/openapi.json   — raw schema (also useful for client codegen)
    <out-dir>/index.html     — self-contained Swagger UI page
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when the script is run directly.
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Provide minimal env so pydantic-settings doesn't complain about a missing
# .env file when running in CI (defaults are fine for schema export).
os.environ.setdefault("APP_SECRET_KEY", "ci-placeholder-not-used-for-schema-export")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://ci:ci@localhost/ci")

from app.main import app  # noqa: E402 — import after path/env setup


def export(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    schema = app.openapi()
    title = schema.get("info", {}).get("title", "API Docs")
    version = schema.get("info", {}).get("version", "")

    # ── openapi.json ─────────────────────────────────────────────────
    json_path = out_dir / "openapi.json"
    json_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"  wrote {json_path}")

    # ── index.html — Swagger UI loading the schema from the same dir ─
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} {version}</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    body {{ margin: 0; }}
    #swagger-ui .topbar {{ display: none; }}   /* hide the default swagger topbar */
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => {{
      SwaggerUIBundle({{
        url: "openapi.json",
        dom_id: "#swagger-ui",
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
        layout: "BaseLayout",
        deepLinking: true,
        displayRequestDuration: true,
        filter: true,
      }});
    }};
  </script>
</body>
</html>
"""
    html_path = out_dir / "index.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  wrote {html_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export OpenAPI docs as static Swagger UI")
    parser.add_argument("--out-dir", default="_site", help="Output directory (default: _site)")
    args = parser.parse_args()

    out = Path(args.out_dir)
    print(f"Exporting OpenAPI docs → {out}/")
    export(out)
    print("Done.")
