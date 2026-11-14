#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash|PowerShell): block changing files through the shell.

Rule it enforces (the CLAUDE.md line that keeps getting ignored):
    "Use the Edit/Write tools to change files. Don't write files with
     heredocs, echo > file, tee, sed -i or python -c."

Why a hook: a malformed heredoc can hang the shell, and shell writes skip the
diff you would review for an Edit. Writing this rule in CLAUDE.md asks; this
hook makes the command fail with a reason Claude can act on.

Blocks
- redirection into a file:   cat <<EOF > app.py    echo x >> notes.md    cmd &> out.txt
- tee into a file:           ... | tee config.yml   tee a.txt < in.txt
- in-place edits:            sed -i ...   perl -pi ...
- python/node one-liners or heredoc scripts that open a file for writing
- PowerShell writes:         Set-Content, Add-Content, Out-File, New-Item -Value
Allows
- /dev/null, /dev/stdout, /dev/stderr, NUL, $null, fd duplication (2>&1)
- temp paths (/tmp/, $TMPDIR, $env:TEMP) and log files (*.log) - see ALLOWED_*
- '>' inside quoted text, '->' and '=>'
Not seen (by design or by limit): 2> file (stderr), writes inside a quoted script
(awk '{print > "f"}', cmd /c "echo > f", bash -c '...'). Not a security boundary:
a determined command can get around pattern checks.
Edit ALLOWED_PREFIXES / ALLOWED_SUFFIXES for your project. Standard library only.
"""
import json
import re
import sys

ALLOWED_PREFIXES = ("/dev/null", "/dev/stdout", "/dev/stderr", "/tmp/", "$TMPDIR", "${TMPDIR",
                    "$env:TEMP", "$env:TMP", "%TEMP%")
ALLOWED_EXACT = ("NUL", "nul", "$null")
ALLOWED_SUFFIXES = (".log",)

# '>', '>>', '&>', '&>>' followed by a target (quoted or bare). Not '2>&1', not '->', not '=>'.
# '>' after a digit is a file-descriptor redirect: 1> (stdout) is checked, 2> etc. are allowed.
REDIRECT = re.compile(r"(?<![02-9>\-=])(&?>>?)(?![&>])\s*(\"[^\"]*\"|'[^']*'|[^\s|;&<>()]+)")
# $((a>b)), ((a>b)) and [[ $a > $b ]] compare; they don't redirect
ARITHMETIC = re.compile(r"\$\(\([^)]*\)\)|\(\([^)]*\)\)|\[\[[^\]]*\]\]")
TEE = re.compile(r"\btee\s+(?:--?[a-zA-Z][a-zA-Z-]*\s+)*(\"[^\"]*\"|'[^']*'|[^\s|;&<>()-][^\s|;&<>()]*)")
IN_PLACE = re.compile(r"\b(sed\s+(?:-[a-zA-Z]*i\b|--in-place)|perl\s+-[a-zA-Z]*i)")
SCRIPT = re.compile(r"\b(python3?|node)\s+(-c|-e|-)\b|\b(python3?|node)\b[^\n|;&]*<<")
WRITE_CALL = re.compile(
    r"open\([^)]*?,\s*(mode\s*=\s*)?['\"][^'\"]*[wax+][^'\"]*['\"]"
    r"|writeFileSync|appendFileSync|createWriteStream|\.write_text\(|\.write_bytes\("
)
POWERSHELL_WRITE = re.compile(
    r"(\bSet-Content\b|\bAdd-Content\b|\bOut-File\b|\bTee-Object\b|\bNew-Item\b[^|;\n]*-Value|\[(?:System\.)?IO\.File\]::(?:Write|Append)\w*)",
    re.IGNORECASE,
)

REASON = (
    "Blocked by project hook: don't change files through the shell ({what}). "
    "Use the Edit tool to change an existing file or the Write tool to create one, "
    "then continue with the task."
)


def quoted_spans(command):
    return [m.span() for m in re.finditer(r"\"(?:\\.|[^\"\\])*\"|'[^']*'", command)]


def inside(pos, spans):
    return any(a <= pos < b for a, b in spans)


def allowed(target):
    t = target.strip("\"'")
    return (not t or t in ALLOWED_EXACT or t.startswith(ALLOWED_PREFIXES)
            or t.lower().endswith(ALLOWED_SUFFIXES))


def violation(command):
    # blank out arithmetic ((a > b)) without shifting positions
    command = ARITHMETIC.sub(lambda m: " " * len(m.group(0)), command)
    spans = quoted_spans(command)
    for m in REDIRECT.finditer(command):
        if inside(m.start(1), spans):
            continue
        if not allowed(m.group(2)):
            return f"redirect into {m.group(2).strip(chr(34) + chr(39))}"
    for m in TEE.finditer(command):
        if not inside(m.start(), spans) and not allowed(m.group(1)):
            return f"tee into {m.group(1).strip(chr(34) + chr(39))}"
    m = IN_PLACE.search(command)
    if m and not inside(m.start(), spans):
        return "in-place edit with " + m.group(1).split()[0]
    if SCRIPT.search(command) and WRITE_CALL.search(command):
        return "inline script that writes a file"
    for m in POWERSHELL_WRITE.finditer(command):
        if inside(m.start(), spans):
            continue
        if m.group(1).startswith("["):
            return m.group(1)
        # target: -Path/-FilePath/-LiteralPath value, or the first positional argument
        rest = command[m.end():].split("|")[0].split(";")[0]
        t = re.search(r"-(?:File|Literal)?Path\s+(\"[^\"]*\"|'[^']*'|\S+)", rest, re.IGNORECASE)
        if not t:
            t = re.search(r"^\s*(\"[^\"]*\"|'[^']*'|[^\s-]\S*)", rest)
        if not (t and allowed(t.group(1))):
            return m.group(1).split()[0]
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    what = violation(command)
    if not what:
        return 0
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": REASON.format(what=what),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
