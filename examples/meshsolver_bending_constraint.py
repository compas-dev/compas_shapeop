from compas_viewer import Viewer

from compas.datastructures import Mesh
from compas_shapeop.meshsolver import MeshSolver

mesh = Mesh.from_meshgrid(10, 8, 10, 8)
mesh.translate([-5, -5, 0])
mesh = mesh.triangulated()

s = MeshSolver(mesh)
s.fix_vertices(vertices=mesh.vertices_where({"vertex_degree": 3}))
s.constrain_edge_lengths()
s.constrain_triface_bending(weight=0.5)
s.add_gravity(0.1)

viewer = Viewer()
mesh_obj = viewer.scene.add(s.mesh)


@viewer.on(interval=1)
def update(frame: int) -> None:
    s.solve(1)
    mesh_obj.update(update_data=True)


viewer.show()
