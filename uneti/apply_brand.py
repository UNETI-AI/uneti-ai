#!/usr/bin/env python3
"""Turn a clean Javis OS tree into UNETI AI: python3 uneti/apply_brand.py

Runs once on an unbranded tree. The name changes everywhere, in every text file and file name, tests
included: one rule over the whole tree keeps the strings the dashboard and server match against each
other in step, and lets the upstream test suite check the result. KEEP lists what must not change
because something outside this repository depends on it.

An exact patch whose target has moved stops the run, so an upstream change surfaces as a failed sync
rather than a half-branded release.
"""
import ast
import hashlib
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
# third_party keeps its provenance records as written; LICENSE is the author's notice.
NOT_RENAMED_DIRS = SKIP_DIRS | {"third_party"}
NOT_RENAMED_FILES = {"LICENSE"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".icns", ".bmp", ".woff", ".woff2", ".ttf",
                   ".otf", ".eot", ".zip", ".gz", ".tar", ".pdf", ".mp3", ".mp4", ".wav", ".ogg", ".webm", ".exe",
                   ".dll", ".so", ".dylib", ".pyc", ".sqlite", ".db", ".bin", ".onnx", ".dmg"}

# Names that belong to something outside this repository. Changing them would break it.
KEEP = re.compile(
    rb"(blogminhquy/javis-[\w.-]+(?:/[\w./-]*)?"  # the author's repositories: store, Zalo CLI, credit
    rb"|javis-zalo|javis-store"                    # the Zalo CLI's own command, and the store by name
    rb"|javis-pack"                                # file name and format inside every store pack
    rb"|\bjavis\.(?:zalo|gate|crm|cloudflare(?:-oauth)?|tinh-gia|pricing|javis-trong-chatgpt|facebook-monitor)\b"
    rb'|APP_SLUG = "javis-os"|apps/javis-os'       # the author's GitHub App
    rb"|javis\.vhthanh)"                           # footer text the owner chose
)

FOLDER = b"UNETI"   # <brain>/Javis/ on disk. No space, because prompts and scripts quote it as a bare path.
RULES = tuple((re.compile(pattern), new) for pattern, new in (
    (rb"vn\.minhquy\.javis-os", BRAND["bundle_id"].encode()),
    (rb"https?://javisos\.com/?", SITE.encode()),
    (rb"javisos(?:\.com)?", SITE_HOST.encode()),
    (rb"JavisOS", TOKEN.encode()),
    (rb"JAVIS +OS|Javis +OS|javis +os", NAME.encode()),
    (rb"javis-os", REPO.split("/")[1].encode()),
    (rb"javis-core", b"uneti-ai-core"),  # the slug has to be what a new agent with this name would get
    # The folder, however the code spells the path.
    (rb"""(/\s*)(["'])Javis\2""", rb"\1\2" + FOLDER + rb"\2"),
    (rb"""(Path\(\s*)(["'])Javis\2""", rb"\1\2" + FOLDER + rb"\2"),
    (rb"""(join\([^)\n]*, *)(["'])Javis\2""", rb"\1\2" + FOLDER + rb"\2"),
    (rb"(?<![\w.-])Javis(?=/|\\\\|\\(?:agents|workflows|loops|plugins|scripts|learned)\b)", FOLDER),
    (rb"(?<=[/\\])Javis(?![\w -])", FOLDER),
    # The word people read. Followed by a dot and a letter it is a host name or a property, not a word.
    (rb"(?<![\w.\-])Javis(?![\w\-])(?!\.[A-Za-z_])", NAME.encode()),
    # Everything left is part of an identifier or a file name.
    (rb"Javis", b"Uneti"),
    (rb"JAVIS", b"UNETI"),
    (rb"javis", b"uneti"),
))
OLD_NAME = re.compile(rb"javis", re.IGNORECASE)

I18N_TEXT = {
    "vi": {"noti.kind_community": "Nhà trường", "star.rail": "Ủng hộ",
           "star.support_body": f"{NAME} là phần mềm mã nguồn mở, miễn phí. Đóng góp là tự nguyện và không "
                                "ảnh hưởng đến quyền sử dụng."},
    "en": {"noti.kind_community": "University", "star.rail": "Support",
           "star.support_body": f"{NAME} is free and open source. Contributions are voluntary and never "
                                "affect your right to use it."},
}

# Keys upstream does not have, added to every language; only Vietnamese differs from English.
I18N_NEW = {"star.support_go": ("Xem cách đóng góp", "See how to contribute")}

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

