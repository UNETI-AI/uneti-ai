#!/usr/bin/env python3
"""Checks that the branded tree still works as intended: python3 uneti/test_brand.py"""
import json
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "uneti"))
import add_announcement as notices  # noqa: E402

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
        self.assertIn(f"https://github.com/{UPSTREAM}", text("dashboard/index.html"))
        self.assertIn("Dựa trên Javis OS", text("dashboard/index.html"))
        self.assertIn("Nguyễn Minh Quý", text("README.md"))

    def test_strings_the_program_matches_stay_unchanged(self):
        self.assertEqual(text("dashboard/app.js").count("trình sửa của Javis:"), 2)
        self.assertIn("X-Javis-Tok", text("dashboard/webhooks.js"))
        self.assertIn('Path("Javis")', text("server/brain_label.py"))
        self.assertIn("Javis/loops/", text("CLAUDE.md"))

    def test_assistant_introduces_itself_by_the_new_name(self):
        self.assertIn(f"Bạn là {NAME}", text("server/context_compiler.py"))
        persona = text("server/voice_persona.py")
        self.assertIn(f'OPENING = "Bạn là {NAME}, trợ lý cá nhân,"', persona)
        self.assertIn(f"Bạn là {NAME}, trợ lý cá nhân,", text("server/voice_brain.py"))

    def test_interface_text_is_valid_and_renamed(self):
        for path in (ROOT / "dashboard" / "i18n").glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse([key for key in data if NAME in key], path.name)
        vietnamese = json.loads(text("dashboard/i18n/vi.json"))
        self.assertEqual(vietnamese["star.support_title"], f"Ủng hộ {NAME}")
        self.assertEqual(vietnamese["noti.kind_community"], "Nhà trường")
        self.assertEqual(json.loads(text("dashboard/manifest.json"))["name"], NAME)
        self.assertIn(f"<title>{NAME}</title>", text("dashboard/index.html"))

    def test_installer_is_separate_from_javis_os(self):
        setup = text("packaging/windows/javis-setup.iss")
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
        self.assertIn("Xem cách đóng góp", text("dashboard/star-nudge.js"))


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
