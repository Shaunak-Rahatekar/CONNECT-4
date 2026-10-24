"""
build.py — Connect-4 Application Static & Serverless Build Generator.

Generates a self-contained 'build/' directory suitable for:
1. Direct Netlify Drag & Drop (Manual Deploy in app.netlify.com).
2. Netlify CLI deployment ('netlify deploy --dir=build --prod').
3. Static preview serving ('python -m http.server --directory build').
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Ensure root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app  # noqa: E402


def build_project() -> None:
    build_dir = PROJECT_ROOT / "build"
    print(f"[*] Starting build process...")
    print(f"[*] Target build directory: {build_dir}")

    # 1. Clean and re-create build directory
    if build_dir.exists():
        print(f"[-] Cleaning existing build/ directory...")
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    # 2. Render static index.html via Flask test client
    print(f"[+] Rendering static index.html from Jinja2 templates...")
    with app.test_client() as client:
        res = client.get("/")
        if res.status_code != 200:
            print(f"[!] Error: Failed to render index.html (status code {res.status_code})")
            sys.exit(1)
        
        index_html = res.data.decode("utf-8")
        index_path = build_dir / "index.html"
        index_path.write_text(index_html, encoding="utf-8")
        print(f"[OK] Rendered index.html ({len(index_html):,} bytes)")

    # 3. Copy static directory (css, js) into build/static
    print(f"[+] Copying static assets (CSS, JavaScript)...")
    static_src = PROJECT_ROOT / "static"
    static_dest = build_dir / "static"
    shutil.copytree(static_src, static_dest)
    print(f"[OK] Copied static/ to build/static/")

    # 4. Generate _redirects file for Netlify edge routing
    print(f"[+] Generating Netlify _redirects file...")
    redirects_content = (
        "# Netlify Edge Redirect Rules for Connect-4 DAA\n"
        "# 1. Serve static assets directly from CDN\n"
        "/static/*   /static/:splat   200\n"
        "\n"
        "# 2. Route all API calls to the serverless Python backend\n"
        "/api/*      /.netlify/functions/app   200\n"
        "\n"
        "# 3. Fallback for client-side navigation\n"
        "/*          /index.html   200\n"
    )
    (build_dir / "_redirects").write_text(redirects_content, encoding="utf-8")
    print(f"[OK] Generated build/_redirects")

    # 5. Copy runtime.txt and requirements.txt for build metadata
    shutil.copy(PROJECT_ROOT / "runtime.txt", build_dir / "runtime.txt")
    shutil.copy(PROJECT_ROOT / "requirements.txt", build_dir / "requirements.txt")
    print(f"[OK] Copied runtime.txt and requirements.txt")

    # 6. Copy serverless function into build/.netlify/functions/
    netlify_func_src = PROJECT_ROOT / "netlify" / "functions"
    netlify_func_dest = build_dir / ".netlify" / "functions"
    netlify_func_dest.mkdir(parents=True, exist_ok=True)
    for func_file in netlify_func_src.glob("*.py"):
        shutil.copy(func_file, netlify_func_dest / func_file.name)
    print(f"[OK] Bundled serverless functions to build/.netlify/functions/")

    print("\n" + "=" * 60)
    print(" BUILD SUCCESSFUL! ")
    print("=" * 60)
    print(f"Output folder: {build_dir}")
    print("\nHow to deploy:")
    print("  Option A (Drag & Drop in Browser):")
    print("    1. Go to https://app.netlify.com/drop")
    print("    2. Drag and drop the 'build' folder into the browser window.")
    print("\n  Option B (Netlify CLI):")
    print("    Run: netlify deploy --dir=build --prod")
    print("=" * 60)


if __name__ == "__main__":
    build_project()
