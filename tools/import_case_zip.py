#!/usr/bin/env python3
"""Import uploaded Sharp Eye case-pack ZIPs into this GitHub Pages repository."""

import hashlib
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
UPLOADS = ROOT / "uploads"
MANIFEST = ROOT / "levels.json"
IMPORTED = ROOT / ".imported-packs.json"
CONTROLS = ROOT / "case-controls.json"


def fail(message: str) -> None:
    raise ValueError(message)


def safe_zip_member(name: str) -> str:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        fail(f"Unsafe path in ZIP: {name}")
    return path.as_posix()


def validate_pack(archive: zipfile.ZipFile, filename: str, known_ids: set[str],
                  known_groups: set[str]) -> tuple[str, list[dict], list[tuple[str, str]]]:
    files = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        path = safe_zip_member(info.filename)
        files[path] = info

    if "levels.json" not in files:
        fail(f"{filename}: ZIP root must contain levels.json (no wrapper folder).")
    try:
        source = json.loads(archive.read(files["levels.json"]).decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"{filename}: levels.json is not valid UTF-8 JSON: {exc}")

    levels = source.get("levels") if isinstance(source, dict) else None
    if not isinstance(levels, list) or not 3 <= len(levels) <= 10:
        fail(f"{filename}: expected between 3 and 10 level records.")
    if any(not isinstance(level, dict) for level in levels):
        fail(f"{filename}: each level record must be a JSON object.")
    raw_group_ids = [level.get("groupId") for level in levels]
    raw_group_names = [level.get("groupName") for level in levels]
    if any(not isinstance(value, str) for value in raw_group_ids):
        fail(f"{filename}: all records must share one non-empty groupId.")
    if any(not isinstance(value, str) for value in raw_group_names):
        fail(f"{filename}: all records must share one non-empty groupName.")
    group_ids = set(raw_group_ids)
    group_names = {value.strip() for value in raw_group_names}
    if len(group_ids) != 1 or not next(iter(group_ids)).strip():
        fail(f"{filename}: all records must share one non-empty groupId.")
    if len(group_names) != 1 or not next(iter(group_names)):
        fail(f"{filename}: all records must share one non-empty groupName.")
    group_id = next(iter(group_ids))
    if group_id in known_groups:
        fail(f"{filename}: {group_id} already exists in the published manifest.")

    staged = []
    for level in levels:
        if not isinstance(level, dict):
            fail(f"{filename}: each level record must be a JSON object.")
        level_id = level.get("id")
        if not isinstance(level_id, str) or not level_id.strip():
            fail(f"{filename}: every level needs a non-empty id.")
        if level_id in known_ids:
            fail(f"{filename}: duplicate level id {level_id}.")
        diffs = level.get("diffs")
        if not isinstance(diffs, list) or not 3 <= len(diffs) <= 8:
            fail(f"{filename}: {level_id} must contain between 3 and 8 differences.")
        for diff in diffs:
            if not isinstance(diff, dict):
                fail(f"{filename}: each difference in {level_id} must be an object.")
            if not all(isinstance(diff.get(key), (int, float)) and
                       not isinstance(diff.get(key), bool)
                       for key in ("x", "y", "r")):
                fail(f"{filename}: each difference in {level_id} needs numeric x, y and r.")
            if not (0 <= diff["x"] <= 1 and 0 <= diff["y"] <= 1 and diff["r"] > 0):
                fail(f"{filename}: difference coordinates in {level_id} are out of range.")
            if not isinstance(diff.get("hint"), str) or not diff["hint"].strip():
                fail(f"{filename}: each difference in {level_id} needs a text hint.")

        normalized = dict(level)
        normalized["groupId"] = group_id
        normalized["groupName"] = next(iter(group_names))
        for key in ("a", "b"):
            path = normalized.get(key)
            if not isinstance(path, str):
                fail(f"{filename}: {level_id} needs image path {key}.")
            path = safe_zip_member(path)
            if not path.startswith(group_id + "/"):
                fail(f"{filename}: image path {path} must be inside {group_id}/.")
            if path not in files:
                fail(f"{filename}: image file {path} is missing from the ZIP.")
            normalized[key] = path
            staged.append((path, files[path]))
        known_ids.add(level_id)

    return group_id, [dict(level) for level in levels], staged


def main() -> int:
    UPLOADS.mkdir(exist_ok=True)
    if not MANIFEST.exists():
        fail("Repository root levels.json was not found.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    existing_levels = manifest.get("levels")
    if not isinstance(existing_levels, list):
        fail("Repository root levels.json must contain a levels array.")
    known_ids = {level["id"] for level in existing_levels}
    known_groups = {level.get("groupId", "group-001") for level in existing_levels}
    processed = json.loads(IMPORTED.read_text(encoding="utf-8")) if IMPORTED.exists() else {}
    if not isinstance(processed, dict):
        fail(".imported-packs.json must be a JSON object.")
    controls = json.loads(CONTROLS.read_text(encoding="utf-8")) if CONTROLS.exists() else {
        "version": 1, "disabledGroups": [], "deletedGroups": []
    }
    if not isinstance(controls, dict):
        fail("case-controls.json must be a JSON object.")

    archives = sorted(UPLOADS.glob("*.zip"))
    if not archives:
        print("No ZIP files found in uploads/.")
        return 0

    imported_count = 0
    for archive_path in archives:
        digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        previous_import = processed.get(digest)
        previous_group = (previous_import.get("groupId")
                          if isinstance(previous_import, dict) else None)
        if digest in processed and previous_group in known_groups:
            print(f"Already imported: {archive_path.name}")
            archive_path.unlink()
            continue
        with zipfile.ZipFile(archive_path) as archive:
            group_id, source_levels, staged = validate_pack(
                archive, archive_path.name, known_ids, known_groups)
            for relative_path, info in staged:
                target = ROOT.joinpath(*PurePosixPath(relative_path).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))

        group_name = source_levels[0]["groupName"].strip()
        for level in source_levels:
            level["groupId"] = group_id
            level["groupName"] = group_name
        manifest["levels"].extend(source_levels)
        manifest["version"] = int(manifest.get("version", 0)) + 1
        processed[digest] = {"file": archive_path.name, "groupId": group_id}
        archive_path.unlink()
        controls["disabledGroups"] = [
            item for item in controls.get("disabledGroups", []) if item != group_id
        ]
        controls["deletedGroups"] = [
            item for item in controls.get("deletedGroups", []) if item != group_id
        ]
        controls["version"] = int(controls.get("version", 0)) + 1
        known_groups.add(group_id)
        imported_count += 1
        print(f"Imported {archive_path.name}: {group_name} ({group_id})")

    if imported_count:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        IMPORTED.write_text(json.dumps(processed, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        CONTROLS.write_text(json.dumps(controls, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print(f"Imported {imported_count} new case pack(s).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"Case ZIP import failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