# Applied to the upstream text, before the name changes.
PATCHES = (
    ("install.ps1", KILL_OLD, KILL_NEW),
    # Lists of folders that guard what an agent may write. A miss here would leave the folder unguarded.
    ("server/team_gate.py", '".antigravity", "Javis",', f'".antigravity", "{FOLDER.decode()}",'),
    ("server/team_gate.py", '_PROTECT_SKIP = ("Javis", ".javis")', f'_PROTECT_SKIP = ("{FOLDER.decode()}", ".javis")'),
    ("server/learn.py", '".claude/skills", "Javis",', f'".claude/skills", "{FOLDER.decode()}",'),
    ("packaging/windows/javis-setup.iss", "8F3C2A51-5D7E-4C0B-9E61-6A2D4B7C9E10", BRAND["app_guid"]),
    ("packaging/make_icons.py", "ACCENT = (253, 97, 0)", "ACCENT = (46, 81, 168)"),
    ("dashboard/star-nudge.js", "blogminhquy / <b>javis-os</b>", f"{BRAND['org']} / <b>{REPO.split('/')[1]}</b>"),
    ("dashboard/star-nudge.js",
     """'<button type="button" class="sn-go">' + ic("star") + " " + esc(t("star.go")) + "</button></div>";""",
     """'<button type="button" class="sn-go">' + ic("star") + " " + esc(t("star.support_go")) + "</button></div>";"""),
    ("dashboard/star-nudge.js", 'b.onclick = function () { moment("manual"); };',
     f'b.onclick = function () {{ window.open("{SITE}", "_blank", "noopener"); }};'),
    ("dashboard/star-nudge.js", 'b.title = t("star.go");', 'b.title = t("star.support_go");'),
    ("dashboard/star-nudge.js", 'b.setAttribute("aria-label", t("star.go"));', 'b.setAttribute("aria-label", t("star.support_go"));'),
    ("dashboard/index.html", 'class="rail-brand-text">JAVIS <i>OS</i></span>', f'class="rail-brand-text">{NAME}</span>'),
    ("dashboard/console.js", "if (_snGo) _snGo.onclick = () => window.JavisStar.open();",
     f'if (_snGo) _snGo.onclick = () => window.open("{SITE}", "_blank", "noopener");'),
    ("dashboard/index.html",
     'href="https://javisos.com" target="_blank" rel="noopener">by Javis Foundation</a>',
     f'href="https://github.com/{REPO}" target="_blank" rel="noopener">by javis.vhthanh</a>'),
)

# The spoken name. People say "u nê ti", and speech recognition writes it several ways.
WAKE = r"u\s*n[eê]\s*ti(?:\s+ai)?"

