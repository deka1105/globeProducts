---
name: save-session
description: Export Claude Code terminal session conversations (prompts, responses, commands, tool output) into readable Markdown log files under session-logs/. Use when the user says "save this session", "export the session log", "save our conversation", "archive this chat", or wants a record of what happened in a session.
---

# Save Session

Exports Claude Code session transcripts into human-readable Markdown logs.

## How it works

Claude Code already records every session losslessly as JSONL in
`~/.claude/projects/<project-slug>/<session-id>.jsonl`. This skill converts
those transcripts into Markdown files in `<project>/session-logs/` — one file
per session, named `session_<date>_<time>_<id>.md` — containing the user
prompts, Claude's responses, every tool call (Bash commands, file edits), and
truncated tool output, with timestamps and a summary header.

Markdown is used because the lossless machine-readable record already exists
(the JSONL); the export's job is to be readable, greppable, and diff-friendly.

## Instructions

1. Run the exporter from the project root:
   ```bash
   python3 .claude/skills/save-session/export_session.py
   ```
   - Default: exports the **latest** session (usually the current one).
   - `--all` — export every session for this project.
   - `--session <id-prefix>` — export one specific session.
   - `--truncate <n>` — max chars per tool input/output block (default 1500);
     raise it if the user wants full command output preserved.
   - `--out <dir>` — change the output directory (default `session-logs/`).

2. Report the written file path(s) to the user.

3. If the current session should be captured *up to this moment*, note to the
   user that the transcript is written continuously, so the export contains
   everything up to the last completed message.

## Notes

- `session-logs/` is gitignored on purpose: this repo has a file watcher that
  auto-commits and pushes every saved file, and conversation logs should not
  be pushed to a public portfolio repo. If the user explicitly wants logs
  versioned, remove the `.gitignore` entry — but confirm first.
- If the script exits with "No transcripts found", verify the project slug:
  the transcripts dir is the cwd path with `/` and `.` replaced by `-`.
