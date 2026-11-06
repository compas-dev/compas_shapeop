import numpy as np

from compas.datastructures import Mesh
from compas_shapeop.meshsolver import MeshSolver
from compas_shapeop.shapeop import Solver

solver = Solver()
solver.points = np.zeros((3, 3), dtype=np.float64)
constraint_added: bool = solver.add_plane_constraint([0, 1, 2])
shape_added: bool = solver.add_shape_constraint([0, 1, 2], shape_type="regular_polygon")
initialized: bool = solver.is_initialized

mesh_solver = MeshSolver(Mesh.from_vertices_and_faces(np.zeros((3, 3)), [[0, 1, 2]]))
constraints: list[bool] = mesh_solver.constrain_face_planarity()
