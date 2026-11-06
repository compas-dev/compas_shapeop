# COMPAS ShapeOp

COMPAS ShapeOp provides Python bindings and COMPAS-oriented convenience APIs
for the [ShapeOp](https://www.shapeop.org/) geometry-processing solver.

The supported public entry points are:

- [`compas_shapeop.shapeop.Solver`][compas_shapeop.shapeop.Solver] for arrays of
  point coordinates.
- [`compas_shapeop.meshsolver.MeshSolver`][compas_shapeop.meshsolver.MeshSolver]
  for COMPAS meshes.

The native extension is private. Applications should not import
`compas_shapeop._shapeop` directly.

## Numerical scope

ShapeOp solves weighted geometric constraints iteratively. Results are floating
point approximations whose accuracy depends on constraint weights, iteration
count, input scale, and compatibility between constraints. A successful solve
does not prove that every constraint has been met exactly.
