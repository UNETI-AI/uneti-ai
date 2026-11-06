#!/usr/bin/env python3
"""Turn a clean Javis OS tree into UNETI AI: python3 uneti/apply_brand.py

Runs once on an unbranded tree. An exact patch whose target has moved stops the run, so an upstream
change surfaces as a failed sync rather than a half-branded release.

Only text people read is renamed. Paths such as <brain>/Javis/, JAVIS_* variables, javis_* tools and
the strings the dashboard and server match against each other stay: a leftover "Javis" is cosmetic,
a renamed protocol string is a bug.
"""
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = json.loads((ROOT / "uneti" / "brand.json").read_text(encoding="utf-8"))
NAME = BRAND["name"]
REPO = BRAND["repo"]
TOKEN = BRAND["install_token"]
SITE = BRAND["site_url"]
SITE_HOST = SITE.split("/")[2]

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "uneti"}
WORD = re.compile(r"(?<![-/\\.])\bJavis\b(?![-/\\])")

# Text people read: safe to rename word by word. Dashboard JS and server Python are not listed
# because they hold matched strings and paths; they get the narrow replacements further down.
DISPLAY_FILES = ("dashboard/index.html", "dashboard/manifest.json", "dashboard/i18n/*.json", "CLAUDE.md",
                 "QUICKSTART*.md", "DEPLOY*.md", "docs/[0-9]*.md", "docs/README.md", "docs/en/*.md")

INSTALLER_FILES = ("packaging/**/*", ".github/workflows/desktop-installers.yml", "bin/*", "install.ps1",
                   "install.sh", "setup.bat", "JAVIS OS.bat", "javis-autostart.*", "open-javis.vbs",
                   "start-javis.*", "stop-javis.*", "Start JAVIS OS.command", "Stop JAVIS OS.command",
                   "JAVIS OS.app/Contents/Info.plist", "JAVIS OS.app/Contents/MacOS/javis",
                   "QUICKSTART*.md", "DEPLOY*.md", "docs/i18n/vi/README.md", ".gitattributes", ".dockerignore",
                   ".gitignore", "tests/python/test_desktop_installer.py", "tests/python/test_windows_launcher.py",
                   "tests/python/test_tu_mo_cung_may.py")

RENAMED_PATHS = ("JAVIS OS.bat", "JAVIS OS.app", "Start JAVIS OS.command", "Stop JAVIS OS.command")

I18N_TEXT = {
    "vi": {"noti.kind_community": "Nhà trường",
           "star.support_body": f"{NAME} là phần mềm mã nguồn mở, miễn phí. Đóng góp là tự nguyện và không "
                                "ảnh hưởng đến quyền sử dụng."},
    "en": {"noti.kind_community": "University",
           "star.support_body": f"{NAME} is free and open source. Contributions are voluntary and never "
                                "affect your right to use it."},
}

KILL_OLD = """    try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop; Ok "Da tat tien trinh cu PID $($c.OwningProcess)" }
    catch { Warn "Khong tat duoc PID $($c.OwningProcess) - dong tay roi chay lai." }
"""
# The upstream installer kills whatever holds the port. Only our own Python server may be stopped:
# the port can belong to something else on the machine, such as another Javis behind wslrelay.
KILL_NEW = """    $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
    if ($p -and $p.ProcessName -match '^pythonw?$') {
      try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop; Ok "Da tat tien trinh cu PID $($c.OwningProcess)" }
      catch { Warn "Khong tat duoc PID $($c.OwningProcess) - dong tay roi chay lai." }
    } else {
      Warn "Cong 7777 dang duoc chuong trinh khac su dung (PID $($c.OwningProcess)). Cai dat khong tu tat chuong trinh do - dong no roi chay lai."
      exit 1
    }
"""

# Applied after the word-by-word rename, so the old text here is what that step left behind.
PATCHES = (
    ("install.ps1", KILL_OLD, KILL_NEW),
    ("server/config.py", '"workspace_name": "Javis OS"', f'"workspace_name": "{NAME}"'),
    ("server/image_gen.py", 'BRAND_SOFTWARE = "Javis OS"', f'BRAND_SOFTWARE = "{NAME}"'),
    ("server/image_gen.py", 'BRAND_SOURCE = "https://javisos.com"', f'BRAND_SOURCE = "{SITE}"'),
    ("tests/python/test_image_gen.py", 'b"javisos.com" in _raw_luu and b"Javis OS" in _raw_luu',
     f'b"{SITE_HOST}" in _raw_luu and b"{NAME}" in _raw_luu'),
    ("tests/python/test_image_gen.py", 'b"javisos.com" in _sau', f'b"{SITE_HOST}" in _sau'),
    ("tests/python/test_image_gen.py", 'b"javisos.com" in _byte_go', f'b"{SITE_HOST}" in _byte_go'),
    # Sync branches carry upstream's changes without a changelog fragment of their own.
    (".github/workflows/ci.yml", 'if [ "$IS_FORK" = "true" ]; then opt=--optional; else opt=; fi', "opt=--optional"),
    ("server/main.py", '_AUTOSTART_NAME = "JavisOS"', f'_AUTOSTART_NAME = "{TOKEN}"'),
    ("packaging/windows/javis-setup.iss", "8F3C2A51-5D7E-4C0B-9E61-6A2D4B7C9E10", BRAND["app_guid"]),
    ("packaging/make_icons.py", "ACCENT = (253, 97, 0)", "ACCENT = (46, 81, 168)"),
    ("dashboard/star-nudge.js", "blogminhquy / <b>javis-os</b>", f"{BRAND['org']} / <b>{REPO.split('/')[1]}</b>"),
    ("dashboard/star-nudge.js",
     """'<button type="button" class="sn-go">' + ic("star") + " " + esc(t("star.go")) + "</button></div>";""",
     """'<button type="button" class="sn-go">' + ic("star") + " Xem cách đóng góp</button></div>";"""),
    ("dashboard/console.js", "if (_snGo) _snGo.onclick = () => window.JavisStar.open();",
     f'if (_snGo) _snGo.onclick = () => window.open("{SITE}", "_blank", "noopener");'),
    ("dashboard/chat-lenh.js", '(sess.title || "Javis")', f'(sess.title || "{NAME}")'),
    ("dashboard/chat-lenh.js", 'tw("lenh.ex_you") : "Javis")', f'tw("lenh.ex_you") : "{NAME}")'),
    ("dashboard/index.html",
     f'href="https://javisos.com" target="_blank" rel="noopener">by {NAME} Foundation</a>',
     f'href="https://github.com/{BRAND["upstream"]}" target="_blank" rel="noopener">Dựa trên Javis OS</a>'),
)


