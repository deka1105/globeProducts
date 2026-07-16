#!/usr/bin/env python3
"""Export Claude Code session transcripts (JSONL) to readable Markdown logs.

Claude Code stores every session as a JSONL transcript under
~/.claude/projects/<project-slug>/<session-id>.jsonl. This script converts
those into human-readable Markdown files in <project>/session-logs/.

Usage:
  python3 export_session.py                 # export the latest session
  python3 export_session.py --all           # export every session
  python3 export_session.py --session <id>  # export a specific session (id prefix ok)
  python3 export_session.py --truncate 3000 # widen tool-output truncation
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def project_slug(cwd: Path) -> str:
    return str(cwd.resolve()).replace("/", "-").replace(".", "-")


def parse_ts(ts: str):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except Exception:
        return None


def fmt_time(ts: str) -> str:
    dt = parse_ts(ts)
    return dt.strftime("%H:%M:%S") if dt else ""


def truncate(text: str, limit: int) -> str:
    text = text.rstrip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n… [truncated, {len(text) - limit} more chars]"


def fence(text: str, lang: str = "") -> str:
    # Widen the fence if the content itself contains backtick fences
    marker = "```"
    while marker in text:
        marker += "`"
    return f"{marker}{lang}\n{text}\n{marker}"


def render_tool_use(block: dict, limit: int) -> str:
    name = block.get("name", "tool")
    inp = block.get("input", {}) or {}
    lines = [f"**🔧 {name}**"]
    if name == "Bash" and "command" in inp:
        desc = inp.get("description")
        if desc:
            lines.append(f"*{desc}*")
        lines.append(fence(truncate(inp["command"], limit), "bash"))
    elif name in ("Read", "Write", "Edit") and "file_path" in inp:
        lines.append(f"`{inp['file_path']}`")
        if name == "Write" and "content" in inp:
            lines.append(fence(truncate(str(inp["content"]), limit)))
        elif name == "Edit":
            lines.append(fence(truncate(
                f"- {inp.get('old_string', '')}\n+ {inp.get('new_string', '')}", limit), "diff"))
    else:
        pretty = json.dumps(inp, indent=2, ensure_ascii=False)
        lines.append(fence(truncate(pretty, limit), "json"))
    return "\n".join(lines)


def content_blocks(message: dict):
    content = message.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return content
    return []


def tool_result_text(block: dict) -> str:
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
        return "\n".join(parts)
    return ""


def render_entry(entry: dict, limit: int) -> str:
    etype = entry.get("type")
    msg = entry.get("message") or {}
    ts = fmt_time(entry.get("timestamp", ""))
    out = []

    if etype == "user":
        for block in content_blocks(msg):
            btype = block.get("type") if isinstance(block, dict) else None
            if btype == "tool_result":
                text = tool_result_text(block).strip()
                if text:
                    status = "❌ error" if block.get("is_error") else "output"
                    out.append(f"<details><summary>Tool {status}</summary>\n\n"
                               f"{fence(truncate(text, limit))}\n\n</details>")
            elif btype == "text" or btype is None:
                text = (block.get("text", "") if isinstance(block, dict) else str(block)).strip()
                if text:
                    out.append(f"### 👤 User · {ts}\n\n{text}")
    elif etype == "assistant":
        for block in content_blocks(msg):
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                text = block.get("text", "").strip()
                if text:
                    out.append(f"### 🤖 Claude · {ts}\n\n{text}")
            elif btype == "tool_use":
                out.append(render_tool_use(block, limit))
            # thinking blocks are internal reasoning; skip them

    return "\n\n".join(out)


def export_session(jsonl_path: Path, out_dir: Path, limit: int) -> Path | None:
    entries = []
    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    convo = [e for e in entries
             if e.get("type") in ("user", "assistant")
             and not e.get("isSidechain")
             and not e.get("isMeta")
             and e.get("message")]
    if not convo:
        return None

    session_id = jsonl_path.stem
    timestamps = [parse_ts(e.get("timestamp", "")) for e in convo]
    timestamps = [t for t in timestamps if t]
    started = timestamps[0] if timestamps else None
    ended = timestamps[-1] if timestamps else None
    cwd = next((e.get("cwd") for e in convo if e.get("cwd")), "")
    n_user = sum(1 for e in convo if e["type"] == "user"
                 and isinstance((e["message"] or {}).get("content"), str))
    n_asst = sum(1 for e in convo if e["type"] == "assistant")

    header = [
        f"# Session log · {started.strftime('%Y-%m-%d') if started else 'unknown date'}",
        "",
        f"- **Session:** `{session_id}`",
        f"- **Project:** `{cwd}`",
        f"- **Started:** {started.strftime('%Y-%m-%d %H:%M:%S %Z') if started else '?'}",
        f"- **Ended:** {ended.strftime('%Y-%m-%d %H:%M:%S %Z') if ended else '?'}",
        f"- **Messages:** {n_user} user / {n_asst} assistant",
        "",
        "---",
    ]

    body = [rendered for e in convo if (rendered := render_entry(e, limit))]

    out_dir.mkdir(parents=True, exist_ok=True)
    date_part = started.strftime("%Y-%m-%d_%H%M") if started else "unknown"
    out_path = out_dir / f"session_{date_part}_{session_id[:8]}.md"
    out_path.write_text("\n".join(header) + "\n\n" + "\n\n".join(body) + "\n")
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true", help="export every session, not just the latest")
    ap.add_argument("--session", help="session id (or unique prefix) to export")
    ap.add_argument("--truncate", type=int, default=1500,
                    help="max chars per tool input/output block (default 1500)")
    ap.add_argument("--out", default="session-logs", help="output directory (default ./session-logs)")
    args = ap.parse_args()

    cwd = Path.cwd()
    transcripts_dir = Path.home() / ".claude" / "projects" / project_slug(cwd)
    if not transcripts_dir.is_dir():
        sys.exit(f"No transcripts found for this project at {transcripts_dir}")

    jsonls = sorted(transcripts_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if args.session:
        jsonls = [p for p in jsonls if p.stem.startswith(args.session)]
        if not jsonls:
            sys.exit(f"No session matching '{args.session}'")
    elif not args.all:
        jsonls = jsonls[:1]
    if not jsonls:
        sys.exit("No session transcripts found.")

    out_dir = cwd / args.out
    exported = 0
    for p in jsonls:
        out = export_session(p, out_dir, args.truncate)
        if out:
            print(f"✓ {out.relative_to(cwd)}")
            exported += 1
        else:
            print(f"– skipped {p.name} (no conversation content)")
    if not exported:
        sys.exit(1)


if __name__ == "__main__":
    main()
