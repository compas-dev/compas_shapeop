"""Exercise only the installed wheel from outside the source tree."""

import numpy as np

from compas_shapeop.shapeop import Solver

solver = Solver()
solver.points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
assert solver.add_closeness_constraint(0)
assert solver.add_closeness_constraint_with_position(1, 1e5, 1.0, 1.0, 0.0)
solver.init()
solver.solve(10)
assert solver.points is not None
assert solver.points.shape == (2, 3)
assert np.isfinite(solver.points).all()
