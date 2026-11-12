#!/usr/bin/env python3
"""Disable, re-enable, or delete one published Sharp Eye case group."""

import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "levels.json"
CONTROLS = ROOT / "case-controls.json"
VALID_ACTIONS = {"disable", "enable", "delete"}


def main() -> int:
    if len(sys.argv) != 3:
        raise ValueError("Usage: manage_case.py ACTION GROUP_ID")
    action, group_id = sys.argv[1:]
    if action not in VALID_ACTIONS:
        raise ValueError(f"Action must be one of: {', '.join(sorted(VALID_ACTIONS))}.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", group_id):
        raise ValueError("Group ID contains unsupported characters.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    controls = json.loads(CONTROLS.read_text(encoding="utf-8"))
    levels = manifest.get("levels")
    if not isinstance(levels, list):
        raise ValueError("levels.json must contain a levels array.")
    published_groups = {level.get("groupId", "group-001") for level in levels}
    disabled = set(controls.get("disabledGroups", []))
    deleted = set(controls.get("deletedGroups", []))

    if action in {"disable", "delete"} and group_id not in published_groups:
        raise ValueError(f"Case {group_id} is not in the published manifest.")
    if action == "enable" and group_id in deleted:
        raise ValueError(
            f"Case {group_id} was deleted. Restore it by uploading its case ZIP again."
        )
    if action == "enable" and group_id not in published_groups:
        raise ValueError(f"Case {group_id} is not in the published manifest.")

    if action == "disable":
        disabled.add(group_id)
        deleted.discard(group_id)
        message = f"Disabled {group_id}; its manifest entries and images are retained."
    elif action == "enable":
        disabled.discard(group_id)
        message = f"Enabled {group_id}."
    else:
        manifest["levels"] = [
            level for level in levels
            if level.get("groupId", "group-001") != group_id
        ]
        case_dir = (ROOT / group_id).resolve()
        if case_dir.parent != ROOT.resolve():
            raise ValueError("Resolved case directory is outside the repository root.")
        if case_dir.is_dir():
            shutil.rmtree(case_dir)
        disabled.discard(group_id)
        deleted.add(group_id)
        message = f"Deleted {group_id} from the published manifest and image files."

    controls["disabledGroups"] = sorted(disabled)
    controls["deletedGroups"] = sorted(deleted)
    controls["version"] = int(controls.get("version", 0)) + 1
    manifest["version"] = int(manifest.get("version", 0)) + 1
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    CONTROLS.write_text(
        json.dumps(controls, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(message)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Case management failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
