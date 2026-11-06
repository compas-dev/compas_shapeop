from compas_viewer import Viewer

from compas.datastructures import Mesh
from compas_shapeop.meshsolver import MeshSolver

mesh = Mesh.from_meshgrid(10, 8, 10, 8)
mesh.translate([-5, -5, 0])

s = MeshSolver(mesh)
s.fix_vertices(vertices=mesh.vertices_where({"vertex_degree": 2}))
s.constrain_edge_lengths()
s.add_gravity()
s.solve(1000)

viewer = Viewer()
viewer.scene.add(s.mesh)
viewer.show()
