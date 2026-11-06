from collections.abc import Iterable
from collections.abc import Sequence
from os import PathLike
from typing import Literal

from compas.datastructures import Mesh
from compas.geometry import Transformation
from compas.typing import PointLike

from .shapeop import Solver


class MeshSolver(Solver):
    """Create a solver from a COMPAS mesh.

    This is a convenience method that allows you to initialize a solver
    directly from a COMPAS mesh.

    Attributes
    ----------
    mesh : Mesh
        A COMPAS mesh.
    points : numpy.ndarray
        Direct reference to the solver's points matrix in shape (n, 3).
    """

    def __init__(self, mesh: Mesh) -> None:
        super().__init__()
        self.mesh: Mesh = mesh
        self._vertex_keys = list(mesh.vertices())
        self._vertex_index = {vertex: index for index, vertex in enumerate(self._vertex_keys)}
        self.points = [mesh.vertex_coordinates(vertex) for vertex in self._vertex_keys]

    def _solver_index(self, vertex: int) -> int:
        """Return the dense native index for a mesh vertex key."""
        return self._vertex_index[vertex]

    def _solver_indices(self, vertices: Iterable[int]) -> list[int]:
        """Return dense native indices for mesh vertex keys."""
        return [self._solver_index(vertex) for vertex in vertices]

    def solve(self, iterations: int = 10) -> None:
        """Solve the constraint problem.

        Parameters
        ----------
        iterations : int, optional
            Number of iterations to run. Default is 10.
        """

        # Intialize the solver, this is needed after you add points, contraints and forces
        if not self.is_initialized:
            self.init()
            self.is_initialized = True

        # Run the solver.
        self._solver.solve(iterations)

        # Update the mesh.
        assert self.points is not None
        for i, vertex in enumerate(self._vertex_keys):
            self.mesh.vertex_attributes(vertex, "xyz", self.points[i])

    @classmethod
    def from_grid(cls, dx: float, nx: int, dy: float, ny: int) -> "MeshSolver":
        """Create a MeshSolver from a rectangular grid mesh.

        Parameters
        ----------
        dx : float
            Size of a grid cell in the x direction.
        nx : int
            Number of grid cells in the x direction.
        dy : float
            Size of a grid cell in the y direction.
        ny : int
            Number of grid cells in the y direction.

        Returns
        -------
        MeshSolver
            A new mesh solver instance.
        """
        mesh: Mesh = Mesh.from_meshgrid(dx, nx, dy, ny).translated([dy * -0.5, dx * -0.5, 0])
        ms: "MeshSolver" = cls(mesh)
        return ms

    @classmethod
    def from_obj(cls, obj: str | PathLike[str], transformation: Transformation | None = None) -> "MeshSolver":
        """Create a MeshSolver from an OBJ file.

        Parameters
        ----------
        obj : str
            Path to the OBJ file.
        transformation : Transformation, optional
            Transformation to apply to the mesh after loading.

        Returns
        -------
        MeshSolver
            A new mesh solver instance.
        """
        mesh: Mesh = Mesh.from_obj(obj)
        if transformation:
            mesh.transform(transformation)
        ms: "MeshSolver" = cls(mesh)
        return ms

    def constrain_edge_lengths(
        self, min_range: float = 0.99, max_range: float = 1.01, shrink_factor: float = 0, exclude_edges: Sequence[tuple[int, int]] | None = None, weight: float = 1e1
    ) -> list[bool]:
        """Add edge length constraints to all edges of a COMPAS mesh.

        Parameters
        ----------
        min_range : float, optional
            Minimum allowed relative length. Default is 0.9.
        max_range : float, optional
            Maximum allowed relative length. Default is 1.1.
        shrink_factor : float, optional
            Target length as a ratio of the original length. The accepted range
            is `shrink_factor - 0.05` to `shrink_factor + 0.05`. A value of
            `0` disables shrinking and uses `min_range` and `max_range`.
        exclude_edges : list, optional
            List of edges to exclude from constraints. Default is None.
        weight : float, optional
            Weight of the constraints. Default is 1.0.

        Returns
        -------
        list[bool]
            Native wrapper statuses for the constraint operations.
        """
        exclude_edges = exclude_edges or []
        constraint_ids: list[bool] = []

        for u, v in self.mesh.edges():
            if (u, v) not in exclude_edges and (v, u) not in exclude_edges:
                if shrink_factor > 0:
                    cid = self.add_shrinking_edge_constraint(self._solver_index(u), self._solver_index(v), weight, shrink_factor)
                    constraint_ids.append(cid)
                else:
                    cid = self.add_edge_strain_constraint(self._solver_index(u), self._solver_index(v), weight, min_range, max_range)
                    constraint_ids.append(cid)

        return constraint_ids

    def constrain_face_diagonals(self, min_range: float = 0.99, max_range: float = 1.01, weight: float = 1e1) -> list[bool]:
        """Add diagonal constraints to quads to prevent shearing.

        Parameters
        ----------
        min_range : float, optional
            Minimum allowed relative length. Default is 0.9.
        max_range : float, optional
            Maximum allowed relative length. Default is 1.1.
        weight : float, optional
            Weight of the constraints. Default is 1.0.

        Returns
        -------
        list[bool]
            Native wrapper statuses for the constraint operations.
        """
        constraint_ids: list[bool] = []
        for fkey in self.mesh.faces():
            vertices = self.mesh.face_vertices(fkey)
            if len(vertices) == 4:  # Only apply to quads
                cid = self.add_edge_strain_constraint(self._solver_index(vertices[0]), self._solver_index(vertices[2]), weight, min_range, max_range)
                constraint_ids.append(cid)
                cid = self.add_edge_strain_constraint(self._solver_index(vertices[1]), self._solver_index(vertices[3]), weight, min_range, max_range)
                constraint_ids.append(cid)
        return constraint_ids

    def constrain_face_planarity(self, type: Literal["plane", "circle"] = "plane", weight: float = 1e5) -> list[bool]:
        """Add plane constraints to all faces of a COMPAS mesh.

        Parameters
        ----------
        type : str, optional
            "plane" or "circle". Default is "plane".
        weight : float, optional
            Weight of the constraints. Default is 1e5.

        Returns
        -------
        list[bool]
            Native wrapper statuses for the constraint operations.
        """

        constraint_ids: list[bool] = []
        for fkey in self.mesh.faces():
            face_vertices = list(self.mesh.face_vertices(fkey))
            solver_vertices = self._solver_indices(face_vertices)
            if type == "plane":
                cid = self.add_plane_constraint(solver_vertices, weight)
            elif type == "circle":
                cid = self.add_circle_constraint(solver_vertices, weight)
            constraint_ids.append(cid)
        return constraint_ids

    def constrain_face_regularization(self, weight: float = 1e3) -> list[bool]:
        """Add equalize face constraints to all faces of a COMPAS mesh.

        Parameters
        ----------
        weight : float, optional
            Weight of the constraints. Default is 1e5.

        Returns
        -------
        list[bool]
            Native wrapper statuses for the constraint operations.
        """
        constraint_ids: list[bool] = []
        for fkey in self.mesh.faces():
            face_vertices = self.mesh.face_vertices(fkey)
            if len(face_vertices) > 3:  # Only apply to non-triangular faces
                cid = self.add_regular_polygon_constraint(self._solver_indices(face_vertices), weight)
                constraint_ids.append(cid)
        return constraint_ids

    def constrain_triface_bending(self, weight: float = 1.0, min_range: float = 1.0, max_range: float = 1.0) -> list[bool]:
        """Add bending constraints to all pairs of adjacent triangular faces in a COMPAS mesh.

        Parameters
        ----------
        weight : float, optional
            Weight of the constraints. Default is 1.0.
        min_range : float, optional
            Minimum bend factor. Default is 1.0.
        max_range : float, optional
            Maximum bend factor. Default is 1.0.

        Returns
        -------
        list[bool]
            Native wrapper statuses for the constraint operations.
        """
        constraint_ids: list[bool] = []
        for edge in self.mesh.edges():
            u: int = edge[0]
            v: int = edge[1]

            # connected faces
            faces = list(self.mesh.edge_faces(edge))
            if faces[0] is None or faces[1] is None:
                continue

            # Get vertices for both faces
            face1_vertices = self.mesh.face_vertices(faces[0])
            face2_vertices = self.mesh.face_vertices(faces[1])

            # Find vertices that are not part of the shared edge
            id2: int | None = None
            for vertex in face1_vertices:
                if vertex != u and vertex != v:
                    id2 = vertex
                    break

            id3: int | None = None
            for vertex in face2_vertices:
                if vertex != u and vertex != v:
                    id3 = vertex
                    break

            # Now we need to order them as [id2, id0, id1, id3]
            # where id0-id1is the shared edge
            if id2 is not None and id3 is not None:
                constraint_ids.append(self.add_bending_constraint(self._solver_indices([u, v, id2, id3]), weight, min_range, max_range))

        return constraint_ids

    def fix_vertices(self, vertices: Iterable[int] | None = None, targets: list[PointLike] | None = None, weight: float = 1e5) -> list[bool]:
        """Add closeness constraints to vertices of a COMPAS mesh.

        Parameters
        ----------
        vertices : list[int], optional
            List of vertices to constrain. If None, all vertices will be constrained.
        targets : list[[float, float, float]], optional
            Target positions for the vertices. Must match length of vertices if provided.
        weight : float, optional
            Weight of the constraints. Default is 1e5.

        Returns
        -------
        list[bool]
            Native wrapper statuses for the constraint operations.
        """
        constraint_ids: list[bool] = []

        if vertices is None:
            vertex_list = list(self.mesh.vertices())
        else:
            vertex_list = list(vertices)

        for idx, v in enumerate(vertex_list):
            target = targets[idx] if isinstance(targets, list) and len(targets) == len(vertex_list) else None
            cid = self.fix_vertex(v, target, weight)
            if cid is not None:
                constraint_ids.append(cid)

        return constraint_ids

    def fix_vertex(self, vertex: int | None = None, target: PointLike | None = None, weight: float = 1e5) -> bool | None:
        """Add closeness constraints to all vertices of a COMPAS mesh to the boundary edges.
        Valence of the vertices allows to select the corners.

        Parameters
        ----------
        vertex : int, optional
            Vertex to constrain. Default is None.
        target : [float, float, float], optional
            Target position for the vertex. Default is None.
        weight : float, optional
            Weight of the constraints. Default is 1e5.

        Returns
        -------
        bool or None
            Native wrapper status, or `None` when no vertex is provided.
        """

        if isinstance(vertex, int):
            solver_index = self._solver_index(vertex)
            if target is not None:
                cid = self.add_closeness_constraint_with_position(solver_index, weight, target[0], target[1], target[2])
                return cid
            else:
                cid = self.add_closeness_constraint(solver_index, weight)
                return cid

        return None

    def add_gravity(self, fz: float = 0.01) -> bool:
        """Add gravity to the mesh.

        Parameters
        ----------
        fz : float, optional
            Z component of the gravity force vector. Default is -0.001.

        Returns
        -------
        bool
            Native wrapper status for the force operation.
        """
        return self._solver.add_gravity_force(0, 0, fz)

    def inflate(self, weight: float = 1e1) -> None:
        """Add inflation force to the mesh.

        Parameters
        ----------
        weight : float, optional
            Weight of the force. Default is 1e5.

        Returns
        -------
        None
            The force is added in place.
        """
        faces_flat: list[int] = []
        face_sizes: list[int] = []
        for face in self.mesh.faces():
            face_vertices = self._solver_indices(self.mesh.face_vertices(face))
            face_size = len(face_vertices)
            face_sizes.append(face_size)
            faces_flat.extend(face_vertices)

        self.add_normal_force_with_faces(faces_flat, face_sizes, weight)
