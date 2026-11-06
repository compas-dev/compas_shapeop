"""Verify the exact contents required of a COMPAS ShapeOp wheel."""

import argparse
import re
import zipfile
from email.parser import Parser
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()

    filename_parts = args.wheel.name.removesuffix(".whl").split("-")
    if len(filename_parts) != 5:
        raise SystemExit(f"Wheel filename does not have five tag fields: {args.wheel.name}")
    distribution, version, python_tag, abi_tag, platform_tag = filename_parts
    if distribution != "compas_shapeop" or python_tag != "cp312" or abi_tag != "abi3" or not platform_tag:
        raise SystemExit(f"Wheel filename is not compas_shapeop-*-cp312-abi3-*: {args.wheel.name}")

    with zipfile.ZipFile(args.wheel) as archive:
        names = set(archive.namelist())

        wheel_metadata_files = [name for name in names if name.endswith(".dist-info/WHEEL")]
        package_metadata_files = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(wheel_metadata_files) != 1 or len(package_metadata_files) != 1:
            raise SystemExit("Wheel must contain exactly one WHEEL file and one METADATA file")

        wheel_metadata = Parser().parsestr(archive.read(wheel_metadata_files[0]).decode())
        tags = wheel_metadata.get_all("Tag", [])
        expected_tag_prefix = f"{python_tag}-{abi_tag}-"
        if not tags or any(not tag.startswith(expected_tag_prefix) for tag in tags):
            raise SystemExit(f"WHEEL tags must all match {expected_tag_prefix}*: {tags}")

        package_metadata = Parser().parsestr(archive.read(package_metadata_files[0]).decode())

    if package_metadata.get("Name") != "compas_shapeop" or package_metadata.get("Version") != version:
        raise SystemExit("METADATA name and version must match the wheel filename")
    if package_metadata.get("Requires-Python") != ">=3.12":
        raise SystemExit("METADATA Requires-Python must be >=3.12")

    requires_dist = package_metadata.get_all("Requires-Dist", [])
    requirements: dict[str, str] = {}
    for requirement in requires_dist:
        match = re.match(r"[A-Za-z0-9_.-]+", requirement)
        if match:
            requirements[match.group().lower().replace("_", "-")] = requirement.replace(" ", "")
    if "compas" not in requirements or ">=3" not in requirements["compas"] or "<4" not in requirements["compas"]:
        raise SystemExit(f"METADATA must require compas>=3,<4: {requires_dist}")
    if "numpy" not in requirements or ">=1.26" not in requirements["numpy"]:
        raise SystemExit(f"METADATA must require numpy>=1.26: {requires_dist}")

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
