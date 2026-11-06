# COMPAS ShapeOp

COMPAS ShapeOp provides Python bindings and COMPAS convenience APIs for the
[ShapeOp](https://www.shapeop.org/) geometry-processing solver.

## Installation

COMPAS ShapeOp requires Python 3.12 or newer.

```bash
python -m pip install compas_shapeop
```

## Development

The repository uses a locked `uv` environment and thin Invoke aliases:

```bash
uv sync --all-groups
uv run invoke test
uv run invoke lint
uv run invoke typecheck
uv run invoke docs
```

See the [documentation](https://compas-dev.github.io/compas_shapeop/) for the
tutorial, examples, API reference, numerical limitations, and source-build
requirements. Report problems in the
[issue tracker](https://github.com/compas-dev/compas_shapeop/issues).
