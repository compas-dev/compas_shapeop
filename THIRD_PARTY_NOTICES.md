# Third-party notices

## ShapeOp

This distribution includes a vendored snapshot of the ShapeOp C++ sources in
`src/shapeop`. The core sources correspond to revision
`7aca78b65efa00282e004f017e07f9b5338f38ef` of the
[ShapeOp source mirror](https://github.com/jeske/ShapeOp). The vendored
`Solver.h` exposes the solver point matrix to the Python binding, and the tree
adds local normal-force and standalone-example sources. The snapshot entered
this repository in commit `85976509bb56e59641bcb089f667222e2238c7ca`.

ShapeOp is distributed under the Mozilla Public License 2.0; see
`LICENSE.shapeop`. The complete corresponding source, including local changes,
is included in the source distribution and published repository.

## Eigen

The build downloads Eigen 3.4.0 from the immutable version archive
<https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz> and verifies
SHA-256 `8586084f71f9bde545ee7fa6d00288b264a2b7ac3607b974e54d13e7162c1c72`.
Eigen is licensed under MPL-2.0 and other compatible licenses documented by the
Eigen project. Eigen is used only while building and is not copied into the
Python package as a source tree.
