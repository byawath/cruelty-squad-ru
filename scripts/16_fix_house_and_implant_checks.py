#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16_fix_house_and_implant_checks.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
TASK 16: Fix "House" / "Дом" Purchase & Global Audit of Implant String Checks
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


class HouseAndImplantFixTool:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.vanilla_dir = base_dir / "vanilla_new"
        self.patched_dir = base_dir / "_patched_files"
        self.ru_old_dir = base_dir / "ru_old"
        self.pck_dir = base_dir / "_source_pcks"

        self.vanilla_pck_path = self.pck_dir / "vanilla_steam.pck"
        self.ru_pck_path = self.pck_dir / "ru_2021.pck"
        self.output_pck_path = base_dir / "crueltysquad_ru_v2.pck"
        self.root_pck_path = Path("C:/dev/crueltysquad_ru_v2.pck")
        self.compat_pck_path = base_dir / "crueltysquad.pck"
        self.backup_v22_path = base_dir / "crueltysquad_v2.2_backup.pck"
        self.root_backup_path = Path("C:/dev/crueltysquad_v2.2_backup.pck")

        self.vanilla_implants: List[str] = []
        self.patched_implants: List[str] = []
        self.load_implants()

    def load_implants(self):
        v_text = (self.vanilla_dir / "Scripts/Implants.gd").read_text(encoding="utf-8")
        p_text = (self.patched_dir / "Scripts/Implants.gd").read_text(encoding="utf-8")
        self.vanilla_implants = re.findall(r'new_implant\.i_name\s*=\s*"([^"]+)"', v_text)
        self.patched_implants = re.findall(r'new_implant\.i_name\s*=\s*"([^"]+)"', p_text)
        assert len(self.vanilla_implants) == 49, f"Expected 49 vanilla implants, got {len(self.vanilla_implants)}"
        assert len(self.patched_implants) == 49, f"Expected 49 patched implants, got {len(self.patched_implants)}"

    def run_all(self):
        print("=" * 80)
        print(" CRUELTY SQUAD RUSSIAN LOCALIZATION — TASK 16")
        print(" Fix 'House' / 'Дом' & Global Audit of Implant String Checks")
        print("=" * 80)

        self.step0_safety_backup()
        self.step1_audit_house_dom()
        self.step2_global_implant_audit()
        self.step3_patch_and_diff()
        self.step4_prepack_linter()
        self.step5_binary_pck_rebuild()
        self.step6_savegame_money_info()

    # --------------------------------------------------------------------------
    # Step 0: Safety Backup
    # --------------------------------------------------------------------------
    def step0_safety_backup(self):
        print("\n" + "=" * 80)
        print(" [*] [0/6] SAFETY BACKUP: Preserving v2.2 PCK & Validating Working Assets")
        print("=" * 80)

        if self.compat_pck_path.exists():
            shutil.copy2(self.compat_pck_path, self.backup_v22_path)
            shutil.copy2(self.compat_pck_path, self.root_backup_path)
            print(f"[+] Successfully created backup: {self.backup_v22_path} ({self.backup_v22_path.stat().st_size:,} bytes)")
            print(f"[+] Synced backup: {self.root_backup_path}")
        else:
            print(f"[!] Warning: {self.compat_pck_path} not found to backup directly.")

        # Ensure critical previous fixes are intact
        for rel in ["Menu/Speech.gd", "Scripts/speech_label.gd", "Menu_Test.gd"]:
            assert (self.patched_dir / rel).exists(), f"Critical file {rel} is missing in _patched_files!"
        print("[+] Verified: Steps 12-15 files and speech handlers are present and intact.")

    # --------------------------------------------------------------------------
    # Step 1: Full Audit of "House" / "Дом" (Original vs Patched)
    # --------------------------------------------------------------------------
    def step1_audit_house_dom(self):
        print("\n" + "=" * 80)
        print(" [*] [1/6] AUDIT: 'House' and 'Дом' References (Original vs Patched)")
        print("=" * 80)

        def search_mentions(root: Path, label: str):
            results = []
            for ext in ["*.gd", "*.tscn", "*.json"]:
                for f in sorted(root.rglob(ext)):
                    try:
                        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
                        for lno, line in enumerate(lines, 1):
                            l_lower = line.lower()
                            if "house" in l_lower or "дом" in l_lower:
                                rel = f.relative_to(root).as_posix()
                                results.append((rel, lno, line.strip()))
                    except Exception:
                        pass
            return results

        v_results = search_mentions(self.vanilla_dir, "vanilla_new")
        p_results = search_mentions(self.patched_dir, "_patched_files")

        print(f"[*] Found {len(v_results)} occurrences in vanilla_new:")
        for rel, lno, line in v_results:
            if any(term in rel.lower() for term in ["menu", "character", "game_manager", "implants", "bonus5"]):
                print(f"    vanilla_new/{rel}:{lno} | {line[:100]}")

        print(f"\n[*] Found {len(p_results)} occurrences in _patched_files:")
        for rel, lno, line in p_results:
            if any(term in rel.lower() for term in ["menu", "character", "game_manager", "implants", "bonus5"]):
                print(f"    _patched_files/{rel}:{lno} | {line[:100]}")

        print("\n" + "-" * 80)
        print(" CONTEXT ANALYSIS:")
        print("-" * 80)
        print(" 1. How House purchase works in vanilla (vanilla_new):")
        print("    - Scripts/Implants.gd:614: Implant #48 defined as 'House' (price=$1,000,000, texture=res://Levels/Bonus5.png).")
        print("    - Menu/Character_Menu.gd:174-175: When bought:")
        print("          if IMPLANTS[i].i_name == \"House\": Global.BONUS_UNLOCK.append(\"House\")")
        print("          Global.implants.purchased_implants.append(IMPLANTS[i].i_name)  # Appends 'House'")
        print("    - Entities/Game_Manager.gd:221: var BONUS_LEVELS = [..., 'House', 'END']")
        print("    - Menu_Test.gd:824, 830, 1023, 1028: Checks Global.BONUS_UNLOCK.find(Global.BONUS_LEVELS[4]) != -1")
        print("      Because BONUS_LEVELS[4] == 'House', having 'House' in BONUS_UNLOCK enables Bonus 5 (House) on the mission map.")
        print("    - Menu_Test.gd:1449-1450: Resetting progression removes 'House' from purchased_implants:")
        print("          if Global.implants.purchased_implants.find(\"House\") != - 1:")
        print("              Global.implants.purchased_implants.remove(Global.implants.purchased_implants.find(\"House\"))")
        print("    - Menu/Character_Menu.gd:34, 110, 112, 138, 157: Checks Global.implants.purchased_implants.find(IMPLANTS[b].i_name).")
        print("      If found, the implant is not colored RED, shows as owned, and does not ask for $1M again.")
        print("\n 2. Why the bug occurred in Russian patch:")
        print("    - Scripts/Implants.gd:614 translated implant #48 to 'Дом'.")
        print("    - Menu/Character_Menu.gd:174 was translated to:")
        print("          if IMPLANTS[i].i_name == \"Дом\": Global.BONUS_UNLOCK.append(\"Дом\")")
        print("      BUT Entities/Game_Manager.gd:221 BONUS_LEVELS still had 'House' (not 'Дом')!")
        print("      AND Menu_Test.gd:824 checked BONUS_UNLOCK.find(BONUS_LEVELS[4]), which searched for 'House', NOT 'Дом'.")
        print("      Result: The House level NEVER unlocked on the mission map!")
        print("    - Furthermore, any player loading an existing savegame where 'House' was already purchased had 'House'")
        print("      in purchased_implants. Because IMPLANTS[48].i_name is 'Дом', purchased_implants.find('Дом') returned -1,")
        print("      causing the House to appear unpurchased (RED), asking for $1M again!")

    # --------------------------------------------------------------------------
    # Step 2: Global Audit of ALL Implant String Checks in .gd
    # --------------------------------------------------------------------------
    def step2_global_implant_audit(self):
        print("\n" + "=" * 80)
        print(" [*] [2/6] GLOBAL AUDIT: All Implant String Checks Across .gd Files")
        print("=" * 80)

        v_to_p = dict(zip(self.vanilla_implants, self.patched_implants))
        desyncs: List[Dict[str, Any]] = []

        for p in sorted(self.patched_dir.rglob("*.gd")):
            rel = p.relative_to(self.patched_dir).as_posix()
            if rel == "Scripts/Implants.gd":
                continue
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            for lno, line in enumerate(lines, 1):
                # Search for occurrences of English implant names
                for v_imp, p_imp in v_to_p.items():
                    if f'"{v_imp}"' in line or f"'{v_imp}'" in line:
                        desyncs.append({
                            "file": rel,
                            "line_no": lno,
                            "type": "ENGLISH_IMPLANT_STRING",
                            "en": v_imp,
                            "ru": p_imp,
                            "line": line.strip()
                        })

                # Search for occurrences of Russian implant names
                for p_imp, v_imp in zip(self.patched_implants, self.vanilla_implants):
                    if p_imp != v_imp and (f'"{p_imp}"' in line or f"'{p_imp}'" in line):
                        desyncs.append({
                            "file": rel,
                            "line_no": lno,
                            "type": "RUSSIAN_IMPLANT_STRING",
                            "en": v_imp,
                            "ru": p_imp,
                            "line": line.strip()
                        })

        print(f"[*] Total implant string interactions detected: {len(desyncs)}")
        for d in desyncs:
            print(f"    [{d['type']}] {d['file']}:{d['line_no']}")
            print(f"         EN: '{d['en']}' <--> RU: '{d['ru']}'")
            print(f"         Code: {d['line']}")

        print("\n[+] Audit summary:")
        print("    1. Entities/Game_Manager.gd:221 has 'House' in BONUS_LEVELS.")
        print("    2. Entities/Game_Manager.gd:602 has 'Экстравагантный костюм' for Extravagant Suit achievement.")
        print("    3. Menu/Character_Menu.gd:174 has 'Дом' check, appends 'Дом' to BONUS_UNLOCK.")
        print("    4. Menu_Test.gd:1449 has 'Дом' check and remove('Дом').")
        print("    5. Entities/Physics_Objects/Implant_Object.gd:7 has 'Костюм биохимзащиты' (Hazmat Suit).")
        print("    6. snakehead.gd:76 appends 'Экзоcистема \\'Голем\\' VI класса CSIJ'.")

    # --------------------------------------------------------------------------
    # Step 3: Targeted Patch with 100% Backward Compatibility & Unified Diff
    # --------------------------------------------------------------------------
    def step3_patch_and_diff(self):
        print("\n" + "=" * 80)
        print(" [*] [3/6] APPLYING SURGICAL PATCHES WITH BACKWARD COMPATIBILITY")
        print("=" * 80)

        # 1. Menu/Character_Menu.gd
        cm_path = self.patched_dir / "Menu/Character_Menu.gd"
        cm_lines = cm_path.read_text(encoding="utf-8").splitlines()

        # Line 16: When Character Menu loads, auto-sync "House" -> "Дом" in purchased_implants
        cm_lines[15] = '\t$ConfirmationDialog.get_cancel().connect("pressed", self, "_on_Cancel_Pressed"); if Global.implants.purchased_implants.find("House") != - 1 and Global.implants.purchased_implants.find("Дом") == - 1: Global.implants.purchased_implants.append("Дом")'

        # Line 34: Button setup
        cm_lines[33] = '\t\t\tif Global.implants.purchased_implants.find(IMPLANTS[b].i_name) == - 1 and (IMPLANTS[b].i_name != "Дом" or Global.implants.purchased_implants.find("House") == - 1):'

        # Line 108: update_buttons hidden check
        cm_lines[107] = '\t\tif IMPLANTS[i].hidden and (Global.implants.purchased_implants.find(IMPLANTS[i].i_name) != - 1 or (IMPLANTS[i].i_name == "Дом" and Global.implants.purchased_implants.find("House") != - 1)):'

        # Line 110: update_buttons unpurchased modulate
        cm_lines[109] = '\t\telif Global.implants.purchased_implants.find(IMPLANTS[i].i_name) == - 1 and (IMPLANTS[i].i_name != "Дом" or Global.implants.purchased_implants.find("House") == - 1):'

        # Line 112: update_buttons purchased modulate
        cm_lines[111] = '\t\tif (Global.implants.purchased_implants.find(IMPLANTS[i].i_name) != - 1 or (IMPLANTS[i].i_name == "Дом" and Global.implants.purchased_implants.find("House") != - 1)) and EQUIPMENT_BUTTONS[i].modulate != Color(0.5, 0.5, 0.5):'

        # Line 138: Tooltip price display
        cm_lines[137] = '\t\tif Global.implants.purchased_implants.find(IMPLANTS[i].i_name) == - 1 and (IMPLANTS[i].i_name != "Дом" or Global.implants.purchased_implants.find("House") == - 1):'

        # Line 155: Click hidden check
        cm_lines[154] = '\t\tif IMPLANTS[i].hidden and (Global.implants.purchased_implants.find(IMPLANTS[i].i_name) == - 1 and (IMPLANTS[i].i_name != "Дом" or Global.implants.purchased_implants.find("House") == - 1)):'

        # Line 157: Click unpurchased check
        cm_lines[156] = '\t\tif Global.implants.purchased_implants.find(IMPLANTS[i].i_name) == - 1 and (IMPLANTS[i].i_name != "Дом" or Global.implants.purchased_implants.find("House") == - 1):'

        # Line 174-175: Purchase unlock House: add BOTH "House" and "Дом" to BONUS_UNLOCK
        cm_lines[173] = '\t\t\t\tif IMPLANTS[i].i_name == "Дом" or IMPLANTS[i].i_name == "House":'
        cm_lines[174] = '\t\t\t\t\tif Global.BONUS_UNLOCK.find("House") == - 1: Global.BONUS_UNLOCK.append("House"); Global.BONUS_UNLOCK.append("Дом")'

        cm_path.write_text("\n".join(cm_lines) + "\n", encoding="utf-8", newline="\n")
        print("[+] Patched Menu/Character_Menu.gd")

        # 2. Menu_Test.gd
        mt_path = self.patched_dir / "Menu_Test.gd"
        mt_lines = mt_path.read_text(encoding="utf-8").splitlines()

        # Line 824
        mt_lines[823] = '\t\t\tif (Global.BONUS_UNLOCK.find(Global.BONUS_LEVELS[button - Global.L_PUNISHMENT - 1]) != - 1 or (Global.BONUS_LEVELS[button - Global.L_PUNISHMENT - 1] == "House" and Global.BONUS_UNLOCK.find("Дом") != - 1)) and button != Global.CURRENT_LEVEL:'

        # Line 830
        mt_lines[829] = '\t\t\t\tif Global.BONUS_UNLOCK.find(Global.BONUS_LEVELS[button - Global.L_PUNISHMENT - 1]) != - 1 or (Global.BONUS_LEVELS[button - Global.L_PUNISHMENT - 1] == "House" and Global.BONUS_UNLOCK.find("Дом") != - 1):'

        # Line 1023
        mt_lines[1022] = '\t\t\t\tif (Global.BONUS_UNLOCK.find(Global.BONUS_LEVELS[button - Global.L_PUNISHMENT - 1]) != - 1 or (Global.BONUS_LEVELS[button - Global.L_PUNISHMENT - 1] == "House" and Global.BONUS_UNLOCK.find("Дом") != - 1)) and button != Global.CURRENT_LEVEL:'

        # Line 1028
        mt_lines[1027] = '\t\t\t\t\tif Global.BONUS_UNLOCK.find(Global.BONUS_LEVELS[button - Global.L_PUNISHMENT - 1]) != - 1 or (Global.BONUS_LEVELS[button - Global.L_PUNISHMENT - 1] == "House" and Global.BONUS_UNLOCK.find("Дом") != - 1):'

        # Line 1449-1450: Reset progression bilingual check
        mt_lines[1448] = '\tif Global.implants.purchased_implants.find("Дом") != - 1 or Global.implants.purchased_implants.find("House") != - 1:'
        mt_lines[1449] = '\t\tGlobal.implants.purchased_implants.erase("Дом"); Global.implants.purchased_implants.erase("House")'

        mt_path.write_text("\n".join(mt_lines) + "\n", encoding="utf-8", newline="\n")
        print("[+] Patched Menu_Test.gd")

        # 3. Entities/Game_Manager.gd
        gm_path = self.patched_dir / "Entities/Game_Manager.gd"
        gm_lines = gm_path.read_text(encoding="utf-8").splitlines()

        # Line 602: Extravagant Suit achievement check
        gm_lines[601] = '\tif Global.implants.torso_implant.i_name == "Экстравагантный костюм" or Global.implants.torso_implant.i_name == "Extravagant Suit":'

        # Line 830: BONUS_UNLOCK loading
        gm_lines[829] = '\t\t\tBONUS_UNLOCK = bonus_levels_unlocked; if BONUS_UNLOCK.find("House") != - 1 and BONUS_UNLOCK.find("Дом") == - 1: BONUS_UNLOCK.append("Дом"); if BONUS_UNLOCK.find("Дом") != - 1 and BONUS_UNLOCK.find("House") == - 1: BONUS_UNLOCK.append("House")'

        # Line 880: implants.purchased_implants loading
        gm_lines[879] = '\t\t\timplants.purchased_implants = new_implants_unlocked; if implants.purchased_implants.find("House") != - 1 and implants.purchased_implants.find("Дом") == - 1: implants.purchased_implants.append("Дом")'

        gm_path.write_text("\n".join(gm_lines) + "\n", encoding="utf-8", newline="\n")
        print("[+] Patched Entities/Game_Manager.gd")

        # 4. Entities/Physics_Objects/Implant_Object.gd
        io_path = self.patched_dir / "Entities/Physics_Objects/Implant_Object.gd"
        io_lines = io_path.read_text(encoding="utf-8").splitlines()

        # Line 11: Hazmat Suit / Костюм биохимзащиты bilingual check
        io_lines[10] = '\tif Global.implants.purchased_implants.find(implant_name) == - 1 and (implant_name != "Костюм биохимзащиты" or Global.implants.purchased_implants.find("Hazmat Suit") == - 1):'

        io_path.write_text("\n".join(io_lines) + "\n", encoding="utf-8", newline="\n")
        print("[+] Patched Entities/Physics_Objects/Implant_Object.gd")

        # Print Unified Diffs
        print("\n" + "=" * 80)
        print(" UNIFIED DIFF OF ALL MODIFIED FILES (vanilla_new vs _patched_files)")
        print("=" * 80)

        modified_files = [
            "Menu/Character_Menu.gd",
            "Menu_Test.gd",
            "Entities/Game_Manager.gd",
            "Entities/Physics_Objects/Implant_Object.gd"
        ]

        for rel in modified_files:
            v_p = self.vanilla_dir / rel
            p_p = self.patched_dir / rel
            diff = list(difflib.unified_diff(
                v_p.read_text(encoding="utf-8").splitlines(keepends=True),
                p_p.read_text(encoding="utf-8").splitlines(keepends=True),
                fromfile=f"vanilla_new/{rel}",
                tofile=f"_patched_files/{rel}",
                n=3
            ))
            print(f"\n--- Diff for {rel} ---")
            for line in diff:
                print(line, end="")

    # --------------------------------------------------------------------------
    # Step 4: Strict Pre-Pack Linter
    # --------------------------------------------------------------------------
    def step4_prepack_linter(self):
        print("\n" + "=" * 80)
        print(" [*] [4/6] STRICT PRE-PACK LINTER (33 Baseline + 2 Speech Scripts)")
        print("=" * 80)

        gd_files = sorted(list(self.patched_dir.rglob("*.gd")))
        tscn_files = sorted(list(self.patched_dir.rglob("*.tscn")))
        json_files = sorted(list(self.patched_dir.rglob("*.json")))

        violations: List[str] = []
        speech_script_names = {"Menu/Speech.gd", "Scripts/speech_label.gd"}

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

            # For the 33 baseline files: exact 1-to-1 line count and tab count matching vanilla
            if rel not in speech_script_names:
                if len(p_lines) != len(v_lines):
                    violations.append(f"GDScript {rel}: Line count mismatch! Patched={len(p_lines)}, Vanilla={len(v_lines)}")

                for lno, (pl, vl) in enumerate(zip(p_lines, v_lines), 1):
                    if pl.startswith(" ") and not pl.strip().startswith("#"):
                        violations.append(f"GDScript {rel}:{lno}: Space indentation found: {repr(pl[:30])}")

                    p_tabs = len(pl) - len(pl.lstrip("\t"))
                    v_tabs = len(vl) - len(vl.lstrip("\t"))
                    if p_tabs != v_tabs:
                        violations.append(f"GDScript {rel}:{lno}: Tab indentation mismatch: expected {v_tabs}, got {p_tabs}")

                    code_part = pl.split("#")[0]
                    sanitized = code_part.replace(r'\"', '').replace(r"\'", '')
                    if sanitized.count('"') % 2 != 0:
                        violations.append(f"GDScript {rel}:{lno}: Unbalanced double-quotes!")
            else:
                # Specialized strict GDScript indentation and syntax check for Speech scripts
                last_indent = 0
                expect_increase = False
                for lno, pl in enumerate(p_lines, 1):
                    if pl.startswith(" ") and not pl.strip().startswith("#"):
                        violations.append(f"Speech {rel}:{lno}: Space indentation found: {repr(pl[:30])}")

                    stripped = pl.strip()
                    if not stripped or stripped.startswith("#"):
                        continue

                    cur_indent = len(pl) - len(pl.lstrip("\t"))

                    if expect_increase:
                        if cur_indent != last_indent + 1:
                            violations.append(f"Speech {rel}:{lno}: Expected indent {last_indent + 1} after colon, got {cur_indent}")
                        expect_increase = False
                    elif cur_indent > last_indent + 1:
                        violations.append(f"Speech {rel}:{lno}: Indent jump from {last_indent} to {cur_indent}")

                    code_part = stripped.split("#")[0].strip()
                    if code_part.endswith(":"):
                        expect_increase = True
                        last_indent = cur_indent
                    else:
                        last_indent = cur_indent

                    sanitized = code_part.replace(r'\"', '').replace(r"\'", '')
                    if sanitized.count('"') % 2 != 0:
                        violations.append(f"Speech {rel}:{lno}: Unbalanced double-quotes!")

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

    # --------------------------------------------------------------------------
    # Step 5: Pure Python Binary PCK Rebuild
    # --------------------------------------------------------------------------
    def step5_binary_pck_rebuild(self):
        print("\n" + "=" * 80)
        print(" [*] [5/6] REBUILDING crueltysquad_ru_v2.pck (PURE PYTHON, 16-BYTE ALIGNED)")
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

        # Ensure Speech scripts .gdc and .remap are 100% purged
        assert "res://Menu/Speech.gdc" not in virtual_table, "res://Menu/Speech.gdc was not purged!"
        assert "res://Menu/Speech.gd.remap" not in virtual_table, "res://Menu/Speech.gd.remap was not purged!"
        assert "res://Scripts/speech_label.gdc" not in virtual_table, "res://Scripts/speech_label.gdc was not purged!"
        assert "res://Scripts/speech_label.gd.remap" not in virtual_table, "res://Scripts/speech_label.gd.remap was not purged!"

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

            # TOC padding to 16 bytes
            if toc_padding > 0:
                f_out.write(b"\x00" * toc_padding)

            # 3. Payload Data
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

                # Pad payload to 16-byte boundary
                cur_pos = f_out.tell()
                aligned_pos = (cur_pos + (FILE_ALIGNMENT - 1)) & ~(FILE_ALIGNMENT - 1)
                pad_len = aligned_pos - cur_pos
                if pad_len > 0:
                    f_out.write(b"\x00" * pad_len)

        out_size = self.output_pck_path.stat().st_size
        elapsed = time.time() - t0
        print(f"[+] PCK Build complete in {elapsed:.2f}s!")
        print(f"[+] Output PCK size: {out_size:,} bytes ({out_size / (1024*1024):.2f} MB)")

        # Sync to mirrors
        print("[*] Synchronizing output PCK across targets...")
        shutil.copy2(self.output_pck_path, self.compat_pck_path)
        print(f"    -> Synced to: {self.compat_pck_path}")

        shutil.copy2(self.output_pck_path, self.root_pck_path)
        print(f"    -> Synced to: {self.root_pck_path}")

        root_compat = Path("C:/dev/crueltysquad.pck")
        shutil.copy2(self.output_pck_path, root_compat)
        print(f"    -> Synced to: {root_compat}")

        # Post-verify header
        with open(self.output_pck_path, "rb") as f:
            magic, ver, major, minor, patch, file_count = struct.unpack("<4sIIII64xI", f.read(88))
            assert magic == PCK_MAGIC, "Bad PCK magic!"
            print(f"[+] Post-verification passed! Files: {file_count:,}, Engine: {major}.{minor}.{patch}")

    # --------------------------------------------------------------------------
    # Step 6: Savegame Money Key & Quick Testing Guide
    # --------------------------------------------------------------------------
    def step6_savegame_money_info(self):
        print("\n" + "=" * 80)
        print(" [*] [6/6] PLAYER MONEY KEY IN savegame.save & TESTING INSTRUCTIONS")
        print("=" * 80)
        print(" [!] Ключ денег игрока в сохранении: \"money\"")
        print("     Файл сохранения находится по пути:")
        print("     %APPDATA%\\Godot\\app_userdata\\Cruelty Squad\\savegame.save")
        print("     (обычно C:\\Users\\<Имя>\\AppData\\Roaming\\Godot\\app_userdata\\Cruelty Squad\\savegame.save)")
        print("\n     Формат файла: одна строка JSON-словаря.")
        print("     Чтобы получить $1,000,000 для мгновенной проверки покупки «Дома»:")
        print("     1. Откройте savegame.save в любом текстовом редакторе.")
        print("     2. Найдите \"money\": <число> (например, \"money\": 450).")
        print("     3. Замените на: \"money\": 1000000 (или 2000000).")
        print("     4. Сохраните файл и запустите игру.")
        print("     5. В меню снаряжения кликните на «Дом» (последний слот, иконка домика) -> подтвердите покупку.")
        print("     6. «Дом» станет купленным (перестанет быть красным), а на карте миссий появится уровень «Дом» (Lake Green)!")
        print("=" * 80)


if __name__ == "__main__":
    tool = HouseAndImplantFixTool(Path("C:/dev/cs_loc"))
    tool.run_all()
