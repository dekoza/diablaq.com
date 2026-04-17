"""
Navigation walkthrough — records a video of the full site navigation.
Serves dist/ over HTTP and navigates using only nav links, breadcrumbs,
and comic covers/titles.
"""
from __future__ import annotations

import subprocess
import time
import signal
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

DIST = Path(__file__).resolve().parent.parent / "dist"
VIDEO_DIR = Path("/tmp/diablaq-nav-video")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
PORT = 9876
BASE = f"http://localhost:{PORT}"


def url(path: str) -> str:
    return f"{BASE}{path}"


def wait(page: Page, ms: int = 900) -> None:
    page.wait_for_timeout(ms)


def screenshot(page: Page, name: str) -> None:
    page.screenshot(path=str(VIDEO_DIR / f"{name}.png"), full_page=False)
    print(f"    📸 {name}.png")


def run() -> None:
    # Start HTTP server
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--directory", str(DIST)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.0)
    print(f"Server started at {BASE}")

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            ctx = browser.new_context(
                viewport={"width": 1440, "height": 900},
                record_video_dir=str(VIDEO_DIR),
                record_video_size={"width": 1440, "height": 900},
            )
            page = ctx.new_page()

            # ── 1. Homepage ───────────────────────────────────────────────────
            print("\n[1] Homepage")
            page.goto(url("/"))
            page.wait_for_load_state("domcontentloaded")
            wait(page, 1500)
            screenshot(page, "01-homepage")

            # ── 2. Click "Komiksy" in nav ─────────────────────────────────────
            print("[2] Nav → Komiksy (catalog)")
            page.locator("nav.nav-desktop a", has_text="Komiksy").first.click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 1200)
            screenshot(page, "02-catalog")

            # ── 3. Click first project cover ──────────────────────────────────
            print("[3] First project cover → project page")
            page.locator(".project-card__cover").first.click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 1200)
            screenshot(page, "03-project-page")

            # ── 4. Breadcrumb → back to Komiksy ───────────────────────────────
            print("[4] Breadcrumb → Komiksy")
            page.locator(".breadcrumb a", has_text="Komiksy").click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 900)

            # ── 5. Multi-edition project (Kodiak) ─────────────────────────────
            print("[5] Catalog → Kodiak")
            kodiak = page.locator(".project-card__title a", has_text="Kodiak").first
            if kodiak.count() > 0:
                kodiak.click()
            else:
                # fallback: pick something with editions
                page.locator(".project-card__title a").nth(3).click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 1200)
            screenshot(page, "05-kodiak")

            # ── 6. Click first edition tile ───────────────────────────────────
            print("[6] Edition tile → edition page")
            tile = page.locator(".edition-tile__cover").first
            if tile.count() > 0:
                tile.click()
                page.wait_for_load_state("domcontentloaded")
                wait(page, 1200)
                screenshot(page, "06-edition-page")

                # ── 7. Breadcrumb → project ───────────────────────────────────
                print("[7] Breadcrumb → project")
                crumbs = page.locator(".breadcrumb a")
                if crumbs.count() >= 2:
                    crumbs.last.click()
                    page.wait_for_load_state("domcontentloaded")
                    wait(page, 900)

                # ── 8. Breadcrumb → Komiksy ───────────────────────────────────
                print("[8] Breadcrumb → Komiksy")
                kc = page.locator(".breadcrumb a", has_text="Komiksy")
                if kc.count() > 0:
                    kc.click()
                else:
                    page.locator("nav.nav-desktop a", has_text="Komiksy").first.click()
                page.wait_for_load_state("domcontentloaded")
                wait(page, 900)

            # ── 9. One-shot: Mama zabiła mi psa ──────────────────────────────
            print("[9] Catalog → Mama zabiła mi psa (one-shot)")
            mama = page.locator(".project-card__title a", has_text="Mama").first
            if mama.count() > 0:
                mama.click()
                page.wait_for_load_state("domcontentloaded")
                wait(page, 1200)
                screenshot(page, "09-oneshot-mama")

            # ── 10. Nav → Blog ────────────────────────────────────────────────
            print("[10] Nav → Blog")
            page.locator("nav.nav-desktop a", has_text="Blog").click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 1200)
            screenshot(page, "10-blog-index")

            # ── 11. First blog post ───────────────────────────────────────────
            print("[11] Blog card → post")
            post = page.locator(".blog-card__title a").first
            if post.count() > 0:
                post.click()
                page.wait_for_load_state("domcontentloaded")
                wait(page, 1200)
                screenshot(page, "11-blog-post")

            # ── 12. Nav → Ludzie ──────────────────────────────────────────────
            print("[12] Nav → Ludzie")
            page.locator("nav.nav-desktop a", has_text="Ludzie").click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 1200)
            screenshot(page, "12-people-index")

            # ── 13. First person → person page ───────────────────────────────
            print("[13] First person → person page")
            person = page.locator(".person-card__name a").first
            if person.count() > 0:
                person.click()
                page.wait_for_load_state("domcontentloaded")
                wait(page, 1200)
                screenshot(page, "13-person-page")

                # Their first edition tile
                etile = page.locator(".edition-tile__cover").first
                if etile.count() > 0:
                    print("[13b] Person → edition tile")
                    etile.click()
                    page.wait_for_load_state("domcontentloaded")
                    wait(page, 1200)
                    screenshot(page, "13b-person-edition")

            # ── 14. Site logo → homepage ──────────────────────────────────────
            print("[14] Logo → Homepage")
            page.locator("a.site-logo").first.click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 1200)
            screenshot(page, "14-home-via-logo")

            # ── 15. Scroll homepage catalog ───────────────────────────────────
            print("[15] Scroll homepage")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.25)")
            wait(page, 800)
            screenshot(page, "15-home-mid")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.6)")
            wait(page, 800)
            screenshot(page, "15b-home-catalog")

            # ── 16. Footer → Kontakt ──────────────────────────────────────────
            print("[16] Footer → Kontakt")
            page.locator("footer a", has_text="Kontakt").click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 1000)
            screenshot(page, "16-kontakt")

            # ── 17. Mobile nav demo ───────────────────────────────────────────
            print("[17] Mobile nav demo")
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(url("/"))
            page.wait_for_load_state("domcontentloaded")
            wait(page, 800)
            screenshot(page, "17-mobile-home")
            page.locator(".nav-toggle-btn").click()
            wait(page, 600)
            screenshot(page, "17b-mobile-menu-open")
            page.locator(".nav-mobile__links a", has_text="Komiksy").click()
            page.wait_for_load_state("domcontentloaded")
            wait(page, 800)
            screenshot(page, "17c-mobile-catalog")

            print("\n✅ All steps complete.")
            ctx.close()
            browser.close()

    finally:
        server.terminate()
        server.wait()
        print("Server stopped.")

    videos = sorted(VIDEO_DIR.glob("*.webm"))
    if videos:
        print(f"\n🎬 Video: {videos[-1]}")
    screenshots = sorted(VIDEO_DIR.glob("*.png"))
    print(f"📸 Screenshots: {len(screenshots)} frames in {VIDEO_DIR}/")
    for s in screenshots:
        print(f"   {s.name}")


if __name__ == "__main__":
    run()
