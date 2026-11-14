# claude-md-triage

**Why does Claude Code ignore my CLAUDE.md?** A free skill, checklist and tested hook to find out,
rule by rule.

Claude Code treats CLAUDE.md as context, not enforced configuration. Anthropic's docs say so:

> "Claude treats them as context, not enforced configuration. To block an action regardless of
> what Claude decides, use a PreToolUse hook instead."

So a failing rule is one of two kinds: written in a way (or a place) that doesn't work, or a rule
that must hold every time and needs enforcement. This repository helps you tell which.

## What's here

| | |
|---|---|
| `skills/claude-md-triage/` | Claude Code skill. Checks which instruction files load, sorts each failing rule into one of nine causes, names the fix. Read-only. |
| `CHECKLIST.md` | The same nine questions on one page. |
| `hooks/no_shell_file_writes.py` | Tested PreToolUse hook: blocks changing files with heredocs, `>`, `tee`, `sed -i` or `python -c`, and tells Claude to use Edit/Write instead. |

## Use the skill

```
mkdir -p .claude/skills
cp -r skills/claude-md-triage .claude/skills/
```

Then in Claude Code: *"Claude keeps ignoring my rule about X — why?"*

## Use the hook

1. Copy `hooks/no_shell_file_writes.py` to `.claude/hooks/` in your project.
2. Add to `.claude/settings.json` (merge into an existing `hooks` object if you have one):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/no_shell_file_writes.py\"" }
        ]
      }
    ]
  }
}
```

Use `python` instead of `python3` on Windows. **The interpreter must be a working Python 3**: if it
isn't, Claude Code shows only "hook error" and nothing is blocked. Check with `python3 --version`.

In a new session, ask Claude to create a file with a heredoc. You should see
`PreToolUse:Bash hook error: Blocked by project hook…`, and Claude should switch to the Write tool.
Tested with Claude Code 2.1.280 on Windows (Bash and PowerShell tools). Allowed: `2>&1`,
`/dev/null`, temp paths and `*.log` files.

## The nine causes

1. Not loaded · 2. Buried · 3. Vague · 4. Conflicting · 5. Wrong moment ·
6. Must never happen · 7. Must be verified · 8. Stale · 9. Spoken, never written

See `CHECKLIST.md` for the questions and fixes.

## The full kit

**When Claude Ignores Your CLAUDE.md — Diagnose & Fix Kit** adds:
- `claude-md-fix`, a skill that also writes the fixes (rewrites, moves, settings) and asks before
  applying them
- four more tested hooks: `git_guard` (force-push, `--no-verify`, push to main),
  `done_needs_test` (code changed → your real test command must run), `phrase_guard` (banned phrases in
  replies), `keyword_context` (rules that arrive with a keyword such as `@deploy`)
- a self-test for the hooks and a 10-page guide, including what live testing showed (e.g. Claude "running the tests" with a
  command that runs none, then reporting they passed)

Get it on Gumroad: https://lgafactory.gumroad.com/l/wzfyg (US$19, one-time purchase)

## License

MIT. Not affiliated with or endorsed by Anthropic. "Claude" and "Claude Code" are trademarks of
Anthropic.
