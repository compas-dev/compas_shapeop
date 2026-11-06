# Development

The repository uses a locked `uv` environment. The Invoke tasks are thin aliases
for the canonical tools and do not add hidden policy.

```bash
uv sync --all-groups
uv run invoke format --check
uv run invoke lint
uv run invoke typecheck
uv run invoke test
uv run invoke docs
```

The source distribution contains the complete vendored ShapeOp source and its
license. Eigen is downloaded into the build tree from the versioned archive and
verified before extraction. Generated test artifacts must use pytest temporary
directories rather than the repository.

Building the native extension requires CMake 3.26 or newer. This minimum is
declared consistently in `CMakeLists.txt`, the locked build dependency group,
and the scikit-build-core configuration because stable-ABI builds require
CMake's `Development.SABIModule` component.
