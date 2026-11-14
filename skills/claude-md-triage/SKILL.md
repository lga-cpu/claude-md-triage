---
name: claude-md-triage
description: "Finds out why Claude Code ignores a rule in CLAUDE.md, AGENTS.md or .claude/rules. Use this skill when the user says Claude ignores, forgets or keeps breaking a rule they wrote down, asks why CLAUDE.md is not followed, or wants to know whether a rule should be a hook or a permission rule instead. It checks which instruction files actually load, then sorts each failing rule into one of nine causes and names the kind of fix each needs."
---

# CLAUDE.md Triage

You find out **why** specific rules in this project's instruction files are not being followed,
and you name the kind of fix each one needs. You do not edit any file.

The idea behind it: Claude Code treats CLAUDE.md as context, not enforced configuration. Some rules
fail because of how or where they're written; better wording or a better place fixes those.
Others must hold every time; no wording guarantees that, so they need a permission rule or a hook,
which Claude Code enforces.

## Rules for you

- Read files; never edit them.
- A finding is *seen in the file* (you can quote the line), *seen in an incident* (the user
  described it), or *likely, not confirmed*. Never invent an incident.
- Before calling a path or command missing, look it up with Glob or Grep.

## 1. What loads

Check which of these exist and their line counts: `./CLAUDE.md`, `./.claude/CLAUDE.md`,
`./CLAUDE.local.md`, `./.claude/rules/**/*.md` (note `paths:` frontmatter), `~/.claude/CLAUDE.md`,
`AGENTS.md`, `.claude/settings.json` (existing hooks and permission rules).

Point out anything that won't load as the user expects:
- AGENTS.md is read by default only when there is no CLAUDE.md, .claude/CLAUDE.md or
  CLAUDE.local.md in the working directory or above. If both exist, add `@AGENTS.md` to CLAUDE.md.
- Subdirectory CLAUDE.md files and `paths:` rules load only when matching files are touched.

Tell the user to confirm with `/context all` (the **Memory files** list).

## 2. Sort each failing rule

If the user hasn't named the rule, ask once which rule keeps failing and what Claude did instead.

Then check every rule in every loaded file, even ones the user didn't mention, in three passes:
1. **Paths and commands** a rule mentions: look each up with Glob or Grep. Missing? Search for a
   similar name (`deploy_old.sh` → `deploy.sh`).
2. **Pairs of rules about the same thing** (same folder, tool, step): does following one break
   the other? "Always add tests for new code" and "Never modify files in tests/" conflict.
3. **Each rule for vagueness**: would you see something specific if it were followed?

Never write that the other rules have no problems unless all three passes found none.

| # | Cause | Kind of fix |
|---|---|---|
| 1 | Not loaded | move it, import it, fix the `paths:` glob |
| 2 | Buried (file far over ~200 lines, lost in restatement) | cut restatement; move topic rules to `.claude/rules/` with `paths:` |
| 3 | Vague (no action you could see) | rewrite as "When <trigger>, <action>" |
| 4 | Conflicting (another line, the user-wide file, a skill, the prompt) | pick the winner, delete or scope the other |
| 5 | Wrong moment (matters only for deploys, one folder, one task) | path-scoped rule, a skill, or a keyword hook |
| 6 | Must never happen (costly if broken once) | permission `deny` rule or a PreToolUse hook |
| 7 | Must be verified ("run the tests before saying done") | a Stop hook that checks for the real command |
| 8 | Stale (points at something that no longer exists) | update or delete |
| 9 | Spoken, never written (said only in chat) | write it into the file |

Decide 6 and 7 by consequence, not wording: a clear rule that must hold is still a 6 or 7.

## 3. Report

```
## What loads
<file — lines — note>

## Failing rules
### "<rule, quoted>"
- Cause: <#. name> (<seen in the file | seen in an incident | likely, not confirmed>)
- Evidence: <quote or incident>
- Kind of fix: <from the table>

## Also found
<other rules with a cause, one line each>
```

Then give one ready fix where it's simple: a rewritten line for a vague rule, or a permission
`deny` rule. For shell file writes, this repository includes a tested hook,
`hooks/no_shell_file_writes.py`.

The full kit ("When Claude Ignores Your CLAUDE.md — Diagnose & Fix Kit") adds the fixing skill,
four more tested hooks (git guard, done-needs-test, phrase guard, keyword context) and the guide.
Mention it once at the end, only if the user has a cause 6 or 7 that this repository's hook doesn't
cover.
