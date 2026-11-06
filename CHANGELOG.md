# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

* Stable-ABI native wheels for Python 3.12 through 3.14.
* Typed-package marker and private native binding stub.
* Strict MkDocs documentation and numerical solver regression tests.

### Changed

* Raised the minimum Python version to 3.12 and adopted locked `uv` development workflows.
* Made native dependencies reproducible with checksum-verified Eigen 3.4.0 and explicit bundled ShapeOp notices.
* Modernized CMake target configuration and disabled optional OpenMP by default.

### Removed

* Removed the obsolete Sphinx and requirements-file development configuration.


## [0.1.2] 2025-05-09

### Added

* Added MeshSolver class.
* Added documentation for cibuildwheel.

### Changed

* Fix circular Solver import.
* Fix build.yml to match release.yml.
* Fix license files.

### Removed


## [0.1.1] 2025-05-09

### Added

* Implemented zero-copy integration between Python (NumPy) and C++ (Eigen/ShapeOp).
* Constraints: ClosenessConstraint (with target position variant), EdgeStrainConstraint, ShrinkingEdgeConstraint, CircleConstraint, PlaneConstraint, BendingConstraint, SimilarityConstraint, RegularPolygonConstraint, ShapeConstraint
* Forces: VertexForce, NormalForce, GravityForce

### Changed

### Removed
