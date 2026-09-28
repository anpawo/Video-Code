#!/usr/bin/env python3
"""Mirror docs/board.html onto the GitHub issues.

Every row gets an issue. A row whose fix is on main closes its issues with a link to the commit;
a Won't do row closes them as not planned, with its reason; a row whose work sits on a pushed
branch gets that branch linked once. Nothing is ever reopened.

A row names its issues in data-issue (space-separated; created and written back when missing),
and its fix in data-fix, else in the SHA of its meta column. A SHA only in the detail is not a
fix: row 63 cites the commit that took it as far as being blocked.

usage: python3 docs/board_issues.py [--dry-run]
"""
import html, json, re, subprocess, sys
from pathlib import Path

REPO = "anpawo/Video-Code"
BOARD = Path(__file__).with_name("board.html")
ROW = re.compile(r'<li([^>]*?) data-b="([^"]*)"([^>]*)>(.*?)</li>')
DRY = "--dry-run" in sys.argv


def run(*a):
    return subprocess.run(a, check=True, capture_output=True, text=True, cwd=BOARD.parent).stdout.strip()


def ok(*a):
    return subprocess.run(a, capture_output=True, cwd=BOARD.parent).returncode == 0


def gh(*a):
    if DRY and a[1] not in ("list", "view"):
        print("  would run: gh", *a[:3], "…")
        return "https://github.com/%s/issues/0" % REPO
    return run("gh", *a, "-R", REPO)


def text(s):
    return re.sub(r"<[^>]+>", "", html.unescape(s)).strip()


def main():
    src = BOARD.read_text()
    state = {i["number"]: i["state"] for i in json.loads(gh("issue", "list", "--state", "all", "--limit", "1000", "--json", "number,state"))}

    def sync(m):
        before, b, after, inner = m.groups()
        card = re.findall(r'<div class="card (\w+)">', src[:m.start()])[-1]
        rid, label, meta = (text(re.search(r'class="%s[^"]*">(.*?)</span>' % k, inner)[1]) for k in ("id", "lbl", "meta"))
        bullets = [text(x) for x in html.unescape(b).split("¦") if x.strip()]
        attrs = before + after
        tag = re.search(r'data-issue="([\d ]+)"', attrs)
        issues = tag[1].split() if tag else []
        if not issues:
            body = "## What\n\n" + "\n".join("- " + x for x in bullets) + \
                   "\n\n---\nBoard row %s — `docs/board.html`, long form in `docs/FEATURES_TODO.md`." % rid
            n = gh("issue", "create", "--title", label, "--body", body, "--assignee", "@me").rsplit("/", 1)[1]
            print(f"row {rid}: created #{n} {label}")
            issues, state[int(n)] = [n], "OPEN"
            before += f' data-issue="{n}"'

        fix = re.search(r'data-fix="([0-9a-f]+)"', attrs) or re.search(r"\b([0-9a-f]{7,40})\b", meta)
        sha = fix[1] if fix and ok("git", "merge-base", "--is-ancestor", fix[1], "main") else None
        branch = re.search(r"\b((?:feat|fix)/[\w.-]+)", " ".join(bullets))
        branch = branch[1] if branch and ok("git", "rev-parse", "--verify", "-q", "origin/" + branch[1]) else None

        for n in issues:
            if state.get(int(n)) != "OPEN":
                continue
            if card == "no":
                gh("issue", "close", n, "--reason", "not planned",
                   "--comment", f"Won't do — {meta}.\n\n" + "\n".join("- " + x for x in bullets))
                print(f"row {rid}: closed #{n} as not planned")
            elif sha:
                gh("issue", "close", n, "--comment", f"Fixed in https://github.com/{REPO}/commit/{run('git', 'rev-parse', sha)}")
                print(f"row {rid}: closed #{n}, fixed in {sha}")
            elif branch:
                url = f"https://github.com/{REPO}/tree/{branch}"
                if url not in gh("issue", "view", n, "--json", "comments", "--jq", ".comments[].body"):
                    gh("issue", "comment", n, "--body", f"Work in progress on {url}")
                    print(f"row {rid}: linked {branch} on #{n}")
        return f'<li{before} data-b="{b}"{after}>{inner}</li>'

    out = ROW.sub(sync, src)
    if out != src and not DRY:
        BOARD.write_text(out)


if __name__ == "__main__":
    main()