def read(path):
    return path.read_bytes().decode("utf-8", "surrogateescape")


def write(path, text):
    path.write_bytes(text.encode("utf-8", "surrogateescape"))


def rename_display(text):
    text = text.replace("JAVIS OS", NAME).replace("Javis OS", NAME)
    return WORD.sub(NAME, text)


def matching(patterns):
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_file() and not path.is_symlink():
                yield path


def repoint_to_our_repo():
    old = re.compile(rb"blogminhquy/javis-os(?![\w-])")
    new = REPO.encode()
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = Path(folder) / name
            if name.startswith("CHANGELOG") or name == "LICENSE" or path.is_symlink():
                continue
            data = path.read_bytes()
            if old.search(data):
                path.write_bytes(old.sub(new, data))


def rename_installer():
    for path in set(matching(INSTALLER_FILES)):
        data = path.read_bytes()
        changed = (data.replace(b"JavisOS", TOKEN.encode())
                   .replace(b"vn.minhquy.javis-os", BRAND["bundle_id"].encode())
                   .replace(b"JAVIS OS", NAME.encode()))
        if changed != data:
            path.write_bytes(changed)
    for old in RENAMED_PATHS:
        if (ROOT / old).exists():
            (ROOT / old).rename(ROOT / old.replace("JAVIS OS", NAME))


def rename_text():
    for path in set(matching(DISPLAY_FILES)):
        text = read(path)
        renamed = rename_display(text)
        if path.parent.name == "i18n" or path.name == "index.html":
            renamed = re.sub(r"\bJAVIS\b", NAME, renamed)
        if renamed != text:
            write(path, renamed)
    for path in (ROOT / "dashboard").glob("*.js"):
        text = read(path)
        renamed = (text.replace("Javis OS", NAME).replace("Javis Store", f"{NAME} Store")
                   .replace("MCP Javis", f"MCP {NAME}"))
        if renamed != text:
            write(path, renamed)
    for path in (ROOT / "server").rglob("*.py"):
        text = read(path)
        renamed = text.replace("Bạn là Javis", f"Bạn là {NAME}").replace("You are Javis", f"You are {NAME}")
        if renamed != text:
            write(path, renamed)


def set_i18n():
    for lang, items in I18N_TEXT.items():
        path = ROOT / "dashboard" / "i18n" / f"{lang}.json"
        text = read(path)
        for key, value in items.items():
            pattern = re.compile(r'("' + re.escape(key) + r'":\s*)"(?:[^"\\]|\\.)*"')
            if not pattern.search(text):
                raise SystemExit(f"Thiếu khóa {key} trong {path.name}: bản gốc đã đổi, cần sửa apply_brand.py")
            encoded = json.dumps(value, ensure_ascii=False)
            text = pattern.sub(lambda m, e=encoded: m.group(1) + e, text, count=1)
        write(path, text)


def apply_patches():
    for rel, old, new in PATCHES:
        path = ROOT / rel
        text = read(path)
        if old not in text and "\r\n" in text:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if old not in text:
            raise SystemExit(f"Không thấy đoạn cần sửa trong {rel}: bản gốc đã đổi, cần sửa apply_brand.py\n{old[:120]}")
        write(path, text.replace(old, new))


def main():
    if f'GITHUB_REPO = "{REPO}"' in read(ROOT / "server" / "main.py"):
        raise SystemExit("Cây mã này đã mang thương hiệu UNETI AI, không áp dụng lần hai.")
    repoint_to_our_repo()
    rename_installer()
    rename_text()
    set_i18n()
    apply_patches()
    (ROOT / ".github" / "CODEOWNERS").unlink(missing_ok=True)
    shutil.copytree(ROOT / "uneti" / "overlay", ROOT, dirs_exist_ok=True)
    print(f"Đã áp dụng thương hiệu {NAME}.")


if __name__ == "__main__":
    main()
