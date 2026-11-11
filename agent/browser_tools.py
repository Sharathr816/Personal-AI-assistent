# agent/browser_tools.py

import os
import socket
import subprocess
import time
import urllib.request
from urllib.parse import quote_plus, urlparse

from pathlib import Path
from playwright.sync_api import sync_playwright




CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
CDP_URL = f"http://{CDP_HOST}:{CDP_PORT}"

BRAVE_PROFILE = (
    Path(os.environ["LOCALAPPDATA"])
    / "Mio"
    / "BraveProfile"
)

_playwright = None
_browser = None
_brave_process = None


def _find_brave() -> Path:
    """Locate the installed Brave executable."""
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        / "BraveSoftware/Brave-Browser/Application/brave.exe",

        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
        / "BraveSoftware/Brave-Browser/Application/brave.exe",

        Path(os.environ.get("LOCALAPPDATA", ""))
        / "BraveSoftware/Brave-Browser/Application/brave.exe",
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "Brave executable not found. Install Brave or update its path "
        "in agent/browser_tools.py."
    )


def _port_is_available() -> bool:
    """Check whether the configured CDP port is unused."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((CDP_HOST, CDP_PORT)) != 0



def connect_brave() -> str:
    """Launch Brave if needed and attach Playwright through CDP."""
    global _playwright, _browser, _brave_process

    # Case 2: Reuse an existing Playwright connection.
    if _browser is not None and _browser.is_connected():
        print("\nAlready connected to brave🤔")
        return "Already connected to Brave."

    if os.name != "nt":
        raise RuntimeError("This Brave launcher is configured for Windows.")

    brave_path = _find_brave()

    # Case 1: No CDP endpoint exists, so launch Brave.
    if _port_is_available():
        print("\nTrying to launch brave...🚀")
        BRAVE_PROFILE.mkdir(parents=True, exist_ok=True)

        command = [
            str(brave_path),
            f"--remote-debugging-port={CDP_PORT}",
            f"--remote-debugging-address={CDP_HOST}",
            f"--user-data-dir={BRAVE_PROFILE}",
            "--no-first-run",
            "--no-default-browser-check",
        ]

        _brave_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Case 2: Port occupied, so assume Brave is already running.
    # In either case, wait for the CDP endpoint to respond.
    endpoint_ready = False

    for _ in range(30):
        try:
            with urllib.request.urlopen(
                f"{CDP_URL}/json/version",
                timeout=1
            ) as response:
                if response.status == 200:
                    endpoint_ready = True
                    break
        except Exception:
            time.sleep(0.5)

    if not endpoint_ready:
        print("Brave's CDP endpoint did not respond within 15 seconds😞")
        raise TimeoutError(
            "Brave's CDP endpoint did not respond within 15 seconds."
        )

    # Attach Playwright to the existing or newly launched Brave.
    _playwright = sync_playwright().start()

    try:
        _browser = _playwright.chromium.connect_over_cdp(
            CDP_URL,
            timeout=10_000
        )
    except Exception:
        _playwright.stop()
        _playwright = None
        raise

    print("Successfully connected to Brave through CDP 😄✅")
    return "Successfully connected to Brave through CDP."



def get_brave_status() -> str:
    """Return basic information about the connected Brave instance."""

    if _browser is None or not _browser.is_connected():
        return "Brave is not connected."

    contexts = _browser.contexts

    if not contexts:
        print("\nBrave is connected, but no browser context is available 🤔")
        return "Brave is connected, but no browser context is available."

    pages = contexts[0].pages
    print("\nBrave connected successfully 😆✅")
    return (
        f"Brave connected successfully.\n"
        f"Browser contexts: {len(contexts)}\n"
        f"Open tabs: {len(pages)}"
    )


'''You tube'''
_youtube_page = None

def _get_youtube_page():
    """Get or create a YouTube tab in Mio's connected Brave browser."""
    global _youtube_page

    if _browser is None or not _browser.is_connected():
        connect_brave()

    context = _browser.contexts[0] # Brave's browser context. It holds the tabs and shared session data, like login cookies.
    if _youtube_page is not None: # If we already have a YouTube tab and it's still open, reuse it
        try:
            if not _youtube_page.is_closed():
                return _youtube_page
        except Exception:
            pass

    # Reuse an existing YouTube tab if one is open.
    for page in context.pages:
        if "youtube.com" in page.url:
            _youtube_page = page
            return page

    _youtube_page = context.new_page()
    return _youtube_page


