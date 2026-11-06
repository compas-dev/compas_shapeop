# Tutorial

A solve has four steps: provide points, add constraints or forces, initialize
the solver, and iterate. Point input has shape `(n, 3)`. The `points` property
becomes the live result array after initialization.

The wrapper copies point input into the native solver's column-major storage.
After `init()`, `points` is a NumPy view of solver-owned memory and `solve()`
mutates that memory in place. Copy the result when it must outlive the solver or
when a stable before/after comparison is required.

Assigning `points` again resets the native solver and invalidates the solver's
current result property. Existing NumPy result views remain owned by the old
native solver and keep their last values, but new constraints and forces must be
added before calling `init()` again.

```python
--8 < --"docs/examples/solver.py"
```

Constraint weights are relative rather than absolute guarantees. Start with
the smallest set of compatible constraints and check residual distances in the
result when a tolerance matters to the application.
