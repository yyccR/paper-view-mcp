"""Validate the version embedded in a tagged Paper View plugin release."""

import argparse
import json
import re
from pathlib import Path


MANIFEST = Path(__file__).resolve().parents[1] / "plugins/paper-view/.codex-plugin/plugin.json"
STABLE_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Git tag being published, such as v0.4.3")
    args = parser.parse_args()

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        version = manifest["version"]
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Cannot read plugin version: {exc}\n")

    if not isinstance(version, str) or not STABLE_VERSION.fullmatch(version):
        parser.exit(1, f"Plugin version must be a stable X.Y.Z release: {version!r}\n")
    if args.tag is not None and args.tag != f"v{version}":
        parser.exit(1, f"Release tag {args.tag!r} does not match plugin version {version!r}\n")

    print(f"Paper View plugin {version}" + (f" ({args.tag})" if args.tag else ""))


if __name__ == "__main__":
    main()
