#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_validate_db.py
--------------------------------------------------------------------------------
Lead Localization Engineering & Reverse-Engineering Tool for Cruelty Squad (Godot 3.x)
Task 4: Comprehensive Syntax, Invariants, and Quality Assurance Validator.
--------------------------------------------------------------------------------
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Reconfigure console output to UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class DatabaseValidator:
    def __init__(self, db_path: Path, glossary_path: Path):
        self.db_path = db_path
        self.glossary_path = glossary_path
        self.db: List[Dict[str, Any]] = []
        self.glossary: Dict[str, Any] = {}
        self.glossary_terms: Dict[str, str] = {}
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def load_data(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        with open(self.db_path, "r", encoding="utf-8") as f:
            self.db = json.load(f)

        if self.glossary_path.exists():
            with open(self.glossary_path, "r", encoding="utf-8") as f:
                self.glossary = json.load(f)
            for t in self.glossary.get("glossary", []):
                self.glossary_terms[t["en"]] = t["ru_canonical"]

    def validate_all(self) -> bool:
        print("=" * 80)
        print(" CRUELTY SQUAD - LOCALIZATION DATABASE QA VALIDATION (TASK 4)")
        print("=" * 80)
        print(f"[*] Validating database: {self.db_path.resolve()}")
        print(f"[*] Total records to verify: {len(self.db):,}\n")

        for idx, entry in enumerate(self.db, 1):
            eid = entry.get("id", f"record_{idx}")
            en = entry.get("en_original", "")
            ru = entry.get("ru_final", "")
            ctx = entry.get("context_code", "")
            fpath = entry.get("file_path", "")
            lno = entry.get("line_num", 0)

            # Rule 1: Non-empty ru_final
            if not ru and en:
                self.errors.append({
                    "id": eid,
                    "rule": "NON_EMPTY",
                    "file": fpath,
                    "line": lno,
                    "message": f"Empty 'ru_final' for en_original: {en!r}"
                })

            # Rule 2: Newline count invariant
            en_nl = en.count("\n")
            ru_nl = ru.count("\n")
            if en_nl != ru_nl:
                self.errors.append({
                    "id": eid,
                    "rule": "NEWLINE_INVARIANT",
                    "file": fpath,
                    "line": lno,
                    "message": f"Newline count mismatch: en has {en_nl}, ru has {ru_nl}"
                })

            # Rule 3: Format specifiers (%s, %d, %f, etc.)
            en_specs = re.findall(r"(%[0-9]*\.?[0-9]*[sdfg])", en)
            ru_specs = re.findall(r"(%[0-9]*\.?[0-9]*[sdfg])", ru)
            if en_specs != ru_specs:
                self.errors.append({
                    "id": eid,
                    "rule": "FORMAT_SPECIFIER_INVARIANT",
                    "file": fpath,
                    "line": lno,
                    "message": f"Format specifiers mismatch: en={en_specs}, ru={ru_specs}"
                })

            # Rule 4: Internal quote escaping (no raw unescaped quotes allowed)
            # Find quotes not preceded by backslash
            unescaped_pos = [m.start() for m in re.finditer(r'(?<!\\)"', ru)]
            if unescaped_pos:
                self.errors.append({
                    "id": eid,
                    "rule": "UNESCAPED_QUOTE_INVARIANT",
                    "file": fpath,
                    "line": lno,
                    "message": f"Unescaped double quote(s) detected at positions {unescaped_pos} in: {ru!r}"
                })

            # Rule 5: Short UI elements length constraint (<= +25% length)
            is_ui_elem = (
                "text =" in ctx or "hint_tooltip =" in ctx or "create_button(" in ctx
                or ".text +=" in ctx or "override_name =" in ctx
            )
            # Only test short UI strings between 4 and 18 chars
            if is_ui_elem and 4 <= len(en.strip()) <= 18:
                en_len = len(en.strip())
                ru_len = len(ru.strip())
                ratio = ru_len / en_len
                # Allow tolerance of at least 2 chars for natural linguistic differences
                if ratio > 1.25 and (ru_len - en_len) > 2:
                    self.errors.append({
                        "id": eid,
                        "rule": "UI_LENGTH_CONSTRAINT",
                        "file": fpath,
                        "line": lno,
                        "message": (
                            f"UI string exceeded +25% limit: en={en_len} chars ('{en.strip()}'), "
                            f"ru={ru_len} chars ('{ru.strip()}'), ratio={ratio:.2f}"
                        )
                    })

            # Rule 6: Glossary adherence for key canonical terms
            if en in self.glossary_terms:
                canonical = self.glossary_terms[en]
                # Compare stripped unescaped representations
                canon_clean = canonical.replace('\\"', '"').strip()
                ru_clean = ru.replace('\\"', '"').strip()
                if ru_clean != canon_clean:
                    # Report deviation
                    self.warnings.append({
                        "id": eid,
                        "rule": "GLOSSARY_DEVIATION",
                        "file": fpath,
                        "line": lno,
                        "message": f"Expected canonical '{canon_clean}', got '{ru_clean}'"
                    })

        self.print_report()
        return len(self.errors) == 0

    def print_report(self):
        print(f"[*] Invariant Verification Results:")
        print(f"    - Records Checked:         {len(self.db):,}")
        print(f"    - Critical Errors:         {len(self.errors)}")
        print(f"    - Style/Glossary Warnings: {len(self.warnings)}")

        if self.errors:
            print("\n[!] CRITICAL ERRORS DETECTED:")
            for err in self.errors[:15]:
                print(f"    [{err['rule']}] {err['file']}:{err['line']} ({err['id']}): {err['message']}")
            if len(self.errors) > 15:
                print(f"    ... and {len(self.errors) - 15} more critical errors.")
        else:
            print("\n[+] 100% of records PASSED all syntax and technical invariants!")

        if self.warnings:
            print(f"\n[*] Glossary Warnings ({len(self.warnings)}):")
            for w in self.warnings[:10]:
                print(f"    [{w['rule']}] {w['file']}:{w['line']}: {w['message']}")

        print("\n" + "=" * 80)
        if len(self.errors) == 0:
            print(" VERIFICATION STATUS: [SUCCESS] ALL INVARIANTS SATISFIED")
        else:
            print(" VERIFICATION STATUS: [FAILED] ERRORS MUST BE RESOLVED")
        print("=" * 80)


def main():
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "localization_db.json").exists():
        base_dir = script_dir
    elif (script_dir / "cs_loc" / "localization_db.json").exists():
        base_dir = script_dir / "cs_loc"
    elif (Path.cwd() / "localization_db.json").exists():
        base_dir = Path.cwd()
    elif (Path.cwd() / "cs_loc" / "localization_db.json").exists():
        base_dir = Path.cwd() / "cs_loc"
    else:
        base_dir = script_dir

    db_path = base_dir / "localization_db.json"
    glossary_path = base_dir / "glossary.json"

    validator = DatabaseValidator(db_path, glossary_path)
    validator.load_data()
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
