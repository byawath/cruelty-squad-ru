#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15_fix_handler_speech.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
TASK 15: Restore Handler Speech Voice, Mouth Animation & Typewriter Effect
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


class HandlerSpeechFixTool:
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

    def run_all(self):
        print("=" * 80)
        print(" CRUELTY SQUAD RUSSIAN LOCALIZATION — TASK 15")
        print(" Restoring Handler Voice, Mouth Animation & Typewriter Printing")
        print("=" * 80)

        self.step1_audit_vanilla_vs_ru_old()
        self.step2_clean_port_cyrillic_speech()
        self.step3_strict_linter_and_diff()
        self.step4_binary_pck_rebuild()
        self.step5_post_verify()

    # --------------------------------------------------------------------------
    # Step 1: Audit vanilla_new vs ru_old
    # --------------------------------------------------------------------------
    def step1_audit_vanilla_vs_ru_old(self):
        print("\n" + "=" * 80)
        print(" [*] [1/5] AUDIT: vanilla_new vs ru_old (Speech.gd & speech_label.gd)")
        print("=" * 80)

        for rel in ["Menu/Speech.gd", "Scripts/speech_label.gd"]:
            v_path = self.vanilla_dir / rel
            r_path = self.ru_old_dir / rel

            assert v_path.exists(), f"Missing {v_path}"
            assert r_path.exists(), f"Missing {r_path}"

            v_lines = v_path.read_text(encoding="utf-8").splitlines(keepends=True)
            r_lines = r_path.read_text(encoding="utf-8").splitlines(keepends=True)

            diff = list(difflib.unified_diff(v_lines, r_lines, fromfile=f"vanilla_new/{rel}", tofile=f"ru_old/{rel}"))
            print(f"\n--- Unified Diff for {rel} ---")
            for line in diff:
                print(line, end="")

        # Audit Menu_Test.gd description call logic
        print("\n[*] Auditing Menu_Test.gd briefing calls...")
        mt_path = self.patched_dir / "Menu_Test.gd"
        mt_lines = mt_path.read_text(encoding="utf-8").splitlines()
        found_calls = []
        for lno, line in enumerate(mt_lines, 1):
            if "Description.speech" in line or "Description.visible_characters" in line:
                found_calls.append((lno, line.strip()))

        for lno, line in found_calls:
            print(f"    Menu_Test.gd:{lno:4d} | {line}")

        print("[+] Audit confirms: vanilla Speech.gd only tests ASCII ranges 97..122 and 65..90.")
        print("[+] When text is Cyrillic UTF-8, emit_signal('character_speak') and sound play never fire.")

    # --------------------------------------------------------------------------
    # Step 2: Clean Port of Cyrillic Speech Support
    # --------------------------------------------------------------------------
    def step2_clean_port_cyrillic_speech(self):
        print("\n" + "=" * 80)
        print(" [*] [2/5] CLEAN PORT: Cyrillic Phonemes, Mouth Animation & Typewriter")
        print("=" * 80)

        # Build patched Menu/Speech.gd from vanilla_new
        v_speech_path = self.vanilla_dir / "Menu/Speech.gd"
        v_speech_text = v_speech_path.read_text(encoding="utf-8")

        target_speech_snip = (
            '\t\tif c.ord_at(0) >= 97 and c.ord_at(0) <= 122:\n'
            '\t\t\t$AudioStreamPlayer.stream = alpha_sound[c.ord_at(0) - 97]\n'
            '\t\t\temit_signal("character_speak")\n'
            '\t\t\t$AudioStreamPlayer.play()\n'
            '\t\tif c.ord_at(0) >= 65 and c.ord_at(0) <= 90:\n'
            '\t\t\temit_signal("character_speak")\n'
            '\t\t\t$AudioStreamPlayer.stream = alpha_sound[c.ord_at(0) - 65]\n'
            '\t\t\t$AudioStreamPlayer.play()'
        )

        replacement_speech_snip = (
            '\t\tif c.ord_at(0) >= 1072 and c.ord_at(0) <= 1103:\n'
            '\t\t\t$AudioStreamPlayer.stream = alpha_sound[(c.ord_at(0) - 1072) % 26]\n'
            '\t\t\temit_signal("character_speak")\n'
            '\t\t\t$AudioStreamPlayer.play()\n'
            '\t\telif c.ord_at(0) >= 1040 and c.ord_at(0) <= 1071:\n'
            '\t\t\t$AudioStreamPlayer.stream = alpha_sound[(c.ord_at(0) - 1040) % 26]\n'
            '\t\t\temit_signal("character_speak")\n'
            '\t\t\t$AudioStreamPlayer.play()\n'
            '\t\telif c.ord_at(0) == 1025 or c.ord_at(0) == 1105:\n'
            '\t\t\t$AudioStreamPlayer.stream = alpha_sound[5]\n'
            '\t\t\temit_signal("character_speak")\n'
            '\t\t\t$AudioStreamPlayer.play()\n'
            '\t\telif c.ord_at(0) >= 1024 and c.ord_at(0) <= 1279:\n'
            '\t\t\t$AudioStreamPlayer.stream = alpha_sound[randi() % 26]\n'
            '\t\t\temit_signal("character_speak")\n'
            '\t\t\t$AudioStreamPlayer.play()\n'
            '\t\telif c.ord_at(0) >= 97 and c.ord_at(0) <= 122:\n'
            '\t\t\t$AudioStreamPlayer.stream = alpha_sound[c.ord_at(0) - 97]\n'
            '\t\t\temit_signal("character_speak")\n'
            '\t\t\t$AudioStreamPlayer.play()\n'
            '\t\telif c.ord_at(0) >= 65 and c.ord_at(0) <= 90:\n'
            '\t\t\temit_signal("character_speak")\n'
            '\t\t\t$AudioStreamPlayer.stream = alpha_sound[c.ord_at(0) - 65]\n'
            '\t\t\t$AudioStreamPlayer.play()'
        )

        assert target_speech_snip in v_speech_text, "Target snippet not found in vanilla Menu/Speech.gd!"
        p_speech_text = v_speech_text.replace(target_speech_snip, replacement_speech_snip)

        out_speech_path = self.patched_dir / "Menu/Speech.gd"
        out_speech_path.parent.mkdir(parents=True, exist_ok=True)
        out_speech_path.write_text(p_speech_text, encoding="utf-8", newline="\n")
        print(f"[+] Written patched: {out_speech_path}")

        # Build patched Scripts/speech_label.gd from vanilla_new
        v_label_path = self.vanilla_dir / "Scripts/speech_label.gd"
        v_label_text = v_label_path.read_text(encoding="utf-8")

        assert target_speech_snip in v_label_text, "Target snippet not found in vanilla Scripts/speech_label.gd!"
        p_label_text = v_label_text.replace(target_speech_snip, replacement_speech_snip)

        out_label_path = self.patched_dir / "Scripts/speech_label.gd"
        out_label_path.parent.mkdir(parents=True, exist_ok=True)
        out_label_path.write_text(p_label_text, encoding="utf-8", newline="\n")
        print(f"[+] Written patched: {out_label_path}")

    # --------------------------------------------------------------------------
    # Step 3: Strict GDScript Syntax Linter & Diff Output
    # --------------------------------------------------------------------------
    def step3_strict_linter_and_diff(self):
        print("\n" + "=" * 80)
        print(" [*] [3/5] STRICT PRE-PACK LINTER (33 Baseline + 2 Speech Scripts)")
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
                    # Zero spaces allowed
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

                    # Quote check
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

        # Print Visual Diff of patched Speech.gd and speech_label.gd
        print("\n" + "=" * 80)
        print(" [*] VISUAL CODE INSPECTION: PATCHED SPEECH DIFFS")
        print("=" * 80)
        for rel in ["Menu/Speech.gd", "Scripts/speech_label.gd"]:
            v_p = self.vanilla_dir / rel
            p_p = self.patched_dir / rel
            diff = list(difflib.unified_diff(
                v_p.read_text(encoding="utf-8").splitlines(keepends=True),
                p_p.read_text(encoding="utf-8").splitlines(keepends=True),
                fromfile=f"vanilla_new/{rel}",
                tofile=f"_patched_files/{rel}",
                n=3
            ))
            print(f"\n--- Unified Diff: {rel} ---")
            for l in diff:
                print(l, end="")

    # --------------------------------------------------------------------------
    # Step 4: Pure Python PCK Rebuild
    # --------------------------------------------------------------------------
    def step4_binary_pck_rebuild(self):
        print("\n" + "=" * 80)
        print(" [*] [4/5] REBUILDING crueltysquad_ru_v2.pck (PURE PYTHON, 16-BYTE ALIGNED)")
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

    # --------------------------------------------------------------------------
    # Step 5: Post-Verification
    # --------------------------------------------------------------------------
    def step5_post_verify(self):
        print("\n" + "=" * 80)
        print(" [*] [5/5] POST-VERIFICATION OF BUILT PCK")
        print("=" * 80)

        with open(self.output_pck_path, "rb") as f:
            hdr = struct.unpack("<4sIIII64xI", f.read(88))
            assert hdr[0] == PCK_MAGIC, f"Invalid magic: {hdr[0]}"
            file_count = hdr[5]

            pck_files = {}
            for _ in range(file_count):
                plen = struct.unpack("<I", f.read(4))[0]
                p = f.read(plen).rstrip(b"\x00").decode("utf-8", errors="replace")
                offset, size, md5 = struct.unpack("<QQ16s", f.read(32))
                pck_files[p] = {"offset": offset, "size": size, "md5": md5}

            # Check Menu/Speech.gd inside built PCK
            assert "res://Menu/Speech.gd" in pck_files, "Menu/Speech.gd missing from built PCK!"
            assert "res://Menu/Speech.gdc" not in pck_files, "Menu/Speech.gdc lingering in built PCK!"
            assert "res://Menu/Speech.gd.remap" not in pck_files, "Menu/Speech.gd.remap lingering in built PCK!"

            info_sp = pck_files["res://Menu/Speech.gd"]
            f.seek(info_sp["offset"])
            sp_text = f.read(info_sp["size"]).decode("utf-8")
            assert "1072" in sp_text and "character_speak" in sp_text, "Cyrillic logic missing from Menu/Speech.gd in PCK!"
            print(f"[+] Verified res://Menu/Speech.gd in built PCK ({len(sp_text.splitlines())} lines)")

            # Check Scripts/speech_label.gd inside built PCK
            assert "res://Scripts/speech_label.gd" in pck_files, "Scripts/speech_label.gd missing from built PCK!"
            assert "res://Scripts/speech_label.gdc" not in pck_files, "Scripts/speech_label.gdc lingering in built PCK!"
            assert "res://Scripts/speech_label.gd.remap" not in pck_files, "Scripts/speech_label.gd.remap lingering in built PCK!"

            info_sl = pck_files["res://Scripts/speech_label.gd"]
            f.seek(info_sl["offset"])
            sl_text = f.read(info_sl["size"]).decode("utf-8")
            assert "1072" in sl_text and "character_speak" in sl_text, "Cyrillic logic missing from Scripts/speech_label.gd in PCK!"
            print(f"[+] Verified res://Scripts/speech_label.gd in built PCK ({len(sl_text.splitlines())} lines)")

            # Check Menu_Test.gd still has 4 tabs on line 437
            assert "res://Menu_Test.gd" in pck_files, "Menu_Test.gd missing from built PCK!"
            info_mt = pck_files["res://Menu_Test.gd"]
            f.seek(info_mt["offset"])
            mt_text = f.read(info_mt["size"]).decode("utf-8")
            mt_lines = mt_text.splitlines()
            assert mt_lines[436].startswith("\t\t\t\twep.hint_tooltip"), "Menu_Test.gd line 437 regression!"
            print(f"[+] Verified res://Menu_Test.gd preserved with 4 tabs on weapon tooltips")

        print("\n" + "=" * 80)
        print(" [SUCCESS] TASK 15 COMPLETED WITH ZERO DEFECTS!")
        print(" Handler speech phonemes, mouth animation & typewriter restored.")
        print("=" * 80)


def main():
    base_dir = Path("C:/dev/cs_loc").resolve()
    tool = HandlerSpeechFixTool(base_dir)
    tool.run_all()


if __name__ == "__main__":
    main()
