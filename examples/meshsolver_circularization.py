from compas_viewer import Viewer

from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Circle
from compas_shapeop.meshsolver import MeshSolver

mesh = Mesh.from_meshgrid(10, 8, 10, 8)
mesh.translate([-5, -5, 0])

s = MeshSolver(mesh)
s.fix_vertices(vertices=mesh.vertices_where({"vertex_degree": 2}), weight=1e4)
s.constrain_edge_lengths(weight=1)
s.constrain_face_planarity(type="circle", weight=1e2)
s.add_gravity(0.03)
s.solve(1000)

viewer = Viewer()
viewer.scene.add(s.mesh)
for f in s.mesh.faces():
    circle = Circle.from_points(s.mesh.vertices_attributes(keys=s.mesh.face_vertices(f), names="xyz"))
    viewer.scene.add(circle, linecolor=Color.red(), u=32)
viewer.show()
