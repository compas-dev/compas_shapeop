import pathlib

from compas_viewer import Viewer

from compas.data import json_load
from compas.datastructures import Mesh
from compas_shapeop.meshsolver import MeshSolver

mesh = json_load(pathlib.Path(__file__).parent.parent / "data/hex_mesh.json")
mesh = Mesh.from_polygons(mesh.to_polygons())
mesh.weld()
mesh.scale(8.5)
mesh.translate([-16.5, -18, -1])
mesh.rotate(-3.14 / 2)

s = MeshSolver(mesh)
s.fix_vertices(vertices=mesh.vertices_on_boundary())
s.constrain_edge_lengths()
s.constrain_face_planarity(type="plane")
s.constrain_face_regularization()

viewer = Viewer()
mesh_obj = viewer.scene.add(s.mesh)


@viewer.on(interval=1)
def update(frame: int) -> None:
    s.solve(1)
    mesh_obj.update(update_data=True)


viewer.show()
