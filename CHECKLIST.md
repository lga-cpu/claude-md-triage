# CLAUDE.md Fix — One-Page Checklist

Take one rule that keeps failing. Stop at the first yes.

**1 · Loaded?** `/context all` → is the file under **Memory files**?
  AGENTS.md is skipped when a CLAUDE.md / CLAUDE.local.md exists (add `@AGENTS.md` to CLAUDE.md).
  Subdirectory CLAUDE.md and `paths:` rules load only when matching files are touched.
  → *Move it, import it, fix the glob.*

**2 · Costly if broken once?** (force-push, secrets, `--no-verify`, generated files, shell writes)
  → *Permission `deny` rule, or a PreToolUse hook. Keep one line in CLAUDE.md saying it's enforced.*

**3 · Needs proof?** ("run the tests before saying done")
  → *Stop hook that checks the transcript and names the exact command.*

**4 · Only ever said in chat?**
  → *Write it into CLAUDE.md. Chat-only instructions don't survive compaction or a new session.*

**5 · Contradicted somewhere?** (another line, your user-wide CLAUDE.md, a skill, your prompt)
  → *Pick the winner, delete or scope the other.*

**6 · Points at something that no longer exists?**
  → *Update or delete. A wrong line is worse than a missing one.*

**7 · Can you say what you'd *see* if it were followed?** If not, it's vague.
  → *Rewrite: "When <trigger>, <action>." Delete "write clean code".*

**8 · Matters only in one situation?** (deploy, one folder, one task)
  → *Path-scoped rule, a skill, or a keyword hook.*

**9 · File far over ~200 lines, rule lost in restatement?**
  → *Delete what the repo already shows. Move topic rules to `.claude/rules/` with `paths:`.*

**Then prove it:** new session → `/context all` → the prompt that used to fail → one case that
should *not* be caught.

Built-in helpers: `/memory` · `/doctor prompt-audit` (recent versions) · `InstructionsLoaded` hook.
