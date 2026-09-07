"""One-time interactive helper to get a Nest OAuth refresh token.

Run this yourself, locally: `python3 nest_setup.py`
It never sends your credentials anywhere but Google's own OAuth endpoints,
and writes the result straight to your local .env file — nothing is
printed that you need to copy into anything else.
"""

import os
import sys
import webbrowser
from urllib.parse import parse_qs, urlencode, urlparse

import requests

SCOPE = "https://www.googleapis.com/auth/sdm.service"
REDIRECT_URI = "https://www.google.com"
ENV_KEYS = ("NEST_PROJECT_ID", "NEST_CLIENT_ID", "NEST_CLIENT_SECRET", "NEST_REFRESH_TOKEN")


def write_env(env_path: str, values: dict):
    lines = []
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = [line for line in f if not line.split("=", 1)[0] in ENV_KEYS]
    lines += [f"{k}={v}\n" for k, v in values.items()]
    with open(env_path, "w") as f:
        f.writelines(lines)


def main():
    project_id = input("Device Access project ID: ").strip()
    client_id = input("OAuth client ID: ").strip()
    client_secret = input("OAuth client secret: ").strip()

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent",
        "response_type": "code",
        "scope": SCOPE,
    }
    auth_url = f"https://nestservices.google.com/partnerconnections/{project_id}/auth?{urlencode(params)}"

    print("\nOpening the Google consent screen in your browser.")
    print("Sign in with the account that owns the Nest device and approve access.")
    print(f"If it doesn't open automatically, visit:\n{auth_url}\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("After approving, your browser lands on google.com with '?code=...' in the URL bar.")
    pasted = input("Paste that full URL (or just the code): ").strip()

    code = parse_qs(urlparse(pasted).query).get("code", [None])[0] if "code=" in pasted else pasted
    if not code:
        print("Could not find an authorization code in that input.", file=sys.stderr)
        sys.exit(1)

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"Token exchange failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    refresh_token = resp.json()["refresh_token"]
    print("\nGot a refresh token.")

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    choice = input(f"Write it (with the project ID / client ID / secret) to {env_path}? [Y/n] ").strip().lower()
    if choice in ("", "y", "yes"):
        write_env(env_path, {
            "NEST_PROJECT_ID": project_id,
            "NEST_CLIENT_ID": client_id,
            "NEST_CLIENT_SECRET": client_secret,
            "NEST_REFRESH_TOKEN": refresh_token,
        })
        print(f"Wrote credentials to {env_path}.")
        print("Next: run `from nest import NestThermostat; NestThermostat().list_devices()` to find your device ID.")
    else:
        print("Not written. If you need it, your refresh token is:")
        print(refresh_token)


if __name__ == "__main__":
    main()
