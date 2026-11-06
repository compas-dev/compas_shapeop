import numpy as np

from compas_shapeop.shapeop import Solver

solver = Solver()
solver.points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
solver.add_closeness_constraint(0, weight=1e5)
solver.add_closeness_constraint_with_position(2, 1e5, 2.0, 1.0, 0.0)
solver.add_edge_strain_constraint(0, 1)
solver.add_edge_strain_constraint(1, 2)
solver.init()
solver.solve(50)

assert solver.points is not None
print(solver.points)
