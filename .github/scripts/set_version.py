#!/usr/bin/env python3

import re
import sys
from pathlib import Path


def replace_or_die(path: Path, pattern: str, repl: str) -> None:
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(pattern, repl, text, flags=re.MULTILINE)
    if n == 0:
        raise SystemExit(f"No matches in {path} for pattern: {pattern}")
    path.write_text(new_text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: set_version.py <version>", file=sys.stderr)
        return 2

    full_version = sys.argv[1].strip()
    if not full_version:
        print("Empty version", file=sys.stderr)
        return 2

    # ufbt requires application.fam fap_version to be strictly "major.minor".
    # We still want a richer version string elsewhere (About screen, release tag).
    match = re.match(r"^(\d+\.\d+)", full_version)
    if not match:
        print(
            f"Invalid version '{full_version}': expected to start with 'major.minor'",
            file=sys.stderr,
        )
        return 2
    fam_version = match.group(1)

    repo_root = Path(__file__).resolve().parents[2]
    app_fam = repo_root / "application.fam"
    radio_c = repo_root / "radio.c"

    # application.fam: fap_version="..."
    replace_or_die(
        app_fam,
        r'^(\s*fap_version\s*=\s*")([^"]+)(",\s*)$',
        rf'\g<1>{fam_version}\g<3>',
    )

    # radio.c header: @version ...
    replace_or_die(
        radio_c,
        r'^(\s*\*\s*@version\s+)(.+)$',
        rf'\g<1>{full_version}',
    )

    # UI/About version macro in radio.c.
    replace_or_die(
        radio_c,
        r'^(\s*#define\s+FRED_FM_UI_VERSION\s+")([^"]+)(")\s*$',
        rf'\g<1>{full_version}\g<3>',
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
