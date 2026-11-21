#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_extract_strings.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
Task 2: Safe String Extractor & Legacy Localization Mapping Database Builder.
--------------------------------------------------------------------------------
"""

import os
import sys
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

# Cyrillic regex pattern
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")

# Rule 1: Forbidden file and resource extensions
RESOURCE_EXTENSIONS = (
    ".tscn", ".scn", ".gd", ".gdc", ".png", ".stex", ".wav", ".ogg",
    ".material", ".shader", ".tres", ".mesh", ".obj", ".dae", ".import",
    ".remap", ".ttf", ".otf", ".font", ".fnt", ".res"
)

# Rules 2, 3, 4: Forbidden call patterns (Engine calls, Node calls, Inputs, Groups, Animations, Steam API)
FORBIDDEN_CALL_PATTERNS = [
    # Engine & Node calls (Rule 2)
    r"\bget_node\b",
    r"\bget_node_or_null\b",
    r"\bfind_node\b",
    r"\bhas_node\b",
    r"\bconnect\b",
    r"\bemit_signal\b",
    r"\bcall\b",
    r"\bcall_deferred\b",
    r"\bload\b",
    r"\bpreload\b",
    r"\bhas_method\b",
    r"\bis_connected\b",
    r"\bdisconnect\b",
    # Input, Groups, Animations, Shaders, Audio (Rule 3)
    r"\bInput\s*\.\s*\w+",
    r"\bInputMap\s*\.\s*\w+",
    r"\bset_inputs\b",
    r"\bplay\b",
    r"\bplay_backwards\b",
    r"\bqueue\b",
    r"\bhas_animation\b",
    r"\bset_shader_param\b",
    r"\badd_to_group\b",
    r"\bis_in_group\b",
    r"\bremove_from_group\b",
    r"\bget_bus_index\b",
    # Steam API (Rule 4)
    r"\b(Steam|SteamGlobal|godotsteam)\s*\.\s*\w+",
    # Engine system / debug calls
    r"\badd_autoload_singleton\b",
    r"\bpush_error\b",
    r"\bpush_warning\b",
    r"\bprint\b",
    r"\bprint_debug\b",
    r"\bprinterr\b",
]

FORBIDDEN_CALL_REGEX = re.compile("|".join(FORBIDDEN_CALL_PATTERNS), re.IGNORECASE)

# String literal tokenization regex
STRING_LITERAL_REGEX = re.compile(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')')

# Rule 6: Allowed visible UI properties and dialogue arrays/fields in .tscn
ALLOWED_TSCN_PROPS = {
    "text", "bbcode_text", "hint_tooltip",
    "dialogue", "lines", "dyn_lines", "dialog_text", "message",
    "npc_name", "implant_name", "override_name", "line", "line2", "value"
}


class SafeStringExtractor:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.vanilla_dir = base_dir / "vanilla_new"
        self.ru_dir = base_dir / "ru_old"
        self.output_db_path = base_dir / "localization_db.json"

    @staticmethod
    def is_resource_path(s: str) -> bool:
        """
        Rule 1: Checks if string is a resource path or file reference.
        """
        s_lower = s.lower().strip()
        if s_lower.startswith(("res://", "user://")):
            return True
        for ext in RESOURCE_EXTENSIONS:
            if ext in s_lower:
                return True
        return False

    @staticmethod
    def is_technical_identifier(s: str) -> bool:
        """
        Rule 5: Checks if string is a technical identifier, single character, or numeric.
        """
        stripped = s.strip()
        # Empty or single character
        if len(stripped) <= 1:
            return True
        # Numeric / float / percentage
        if re.match(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?%?$", stripped):
            return True
        # Hex color or hex number
        if re.match(r"^#[0-9a-fA-F]{3,8}$", stripped) or re.match(r"^0x[0-9a-fA-F]+$", stripped):
            return True
        # Format specifiers
        if re.match(r"^%[0-9]*\.?[0-9]*[sdfg]$", stripped):
            return True

        # Placeholder / punctuation strings
        if stripped in ("N/A", "0/0", "???", "...", "\\n", "\\n(", "%\\nMKC: $", "n/a", "0", "1", "Nicegdgbffhfhfh"):
            return True

        # If string contains spaces, it is a human-readable phrase, title, or sentence
        if " " in stripped:
            return False

        # snake_case (contains underscore)
        if "_" in stripped:
            return True

        # camelCase / PascalCase with multiple words (e.g., playerHealth, NodePath)
        if re.search(r"[a-z][A-Z]", stripped):
            return True

        # Short uppercase tickers or codes (e.g. CRUS, AAPL, TST, CIV, POOL)
        if re.match(r"^[A-Z0-9]{2,6}$", stripped):
            return True

        # Single all-lowercase identifier (e.g. equity, default, stocks, idle)
        if re.match(r"^[a-z0-9]+$", stripped):
            return True

        return False

    @staticmethod
    def get_enclosing_call(prefix: str) -> str:
        """
        Determines enclosing function/method call before string literal.
        """
        depth = 0
        paren_pos = -1
        for idx in range(len(prefix) - 1, -1, -1):
            if prefix[idx] == ")":
                depth += 1
            elif prefix[idx] == "(":
                if depth > 0:
                    depth -= 1
                else:
                    paren_pos = idx
                    break
        if paren_pos != -1:
            before_paren = prefix[:paren_pos].strip()
            m = re.search(r"([a-zA-Z0-9_$.]+)\s*$", before_paren)
            if m:
                return m.group(1)
        return ""

    @staticmethod
    def clean_escapes(s: str) -> str:
        """
        Safely unescapes escaped quotes and backslashes without corrupting UTF-8 characters.
        """
        return s.replace(r'\"', '"').replace(r"\'", "'").replace(r"\\", "\\")

    def extract_from_gd(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts valid translatable strings from a .gd script.
        """
        results = []
        if not file_path.exists():
            return results

        with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
            lines = fp.readlines()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Node name checks and animation name checks
            if re.search(r'\b(current_animation|has_animation|_ANIMS|ANIMS|DEATH_ANIMS|IDLE_ANIM|FIRE_ANIM|has_anim_\w+)\b', line):
                continue
            if re.search(r'(\.name\s*==|name\s*==|\bname\s*=)', line):
                continue
            if "BONUS_LEVELS" in line or "export var level_name" in line:
                continue
            if 'button == "WEAPON' in line:
                continue

            for sub_i, match in enumerate(STRING_LITERAL_REGEX.finditer(line)):
                raw_content = match.group(1)[1:-1]
                val = self.clean_escapes(raw_content)

                # Rule 1: Resource paths
                if self.is_resource_path(val):
                    continue

                prefix = line[:match.start()]
                # NodePath shorthand ($"path/to/node")
                if prefix.rstrip().endswith("$"):
                    continue

                # Rules 2, 3, 4: Forbidden call checks
                call = self.get_enclosing_call(prefix)
                if call and FORBIDDEN_CALL_REGEX.search(call):
                    continue

                # Rule 5: Technical identifiers
                if self.is_technical_identifier(val):
                    continue

                results.append({
                    "line_num": idx,
                    "sub_index": sub_i,
                    "val": val,
                    "call": call,
                    "context_code": line.strip()
                })

        return results

    def extract_from_tscn(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Rule 6: Extracts valid UI and dialogue strings from a .tscn scene file.
        Strictly ignores [ext_resource], [sub_resource], and NodePath expressions.
        """
        results = []
        if not file_path.exists():
            return results

        with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
            lines = fp.readlines()

        in_node = False
        current_node = ""
        idx = 0
        total_lines = len(lines)

        while idx < total_lines:
            line_num = idx + 1
            line = lines[idx]
            stripped = line.strip()

            if stripped.startswith("["):
                if stripped.startswith("[node"):
                    in_node = True
                    nm = re.search(r'name="([^"]+)"', stripped)
                    pm = re.search(r'parent="([^"]+)"', stripped)
                    n_name = nm.group(1) if nm else "Node"
                    p_name = pm.group(1) if pm else ""
                    current_node = f"{p_name}/{n_name}" if p_name else n_name
                else:
                    in_node = False
                idx += 1
                continue

            if not in_node:
                idx += 1
                continue

            # Parse property key-value pair
            pm = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*(.*)$", stripped)
            if pm:
                prop_name = pm.group(1)
                prop_val = pm.group(2)

                if prop_name.lower() in ALLOWED_TSCN_PROPS:
                    full_val = prop_val
                    # Multiline string support
                    if full_val.startswith('"') and (not full_val.endswith('"') or full_val == '"'):
                        while idx + 1 < total_lines:
                            idx += 1
                            full_val += "\n" + lines[idx].rstrip("\r\n")
                            if lines[idx].rstrip("\r\n").endswith('"'):
                                break
                    # Array support
                    elif full_val.startswith("[") and not full_val.endswith("]"):
                        while idx + 1 < total_lines:
                            idx += 1
                            full_val += " " + lines[idx].strip()
                            if lines[idx].strip().endswith("]"):
                                break

                    # Extract string literals from property value
                    matches = STRING_LITERAL_REGEX.finditer(full_val)
                    for s_idx, m in enumerate(matches):
                        raw_s = m.group(1)[1:-1]
                        val = self.clean_escapes(raw_s)

                        # Rule 1 & Rule 5 validation
                        if self.is_resource_path(val):
                            continue
                        if self.is_technical_identifier(val):
                            continue

                        results.append({
                            "node": current_node,
                            "property": prop_name,
                            "sub_index": s_idx,
                            "line_num": line_num,
                            "context_code": line.strip(),
                            "val": val
                        })
            idx += 1

        return results

    def extract_and_map_all(self) -> List[Dict[str, Any]]:
        """
        Scans vanilla_new, extracts strings, and maps with ru_old.
        """
        db_entries = []

        # Find all .gd and .tscn in vanilla_new (excluding addons and editor/import folders)
        all_files: List[Tuple[str, str]] = []
        for root, _, files in os.walk(self.vanilla_dir):
            rel_root = Path(root).relative_to(self.vanilla_dir).as_posix()
            if rel_root.startswith("addons") or rel_root.startswith(".import") or rel_root.startswith(".autoconverted"):
                continue
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in (".gd", ".tscn"):
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(self.vanilla_dir).as_posix()
                    all_files.append((rel_p, ext))

        all_files.sort(key=lambda x: x[0])

        for rel_path, ext in all_files:
            v_path = self.vanilla_dir / rel_path
            r_path = self.ru_dir / rel_path

            if ext == ".tscn":
                v_items = self.extract_from_tscn(v_path)
                r_items = self.extract_from_tscn(r_path) if r_path.exists() else []

                # Index RU items by (node, property, sub_index)
                r_map = {(x["node"], x["property"], x["sub_index"]): x for x in r_items}

                for item in v_items:
                    k = (item["node"], item["property"], item["sub_index"])
                    ru_legacy = None
                    if k in r_map:
                        candidate = r_map[k]["val"]
                        if CYRILLIC_RE.search(candidate):
                            ru_legacy = candidate

                    status = "NEEDS_REVIEW" if ru_legacy else "NEEDS_TRANSLATION"
                    unique_id = f"{rel_path}:{item['line_num']}:{item['sub_index']}"

                    db_entries.append({
                        "id": unique_id,
                        "file_path": rel_path,
                        "line_num": item["line_num"],
                        "context_code": item["context_code"],
                        "en_original": item["val"],
                        "ru_legacy": ru_legacy,
                        "status": status,
                        "ru_final": ""
                    })

            elif ext == ".gd":
                v_items = self.extract_from_gd(v_path)
                r_items = self.extract_from_gd(r_path) if r_path.exists() else []

                # Helper to get statement signature (e.g., 'create_button(', 'wep.hint_tooltip =')
                def get_stmt_sig(code_str: str) -> str:
                    m = re.match(r"^\s*([a-zA-Z0-9_$.]+(?:\s*=\s*|\s*\())", code_str)
                    return m.group(1).strip() if m else code_str[:25].strip()

                r_by_line = {(x["line_num"], x["sub_index"]): x for x in r_items}
                r_cyr = [x for x in r_items if CYRILLIC_RE.search(x["val"])]
                used_r_ids: Set[int] = set()

                for item in v_items:
                    ru_legacy = None
                    v_sig = get_stmt_sig(item["context_code"])

                    # 1. Nearby signature match (+/- 3 lines) - handles off-by-one decompiler shifts
                    for r_cand in r_items:
                        if id(r_cand) in used_r_ids:
                            continue
                        if abs(r_cand["line_num"] - item["line_num"]) <= 3:
                            if item["sub_index"] == r_cand["sub_index"]:
                                if get_stmt_sig(r_cand["context_code"]) == v_sig:
                                    if CYRILLIC_RE.search(r_cand["val"]):
                                        ru_legacy = r_cand["val"]
                                        used_r_ids.add(id(r_cand))
                                        break

                    # 2. Direct line & sub_index match
                    if ru_legacy is None:
                        direct_k = (item["line_num"], item["sub_index"])
                        if direct_k in r_by_line and id(r_by_line[direct_k]) not in used_r_ids:
                            cand = r_by_line[direct_k]["val"]
                            if CYRILLIC_RE.search(cand):
                                ru_legacy = cand
                                used_r_ids.add(id(r_by_line[direct_k]))

                    # 3. Heuristic match within context window (+/- 30 lines)
                    if ru_legacy is None and r_cyr:
                        v_code = item["context_code"]
                        v_left = v_code.split("=")[0].strip() if "=" in v_code else ""

                        for r_cand in r_cyr:
                            if id(r_cand) in used_r_ids:
                                continue
                            if abs(r_cand["line_num"] - item["line_num"]) <= 30:
                                r_code = r_cand["context_code"]
                                r_left = r_code.split("=")[0].strip() if "=" in r_code else ""
                                # Variable or assignment match
                                if v_left and v_left == r_left:
                                    ru_legacy = r_cand["val"]
                                    used_r_ids.add(id(r_cand))
                                    break
                                # Method call match
                                if item["call"] and item["call"] == r_cand["call"]:
                                    ru_legacy = r_cand["val"]
                                    used_r_ids.add(id(r_cand))
                                    break

                    status = "NEEDS_REVIEW" if ru_legacy else "NEEDS_TRANSLATION"
                    unique_id = f"{rel_path}:{item['line_num']}:{item['sub_index']}"

                    db_entries.append({
                        "id": unique_id,
                        "file_path": rel_path,
                        "line_num": item["line_num"],
                        "context_code": item["context_code"],
                        "en_original": item["val"],
                        "ru_legacy": ru_legacy,
                        "status": status,
                        "ru_final": ""
                    })

        return db_entries

    def build_and_save_db(self) -> List[Dict[str, Any]]:
        """
        Executes the extraction and mapping pipeline and saves localization_db.json.
        """
        print("=" * 80)
        print(" CRUELTY SQUAD - SAFE STRING EXTRACTOR & MAPPING PIPELINE (TASK 2)")
        print("=" * 80)
        print(f"[*] Vanilla source tree:    {self.vanilla_dir.resolve()}")
        print(f"[*] RU 2021 source tree:    {self.ru_dir.resolve()}")

        entries = self.extract_and_map_all()

        # Compute statistics
        total = len(entries)
        needs_review = sum(1 for e in entries if e["status"] == "NEEDS_REVIEW")
        needs_translation = sum(1 for e in entries if e["status"] == "NEEDS_TRANSLATION")
        gd_count = sum(1 for e in entries if e["file_path"].endswith(".gd"))
        tscn_count = sum(1 for e in entries if e["file_path"].endswith(".tscn"))

        files_affected = len(set(e["file_path"] for e in entries))
        files_with_legacy = len(set(e["file_path"] for e in entries if e["ru_legacy"] is not None))

        print(f"\n[+] Extraction Complete:")
        print(f"    - Total translatable strings extracted: {total:,}")
        print(f"    - From .gd scripts:                     {gd_count:,}")
        print(f"    - From .tscn scenes:                    {tscn_count:,}")
        print(f"    - Unique files containing text:         {files_affected}")

        print(f"\n[+] Mapping with RU 2021 Legacy Translation:")
        print(f"    - Strings matched (NEEDS_REVIEW):       {needs_review:,} ({needs_review / total * 100:.1f}%)")
        print(f"    - New / Unmatched (NEEDS_TRANSLATION):  {needs_translation:,} ({needs_translation / total * 100:.1f}%)")
        print(f"    - Files with mapped legacy text:        {files_with_legacy}")

        # Top files breakdown
        print(f"\n[*] Top 10 Files by String Count:")
        file_counts: Dict[str, int] = {}
        for e in entries:
            file_counts[e["file_path"]] = file_counts.get(e["file_path"], 0) + 1

        top_files = sorted(file_counts.items(), key=lambda x: -x[1])[:10]
        for fpath, cnt in top_files:
            f_rev = sum(1 for e in entries if e["file_path"] == fpath and e["status"] == "NEEDS_REVIEW")
            print(f"    - {fpath:36}: {cnt:4} strings ({f_rev} mapped from 2021)")

        # Save to JSON
        with open(self.output_db_path, "w", encoding="utf-8") as fp:
            json.dump(entries, fp, indent=2, ensure_ascii=False)

        print(f"\n[+] Localization database saved to: {self.output_db_path.resolve()}")
        print("=" * 80)
        return entries


def main():
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "vanilla_new").exists():
        base_dir = script_dir
    elif (script_dir / "cs_loc" / "vanilla_new").exists():
        base_dir = script_dir / "cs_loc"
    elif (Path.cwd() / "vanilla_new").exists():
        base_dir = Path.cwd()
    elif (Path.cwd() / "cs_loc" / "vanilla_new").exists():
        base_dir = Path.cwd() / "cs_loc"
    else:
        base_dir = script_dir

    extractor = SafeStringExtractor(base_dir)
    extractor.build_and_save_db()


if __name__ == "__main__":
    main()
