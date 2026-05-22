#!/usr/bin/env python3
"""Fetch cohort submission JSONs and print base participant stubs (A2)."""

import json
import os

from dotenv import load_dotenv

from help_finder.clients.github import GitHubClient
from help_finder.submissions import fetch_participants


def main() -> None:
    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    client = GitHubClient(token=token or None)
    try:
        participants = fetch_participants(client)
        stubs = [p.to_dict() for p in participants]
        print(json.dumps(stubs, indent=2))
        print(f"\n# {len(stubs)} submission stubs", flush=True)
    finally:
        client.close()


if __name__ == "__main__":
    main()
