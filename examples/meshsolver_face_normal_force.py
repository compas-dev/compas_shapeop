import pathlib

from compas_viewer import Viewer

from compas_shapeop.meshsolver import MeshSolver

s = MeshSolver.from_obj(pathlib.Path(__file__).parent.parent / "data/m0.obj")
s.fix_vertices(weight=0.1)
s.constrain_edge_lengths()
s.inflate(weight=3)

viewer = Viewer()
mesh_obj = viewer.scene.add(s.mesh)


@viewer.on(interval=1)
def update(frame: int) -> None:
    s.solve(1)
    mesh_obj.update(update_data=True)


viewer.show()
