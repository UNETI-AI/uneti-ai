#!/usr/bin/env python3
"""Checks that the branded tree still works as intended: python3 uneti/test_brand.py"""
import json
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "uneti"))
import add_announcement as notices  # noqa: E402
import apply_brand as brand  # noqa: E402

BRAND = json.loads((ROOT / "uneti" / "brand.json").read_text(encoding="utf-8"))
NAME, REPO, UPSTREAM = BRAND["name"], BRAND["repo"], BRAND["upstream"]


def text(rel):
    return (ROOT / rel).read_bytes().decode("utf-8", "surrogateescape")


class Branding(unittest.TestCase):
    def test_updates_and_news_come_from_our_repo(self):
        self.assertIn(f'GITHUB_REPO = "{REPO}"', text("server/main.py"))
        self.assertIn(f'"https://github.com/{REPO}.git"', text("server/updater.py"))
        self.assertIn(f'OFFICIAL_IMAGE = "ghcr.io/{REPO}"', text("server/deploy_info.py"))
        self.assertIn(f'"https://github.com/{REPO}.git"', text("packaging/windows/bootstrap.ps1"))

    def test_author_keeps_credit(self):
        self.assertIn("Nguyễn Minh Quý", text("LICENSE"))
        self.assertIn("Nguyễn Minh Quý", text("README.md"))
        self.assertIn(f"https://github.com/{UPSTREAM}", text("README.md"))
        self.assertIn(">by javis.vhthanh</a>", text("dashboard/index.html"))

    def test_strings_the_program_matches_stay_in_step(self):
        self.assertEqual(text("dashboard/app.js").count(f"trình sửa của {NAME}:"), 2)
        self.assertIn("X-Uneti-Tok", text("dashboard/webhooks.js"))
        self.assertIn('Path("UNETI")', text("server/brain_label.py"))
        self.assertIn("UNETI/loops/", text("CLAUDE.md"))
        self.assertIn(f'NAME = "{NAME} Core"', text("server/uneti_core.py"))
        self.assertIn(f'"{NAME} Core"', text("dashboard/tasks.js"))
        self.assertIn('".antigravity", "UNETI",', text("server/team_gate.py"))
        self.assertIn('_PROTECT_SKIP = ("UNETI",', text("server/team_gate.py"))
        self.assertIn('".claude/skills", "UNETI",', text("server/learn.py"))

    def test_names_owned_by_others_are_kept(self):
        self.assertIn('APP_SLUG = "javis-os"', text("server/github_oauth.py"))
        self.assertIn('"javis-pack.yaml"', text("server/packs.py"))
        self.assertIn('FORMAT = "javis-pack-index"', text("server/packs_store.py"))
        self.assertIn("blogminhquy/javis-store/", text("server/packs_store.py"))
        self.assertIn("blogminhquy/javis-zalo", text("system/mcp-catalog.json"))
        self.assertIn('"javis.zalo"', text("system/mcp-catalog.json"))

    def test_old_name_is_gone(self):
        # The credit, and the two filters that show the author's store under this copy's name.
        allowed = {"README.md", "server/packs_store.py", "dashboard/packs.js"}
        left = []
        for folder, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in brand.NOT_RENAMED_DIRS]
            relative = Path(folder).relative_to(ROOT)
            if relative.as_posix().startswith(".github/workflows"):
                continue  # ours, edited in place
            for name in dirs + files:
                if brand.OLD_NAME.search(name.encode("utf-8", "surrogateescape")):
                    left.append((relative / name).as_posix())
            for name in files:
                path = Path(folder) / name
                rel = (relative / name).as_posix()
                if rel in allowed or name in brand.NOT_RENAMED_FILES or path.suffix.lower() in brand.BINARY_SUFFIXES:
                    continue
                if brand.OLD_NAME.search(brand.KEEP.sub(b"", path.read_bytes())):
                    left.append(rel)
        self.assertEqual(left, [])

    def test_assistant_introduces_itself_by_the_new_name(self):
        self.assertIn(f"Bạn là {NAME}", text("server/context_compiler.py"))
        persona = text("server/voice_persona.py")
        self.assertIn(f'OPENING = "Bạn là {NAME}, trợ lý cá nhân,"', persona)
        self.assertIn(f"Bạn là {NAME}, trợ lý cá nhân,", text("server/voice_brain.py"))

    def test_interface_text_is_valid_and_renamed(self):
        for path in (ROOT / "dashboard" / "i18n").glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))
        vietnamese = json.loads(text("dashboard/i18n/vi.json"))
        self.assertEqual(vietnamese["star.support_title"], f"Ủng hộ {NAME}")
        self.assertEqual(vietnamese["noti.kind_community"], "Nhà trường")
        self.assertEqual(json.loads(text("dashboard/manifest.json"))["name"], NAME)
        self.assertIn(f"<title>{NAME}</title>", text("dashboard/index.html"))
        self.assertNotIn("<i>OS</i>", text("dashboard/index.html"))

    def test_installer_is_separate_from_javis_os(self):
        setup = text("packaging/windows/uneti-setup.iss")
        self.assertNotIn("8F3C2A51-5D7E-4C0B-9E61-6A2D4B7C9E10", setup)
        self.assertIn(BRAND["app_guid"], setup)
        self.assertIn(f"AppName={NAME}", setup)
        self.assertIn(f"OutputBaseFilename={BRAND['install_token']}-Setup", setup)
        self.assertTrue((ROOT / f"{NAME}.bat").exists())
        self.assertFalse((ROOT / "JAVIS OS.bat").exists())

    def test_installer_leaves_other_programs_on_the_port_alone(self):
        script = text("install.ps1")
        self.assertIn("-match '^pythonw?$'", script)
        self.assertEqual(script.count("Stop-Process -Id $c.OwningProcess"), 1)

    def test_support_card_opens_the_contribution_page(self):
        self.assertIn(BRAND["site_url"], text("dashboard/console.js"))
        self.assertIn('t("star.support_go")', text("dashboard/star-nudge.js"))
        self.assertIn(BRAND["site_url"], text("dashboard/star-nudge.js"))
        self.assertEqual(json.loads(text("dashboard/i18n/vi.json"))["star.rail"], "Ủng hộ")
        for path in (ROOT / "dashboard" / "i18n").glob("*.json"):
            self.assertIn("star.support_go", json.loads(path.read_text(encoding="utf-8")), path.name)
        self.assertEqual(json.loads(text("dashboard/i18n/vi.json"))["star.support_go"], "Xem cách đóng góp")

    def test_bell_notices_kept_from_upstream(self):
        ids = [row["id"] for row in json.loads(text("ANNOUNCEMENTS.json"))["announcements"]]
        self.assertIn("community-notification-inbox-launch", ids)


