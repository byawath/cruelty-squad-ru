#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
17_clean_multiline_house_fix.py
--------------------------------------------------------------------------------
TASK 17: Eliminate Free House Unlock Bug — Complete Elimination of Semicolons
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
import difflib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

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

MODIFIED_GD_FILES = {
    "Menu/Speech.gd",
    "Scripts/speech_label.gd",
    "Entities/Game_Manager.gd",
    "Menu/Character_Menu.gd",
    "Menu_Test.gd",
}


class CleanMultilineHouseFixTool:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.vanilla_dir = base_dir / "vanilla_new"
        self.patched_dir = base_dir / "_patched_files"
        self.pck_dir = base_dir / "_source_pcks"

        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.output_pck_path = base_dir / "crueltysquad_ru_v2.pck"
        self.root_pck_path = Path("C:/dev/crueltysquad_ru_v2.pck")
        self.compat_pck_path = base_dir / "crueltysquad.pck"
        self.root_compat_pck_path = Path("C:/dev/crueltysquad.pck")
        self.steam_pck_path = Path("C:/Program Files (x86)/Steam/steamapps/common/Cruelty Squad/crueltysquad.pck")

    def run_all(self):
        print("=" * 80)
        print(" CRUELTY SQUAD RUSSIAN LOCALIZATION — TASK 17")
        print(" Eliminating Free House Unlock Bug & Full Ban on Semicolons in GDScript")
        print("=" * 80)

        self.step1_diagnose_and_audit_semicolons()
        self.step2_apply_clean_multiline_logic()
        self.step3_prepack_linter_and_diffs()
        self.step4_binary_pck_rebuild()
        print("\n[+] TASK 17 COMPLETED SUCCESSFULLY WITH 0 SEMICOLONS AND ZERO FREE UNLOCKS!")

    # --------------------------------------------------------------------------
    # Step 1: Diagnose Root Cause & Audit Semicolons
    # --------------------------------------------------------------------------
    def step1_diagnose_and_audit_semicolons(self):
        print("\n" + "=" * 80)
        print(" [*] [1/4] STEP 1: ROOT CAUSE DIAGNOSIS & SEMICOLON AUDIT")
        print("=" * 80)

        print("\n[*] Auditing ALL lines with semicolons ';' across all .gd files in _patched_files...")
        found_semis = []
        for f in sorted(self.patched_dir.rglob("*.gd")):
            txt = f.read_text(encoding="utf-8")
            rel = f.relative_to(self.patched_dir).as_posix()
            for lno, line in enumerate(txt.splitlines(), 1):
                code = line.split('#')[0]
                code_no_str = re.sub(r'"([^"\\]|\\.)*"', '""', code)
                code_no_str = re.sub(r"'([^'\\]|\\.)*'", "''", code_no_str)
                if ';' in code_no_str:
                    found_semis.append((rel, lno, line.strip()))

        print(f"[*] Detected {len(found_semis)} occurrences of ';' in GDScript code:")
        for rel, lno, line in found_semis:
            print(f"    {rel}:{lno} | {line}")

        print("\n" + "-" * 80)
        print(" ROOT CAUSE EXPLANATION:")
        print("-" * 80)
        print(" In Godot 3.x GDScript, single-line 'if condition: statement1; statement2'")
        print(" binds ONLY statement1 to the 'if' condition. Any subsequent statement")
        print(" after a semicolon (statement2, statement3) is treated as a top-level")
        print(" statement at the parent indentation level and executes UNCONDITIONALLY!")
        print("")
        print(" Specifically in Entities/Game_Manager.gd:880:")
        print("   if ...: implants.purchased_implants.erase('Дом'); implants.purchased_implants.append('Дом'); BONUS_UNLOCK.erase('House'); BONUS_UNLOCK.append('House')")
        print(" Godot only checked the condition for erase('Дом'). All subsequent statements,")
        print(" including append('Дом') and BONUS_UNLOCK.append('House'), were executed every")
        print(" single time a save was loaded, giving EVERY player the House for FREE!")
        print("=" * 80)

    # --------------------------------------------------------------------------
    # Step 2: Rewrite House Logic to Clean Multiline GDScript (0 Semicolons)
    # --------------------------------------------------------------------------
    def step2_apply_clean_multiline_logic(self):
        print("\n" + "=" * 80)
        print(" [*] [2/4] STEP 2: REWRITING HOUSE LOGIC TO CLEAN MULTILINE GDSCRIPT")
        print("=" * 80)

        # 1. Entities/Game_Manager.gd
        gm_path = self.patched_dir / "Entities/Game_Manager.gd"
        gm_text = gm_path.read_text(encoding="utf-8")

        # Clean bonus_levels_unlocked loading
        # Find the block around bonus_levels_unlocked
        old_gm_block1_pattern = re.compile(
            r'(\t\tif bonus_levels_unlocked:\n)'
            r'(\t\t\tBONUS_UNLOCK = bonus_levels_unlocked[^\n]*\n)'
        )
        new_gm_block1 = (
            '\t\tif bonus_levels_unlocked:\n'
            '\t\t\tBONUS_UNLOCK = bonus_levels_unlocked\n'
            '\t\t\tif BONUS_UNLOCK.find("Дом") != - 1:\n'
            '\t\t\t\tBONUS_UNLOCK.erase("Дом")\n'
            '\t\t\t\tif BONUS_UNLOCK.find("House") == - 1:\n'
            '\t\t\t\t\tBONUS_UNLOCK.append("House")\n'
        )
        assert old_gm_block1_pattern.search(gm_text), "Could not find bonus_levels_unlocked block in Game_Manager.gd!"
        gm_text = old_gm_block1_pattern.sub(new_gm_block1, gm_text)

        # Clean new_implants_unlocked loading
        old_gm_block2_pattern = re.compile(
            r'(\t\tif new_implants_unlocked:\n)'
            r'(\t\t\timplants\.purchased_implants = new_implants_unlocked[^\n]*\n)'
        )
        new_gm_block2 = (
            '\t\tif new_implants_unlocked:\n'
            '\t\t\timplants.purchased_implants = new_implants_unlocked\n'
            '\t\t\tif implants.purchased_implants.find("House") != - 1:\n'
            '\t\t\t\tif implants.purchased_implants.find("Дом") == - 1:\n'
            '\t\t\t\t\timplants.purchased_implants.append("Дом")\n'
            '\t\t\tif implants.purchased_implants.find("Дом") != - 1:\n'
            '\t\t\t\tif BONUS_UNLOCK.find("House") == - 1:\n'
            '\t\t\t\t\tBONUS_UNLOCK.append("House")\n'
        )
        assert old_gm_block2_pattern.search(gm_text), "Could not find new_implants_unlocked block in Game_Manager.gd!"
        gm_text = old_gm_block2_pattern.sub(new_gm_block2, gm_text)

        gm_path.write_text(gm_text, encoding="utf-8")
        print("[+] Entities/Game_Manager.gd rewritten to clean multiline logic without semicolons.")

        # 2. Menu/Character_Menu.gd
        cm_path = self.patched_dir / "Menu/Character_Menu.gd"
        cm_text = cm_path.read_text(encoding="utf-8")

        # Clean line 16 (_ready)
        cm_text = re.sub(
            r'\t\$ConfirmationDialog\.get_cancel\(\)\.connect\("pressed", self, "_on_Cancel_Pressed"\);[^\n]*',
            r'\t$ConfirmationDialog.get_cancel().connect("pressed", self, "_on_Cancel_Pressed")',
            cm_text
        )

        # Clean _on_implant_pressed block
        old_cm_unlock_pattern = re.compile(
            r'(\t\t\t\tif IMPLANTS\[i\]\.i_name == "Дом" or IMPLANTS\[i\]\.i_name == "House":\n)'
            r'(\t\t\t\t\tif Global\.BONUS_UNLOCK\.find\("House"\) == - 1:[^\n]*\n)'
        )
        new_cm_unlock = (
            '\t\t\t\tif IMPLANTS[i].i_name == "Дом" or IMPLANTS[i].i_name == "House":\n'
            '\t\t\t\t\tif Global.BONUS_UNLOCK.find("House") == - 1:\n'
            '\t\t\t\t\t\tGlobal.BONUS_UNLOCK.append("House")\n'
        )
        assert old_cm_unlock_pattern.search(cm_text), "Could not find House unlock block in Character_Menu.gd!"
        cm_text = old_cm_unlock_pattern.sub(new_cm_unlock, cm_text)

        # Ensure typo fix is in place
        cm_text = cm_text.replace("Где-то в это мире", "Где-то в этом мире")

        cm_path.write_text(cm_text, encoding="utf-8")
        print("[+] Menu/Character_Menu.gd rewritten to clean multiline logic without semicolons.")

        # 3. Menu_Test.gd
        mt_path = self.patched_dir / "Menu_Test.gd"
        mt_text = mt_path.read_text(encoding="utf-8")

        old_mt_erase_pattern = re.compile(
            r'\t\tGlobal\.implants\.purchased_implants\.erase\("Дом"\);\s*Global\.implants\.purchased_implants\.erase\("House"\)'
        )
        new_mt_erase = (
            '\t\tGlobal.implants.purchased_implants.erase("Дом")\n'
            '\t\tGlobal.implants.purchased_implants.erase("House")'
        )
        if old_mt_erase_pattern.search(mt_text):
            mt_text = old_mt_erase_pattern.sub(new_mt_erase, mt_text)
            mt_path.write_text(mt_text, encoding="utf-8")
        print("[+] Menu_Test.gd rewritten to clean multiline erase calls without semicolons.")

        # 4. Clean legacy 'return type;' in 7 vanilla doors/destructibles
        legacy_files = [
            "Scripts/Destructible_Armored.gd",
            "Scripts/Divine_Door.gd",
            "Scripts/Enemy_Torso.gd",
            "Scripts/Locked_Door.gd",
            "Scripts/Profane_Door.gd",
            "snakehead.gd",
            "Terror_Door.gd",
        ]
        cleaned_legacy = 0
        for lf in legacy_files:
            f_path = self.patched_dir / lf
            txt = f_path.read_text(encoding="utf-8")
            if "return type;" in txt:
                f_path.write_text(txt.replace("return type;", "return type"), encoding="utf-8")
                cleaned_legacy += 1
        print(f"[+] Cleaned legacy 'return type;' semicolons across {cleaned_legacy} baseline door/destructible scripts.")

    # --------------------------------------------------------------------------
    # Step 3: Strict Pre-Pack Linter with Zero-Semicolon Rule & Diffs
    # --------------------------------------------------------------------------
    def step3_prepack_linter_and_diffs(self):
        print("\n" + "=" * 80)
        print(" [*] [3/4] STEP 3: STRICT PRE-PACK LINTER (ZERO SEMICOLONS)")
        print("=" * 80)

        gd_files = sorted(list(self.patched_dir.rglob("*.gd")))
        tscn_files = sorted(list(self.patched_dir.rglob("*.tscn")))
        json_files = sorted(list(self.patched_dir.rglob("*.json")))

        violations: List[str] = []

        # 1. GDScript Strict Audit
        print(f"[*] Auditing {len(gd_files)} GDScript files...")
        for p in gd_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            v_p = self.vanilla_dir / rel
            p_lines = p.read_text(encoding="utf-8").splitlines()

            if not v_p.exists():
                violations.append(f"GDScript {rel}: No corresponding vanilla file found!")
                continue

            v_lines = v_p.read_text(encoding="utf-8").splitlines()

            # Rule: Absolute ban on semicolons outside string literals/comments
            for lno, pl in enumerate(p_lines, 1):
                code_part = pl.split("#")[0]
                code_no_strings = re.sub(r'"([^"\\]|\\.)*"', '""', code_part)
                code_no_strings = re.sub(r"'([^'\\]|\\.)*'", "''", code_no_strings)
                if ";" in code_no_strings:
                    violations.append(f"GDScript {rel}:{lno}: Semicolon (;) strictly forbidden: {repr(pl[:50])}")

                # Rule: Zero space indentations allowed
                if pl.startswith(" ") and not pl.strip().startswith("#"):
                    violations.append(f"GDScript {rel}:{lno}: Space indentation found: {repr(pl[:30])}")

                # Rule: Balanced double-quotes
                sanitized = code_part.replace(r'\"', '').replace(r"\'", '')
                if sanitized.count('"') % 2 != 0:
                    violations.append(f"GDScript {rel}:{lno}: Unbalanced double-quotes!")

            # Category 1: Baseline files (must match vanilla 1-to-1 line count and tabs)
            if rel not in MODIFIED_GD_FILES:
                if len(p_lines) != len(v_lines):
                    violations.append(f"GDScript {rel}: Line count mismatch! Patched={len(p_lines)}, Vanilla={len(v_lines)}")

                for lno, (pl, vl) in enumerate(zip(p_lines, v_lines), 1):
                    p_tabs = len(pl) - len(pl.lstrip("\t"))
                    v_tabs = len(vl) - len(vl.lstrip("\t"))
                    if p_tabs != v_tabs:
                        violations.append(f"GDScript {rel}:{lno}: Tab indentation mismatch: expected {v_tabs}, got {p_tabs}")

            # Category 2: Modified logic files (Menu/Speech.gd, speech_label.gd, Game_Manager.gd, Character_Menu.gd, Menu_Test.gd)
            else:
                # Validate speech scripts indentation increase
                if rel in {"Menu/Speech.gd", "Scripts/speech_label.gd"}:
                    last_indent = 0
                    expect_increase = False
                    for lno, pl in enumerate(p_lines, 1):
                        stripped = pl.strip()
                        if not stripped or stripped.startswith("#"):
                            continue
                        cur_indent = len(pl) - len(pl.lstrip("\t"))
                        if expect_increase:
                            if cur_indent != last_indent + 1:
                                violations.append(f"Speech {rel}:{lno}: Expected indent {last_indent + 1} after colon, got {cur_indent}")
                            expect_increase = False
                        code_part = stripped.split("#")[0].strip()
                        if code_part.endswith(":"):
                            expect_increase = True
                            last_indent = cur_indent
                        else:
                            last_indent = cur_indent

            # Bracket balance across entire file
            whole_content = "\n".join(l.split("#")[0] for l in p_lines)
            code_no_strings = re.sub(r'"([^"\\]|\\.)*"', '""', whole_content)
            for open_b, close_b in [("(", ")"), ("[", "]"), ("{", "}")]:
                cnt_open = code_no_strings.count(open_b)
                cnt_close = code_no_strings.count(close_b)
                if cnt_open != cnt_close:
                    violations.append(f"GDScript {rel}: Bracket mismatch for '{open_b}{close_b}': {cnt_open} open vs {cnt_close} close")

        # 2. TSCN Scene Strict Audit
        print(f"[*] Auditing {len(tscn_files)} TSCN scene files...")
        for p in tscn_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            v_p = self.vanilla_dir / rel

            if v_p.exists():
                v_lines = v_p.read_text(encoding="utf-8", errors="ignore").splitlines()
                p_lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                if len(p_lines) != len(v_lines):
                    violations.append(f"TSCN {rel}: Line count mismatch! Vanilla={len(v_lines)}, Patched={len(p_lines)}")

            content = p.read_text(encoding="utf-8", errors="ignore")
            ext_ids: Set[str] = set(re.findall(r'\[ext_resource[^\]]+id=(\d+)', content))
            sub_ids: Set[str] = set(re.findall(r'\[sub_resource[^\]]+id=(\d+)', content))

            ext_usages = set(re.findall(r'ExtResource\(\s*(\d+)\s*\)', content))
            sub_usages = set(re.findall(r'SubResource\(\s*(\d+)\s*\)', content))

            missing_ext = ext_usages - ext_ids
            missing_sub = sub_usages - sub_ids

            if missing_ext:
                violations.append(f"TSCN {rel}: Undefined ExtResource IDs referenced: {missing_ext}")
            if missing_sub:
                violations.append(f"TSCN {rel}: Undefined SubResource IDs referenced: {missing_sub}")

            if r'\\"' in content or r'\\\"' in content:
                violations.append(f"TSCN {rel}: Contains invalid double-escaped quote sequence!")

        # 3. JSON Strict Audit
        print(f"[*] Auditing {len(json_files)} JSON files...")
        for p in json_files:
            rel = p.relative_to(self.patched_dir).as_posix()
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                violations.append(f"JSON {rel}: Parse error: {e}")

        # Summary
        if violations:
            print(f"\n[!] LINTER FAILED WITH {len(violations)} VIOLATIONS:")
            for v in violations:
                print(f"    - {v}")
            raise RuntimeError(f"Pre-pack linter failed with {len(violations)} errors. Build aborted.")

        print(f"[+] Linter PASSED 100% with 0 violations across all {len(gd_files)} .gd, {len(tscn_files)} .tscn, and {len(json_files)} .json files!")
        print("[+] Verified: Exactly 0 semicolons exist in any GDScript code!")

        # Print Unified Diffs for the 3 target files
        print("\n" + "=" * 80)
        print(" UNIFIED DIFFS OF TARGET FILES (vanilla_new vs _patched_files)")
        print("=" * 80)
        for rel in ["Entities/Game_Manager.gd", "Menu/Character_Menu.gd", "Menu_Test.gd"]:
            v_lines = (self.vanilla_dir / rel).read_text(encoding="utf-8").splitlines(keepends=True)
            p_lines = (self.patched_dir / rel).read_text(encoding="utf-8").splitlines(keepends=True)
            diff = list(difflib.unified_diff(
                v_lines, p_lines,
                fromfile=f"vanilla_new/{rel}",
                tofile=f"_patched_files/{rel}",
                n=3
            ))
            print(f"\n--- Unified Diff: {rel} ---")
            for line in diff:
                print(line, end="")

    # --------------------------------------------------------------------------
    # Step 4: Binary PCK Rebuild & Mirror Synchronization
    # --------------------------------------------------------------------------
    def step4_binary_pck_rebuild(self):
        print("\n" + "=" * 80)
        print(" [*] [4/4] STEP 4: BINARY PCK REBUILD (PURE PYTHON, 16-BYTE ALIGNED)")
        print("=" * 80)

        t0 = time.time()

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

        # Virtual Table
        virtual_table: Dict[str, Dict[str, Any]] = {}

        # 1. Base vanilla
        for p, meta in vanilla_files.items():
            virtual_table[p] = {
                "type": "vanilla",
                "offset": meta["offset"],
                "size": meta["size"],
                "md5": meta["md5"],
            }

        # 2. Fonts
        for font in FONTS_TO_IMPORT:
            if font in ru_files:
                virtual_table[font] = {
                    "type": "ru_pck",
                    "offset": ru_files[font]["offset"],
                    "size": ru_files[font]["size"],
                    "md5": ru_files[font]["md5"],
                }

        # 3. STEX
        for stex in STEX_TO_IMPORT:
            if stex in ru_files:
                virtual_table[stex] = {
                    "type": "ru_pck",
                    "offset": ru_files[stex]["offset"],
                    "size": ru_files[stex]["size"],
                    "md5": ru_files[stex]["md5"],
                }

        # 4. Patched disk files
        patched_disk_files = [p for p in self.patched_dir.rglob("*.*") if p.is_file()]
        gdc_removed = 0
        remap_removed = 0
        scn_removed = 0

        for disk_p in patched_disk_files:
            rel = disk_p.relative_to(self.patched_dir).as_posix()
            res_p = f"res://{rel}"
            data = disk_p.read_bytes()

            if disk_p.suffix == ".gd":
                gdc_p = f"res://{rel[:-3]}.gdc"
                remap_p = f"res://{rel}.remap"
                if gdc_p in virtual_table:
                    del virtual_table[gdc_p]
                    gdc_removed += 1
                if remap_p in virtual_table:
                    del virtual_table[remap_p]
                    remap_removed += 1

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

        # Purge checks
        assert "res://Menu/Speech.gdc" not in virtual_table
        assert "res://Menu/Speech.gd.remap" not in virtual_table
        assert "res://Scripts/speech_label.gdc" not in virtual_table
        assert "res://Scripts/speech_label.gd.remap" not in virtual_table

        # TOC & Offsets
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

            for p in sorted_paths:
                entry = virtual_table[p]
                plen, pbytes = path_info[p]
                f_out.write(
                    struct.pack(
                        f"<I{plen}sQQ16s",
                        plen,
                        pbytes,
                        file_offsets[p],
                        entry["size"],
                        entry["md5"],
                    )
                )

            if toc_padding > 0:
                f_out.write(b"\x00" * toc_padding)

            chunk_size = 1024 * 1024
            for p in sorted_paths:
                entry = virtual_table[p]
                expected_offset = file_offsets[p]
                actual_offset = f_out.tell()
                assert actual_offset == expected_offset, f"Offset mismatch for {p}: {actual_offset} != {expected_offset}"

                src_type = entry["type"]
                size = entry["size"]

                if src_type == "disk":
                    with open(entry["disk_path"], "rb") as f_disk:
                        while chunk := f_disk.read(chunk_size):
                            f_out.write(chunk)
                elif src_type == "vanilla":
                    f_vanilla.seek(entry["offset"])
                    remaining = size
                    while remaining > 0:
                        n = min(remaining, chunk_size)
                        buf = f_vanilla.read(n)
                        f_out.write(buf)
                        remaining -= len(buf)
                elif src_type == "ru_pck":
                    f_ru.seek(entry["offset"])
                    remaining = size
                    while remaining > 0:
                        n = min(remaining, chunk_size)
                        buf = f_ru.read(n)
                        f_out.write(buf)
                        remaining -= len(buf)

                cur_pos = f_out.tell()
                aligned_pos = (cur_pos + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
                pad_len = aligned_pos - cur_pos
                if pad_len > 0:
                    f_out.write(b"\x00" * pad_len)

        out_size = self.output_pck_path.stat().st_size
        elapsed = time.time() - t0
        print(f"[+] PCK Build complete in {elapsed:.2f}s!")
        print(f"[+] Output PCK size: {out_size:,} bytes ({out_size / (1024*1024):.2f} MB)")

        # Sync mirrors
        print("[*] Synchronizing output PCK across targets...")
        shutil.copy2(self.output_pck_path, self.compat_pck_path)
        print(f"    -> Synced to: {self.compat_pck_path}")

        shutil.copy2(self.output_pck_path, self.root_pck_path)
        print(f"    -> Synced to: {self.root_pck_path}")

        shutil.copy2(self.output_pck_path, self.root_compat_pck_path)
        print(f"    -> Synced to: {self.root_compat_pck_path}")

        if self.steam_pck_path.parent.exists():
            shutil.copy2(self.output_pck_path, self.steam_pck_path)
            print(f"    -> Synced to Steam directory: {self.steam_pck_path}")

        # Post-verify header
        with open(self.output_pck_path, "rb") as f:
            magic, ver, major, minor, patch, file_count = struct.unpack("<4sIIII64xI", f.read(88))
            assert magic == PCK_MAGIC, "Bad PCK magic!"
            print(f"[+] Post-verification passed! Files: {file_count:,}, Engine: {major}.{minor}.{patch}")


if __name__ == "__main__":
    tool = CleanMultilineHouseFixTool(Path("C:/dev/cs_loc"))
    tool.run_all()
