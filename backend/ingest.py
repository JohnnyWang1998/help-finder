#!/usr/bin/env python3
"""Thin CLI entrypoint for the ingest pipeline."""

from help_finder.pipeline import run_ingest

if __name__ == "__main__":
    participants = run_ingest()
    print(f"Wrote {len(participants)} participants to data/participants.json")