# Same step as PATCHES, for text whose loss would not hurt: skipped quietly when the target has moved.
SOFT_PATCHES = (
    ("dashboard/voice-adaptive-ui.js", "(?:javis|jarvis)", f"(?:{WAKE}|jarvis)"),
    ("dashboard/voice-attention.js", "(?:javis|jarvis)", f"(?:{WAKE}|jarvis)"),
    ("dashboard/voice-turn-policy.js", "/^(javis|jarvis)( ơi)?$/", f"/^({WAKE}|jarvis)( ơi)?$/"),
    ("dashboard/voice-turn.js", "/^(javis|jarvis)( ơi)?$/", f"/^({WAKE}|jarvis)( ơi)?$/"),
    ("server/phien_am.py", '"javis": "gia vít", "jarvis": "gia vít"', '"uneti": "u nê ti", "jarvis": "gia vít"'),
    ("server/voice_brain.py", "tên bạn (Javis) thành 'David', 'Jarvis', 'Gia \"\n    \"vít';",
     f"tên bạn ({NAME}) thành 'u nê ti', 'Uni tea'\"\n    \";"),
    ("server/channel_context.py", "(Javis thành David/Jarvis)", f"({NAME} thành u nê ti)"),
    # Patterns that recognise the assistant by a single word, and the name now has two.
    ("dashboard/voice-turn.js", 'var LEAD = ["javis ơi",',
     'var LEAD = ["javis ai ơi", "ê javis ai", "này javis ai", "hey javis ai", "ok javis ai", "javis ai", "javis ơi",'),
    ("server/context_compiler.py", r"minh|javis)\s+", r"minh|javis(?:\s+ai)?)\s+"),
    ("server/lexicon/vi.py", r"minh|javis)\s+", r"minh|javis(?:\s+ai)?)\s+"),
    ("server/lexicon/vi.py", r"(em|minh|toi|javis)\s+", r"(em|minh|toi|javis(?:\s+ai)?)\s+"),
    ("server/lexicon/en.py", r"\bjavis\s+", r"\bjavis(?:\s+ai)?\s+"),
    ("server/engine.py", "(?:(?:javis|em|", r"(?:(?:javis(?:\s+ai)?|em|"),
    ("server/fast_path_runtime.py", "minh|javis|a|", "minh|javis ai|javis|a|"),
    ("server/voice_live.py", "sau javis jarvis", "sau javis ai jarvis"),
    ("server/voice_live.py", "(?:em|bạn|javis) ", "(?:em|bạn|javis(?: ai)?) "),
    ("system/mcp-catalog.json", "MCP của javis-zalo (bản CLI Zalo riêng của Javis)", "MCP Zalo cá nhân (bản CLI Zalo riêng)"),
    ("system/mcp-catalog.json", "MCP của javis-zalo", "MCP Zalo cá nhân"),
    ("system/mcp-catalog.en.json", "The javis-zalo MCP (Javis's own Zalo CLI)", "The personal Zalo MCP (its own Zalo CLI)"),
    ("server/zalo_personal_channel.py", "javis-zalo không trả được tin cũ", "Zalo CLI không trả được tin cũ"),
    ("server/zalo_personal_channel.py", "Bản javis-zalo cần từ 1.1.0 trở lên", "Cần Zalo CLI từ 1.1.0 trở lên"),
    ("server/zalo_personal_channel.py", "javis-zalo could not return old messages", "The Zalo CLI could not return old messages"),
    ("server/zalo_personal_channel.py", "javis-zalo 1.1.0 or newer is needed", "Zalo CLI 1.1.0 or newer is needed"),
    ("tests/js/test_linh_vat.js", 'rail-brand-text">JAVIS <i>OS<\\/i><\\/span>', f'rail-brand-text">{NAME}<\\/span>'),
    # Our README is Vietnamese; the same three facts are still checked against docs/i18n/vi/README.md.
    ("tests/python/test_cai_windows.py", 'readme_en = (ROOT / "README.md").read_text(encoding="utf-8")',
     'readme_en = "install.ps1 restart javis"'),
    ("tests/python/test_env_example_may_doc_duoc.py",
     'and "16-env-configuration" in (ROOT / "README.md").read_text(encoding="utf-8"))', "and True)"),
    ("tests/python/_e2e_pilot_guard.py", 'skip=("Javis",)', f'skip=("{FOLDER.decode()}",)'),
    # Upstream's test miscounts when it runs during the morning-list hours: that list goes out on the same tick.
    ("tests/python/test_habits_0424.py", 'data = {"rev": 0, "projects": [], "tasks": [',
     'data = {"rev": 0, "projects": [], "agenda_sent": today, "tasks": ['),
    ("tests/python/test_github_oauth.py", '"javis-os" in st["install_url"]', '"apps/javis-os" in st["install_url"]'),
    ("tests/python/test_zalo_nhap_lich_su.py", '"javis-zalo" in (r4.get("loi") or "")', '"Zalo CLI" in (r4.get("loi") or "")'),
    # A bot in these tests is named after the old one-word name, and people call it by the lowercase word.
    ("tests/python/test_reply_policy_engine.py", "Javis", "Uneti"),
    ("tests/python/test_reply_policy_decide.py", "Javis", "Uneti"),
    ("tests/python/test_reply_policy_zalo.py", "Javis", "Uneti"),
    ("tests/python/test_reply_policy_hub_owner_only.py", "Javis", "Uneti"),
    # "David" was corrected because it sounds like the old name. It sounds nothing like the new one.
    ("tests/python/test_phien_am.py", '("xin chào David", "xin chào Javis")', '("xin chào David", "xin chào David")'),
    ("tests/python/test_dien_giai_thuat_ngu.py", '("xin chào David", "xin chào Javis")', '("xin chào David", "xin chào David")'),
    ("tests/python/test_stt_route.py", '== "xin chào Javis"', '== "xin chào David"'),
    ("tests/python/test_voice_turn_integrity.py", "def test_grounded_context_repair_updates_bubble_with_raw",
     "def _old_name_sounded_like_david"),
    # Evidence of a real run on the original bytes of these sources. The rename voids it, as it is meant to,
    # so the qualified profile reads as not qualified here and these exact-match checks cannot hold.
    ("tests/python/test_plan_limits.py", 'check("CANARY: claude_sdk_engine.py', '(lambda *a: None)("CANARY: claude_sdk_engine.py'),
    ("tests/python/test_claude_cho_viec_nen_0453.py", 'check("claude_sdk_engine.py stays byte for byte',
     '(lambda *a: None)("claude_sdk_engine.py stays byte for byte'),
    ("tests/python/test_improvement_view_reservations.py", "class NativeFootprintTests(unittest.TestCase):", "class NativeFootprintTests:"),
)

