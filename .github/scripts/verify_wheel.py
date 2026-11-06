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
    distribution, version, python_component, abi_component, platform_component = filename_parts
    python_tags = python_component.split(".")
    abi_tags = abi_component.split(".")
    platform_tags = platform_component.split(".")
    if distribution != "compas_shapeop" or set(python_tags) != {"cp312"} or set(abi_tags) != {"abi3"} or not all(platform_tags):
        raise SystemExit(f"Wheel filename is not compas_shapeop-*-cp312-abi3-*: {args.wheel.name}")
    if "any" in platform_tags:
        raise SystemExit("Native wheel filename platform tag must not be 'any'")

    expected_tags = {f"{python_tag}-{abi_tag}-{platform_tag}" for python_tag in python_tags for abi_tag in abi_tags for platform_tag in platform_tags}

    with zipfile.ZipFile(args.wheel) as archive:
        names = set(archive.namelist())

        wheel_metadata_files = [name for name in names if name.endswith(".dist-info/WHEEL")]
        package_metadata_files = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(wheel_metadata_files) != 1 or len(package_metadata_files) != 1:
            raise SystemExit("Wheel must contain exactly one WHEEL file and one METADATA file")

        wheel_metadata = Parser().parsestr(archive.read(wheel_metadata_files[0]).decode())
        tags = set(wheel_metadata.get_all("Tag", []))
        if tags != expected_tags:
            missing = sorted(expected_tags - tags)
            extra = sorted(tags - expected_tags)
            raise SystemExit(f"WHEEL tag set does not match the expanded filename tags; missing={missing}, extra={extra}")

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
    native_extension = native[0]
    windows_platform = all(platform_tag.startswith("win") for platform_tag in platform_tags)
    if native_extension.endswith(".pyd"):
        if not windows_platform:
            raise SystemExit(f"A .pyd native extension requires a Windows wheel platform tag: {native_extension}")
    elif windows_platform:
        raise SystemExit(f"A Windows wheel must contain a .pyd native extension: {native_extension}")
    elif ".abi3" not in native_extension:
        raise SystemExit(f"POSIX native extension does not use an abi3 import suffix: {native_extension}")

    forbidden = [name for name in names if "/shapeop/" in name or "/eigen/" in name or name.startswith("include/eigen3/") or name.startswith("share/pkgconfig/eigen3")]
    if forbidden:
        raise SystemExit(f"Wheel contains native source trees: {forbidden[:10]}")

    license_names = [name.rsplit("/", 1)[-1] for name in names if ".dist-info/licenses/" in name]
    for expected in ("LICENSE", "LICENSE.shapeop", "THIRD_PARTY_NOTICES.md"):
        if expected not in license_names:
            raise SystemExit(f"Wheel is missing {expected} from dist-info/licenses")


if __name__ == "__main__":
    main()