def search_youtube(query: str, max_results: int = 5) -> str:
    """Search YouTube and return matching video titles, channels and URLs."""

    if not query.strip():
        raise ValueError("YouTube search query cannot be empty.")

    if not 1 <= max_results <= 10:
        raise ValueError("max_results must be between 1 and 10.")

    print("\nSearching Youtube...😎")
    page = _get_youtube_page()
    search_url = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(query)
    )

    page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
    results_locator = page.locator("ytd-video-renderer")

    try:
        results_locator.first.wait_for(timeout=20000)
    except Exception:
        print("\nHmmm...🤔, I got rejected by you tube. Help me🫠")
        return (
            "YouTube search results did not load. "
            "The page may require sign-in, consent, or CAPTCHA verification."
        )

    results = []

    for i in range(min(results_locator.count(), max_results)):
        video = results_locator.nth(i)
        title_link = video.locator("a#video-title").first
        title = title_link.get_attribute("title") or ""
        url = title_link.get_attribute("href") or ""

        if not title or not url:
            continue

        if url.startswith("/"):
            url = "https://www.youtube.com" + url

        parsed = urlparse(url)

        if parsed.hostname not in {
            "www.youtube.com",
            "youtube.com",
        }:
            continue

        channel_locator = video.locator(
            "ytd-channel-name a"
        ).first

        channel = ""

        try:
            channel = channel_locator.inner_text(timeout=2000)
        except Exception:
            pass

        results.append({
            "title": title.strip(),
            "channel": channel.strip(),
            "url": url
        })

    if not results:
        print("No YouTube video results were found😞")
        return "No YouTube video results were found."

    output = [f"YouTube results for: {query}"]
    for i, result in enumerate(results, start=1):
        output.append(
            f"\n{i}. {result['title']}"
            f"\n   Channel: {result['channel'] or 'Unknown'}"
            f"\n   URL: {result['url']}"
        )
    print("\nFound some contents😆✨")
    return "\n".join(output)


def play_youtube_video(video_url: str) -> str:
    """Open a YouTube video URL and attempt playback."""

    parsed = urlparse(video_url)
    allowed_hosts = {
        "www.youtube.com",
        "youtube.com",
        "m.youtube.com",
        "youtu.be",
    }

    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        print("\nProblem with url😳")
        raise ValueError("Only valid HTTPS YouTube URLs are allowed.")

    if parsed.hostname in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        print("\nProblem with url😳")
        if not parsed.path.startswith("/watch"):
            raise ValueError("URL must point to a YouTube video.")
        if not parsed.query or "v=" not in parsed.query:
            raise ValueError("YouTube video URL is missing its video ID.")

    elif parsed.hostname == "youtu.be":
        print("\nProblem with url😳")
        if not parsed.path.strip("/"):
            raise ValueError("YouTube short URL is missing its video ID.")

    print("\nWait a sec, trying to play the video📽️")
    page = _get_youtube_page()
    page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
    video = page.locator("video.html5-main-video")

    try:
        video.wait_for(state="attached", timeout=20000)
    except Exception:
        print("\nVideo did not load😞")
        return "The YouTube video player did not load."

    page.wait_for_timeout(1500)

    # Check whether the video is already playing.
    is_playing = video.evaluate("(element) => !element.paused")
    if not is_playing:
        play_button = page.locator(
            "#movie_player button.ytp-play-button"
        )

        try:
            play_button.click(timeout=5000)
            page.wait_for_timeout(1500)
        except Exception:
            print("\nCouldn't attempt playback, sorry🥺")
            return (
                "The video opened, but Mio could not activate playback. "
                "It may require interaction or have a playback restriction."
            )

    is_playing = video.evaluate("(element) => !element.paused")

    if is_playing:
        title = page.title()
        print(f"\nPlayback started successfully, enjoy😆")
        return f"Playback started successfully: {title}"

    print("\nHmmm...🤔, I got rejected by you tube during playback. Help me🫠")
    return (
        "The video opened, but playback has not started. "
        "Check for consent, sign-in, age restrictions, or other prompts."
    )