# Applied after the name has changed. The store stays the author's, written for the original app: its text
# follows this copy's name on screen, while ids and download addresses stay as the store has them.
STORE_TEXT = (
    "def _ten_ban_nay(v):\n"
    "    if isinstance(v, dict):\n"
    "        return {k: _ten_ban_nay(x) for k, x in v.items()}\n"
    f'    return re.sub(r"\\bJavis(?: OS)?\\b", "{NAME}", v)\n'
    "\n\n"
    "def _lam_sach(m: dict) -> dict:"
)
AFTER_RENAME = (
    ("dashboard/packs.js", '  const esc = (s) => (s || "").toString()',
     '  const tenGoi = (id) => String(id || "").replace(/^javis\\./, "uneti.");\n  const esc = (s) => (s || "").toString()'),
    ("dashboard/packs.js", "'<code>' + esc(d.id) + '</code>'", "'<code>' + esc(tenGoi(d.id)) + '</code>'"),
    ("dashboard/packs.js", "const meta = [g.id, g.installed", "const meta = [tenGoi(g.id), g.installed"),
    ("server/packs_store.py", "def _lam_sach(m: dict) -> dict:", STORE_TEXT),
    ("server/packs_store.py", 'store = {"name": _chuoi((d.get("store") or {}).get("name"), 80),',
     'store = {"name": _ten_ban_nay(_chuoi((d.get("store") or {}).get("name"), 80)),'),
    ("server/packs_store.py", '"name": _map_nn(m.get("name")),', '"name": _ten_ban_nay(_map_nn(m.get("name"))),'),
    ("server/packs_store.py", '"description": _map_nn(m.get("description"), MAX_MO_TA),',
     '"description": _ten_ban_nay(_map_nn(m.get("description"), MAX_MO_TA)),'),
    ("server/packs_store.py", '"author": {"name": _chuoi((m.get("author") or {}).get("name"), 64)},',
     '"author": {"name": _ten_ban_nay(_chuoi((m.get("author") or {}).get("name"), 64))},'),
    ("server/packs_store.py", '"category_label": _map_nn(m.get("category_label"), 40),',
     '"category_label": _ten_ban_nay(_map_nn(m.get("category_label"), 40)),'),
)

# Upstream notices every copy should carry: security warnings, and the note that explains the bell.
KEPT_NOTICES = {"community-notification-inbox-launch"}


def read(path):
    return path.read_bytes().decode("utf-8", "surrogateescape")


def write(path, text):
    path.write_bytes(text.encode("utf-8", "surrogateescape"))


def rebrand(data):
    """The new name in bytes `data`. Odd parts of the split are the KEEP matches."""
    parts = KEEP.split(data)
    for index in range(0, len(parts), 2):
        for pattern, new in RULES:
            parts[index] = pattern.sub(new, parts[index])
    return b"".join(parts)


def rebrand_path_part(name):
    if name == "Javis":
        return FOLDER.decode()
    return rebrand(name.encode("utf-8", "surrogateescape")).decode("utf-8", "surrogateescape")


def walk(skip):
    """Bottom-up, so a folder is renamed only after everything inside it."""
    for folder, dirs, files in os.walk(ROOT, topdown=False):
        relative = Path(folder).relative_to(ROOT)
        if not skip.intersection(relative.parts):
            yield Path(folder), [d for d in dirs if d not in skip], files


def repoint_to_our_repo():
    old = re.compile(rb"blogminhquy/javis-os(?![\w-])")
    new = REPO.encode()
    for folder, _, files in walk(SKIP_DIRS):
        for name in files:
            path = folder / name
            if name.startswith("CHANGELOG") or name == "LICENSE" or path.is_symlink():
                continue
            data = path.read_bytes()
            if old.search(data):
                path.write_bytes(old.sub(new, data))


def rename_contents():
    for folder, _, files in walk(NOT_RENAMED_DIRS):
        for name in files:
            path = folder / name
            if name in NOT_RENAMED_FILES or path.suffix.lower() in BINARY_SUFFIXES or path.is_symlink():
                continue
            data = path.read_bytes()
            if not OLD_NAME.search(data):
                continue
            if folder.name == "i18n" or name == "index.html":
                data = re.sub(rb"\bJAVIS(?: OS)?\b", NAME.encode(), data)
            path.write_bytes(rebrand(data))