class Notices(unittest.TestCase):
    TODAY = date(2026, 11, 6)
    FORM = ("### Tiêu đề\n\nLịch nghỉ Tết\n\n### Tóm tắt\n\nNghỉ từ 10/2\n\n### Nội dung\n\nDòng 1\nDòng 2\n\n"
            "### Mức độ\n\nQuan trọng\n\n### Ngày hết hạn\n\n2027-03-01\n\n### Chữ trên nút\n\n_No response_\n\n"
            "### Liên kết\n\nhttps://uneti.edu.vn/tb\n")

    def build(self, form):
        return notices.build_notice(7, notices.parse_form(form), self.TODAY)

    def test_form_becomes_the_format_the_app_reads(self):
        notice = self.build(self.FORM)
        self.assertRegex(notice["id"], r"^[\w.:-]+$")
        self.assertEqual(notice["id"], "uneti-7")
        self.assertEqual(notice["kind"], "community")
        self.assertEqual(notice["body"], "Dòng 1\nDòng 2")
        self.assertEqual(notice["priority"], "high")
        self.assertEqual(notice["expires_at"], "2027-03-01")
        self.assertEqual(notice["cta"], {"label": "Xem chi tiết", "url": "https://uneti.edu.vn/tb"})

    def test_bad_forms_are_refused(self):
        for bad in ("### Tiêu đề\n\nA\n",
                    self.FORM.replace("https://uneti.edu.vn/tb", "javascript:alert(1)"),
                    self.FORM.replace("2027-03-01", "2020-01-01"),
                    self.FORM.replace("2027-03-01", "mai"),
                    self.FORM.replace("Lịch nghỉ Tết", "x" * 181)):
            with self.assertRaises(ValueError):
                self.build(bad)

    def test_publish_then_withdraw(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = notices.NOTICES
            notices.NOTICES = Path(tmp) / "ANNOUNCEMENTS.json"
            try:
                notices.save({"format_version": 1, "announcements": []})
                issue = {"number": 7, "body": self.FORM}
                self.assertTrue(notices.handle({"action": "opened", "issue": issue}, self.TODAY)[0])
                self.assertEqual(notices.load()["announcements"][0]["id"], "uneti-7")
                self.assertTrue(notices.handle({"action": "labeled", "issue": issue}, self.TODAY)[0])
                self.assertEqual(notices.load()["announcements"], [])
                self.assertFalse(notices.handle({"action": "labeled", "issue": issue}, self.TODAY)[0])
            finally:
                notices.NOTICES = original

    def test_starter_file_is_valid(self):
        self.assertIsInstance(json.loads(text("ANNOUNCEMENTS.json"))["announcements"], list)


if __name__ == "__main__":
    unittest.main(verbosity=1)
