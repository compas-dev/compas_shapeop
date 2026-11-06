from compas_viewer import Viewer

from compas.datastructures import Mesh
from compas.typing import PointLike
from compas_shapeop.meshsolver import MeshSolver

mesh = Mesh.from_meshgrid(10.0, 10, 10.0, 10)
mesh.translate([-5, -5, 0])

v = list(mesh.vertices_where({"vertex_degree": 2}))
p = mesh.vertices_attributes(keys=v, names="xyz")

t: list[PointLike] = [
    [p[0][0], p[0][1], 3],
    [p[1][0], p[1][1], 5],
    [p[2][0], p[2][1], 5],
    [p[3][0], p[3][1], -1],
]

s = MeshSolver(mesh)
s.fix_vertices(vertices=v, targets=t)
s.constrain_edge_lengths(shrink_factor=0.25)
s.solve(100)

viewer = Viewer()
viewer.scene.add(s.mesh)
viewer.show()