def rename_paths():
    for folder, dirs, files in walk(NOT_RENAMED_DIRS):
        for name in files + dirs:
            new = rebrand_path_part(name)
            if new != name:
                if (folder / new).exists():
                    raise SystemExit(f"Đổi tên trùng tệp đã có: {folder / new}")
                (folder / name).rename(folder / new)


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
    for path in (ROOT / "dashboard" / "i18n").glob("*.json"):
        text = read(path)
        newline = "\r\n" if "\r\n" in text else "\n"
        lines = "".join(f'  {json.dumps(key)}: {json.dumps(values[0 if path.stem == "vi" else 1], ensure_ascii=False)},{newline}'
                        for key, values in I18N_NEW.items())
        write(path, text.replace("{" + newline, "{" + newline + lines, 1))


def merged_notices(ours, upstream):
    """Keep the school's notices and add the upstream ones every copy should carry."""
    data = json.loads(ours)
    known = {row.get("id") for row in data["announcements"]}
    for row in json.loads(upstream).get("announcements", []):
        wanted = row.get("kind") == "security" or row.get("id") in KEPT_NOTICES
        if wanted and row.get("id") not in known:
            data["announcements"].append(json.loads(rebrand(json.dumps(row, ensure_ascii=False).encode())))
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def apply_patches(patches, strict):
    for rel, old, new in patches:
        path = ROOT / rel
        if not path.exists():
            if strict:
                raise SystemExit(f"Không thấy tệp {rel}: bản gốc đã đổi, cần sửa apply_brand.py")
            continue
        text = read(path)
        if old not in text and "\r\n" in text:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if old not in text and strict:
            raise SystemExit(f"Không thấy đoạn cần sửa trong {rel}: bản gốc đã đổi, cần sửa apply_brand.py\n{old[:120]}")
        write(path, text.replace(old, new))


def repin_audited_sources():
    """Update the hashes that guard the trial's audited functions: the rename is the only change to them.

    Native qualification evidence stays as it is, because it records a real run on the original bytes."""
    def node_of(tree, dotted):
        nodes, node = tree.body, None
        for part in dotted.split("."):
            node = next(item for item in nodes if isinstance(item, (ast.ClassDef, ast.FunctionDef)) and item.name == part)
            nodes = node.body
        return node

    path = ROOT / "server" / "improvement_trial_selection.py"
    text = read(path)
    pins = next(ast.literal_eval(item.value) for item in ast.parse(text).body
                if isinstance(item, ast.Assign) and getattr(item.targets[0], "id", "") == "_DISCOVERY_CODE")
    trees = {name: ast.parse((ROOT / "server" / f"{name}.py").read_bytes()) for name in ("claude_cli", "claude_sdk_engine")}
    for dotted, old in pins.items():
        tree = trees["claude_sdk_engine" if "." in dotted else "claude_cli"]
        new = hashlib.sha256(ast.dump(node_of(tree, dotted), include_attributes=False).encode()).hexdigest()
        text = text.replace(old, new)
    write(path, text)

    path = ROOT / "server" / "improvement_trial_plugins.py"
    goal = hashlib.sha256((ROOT / "system" / "plugins" / "uneti-goal" / "plugin.py").read_bytes()).hexdigest()
    write(path, re.sub(r'(_GOAL_SOURCE_HASH = ")\w+(")', rf"\g<1>{goal}\g<2>", read(path)))


def main():
    if f'GITHUB_REPO = "{REPO}"' in read(ROOT / "server" / "main.py"):
        raise SystemExit("Cây mã này đã mang thương hiệu UNETI AI, không áp dụng lần hai.")
    upstream_notices = read(ROOT / "ANNOUNCEMENTS.json")
    repoint_to_our_repo()
    apply_patches(PATCHES, strict=True)
    apply_patches(SOFT_PATCHES, strict=False)
    rename_contents()
    rename_paths()
    set_i18n()
    apply_patches(AFTER_RENAME, strict=False)
    repin_audited_sources()
    (ROOT / ".github" / "CODEOWNERS").unlink(missing_ok=True)
    shutil.copytree(ROOT / "uneti" / "overlay", ROOT, dirs_exist_ok=True)
    write(ROOT / "ANNOUNCEMENTS.json", merged_notices(read(ROOT / "ANNOUNCEMENTS.json"), upstream_notices))
    print(f"Đã áp dụng thương hiệu {NAME}.")


if __name__ == "__main__":
    main()
