"""One-time Strava OAuth helper.

Usage:
    1. Put STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in your local .env
    2. Run:  python3 scripts/strava_oauth.py
    3. Browser opens. Click "Authorize".
    4. Script prints your STRAVA_REFRESH_TOKEN — paste it into Vercel env vars.

The refresh token doesn't expire unless you revoke the app or change scopes,
so this should be a one-time operation.
"""
import os
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
PORT = 8765
REDIRECT_URI = f"http://localhost:{PORT}/callback"
SCOPES = "read,activity:read_all"

AUTH_URL = (
    "https://www.strava.com/oauth/authorize?"
    + urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "approval_prompt": "force",
        "scope": SCOPES,
    })
)

_code: dict = {}


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _code["value"] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h2>Strava authorised.</h2><p>You can close this tab and "
                b"return to the terminal.</p>"
            )
        else:
            err = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Authorization error: {err}".encode())

    def log_message(self, *args, **kwargs):
        pass  # silence default stderr logging


def main() -> int:
    if not CLIENT_ID or not CLIENT_SECRET:
        print(
            "ERROR: set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in .env first.\n"
            "Get them from https://www.strava.com/settings/api"
        )
        return 1

    print(f"Opening browser to authorise…")
    print(f"If it doesn't open, visit: {AUTH_URL}\n")

    server = HTTPServer(("localhost", PORT), _CallbackHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    webbrowser.open(AUTH_URL)

    print(f"Waiting for callback on localhost:{PORT}…")
    while "value" not in _code:
        try:
            import time
            time.sleep(0.2)
        except KeyboardInterrupt:
            server.shutdown()
            return 1

    server.shutdown()
    code = _code["value"]
    print("Got code. Exchanging for tokens…")

    resp = httpx.post(
        "https://www.strava.com/api/v3/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"Token exchange failed: {resp.status_code} {resp.text}")
        return 1

    data = resp.json()
    print("\n" + "=" * 60)
    print("SUCCESS. Paste the following into Vercel env vars:")
    print("=" * 60)
    print(f"STRAVA_REFRESH_TOKEN={data['refresh_token']}")
    print("=" * 60)
    print(f"\nAthlete: {data.get('athlete', {}).get('firstname', '')} "
          f"{data.get('athlete', {}).get('lastname', '')}")
    print(f"Scope granted: {SCOPES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
