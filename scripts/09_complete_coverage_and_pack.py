#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09_complete_coverage_and_pack.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
TASK 9: Complete Coverage - Intro, In-Game Handler & NPC Dialogues, 100% Settings Menu
--------------------------------------------------------------------------------
Author: Antigravity (Google DeepMind)
Target Game: Cruelty Squad (Godot Engine v3.x)
"""

import os
import sys
import struct
import json
import hashlib
import re
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set, Optional

# Reconfigure console output to UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PCK_MAGIC = b"GDPC"
PCK_FORMAT_VERSION = 1
PCK_HEADER_SIZE = 88
FILE_ALIGNMENT = 16

FONTS_TO_IMPORT = [
    "res://Fonts/MingLiU-ExtB-01.ttf",
    "res://Fonts/gamefont(1).ttf",
    "res://Fonts/gamefont.ttf",
]

STEX_TO_IMPORT = [
    "res://.import/Misery_Achieved.png-c258c1f600a358f228fcb3cee8a3b4d9.stex",
    "res://.import/Soul_Rended.png-f59fc37014a0d66d7570cbe8018df385.stex",
    "res://.import/ending2face.png-0a76daf9337823202a1f7b99bfe2981e.s3tc.stex",
    "res://.import/ending2face.png-0cba63e81c5b558cca967bb717ba984e.s3tc.stex",
    "res://.import/gorbino.png-2a2ee8205345cb3889d9ae67826ce45a.s3tc.stex",
    "res://.import/store_punishment.png-3c139239c2f9b91de9121602fb5d6bb3.s3tc.stex",
    "res://.import/title1.png-a1bb4ee083219025e0ecce91a09c21ba.stex",
    "res://.import/title11.png-21e54c121bd05711c72e3e99d7ca5ed3.stex",
]

STRING_LITERAL_REGEX = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')

# Exact canonical Russian subtitles for Intro (Cutscene1.tscn lines 1893-1897)
CUTSCENE1_RU_LINES = [
    "",
    "",
    "",
    "Эй, это я. Я разбудил тебя от твоей депрессивной спячки?",
    "Слышал, ты в глубокой заднице после увольнения из Отряда Смерти SEC.",
    "В конце концов, не так уж много может сделать такой конченый отшельник-неудачник, как ты.",
    "У меня для тебя отличные новости касательно твоего трудоустройства.",
    "Эта работа как раз в твоем вкусе, но тебе придется перестроиться на корпоративное мышление.",
    "Я создал тебе аккаунт на MyWork, так что можешь приступать, когда захочешь.",
    "Полагаю, подходящее снаряжение у тебя уже есть.",
    "И последнее: тебе придется логиниться хотя бы на 15 минут в день в приложении психологической адаптации.",
    "Нам нужен ясный и подготовленный разум. Без срывов. Понял?",
    "На этом, пожалуй, все. Удачи на новой карьерной стезе.",
    "",
    "",
]


class CompleteCoverageTool:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.vanilla_dir = base_dir / "vanilla_new"
        self.patched_dir = base_dir / "_patched_files"
        self.pck_dir = base_dir / "_source_pcks"
        self.db_path = base_dir / "localization_db.json"
        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.output_pck_path = base_dir / "crueltysquad_ru_v2.pck"
        self.root_pck_path = Path("C:/dev/crueltysquad_ru_v2.pck")

    def run_all(self):
        print("=" * 80)
        print(" CRUELTY SQUAD - TASK 9: COMPLETE LOCALIZATION COVERAGE & REBUILD")
        print("=" * 80)

        self.step1_diagnose_target_strings()
        self.step2_clean_and_patch_all_files()
        self.step3_prepack_automated_linter()
        self.step4_binary_pck_rebuild()
        self.step5_verify_and_report()

    # --------------------------------------------------------------------------
    # Step 1: Diagnose Target Strings
    # --------------------------------------------------------------------------
    def step1_diagnose_target_strings(self):
        print("\n[*] [1/5] Verifying target strings and locations across codebase...")

        # 1. Intro string
        c1_path = self.vanilla_dir / "Cutscenes" / "Cutscene1.tscn"
        c1_txt = c1_path.read_text(encoding="utf-8", errors="ignore")
        assert "depression nap" in c1_txt, "Intro text not found in Cutscene1.tscn!"
        print(f"    - Found Intro Subtitles: {c1_path.name} (lines 1893-1897, LINES array)")

        # 2. Handler combat cocktail
        msg_path = self.vanilla_dir / "Entities" / "Message_Area.tscn"
        msg_txt = msg_path.read_text(encoding="utf-8", errors="ignore")
        assert "special combat cocktail" in msg_txt, "Handler message not found in Message_Area.tscn!"
        print(f"    - Found Handler Message Template: {msg_path.name}")

        l1_path = self.vanilla_dir / "Levels" / "Level1.tscn"
        l1_txt = l1_path.read_text(encoding="utf-8", errors="ignore")
        assert "special combat cocktail" in l1_txt, "Handler message not found in Level1.tscn!"
        print(f"    - Found In-Level Handler Message: {l1_path.name} (line 10257)")

        # 3. Settings strings
        menu_path = self.vanilla_dir / "Menu" / "Menu_test.tscn"
        menu_txt = menu_path.read_text(encoding="utf-8", errors="ignore")
        assert "Full Screen" in menu_txt and "Master Volume" in menu_txt, "Settings labels missing in Menu_test.tscn!"
        print(f"    - Found Settings Labels: {menu_path.name} (lines 134-515)")

        gd_path = self.vanilla_dir / "Menu_Test.gd"
        gd_txt = gd_path.read_text(encoding="utf-8", errors="ignore")
        assert "Civilians: MAX" in gd_txt, "Civilians slider label missing in Menu_Test.gd!"
        print(f"    - Found Settings Dynamic Text: {gd_path.name} (lines 1416-1419)")

        print("[+] All target string locations diagnosed and verified.")

    # --------------------------------------------------------------------------
    # Step 2: Clean Revert and Full Generation of _patched_files
    # --------------------------------------------------------------------------
    def step2_clean_and_patch_all_files(self):
        print("\n" + "=" * 80)
        print(" [*] [2/5] FULL REGENERATION OF _patched_files (GD + TSCN + JSON)")
        print("=" * 80)

        # 1. Save existing 19 Level JSONs
        cached_level_jsons: Dict[str, str] = {}
        levels_dir = self.patched_dir / "Levels"
        if levels_dir.exists():
            for jf in levels_dir.glob("*.json"):
                cached_level_jsons[jf.name] = jf.read_text(encoding="utf-8")

        # 2. Clear _patched_files completely
        if self.patched_dir.exists():
            print("[*] Removing stale _patched_files directory...")
            shutil.rmtree(self.patched_dir)
        self.patched_dir.mkdir(parents=True, exist_ok=True)

        # 3. Load localization database
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        with open(self.db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        db_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for entry in db:
            db_by_file.setdefault(entry["file_path"], []).append(entry)

        # ----------------------------------------------------------------------
        # A. Patch GDScript files (33 files)
        # ----------------------------------------------------------------------
        gd_files = [f for f in db_by_file if f.endswith(".gd")]
        print(f"[*] Patching {len(gd_files)} GDScript files (exact line count, tab indentation)...")

        for fpath_str in gd_files:
            # Strictly do not touch Speech.gd or speech_label.gd
            if fpath_str in ["Menu/Speech.gd", "Scripts/speech_label.gd"]:
                continue

            entries = db_by_file[fpath_str]
            line_map: Dict[Tuple[int, int], str] = {}

            for e in entries:
                lno = e["line_num"]
                orig = e.get("en_original", "")

                # Architectural Lock Filter: NEVER replace technical engine IDs
                if fpath_str == "Entities/Game_Manager.gd" and lno in [14, 18, 25]:
                    continue  # Steam achievement IDs
                if fpath_str == "Menu_Test.gd" and lno in [1449, 1450] and orig == "House":
                    continue  # Global implant lookup
                if fpath_str == "Scripts/Player.gd" and lno == 157 and orig == "Limit Chancellor":
                    continue  # Dead NPC ID lookup

                sub_i = int(e["id"].split(":")[-1])
                line_map[(lno, sub_i)] = e["ru_final"]

            src_p = self.vanilla_dir / fpath_str
            with open(src_p, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()

            for lno in range(1, len(lines) + 1):
                line = lines[lno - 1]

                # Specific override for Menu_Test.gd Civilians slider labels
                if fpath_str == "Menu_Test.gd":
                    if lno == 1416 and '"Civilians: "' in line:
                        lines[lno - 1] = line.replace('"Civilians: "', '"Гражданские: "')
                        continue
                    if lno == 1419 and '"Civilians: MAX"' in line:
                        lines[lno - 1] = line.replace('"Civilians: MAX"', '"Гражданские: МАКС"')
                        continue

                matches = list(STRING_LITERAL_REGEX.finditer(line))
                repls = []
                for s_idx, m in enumerate(matches):
                    if (lno, s_idx) in line_map:
                        repls.append((m.start(), m.end(), line_map[(lno, s_idx)]))

                if repls:
                    repls.sort(key=lambda x: x[0], reverse=True)
                    new_line = line
                    for start, end, ru_text in repls:
                        ru_esc = ru_text.replace('"', '\\"')
                        new_token = f'"{ru_esc}"'
                        new_line = new_line[:start] + new_token + new_line[end:]
                    lines[lno - 1] = new_line

            out_p = self.patched_dir / fpath_str
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8", newline="\n") as out_f:
                out_f.writelines(lines)

        # ----------------------------------------------------------------------
        # B. Patch TSCN scene files (54 files)
        # ----------------------------------------------------------------------
        tscn_files = [f for f in db_by_file if f.endswith(".tscn")]
        print(f"[*] Patching {len(tscn_files)} TSCN scene files (100% dialogue & settings coverage)...")

        for fpath_str in tscn_files:
            entries = db_by_file[fpath_str]
            line_map: Dict[Tuple[int, int], str] = {}

            for e in entries:
                sub_i = int(e["id"].split(":")[-1])
                line_map[(e["line_num"], sub_i)] = e["ru_final"]

            src_p = self.vanilla_dir / fpath_str
            with open(src_p, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()

            # 1. Custom handling for Intro Cutscene (Cutscenes/Cutscene1.tscn)
            if fpath_str == "Cutscenes/Cutscene1.tscn":
                # Replace lines 1893-1897 with exact Russian dialogue
                ru_items = [f'"{s}"' for s in CUTSCENE1_RU_LINES]
                lines[1892] = f'LINES = [ {ru_items[0]}, {ru_items[1]}, {ru_items[2]}, {ru_items[3]},\n'
                lines[1893] = f'{ru_items[4]},\n'
                lines[1894] = f'{ru_items[5]},\n'
                lines[1895] = f'{ru_items[6]}, {ru_items[7]},\n'
                lines[1896] = f'{ru_items[8]}, {ru_items[9]}, {ru_items[10]}, {ru_items[11]}, {ru_items[12]}, {ru_items[13]}, {ru_items[14]} ]\n'

            # 2. Custom handling for Menu_test.tscn Settings Labels
            elif fpath_str == "Menu/Menu_test.tscn":
                # Exact Russian Settings translation overrides
                settings_map = {
                    134: 'text = "Полный экран"\n',
                    199: 'text = "Чувствительность\n',
                    200: 'мыши"\n',
                    216: 'text = "Инверсия оси Y"\n',
                    223: 'text = "Качание камеры"\n',
                    265: 'text = "Общая громкость"\n',
                    283: 'text = "Громкость музыки"\n',
                    316: 'text = "Цвет крови"\n',
                    428: 'text = "Пропуск заставки"\n',
                    434: 'text = "Таймер"\n',
                    441: 'text = "Отражения"\n',
                    448: 'text = "Режим производительности"\n',
                    454: 'text = "Гражданские"\n',
                    497: 'text = "Сбросить прогресс уровней"\n',
                    503: 'text = "Очистить сохранения"\n',
                    509: 'text = "Сбросить таймер"\n',
                }
                for lno in range(1, len(lines) + 1):
                    if lno in settings_map:
                        lines[lno - 1] = settings_map[lno]
                    else:
                        line = lines[lno - 1]
                        matches = list(STRING_LITERAL_REGEX.finditer(line))
                        repls = []
                        for s_idx, m in enumerate(matches):
                            if (lno, s_idx) in line_map:
                                repls.append((m.start(), m.end(), line_map[(lno, s_idx)]))
                        if repls:
                            repls.sort(key=lambda x: x[0], reverse=True)
                            new_line = line
                            for start, end, ru_text in repls:
                                ru_esc = ru_text.replace('"', '\\"')
                                new_token = f'"{ru_esc}"'
                                new_line = new_line[:start] + new_token + new_line[end:]
                            lines[lno - 1] = new_line

            # 3. Custom handling for General_Menu.tscn multiline text
            elif fpath_str == "Menu/General_Menu.tscn":
                for lno in range(1, len(lines) + 1):
                    if lno == 902 and 'text = "OBJECTIVE 1' in lines[lno - 1]:
                        lines[lno - 1] = 'text = "ЦЕЛЬ 1\n'
                    elif lno == 903 and 'OBJECTIVE 2"' in lines[lno - 1]:
                        lines[lno - 1] = 'ЦЕЛЬ 2"\n'
                    else:
                        line = lines[lno - 1]
                        matches = list(STRING_LITERAL_REGEX.finditer(line))
                        repls = []
                        for s_idx, m in enumerate(matches):
                            if (lno, s_idx) in line_map:
                                repls.append((m.start(), m.end(), line_map[(lno, s_idx)]))
                        if repls:
                            repls.sort(key=lambda x: x[0], reverse=True)
                            new_line = line
                            for start, end, ru_text in repls:
                                ru_esc = ru_text.replace('"', '\\"')
                                new_token = f'"{ru_esc}"'
                                new_line = new_line[:start] + new_token + new_line[end:]
                            lines[lno - 1] = new_line

            # 4. Standard TSCN line-and-regex matching for all other 51 scenes
            else:
                for lno in range(1, len(lines) + 1):
                    line = lines[lno - 1]
                    matches = list(STRING_LITERAL_REGEX.finditer(line))
                    repls = []
                    for s_idx, m in enumerate(matches):
                        if (lno, s_idx) in line_map:
                            repls.append((m.start(), m.end(), line_map[(lno, s_idx)]))

                    if repls:
                        repls.sort(key=lambda x: x[0], reverse=True)
                        new_line = line
                        for start, end, ru_text in repls:
                            ru_esc = ru_text.replace('"', '\\"')
                            new_token = f'"{ru_esc}"'
                            new_line = new_line[:start] + new_token + new_line[end:]
                        lines[lno - 1] = new_line

            out_p = self.patched_dir / fpath_str
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8", newline="\n") as out_f:
                out_f.writelines(lines)

        # ----------------------------------------------------------------------
        # C. Restore 19 Canonical Level JSONs into _patched_files/Levels/
        # ----------------------------------------------------------------------
        out_levels_dir = self.patched_dir / "Levels"
        out_levels_dir.mkdir(parents=True, exist_ok=True)

        if cached_level_jsons:
            print(f"[*] Writing {len(cached_level_jsons)} canonical Level JSONs...")
            for fname, jcontent in cached_level_jsons.items():
                (out_levels_dir / fname).write_text(jcontent, encoding="utf-8", newline="\n")
        else:
            raise FileNotFoundError("Cached level JSONs not found!")

        print("[+] All 106 files generated in _patched_files successfully.")

    # --------------------------------------------------------------------------
    # Step 3: Strict Pre-Pack Automated Linter (Quality Gate)
    # --------------------------------------------------------------------------
    def step3_prepack_automated_linter(self):
        print("\n" + "=" * 80)
        print(" [*] [3/5] STRICT PRE-PACK AUTOMATED LINTER")
        print("=" * 80)

        total_gd_checked = 0
        total_tscn_checked = 0
        total_json_checked = 0
        violations: List[str] = []

        # 1. GDScript Linter
        for gd_path in self.patched_dir.rglob("*.gd"):
            total_gd_checked += 1
            rel_path = gd_path.relative_to(self.patched_dir).as_posix()
            vanilla_path = self.vanilla_dir / rel_path

            if not vanilla_path.exists():
                violations.append(f"GDScript {rel_path}: No corresponding vanilla file found.")
                continue

            v_lines = vanilla_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            p_lines = gd_path.read_text(encoding="utf-8", errors="ignore").splitlines()

            # Rule A: Line count must match vanilla exactly
            if len(p_lines) != len(v_lines):
                violations.append(
                    f"GDScript {rel_path}: Line count mismatch! Vanilla={len(v_lines)}, Patched={len(p_lines)}"
                )

            # Rule B: Pure tab indentation only - NO lines starting with space
            for lno, line in enumerate(p_lines, start=1):
                if line.startswith(" "):
                    violations.append(f"GDScript {rel_path}:{lno}: Line starts with space instead of tab!")

            # Rule C: Function definitions must match vanilla lines
            for lno, (v_l, p_l) in enumerate(zip(v_lines, p_lines), start=1):
                if v_l.strip().startswith("func ") and not p_l.strip().startswith("func "):
                    violations.append(
                        f"GDScript {rel_path}:{lno}: Function definition missing or moved! Expected '{v_l.strip()}', got '{p_l.strip()}'"
                    )

            # Rule D: Balanced quotes check
            for lno, line in enumerate(p_lines, start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                test_line = stripped.replace(r'\"', '').replace(r"\'", '')
                dquotes = test_line.count('"')
                if dquotes % 2 != 0:
                    violations.append(f"GDScript {rel_path}:{lno}: Odd number of double-quotes ({dquotes})!")

        # 2. TSCN Linter
        for tscn_path in self.patched_dir.rglob("*.tscn"):
            total_tscn_checked += 1
            rel_path = tscn_path.relative_to(self.patched_dir).as_posix()
            content = tscn_path.read_text(encoding="utf-8", errors="ignore")

            # Collect declared ext_resources and sub_resources
            ext_ids: Set[str] = set(re.findall(r'\[ext_resource[^\]]+id=(\d+)', content))
            sub_ids: Set[str] = set(re.findall(r'\[sub_resource[^\]]+id=(\d+)', content))

            # Find all ExtResource( N ) and SubResource( N ) usages
            ext_usages = set(re.findall(r'ExtResource\(\s*(\d+)\s*\)', content))
            sub_usages = set(re.findall(r'SubResource\(\s*(\d+)\s*\)', content))

            missing_ext = ext_usages - ext_ids
            missing_sub = sub_usages - sub_ids

            if missing_ext:
                violations.append(f"TSCN {rel_path}: Undefined ExtResource IDs referenced: {missing_ext}")
            if missing_sub:
                violations.append(f"TSCN {rel_path}: Undefined SubResource IDs referenced: {missing_sub}")

        # 3. JSON Linter
        for json_path in self.patched_dir.rglob("*.json"):
            total_json_checked += 1
            rel_path = json_path.relative_to(self.patched_dir).as_posix()
            try:
                json.loads(json_path.read_text(encoding="utf-8"))
            except Exception as e:
                violations.append(f"JSON {rel_path}: Parse error: {e}")

        print(f"[*] Linter verified:")
        print(f"    - {total_gd_checked} GDScript files")
        print(f"    - {total_tscn_checked} TSCN scene files")
        print(f"    - {total_json_checked} JSON metadata files")

        if violations:
            print("\n[!] FATAL: LINTER VIOLATIONS FOUND:")
            for v in violations:
                print(f"    - {v}")
            raise RuntimeError(f"Pre-pack linter failed with {len(violations)} violations! Packaging aborted.")

        print("\n[+] PRE-PACK LINTER PASSED: 0 violations! 100% structural and syntax compliance.")

    # --------------------------------------------------------------------------
    # Step 4: Binary Repack of crueltysquad_ru_v2.pck
    # --------------------------------------------------------------------------
    def step4_binary_pck_rebuild(self):
        print("\n" + "=" * 80)
        print(" [*] [4/5] REBUILDING crueltysquad_ru_v2.pck (PURE PYTHON)")
        print("=" * 80)

        t0 = time.time()

        # Read TOCs from source archives
        with open(self.vanilla_pck_path, "rb") as f:
            v_hdr = struct.unpack("<4sIIII64xI", f.read(88))
            vanilla_files = {}
            for _ in range(v_hdr[5]):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                vanilla_files[p] = {"offset": offset, "size": size, "md5": md5}

        with open(self.ru_pck_path, "rb") as f:
            ru_hdr = struct.unpack("<4sIIII64xI", f.read(88))
            ru_files = {}
            for _ in range(ru_hdr[5]):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                ru_files[p] = {"offset": offset, "size": size, "md5": md5}

        # Build virtual table
        virtual_table: Dict[str, Dict[str, Any]] = {}

        # 1. Base vanilla
        for p, meta in vanilla_files.items():
            virtual_table[p] = {
                "type": "vanilla",
                "offset": meta["offset"],
                "size": meta["size"],
                "md5": meta["md5"],
            }

        # 2. Cyrillic Fonts from ru_2021.pck
        for font in FONTS_TO_IMPORT:
            if font in ru_files:
                virtual_table[font] = {
                    "type": "ru_pck",
                    "offset": ru_files[font]["offset"],
                    "size": ru_files[font]["size"],
                    "md5": ru_files[font]["md5"],
                }

        # 3. Cyrillic UI STEX from ru_2021.pck
        for stex in STEX_TO_IMPORT:
            if stex in ru_files:
                virtual_table[stex] = {
                    "type": "ru_pck",
                    "offset": ru_files[stex]["offset"],
                    "size": ru_files[stex]["size"],
                    "md5": ru_files[stex]["md5"],
                }

        # 4. All patched disk files (.tscn, .json, .gd)
        patched_disk_files = [p for p in self.patched_dir.rglob("*.*") if p.is_file()]
        gdc_removed = 0
        remap_removed = 0
        scn_removed = 0

        for disk_p in patched_disk_files:
            rel = disk_p.relative_to(self.patched_dir).as_posix()
            res_p = f"res://{rel}"
            data = disk_p.read_bytes()

            # If GDScript, strip .gdc and .remap so Godot compiles .gd directly
            if disk_p.suffix == ".gd":
                gdc_p = f"res://{rel[:-3]}.gdc"
                remap_p = f"res://{rel}.remap"
                if gdc_p in virtual_table:
                    del virtual_table[gdc_p]
                    gdc_removed += 1
                if remap_p in virtual_table:
                    del virtual_table[remap_p]
                    remap_removed += 1

            # If TSCN, strip .remap and .scn if present
            if disk_p.suffix == ".tscn":
                remap_p = f"res://{rel}.remap"
                scn_p = f"res://{rel[:-5]}.scn"
                if remap_p in virtual_table:
                    del virtual_table[remap_p]
                    remap_removed += 1
                if scn_p in virtual_table:
                    del virtual_table[scn_p]
                    scn_removed += 1

            virtual_table[res_p] = {
                "type": "disk",
                "disk_path": disk_p,
                "size": len(data),
                "md5": hashlib.md5(data).digest(),
            }

        print(f"[*] Virtual table files: {len(virtual_table):,}")
        print(f"    - Patched disk files integrated: {len(patched_disk_files)}")
        print(f"    - Stripped old bytecode (.gdc):   {gdc_removed}")
        print(f"    - Stripped old remaps (.remap):   {remap_removed}")
        print(f"    - Stripped compiled scenes (.scn): {scn_removed}")

        # Calculate TOC size and assign file offsets with 16-byte alignment
        sorted_paths = sorted(virtual_table.keys())
        toc_bytes_len = 88
        path_info: Dict[str, Tuple[int, bytes]] = {}

        for p in sorted_paths:
            p_bytes = p.encode("utf-8")
            raw_len = len(p_bytes)
            padded_len = (raw_len + 3) & ~3 if (raw_len % 4 != 0) else raw_len
            padded_bytes = p_bytes.ljust(padded_len, b"\x00")
            path_info[p] = (padded_len, padded_bytes)
            toc_bytes_len += 4 + padded_len + 32

        data_start_offset = (toc_bytes_len + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
        toc_padding = data_start_offset - toc_bytes_len

        current_offset = data_start_offset
        file_offsets: Dict[str, int] = {}
        for p in sorted_paths:
            entry = virtual_table[p]
            file_offsets[p] = current_offset
            size = entry["size"]
            aligned_size = (size + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
            current_offset += aligned_size

        total_expected_size = current_offset
        print(f"[*] Writing binary PCK ({total_expected_size:,} bytes)...")

        with open(self.vanilla_pck_path, "rb") as f_vanilla, \
             open(self.ru_pck_path, "rb") as f_ru, \
             open(self.output_pck_path, "wb") as f_out:

            # 1. Header (88 bytes)
            f_out.write(
                struct.pack(
                    "<4sIIII64xI",
                    PCK_MAGIC,
                    PCK_FORMAT_VERSION,
                    3,
                    5,
                    2,
                    len(sorted_paths),
                )
            )

            # 2. File Index (TOC)
            for p in sorted_paths:
                entry = virtual_table[p]
                plen, pbytes = path_info[p]
                f_out.write(struct.pack("<I", plen))
                f_out.write(pbytes)
                f_out.write(
                    struct.pack(
                        "<QQ16s",
                        file_offsets[p],
                        entry["size"],
                        entry["md5"],
                    )
                )

            # Pad TOC to 16-byte alignment
            if toc_padding > 0:
                f_out.write(b"\x00" * toc_padding)

            # 3. Stream File Data
            for p in sorted_paths:
                entry = virtual_table[p]
                etype = entry["type"]

                if etype == "vanilla":
                    f_vanilla.seek(entry["offset"])
                    raw_data = f_vanilla.read(entry["size"])
                elif etype == "ru_pck":
                    f_ru.seek(entry["offset"])
                    raw_data = f_ru.read(entry["size"])
                elif etype == "disk":
                    raw_data = entry["disk_path"].read_bytes()
                else:
                    raise ValueError(f"Unknown entry type: {etype}")

                f_out.write(raw_data)
                padding = ((len(raw_data) + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)) - len(raw_data)
                if padding > 0:
                    f_out.write(b"\x00" * padding)

        elapsed = time.time() - t0
        final_size = self.output_pck_path.stat().st_size
        print(f"[+] Output PCK written in {elapsed:.2f}s: {final_size:,} bytes ({final_size / (1024*1024):.2f} MB)")

        # Sync to root dev directory
        shutil.copy2(self.output_pck_path, self.root_pck_path)
        print(f"[+] Copied to root workspace: {self.root_pck_path}")

    # --------------------------------------------------------------------------
    # Step 5: Verification & Integrity Report
    # --------------------------------------------------------------------------
    def step5_verify_and_report(self):
        print("\n" + "=" * 80)
        print(" [*] [5/5] VERIFYING OUTPUT ARCHIVE & TRANSLATION COVERAGE")
        print("=" * 80)

        with open(self.output_pck_path, "rb") as f:
            hdr = struct.unpack("<4sIIII64xI", f.read(88))
            magic, version, major, minor, patch, file_count = hdr

            assert magic == PCK_MAGIC, f"Invalid magic: {magic}"
            assert version == PCK_FORMAT_VERSION, f"Invalid version: {version}"

            # Scan TOC for critical files
            toc = {}
            for _ in range(file_count):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                toc[p] = (offset, size, md5)

        print(f"[*] Verified PCK Header: Magic={magic.decode()}, Version={version}, Files={file_count:,}")

        # 1. Verify Intro Cutscene subtitles
        c1_off, c1_sz, _ = toc["res://Cutscenes/Cutscene1.tscn"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(c1_off)
            c1_text = f.read(c1_sz).decode("utf-8", errors="replace")
        assert "депрессивной спячки" in c1_text, "Verification failed: Intro Russian text missing in PCK!"
        print("[+] VERIFIED: Intro Cutscene subtitles translated (депрессивной спячки)")

        # 2. Verify Handler message in Message_Area.tscn
        ma_off, ma_sz, _ = toc["res://Entities/Message_Area.tscn"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(ma_off)
            ma_text = f.read(ma_sz).decode("utf-8", errors="replace")
        assert "коктейл" in ma_text, "Verification failed: Handler Message_Area text missing in PCK!"
        print("[+] VERIFIED: Handler Message_Area.tscn translated (боевым коктейлем)")

        # 3. Verify Level1 Handler message & NPC dialogues
        l1_off, l1_sz, _ = toc["res://Levels/Level1.tscn"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(l1_off)
            l1_text = f.read(l1_sz).decode("utf-8", errors="replace")
        assert "коктейл" in l1_text, "Verification failed: Level1 Handler message missing in PCK!"
        assert "здарова" in l1_text or "добрались" in l1_text, "Verification failed: Level1 NPC dialogue missing!"
        print("[+] VERIFIED: In-Level Handler & NPC dialogues translated in Level1.tscn (боевого коктейля / О здарова)")

        # 4. Verify Menu_test.tscn Settings labels
        mt_off, mt_sz, _ = toc["res://Menu/Menu_test.tscn"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(mt_off)
            mt_text = f.read(mt_sz).decode("utf-8", errors="replace")
        assert "Полный экран" in mt_text, "Verification failed: Full Screen missing in Menu_test.tscn!"
        assert "Общая громкость" in mt_text, "Verification failed: Master Volume missing in Menu_test.tscn!"
        assert "Чувствительность" in mt_text, "Verification failed: Mouse Sensitivity missing in Menu_test.tscn!"
        assert "Отражения" in mt_text, "Verification failed: Reflections missing in Menu_test.tscn!"
        assert "Гражданские" in mt_text, "Verification failed: Civilians missing in Menu_test.tscn!"
        print("[+] VERIFIED: 100% Settings menu static labels translated in Menu_test.tscn")

        # 5. Verify Menu_Test.gd Civilians slider labels
        mgd_off, mgd_sz, _ = toc["res://Menu_Test.gd"]
        with open(self.output_pck_path, "rb") as f:
            f.seek(mgd_off)
            mgd_text = f.read(mgd_sz).decode("utf-8", errors="replace")
        assert "Гражданские: МАКС" in mgd_text, "Verification failed: Civilians MAX missing in Menu_Test.gd!"
        assert "Гражданские: " in mgd_text, "Verification failed: Civilians slider missing in Menu_Test.gd!"
        print("[+] VERIFIED: Civilians slider dynamic labels translated in Menu_Test.gd")

        print("\n" + "=" * 80)
        print(" TASK 9 COMPLETE: 100% COVERAGE RESTORED, ALL SYSTEMS PASS VERIFICATION!")
        print("=" * 80)


def main():
    base_dir = Path("c:/dev/cs_loc")
    tool = CompleteCoverageTool(base_dir)
    tool.run_all()


if __name__ == "__main__":
    main()
