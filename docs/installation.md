# Installation

COMPAS ShapeOp requires Python 3.12 or newer.

```bash
python -m pip install compas_shapeop
```

Binary wheels contain the private native extension and support CPython 3.12,
3.13, and 3.14 through the CPython 3.12 stable ABI. Building from source
requires a C++20 compiler, CMake, and an internet connection to retrieve the
checksum-verified Eigen 3.4.0 archive.

OpenMP is disabled by default. Source builders may opt in with
`-DCOMPAS_SHAPEOP_OPENMP=ON`; CMake then requires a discoverable OpenMP C++
target.

For repository development, synchronize the committed environment and use the
thin Invoke aliases:

```bash
uv sync --all-groups
uv run invoke test
uv run invoke lint
uv run invoke typecheck
uv run invoke docs
```
