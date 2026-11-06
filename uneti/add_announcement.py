#!/usr/bin/env python3
"""Publish or withdraw a school notice from a GitHub issue (uneti-announce.yml).

Issue text is untrusted: it only ever becomes JSON values, never shell text or file paths. The limits
mirror _parse_announcements in server/main.py, which would silently cut anything longer.
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTICES = ROOT / "ANNOUNCEMENTS.json"
HEADINGS = {"Tiêu đề": "title", "Tóm tắt": "summary", "Nội dung": "body", "Mức độ": "priority",
            "Ngày hết hạn": "expires_at", "Chữ trên nút": "cta_label", "Liên kết": "cta_url"}
LIMITS = {"title": ("Tiêu đề", 180), "summary": ("Tóm tắt", 500), "body": ("Nội dung", 3000),
          "cta_label": ("Chữ trên nút", 80), "cta_url": ("Liên kết", 500)}


def parse_form(body):
    fields, current = {}, None
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        heading = re.fullmatch(r"###\s+(.+?)\s*", line)
        if heading and heading.group(1) in HEADINGS:
            current = HEADINGS[heading.group(1)]
            fields[current] = []
        elif current:
            fields[current].append(line)
    cleaned = {key: "\n".join(lines).strip() for key, lines in fields.items()}
    return {key: "" if value == "_No response_" else value for key, value in cleaned.items()}


def build_notice(number, fields, today):
    title, summary = fields.get("title", ""), fields.get("summary", "")
    if not title or not summary:
        raise ValueError("Cần có Tiêu đề và Tóm tắt.")
    for key, (label, limit) in LIMITS.items():
        if len(fields.get(key, "")) > limit:
            raise ValueError(f"{label} dài quá {limit} ký tự.")
    notice = {"id": f"uneti-{number}", "kind": "community", "title": title, "summary": summary,
              "body": fields.get("body", ""), "published_at": today.isoformat(),
              "priority": "high" if fields.get("priority") == "Quan trọng" else "normal"}
    expires = fields.get("expires_at", "")
    if expires:
        try:
            if date.fromisoformat(expires) < today:
                raise ValueError("Ngày hết hạn đã qua.")
        except ValueError as error:
            raise ValueError(str(error) if "đã qua" in str(error) else "Ngày hết hạn phải có dạng 2026-12-31.")
        notice["expires_at"] = expires
    url = fields.get("cta_url", "")
    if url:
        if not re.match(r"^https?://\S+$", url, flags=re.I):
            raise ValueError("Liên kết phải bắt đầu bằng http:// hoặc https://.")
        notice["cta"] = {"label": fields.get("cta_label") or "Xem chi tiết", "url": url}
    elif fields.get("cta_label"):
        raise ValueError("Có Chữ trên nút thì phải có Liên kết.")
    return notice


def load():
    return json.loads(NOTICES.read_text(encoding="utf-8"))


def save(data):
    NOTICES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def handle(event, today):
    """Return (changed, message). A bad form changes nothing and tells the author what to fix."""
    issue = event["issue"]
    notice_id = f"uneti-{issue['number']}"
    data = load()
    rows = data["announcements"]
    if event["action"] == "labeled":
        kept = [row for row in rows if row.get("id") != notice_id]
        if len(kept) == len(rows):
            return False, "Không thấy tin này trong danh sách đang đăng."
        data["announcements"] = kept
        save(data)
        return True, "Đã gỡ tin. Các máy sẽ không còn thấy tin này khi tải lại thông báo."
    try:
        notice = build_notice(issue["number"], parse_form(issue.get("body")), today)
    except ValueError as error:
        return False, f"Chưa đăng được: {error} Bạn sửa lại rồi tạo thông báo mới."
    data["announcements"] = [row for row in rows if row.get("id") != notice_id]
    data["announcements"].insert(0, notice)
    save(data)
    return True, "Đã đăng tin. Người dùng sẽ thấy ở chuông thông báo khi mở phần mềm."


def main():
    event = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    changed, message = handle(event, date.today())
    print(message)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"changed={'true' if changed else 'false'}\nmessage={message}\n")


if __name__ == "__main__":
    main()
