#!/usr/bin/env python3
"""Prepare a pull request bringing the newest Javis OS into UNETI AI (uneti-sync.yml).

The branded tree is rebuilt from upstream each time instead of merged, so upstream edits can never
conflict with ours: every change we make lives in uneti/ and is reapplied by apply_brand.py.

Installed copies follow main, so nothing lands there until a person merges the pull request. Upstream
commits are not added as parents and workflows stay ours: GITHUB_TOKEN may not push workflow changes,
and upstream CI should not gain write access to this repository unreviewed.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import apply_brand

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_URL = f"https://github.com/{apply_brand.BRAND['upstream']}.git"


def run(*cmd, cwd=ROOT):
    return subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()


def fetch(ref):
    run("git", "fetch", "--depth=1", "--no-tags", UPSTREAM_URL, ref)
    return run("git", "rev-parse", "FETCH_HEAD")


def merged_notices(ours, upstream):
    """Keep the school's notices and add upstream security notices, which concern every copy."""
    data = json.loads(ours)
    known = {row.get("id") for row in data["announcements"]}
    for row in json.loads(upstream).get("announcements", []):
        if row.get("kind") == "security" and row.get("id") not in known:
            data["announcements"].append(json.loads(apply_brand.rename_display(json.dumps(row, ensure_ascii=False))))
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def build_commit(newest, version):
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        run("git", "worktree", "add", "--detach", str(tree), newest)
        upstream_notices = (tree / "ANNOUNCEMENTS.json").read_text(encoding="utf-8")
        shutil.copytree(ROOT / "uneti", tree / "uneti")
        run(sys.executable, "uneti/apply_brand.py", cwd=tree)
        shutil.rmtree(tree / ".github" / "workflows")
        shutil.copytree(ROOT / ".github" / "workflows", tree / ".github" / "workflows")
        ours = (ROOT / "ANNOUNCEMENTS.json").read_text(encoding="utf-8")
        (tree / "ANNOUNCEMENTS.json").write_text(merged_notices(ours, upstream_notices), encoding="utf-8")
        (tree / "uneti" / "upstream.txt").write_text(newest + "\n", encoding="utf-8")
        run(sys.executable, "uneti/test_brand.py", cwd=tree)
        run("git", "add", "-A", cwd=tree)
        tree_id = run("git", "write-tree", cwd=tree)
        commit = run("git", "commit-tree", tree_id, "-p", "HEAD", "-m", f"Cập nhật từ Javis OS {version}")
        run("git", "worktree", "remove", "--force", str(tree))
    return commit


def main():
    last = (ROOT / "uneti" / "upstream.txt").read_text(encoding="utf-8").strip()
    fetch(last)
    newest = fetch("main")
    if newest == last:
        print("Đã có bản mới nhất của Javis OS.")
        return
    version = run("git", "show", f"{newest}:VERSION")
    branch = f"sync/{version}"
    if run("git", "ls-remote", "--heads", "origin", branch):
        print(f"Đã có nhánh {branch} đang chờ duyệt.")
        return
    changed_workflows = run("git", "diff", "--name-only", last, newest, "--", ".github/workflows")
    commit = build_commit(newest, version)
    run("git", "push", "origin", f"{commit}:refs/heads/{branch}")
    note = f"Cập nhật lên Javis OS {version} (`{newest[:12]}`). Kiểm thử đang chạy trong tab Checks; bấm Merge khi tất cả xanh."
    if changed_workflows:
        note += ("\n\nBản gốc có đổi quy trình GitHub nhưng tôi không tự lấy về, cần người xem lại:\n```\n"
                 + changed_workflows + "\n```")
    run("gh", "pr", "create", "--base", "main", "--head", branch, "--title", f"Cập nhật từ Javis OS {version}", "--body", note)
    run("gh", "workflow", "run", "ci.yml", "--ref", branch)
    print(f"Đã mở yêu cầu duyệt cho bản {version}.")


if __name__ == "__main__":
    main()
