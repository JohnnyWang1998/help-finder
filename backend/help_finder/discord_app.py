from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

from help_finder.matching import rank_participants
from help_finder.models import Participant, RankedParticipant
from help_finder.pipeline import default_paths


def load_participants(path: Path | None = None) -> list[Participant]:
    _, _, repo_root = default_paths()
    data_path = path or repo_root / "data" / "participants.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [Participant.from_dict(item) for item in raw]


def _format_active(last_commit_at: str) -> str:
    if not last_commit_at:
        return "no recent activity"
    try:
        dt = datetime.fromisoformat(last_commit_at.replace("Z", "+00:00"))
    except ValueError:
        return "unknown activity"
    delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        return "active just now"
    if hours < 24:
        return f"active {hours}h ago"
    days = hours // 24
    return f"active {days}d ago"


def format_help_reply(
    ranked: list[RankedParticipant],
    *,
    dashboard_base_url: str,
) -> str:
    if not ranked:
        return "No matches found. Try a tech name like `react` or `streamlit`."

    lines: list[str] = []
    for i, item in enumerate(ranked, start=1):
        p = item.participant
        stack = ", ".join(p.techStack[:6]) or "unknown stack"
        active = _format_active(p.lastCommitAt)
        dash = f"{dashboard_base_url.rstrip('/')}?highlight={p.githubHandle}"
        lines.append(
            f"**{i}. {p.name}** (@{p.githubHandle})\n"
            f"Stack: {stack}\n"
            f"{active} · [Dashboard]({dash})"
        )
    return "\n\n".join(lines)


def run_bot() -> None:
    """Start Discord bot with /help slash command."""
    load_dotenv()
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN is required")

    dashboard_base = os.environ.get("DASHBOARD_BASE_URL", "http://localhost:3000")
    out_path, _, _ = default_paths()

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    _participants: list[Participant] = []
    _mtime: float = 0.0

    def refresh_participants() -> list[Participant]:
        nonlocal _participants, _mtime
        if not out_path.exists():
            return []
        mtime = out_path.stat().st_mtime
        if mtime != _mtime:
            _participants = load_participants(out_path)
            _mtime = mtime
        return _participants

    @client.event
    async def on_ready() -> None:
        await tree.sync()
        print(f"Logged in as {client.user} (synced /help)")

    @tree.command(name="help", description="Find cohort members who can help with a topic")
    @app_commands.describe(topic="Tech or topic, e.g. streamlit, react, supabase")
    async def help_command(interaction: discord.Interaction, topic: str) -> None:
        participants = refresh_participants()
        if not participants:
            await interaction.response.send_message(
                "No participant data loaded. Run `python ingest.py` first.",
                ephemeral=True,
            )
            return
        ranked = rank_participants(topic, participants, limit=3)
        message = format_help_reply(ranked, dashboard_base_url=dashboard_base)
        await interaction.response.send_message(message)

    client.run(token)
