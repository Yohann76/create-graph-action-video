#!/usr/bin/env python3
"""
Investment Graph Video Generator
Usage: python3 render.py [--scenario scenario.json]
"""

import argparse
import asyncio
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[ERROR] Playwright not installed. Run: pip install playwright && python3 -m playwright install chromium")
    sys.exit(1)

import fetcher

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30


def ensure_d3(project_dir: Path):
    d3_path = project_dir / "d3.v7.min.js"
    if not d3_path.exists():
        url = "https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"
        print("[INFO] Downloading D3.js v7...")
        urllib.request.urlretrieve(url, d3_path)
        print(f"[INFO] D3.js saved to {d3_path}")


def start_http_server(directory: Path, port: int) -> http.server.HTTPServer:
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None
    original_dir = os.getcwd()
    os.chdir(directory)
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.chdir(original_dir)
    return server


async def capture_via_playwright(project_dir: Path, duration: float, port: int) -> Path:
    server = start_http_server(project_dir, port)
    print(f"[INFO] HTTP server on port {port}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                f"--window-size={WIDTH},{HEIGHT}",
            ],
        )

        video_dir = Path(tempfile.mkdtemp())
        context = await browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1,
            record_video_dir=str(video_dir),
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        page = await context.new_page()

        url = f"http://127.0.0.1:{port}/index.html"
        print(f"[INFO] Loading {url}")
        await page.goto(url, wait_until="networkidle")

        print(f"[INFO] Rendering animation (~{duration:.0f}s)...")
        timeout_ms = int((duration + 30) * 1000)
        await page.wait_for_function(
            "() => window.__RENDER_DONE__ === true",
            timeout=timeout_ms,
        )
        await asyncio.sleep(1.0)

        webm_path = Path(await page.video.path())
        await page.close()
        await context.close()
        await browser.close()

    server.shutdown()
    return webm_path


def encode_video(webm_path: Path, output_path: Path, fps: int):
    print("[INFO] Encoding MP4...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(webm_path),
        "-r", str(fps),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "medium",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("[ERROR] FFmpeg encoding failed:")
        print(result.stderr)
        sys.exit(1)
    webm_path.unlink(missing_ok=True)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def main():
    parser = argparse.ArgumentParser(description="Investment Graph Video Generator")
    parser.add_argument("--scenario", default="scenario.json")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        alt = script_dir / "output" / "scenarios" / args.scenario
        if alt.exists():
            scenario_path = alt
        else:
            print(f"[ERROR] Scenario not found: {scenario_path}")
            sys.exit(1)

    with open(scenario_path) as f:
        scenario = json.load(f)

    project_dir = script_dir

    # ── D3.js (download once if missing) ─────────────────────────────────────
    ensure_d3(project_dir)

    # ── Fetch & compute data ──────────────────────────────────────────────────
    ticker = scenario["data"]["ticker"]
    print(f"[INFO] Fetching data for {ticker}...")
    computed = fetcher.fetch_and_compute(scenario["data"])
    print(f"[INFO] {len(computed['series'])} trading days | dividends: {computed['has_dividends']}")

    # ── Write computed JSON for the HTML ──────────────────────────────────────
    computed_path = project_dir / "_computed.json"
    with open(computed_path, "w") as f:
        json.dump({
            "text":     scenario["text"],
            "video":    scenario["video"],
            "computed": computed,
        }, f)

    # ── Capture + encode ──────────────────────────────────────────────────────
    duration = float(scenario["video"]["duration_seconds"])
    fps      = int(scenario["video"].get("fps", FPS))
    videos_dir = script_dir / "output" / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    output   = videos_dir / Path(scenario["video"]["output"]).name
    port     = 9754

    webm_path = asyncio.run(capture_via_playwright(project_dir, duration, port))
    encode_video(webm_path, output, fps)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    computed_path.unlink(missing_ok=True)

    final_dur = probe_duration(output)
    print(f"[DONE] {output.resolve()}")
    print(f"       {final_dur:.1f}s | {fps}fps")


if __name__ == "__main__":
    main()
