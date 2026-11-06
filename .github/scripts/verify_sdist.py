"""Verify the exact contents required of a COMPAS ShapeOp source archive."""

import argparse
import tarfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sdist", type=Path)
    args = parser.parse_args()

    with tarfile.open(args.sdist, "r:gz") as archive:
        names = set(archive.getnames())

    def contains(suffix: str) -> bool:
        return any(name.endswith(suffix) for name in names)

    required = (
        "CMakeLists.txt",
        ".github/scripts/verify_docs.py",
        "LICENSE",
        "LICENSE.shapeop",
        "REFERENCES.md",
        "THIRD_PARTY_NOTICES.md",
        "mkdocs.yml",
        "docs/index.md",
        "tests/test_solver.py",
        "src/shapeop/Constraint.cpp",
        "src/shapeop/Solver.cpp",
        "src/shapeop.cpp",
        "src/compas_shapeop/_shapeop.pyi",
        "src/compas_shapeop/py.typed",
    )
    missing = [name for name in required if not contains(name)]
    if missing:
        raise SystemExit(f"Source distribution is missing required files: {missing}")

    forbidden = [name for name in names if "/external/eigen/" in name or "/build/" in name or "/.venv/" in name]
    if forbidden:
        raise SystemExit(f"Source distribution contains generated dependency/build files: {forbidden[:10]}")


if __name__ == "__main__":
    main()
