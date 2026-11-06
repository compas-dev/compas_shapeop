from collections.abc import Sequence

import numpy as np

from compas.datastructures import Mesh
from compas_shapeop.meshsolver import MeshSolver


class RecordingMeshSolver(MeshSolver):
    def __init__(self, mesh: Mesh) -> None:
        super().__init__(mesh)
        self.edge_constraints: list[tuple[int, int, float, float, float]] = []
        self.bending_constraints: list[tuple[list[int], float, float, float]] = []

    def add_edge_strain_constraint(
        self,
        start_vertex: int,
        end_vertex: int,
        weight: float = 1.0,
        min_range: float = 0.9,
        max_range: float = 1.1,
    ) -> bool:
        self.edge_constraints.append((start_vertex, end_vertex, weight, min_range, max_range))
        return True

    def add_bending_constraint(
        self,
        indices: Sequence[int],
        weight: float = 1.0,
        min_range: float = 1.0,
        max_range: float = 1.0,
    ) -> bool:
        self.bending_constraints.append((list(indices), weight, min_range, max_range))
        return True


def test_meshsolver_updates_mesh_with_finite_coordinates():
    mesh = Mesh.from_meshgrid(dx=2.0, nx=2, dy=2.0, ny=2)
    solver = MeshSolver(mesh)
    solver.fix_vertices([0, 2, 6, 8])
    solver.constrain_edge_lengths()
    solver.add_gravity(fz=-0.001)

    solver.solve(10)

    coordinates = np.asarray([mesh.vertex_coordinates(vertex) for vertex in mesh.vertices()])
    assert coordinates.shape == (9, 3)
    assert np.isfinite(coordinates).all()


def test_fix_vertex_moves_vertex_near_finite_weight_target():
    mesh = Mesh.from_vertices_and_faces(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        [[0, 1, 2]],
    )
    solver = MeshSolver(mesh)
    target = np.array([0.25, 0.25, 1.0])
    solver.fix_vertex(0, target, weight=1e5)
    solver.constrain_edge_lengths(weight=1.0)

    solver.solve(50)

    result = np.asarray(mesh.vertex_coordinates(0))
    assert np.linalg.norm(result - target) < 1e-3


def test_noncontiguous_mesh_keys_are_mapped_to_dense_solver_indices():
    mesh = Mesh()
    mesh.add_vertex(key=10, x=0.0, y=0.0, z=0.0)
    mesh.add_vertex(key=20, x=1.0, y=0.0, z=0.0)
    mesh.add_vertex(key=30, x=1.0, y=1.0, z=0.1)
    mesh.add_vertex(key=40, x=0.0, y=1.0, z=0.0)
    mesh.add_face([10, 20, 30, 40])
    solver = MeshSolver(mesh)
    solver.fix_vertex(10)
    solver.constrain_edge_lengths()
    solver.constrain_face_diagonals()
    solver.constrain_face_planarity()
    solver.constrain_face_regularization()
    solver.inflate(weight=0.001)

    solver.solve(10)

    coordinates = np.asarray([mesh.vertex_coordinates(vertex) for vertex in mesh.vertices()])
    assert np.isfinite(coordinates).all()


def test_face_diagonal_options_are_forwarded():
    mesh = Mesh()
    mesh.add_vertex(key=10, x=0.0, y=0.0, z=0.0)
    mesh.add_vertex(key=20, x=1.0, y=0.0, z=0.0)
    mesh.add_vertex(key=30, x=1.0, y=1.0, z=0.0)
    mesh.add_vertex(key=40, x=0.0, y=1.0, z=0.0)
    mesh.add_face([10, 20, 30, 40])
    solver = RecordingMeshSolver(mesh)

    statuses = solver.constrain_face_diagonals(min_range=0.8, max_range=1.2, weight=4.0)

    assert statuses == [True, True]
    assert solver.edge_constraints == [
        (0, 2, 4.0, 0.8, 1.2),
        (1, 3, 4.0, 0.8, 1.2),
    ]


def test_nonflat_bending_uses_shared_edge_vertices_first():
    mesh = Mesh()
    mesh.add_vertex(key=10, x=0.0, y=0.0, z=0.0)
    mesh.add_vertex(key=20, x=1.0, y=0.0, z=0.0)
    mesh.add_vertex(key=30, x=0.0, y=1.0, z=0.0)
    mesh.add_vertex(key=40, x=0.0, y=0.0, z=1.0)
    mesh.add_face([10, 20, 30])
    mesh.add_face([20, 10, 40])
    solver = RecordingMeshSolver(mesh)

    statuses = solver.constrain_triface_bending(weight=2.0, min_range=0.8, max_range=1.2)

    assert statuses == [True]
    assert solver.bending_constraints == [([0, 1, 2, 3], 2.0, 0.8, 1.2)]
