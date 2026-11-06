"""Verify the exact contents required of a COMPAS ShapeOp wheel."""

import argparse
import zipfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()

    with zipfile.ZipFile(args.wheel) as archive:
        names = set(archive.namelist())

    required_suffixes = {
        "compas_shapeop/py.typed",
        "compas_shapeop/_shapeop.pyi",
    }
    missing = [suffix for suffix in required_suffixes if not any(name.endswith(suffix) for name in names)]
    if missing:
        raise SystemExit(f"Wheel is missing required files: {missing}")

    native = [name for name in names if "compas_shapeop/_shapeop" in name and name.endswith((".so", ".pyd", ".dylib"))]
    if len(native) != 1:
        raise SystemExit(f"Expected exactly one private native extension, found: {native}")
    if ".abi3" not in native[0]:
        raise SystemExit(f"Native extension does not use an abi3 import suffix: {native[0]}")

    forbidden = [name for name in names if "/shapeop/" in name or "/eigen/" in name or name.startswith("include/eigen3/") or name.startswith("share/pkgconfig/eigen3")]
    if forbidden:
        raise SystemExit(f"Wheel contains native source trees: {forbidden[:10]}")

    license_names = [name.rsplit("/", 1)[-1] for name in names if ".dist-info/licenses/" in name]
    for expected in ("LICENSE", "LICENSE.shapeop", "THIRD_PARTY_NOTICES.md"):
        if expected not in license_names:
            raise SystemExit(f"Wheel is missing {expected} from dist-info/licenses")


if __name__ == "__main__":
    main()
