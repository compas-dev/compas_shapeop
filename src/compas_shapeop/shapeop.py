from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike
from numpy.typing import NDArray

from compas.datastructures import Mesh
from compas.typing import RealInput

from ._shapeop import SolverWrapper

type PointsInput = NDArray[np.float64] | Sequence[Sequence[float]]


class Solver:
    """Optimized ShapeOp solver with direct zero-copy access to solver memory.

    This solver uses nanobind's Eigen integration to provide direct zero-copy
    access to the ShapeOp solver's internal memory. This ensures maximum
    performance for dynamic simulations.

    The implementation maintains a direct numpy view into the C++ solver's
    Eigen matrix memory. When the solver modifies point positions, the NumPy
    array is automatically updated without any copying or data conversion.

    Available constraints:
    - Closeness: Keeps vertices close to their original or target positions
    - EdgeStrain: Maintains edge lengths within a specified range
    - ShrinkingEdge: Forces edge lengths to decrease by a specified factor
    - Circle: Makes vertices form a circular shape
    - Plane: Restricts vertices to lie on a plane
    - Bending: Controls the angle between adjacent triangular faces
    - Similarity: Preserves the shape of a group of vertices
    - RegularPolygon: Makes vertices form a regular polygon shape
    - Shape: Unified constraint that can create various shapes (circle, polygon, etc.)

    Available forces:
    - VertexForce: Applies a force to specific vertices
    - NormalForce: Applies a force in the normal direction of mesh faces
    - GravityForce: Applies a uniform force to all vertices (typically downward)

    Attributes
    ----------
    points : numpy.ndarray
        Direct reference to the initialized solver's points matrix in shape
        `(n, 3)`, or `None` before initialization. Assigning new points resets
        the native solver, including its constraints and forces, and requires
        another call to `init()`.
    """

    def __init__(self) -> None:
        """Initialize a new optimized Solver.

        Creates a new SolverWrapper instance that handles direct
        memory sharing between C++ and Python.
        """
        self._solver = SolverWrapper()
        self._points: NDArray[np.float64] | None = None
        self._retired_solvers: list[SolverWrapper] = []
        self.is_initialized: bool = False

    @property
    def points(self) -> NDArray[np.float64] | None:
        return self._points

    @points.setter
    def points(self, points: PointsInput) -> None:
        self._set_points(points)

    def _set_points(self, points: PointsInput) -> None:
        """Set the vertex positions in the solver.

        This method initializes the solver's internal memory with the
        provided points. After setting the points, it establishes a
        direct zero-copy view to the solver's memory.

        Parameters
        ----------
        points : array-like
            Array of 3D points in shape (n, 3).
        """

        # Convert any input to a numpy array first
        if not isinstance(points, np.ndarray):
            # Convert list of points to numpy array
            points_array = np.array(points, dtype=np.float64)
        else:
            points_array = points

        # Make sure array has the right shape (n, 3)
        if not (len(points_array.shape) == 2 and points_array.shape[1] == 3):
            raise ValueError(f"Points must have shape (n, 3), got {points_array.shape}")

        # Convert to (3, n) Fortran-ordered array for efficient transfer to C++
        fortran_points = np.asfortranarray(points_array.T)

        # Point count changes can invalidate constraints, forces, and exported
        # views. A fresh wrapper gives reassignment one explicit lifecycle: add
        # constraints and forces again, then initialize again.
        if self._points is not None:
            self._retired_solvers.append(self._solver)
        self._solver = SolverWrapper()
        self._solver.set_points(fortran_points)
        self._points = None
        self.is_initialized = False

    def init(self, dynamic: bool = False, masses: float = 1.0, damping: float = 1.0, timestep: float = 1.0) -> None:
        """Initialize the solver with simulation parameters.

        Parameters
        ----------
        dynamic : bool, optional
            Whether to use dynamic simulation. Default is False.
        masses : float, optional
            Mass value for dynamic simulation. Default is 1.0.
        damping : float, optional
            Damping factor for dynamic simulation. Default is 1.0.
        timestep : float, optional
            Time step for dynamic simulation. Default is 1.0.
        """
        result: bool = self._solver.initialize(dynamic, masses, damping, timestep)

        # Set up the direct view after initialization when memory is fully prepared
        if result:
            self._points = self._solver.get_points().T
            self.is_initialized = True
        else:
            print("Failed to initialize solver")

    def solve(self, iterations: int = 10) -> None:
        """Solve the constraint problem.

        Parameters
        ----------
        iterations : int, optional
            Number of iterations to run. Default is 10.
        """
        self._solver.solve(iterations)

    # ==========================================================================
    # CONSTRAINTS
    # ==========================================================================

    def add_closeness_constraint(self, index: int, weight: float = 1e5) -> bool:
        """Add a closeness constraint to the solver.

        A closeness constraint tries to keep vertices close to their
        original positions. This directly adds the constraint to the C++ solver.

        Parameters
        ----------
        index : int
            Index of the vertex to constrain.
        weight : float, optional
            Weight of the constraint. Default is 1e5.

        Returns
        -------
        bool
            Native wrapper status for the constraint operation.
        """
        return self._solver.add_closeness_constraint(index, weight)

    def add_closeness_constraints(self, vertices: Sequence[int], weight: float = 1e5) -> list[bool]:
        """Add closeness constraints to multiple vertices.

        Parameters
        ----------
        vertices : list
            List of vertex indices to constrain.
        weight : float, optional
            Weight of the constraints. Default is 1e5.
        """
        constraint_ids: list[bool] = []
        for vertex in vertices:
            constraint_id = self.add_closeness_constraint(vertex, weight)
            constraint_ids.append(constraint_id)
        return constraint_ids

    def add_closeness_constraint_with_position(self, index: int, weight: float, x: RealInput, y: RealInput, z: RealInput) -> bool:
        """Add a closeness constraint at a specific xyz coordinate.

        A closeness constraint that keeps vertices close to a specified target position
        rather than their original positions. This is useful for fixing points in space
        or forcing points to move to specific locations.

        Parameters
        ----------
        index : int
            Vertex index to constrain.
        weight : float
            Weight of the constraint. Higher values make the constraint stronger.
        x : float
            X-coordinate of the target position.
        y : float
            Y-coordinate of the target position.
        z : float
            Z-coordinate of the target position.

        Returns
        -------
        bool
            Native wrapper status for the constraint operation.
        """
        return self._solver.add_closeness_constraint_with_position(index, weight, x, y, z)

    def add_edge_strain_constraint(self, start_vertex: int, end_vertex: int, weight: float = 1.0, min_range: float = 0.9, max_range: float = 1.1) -> bool:
        """Add an edge strain constraint between two specific vertices.

        An edge strain constraint tries to keep the distance between two vertices
        within a specified range relative to the original distance.
        This directly adds the constraint to the C++ solver.

        Parameters
        ----------
        start_vertex : int
            Index of the first vertex.
        end_vertex : int
            Index of the second vertex.
        weight : float, optional
            Weight of the constraint. Higher values make the constraint stronger.
            Default is 1.0.
        min_range : float, optional
            Minimum allowed relative length. Default is 0.9 (90% of original length).
        max_range : float, optional
            Maximum allowed relative length. Default is 1.1 (110% of original length).

        Returns
        -------
        bool
            Native wrapper status for the constraint operation.
        """
        return self._solver.add_edge_strain_constraint(start_vertex, end_vertex, weight, min_range, max_range)

    def add_shrinking_edge_constraint(self, start_vertex: int, end_vertex: int, weight: float = 1.0, shrink_factor: float = 0.25) -> bool:
        """Add a shrinking edge constraint to the solver.

        A shrinking edge constraint tries to shrink the edge length by a specified factor.
        This is particularly useful for cable nets and other structures that need to
        maintain tension. The constraint creates a min/max range of ±5% around the target length.

        Parameters
        ----------
        start_vertex : int
            Index of the first vertex.
        end_vertex : int
            Index of the second vertex.
        weight : float, optional
            Weight of the constraint. Higher values make the constraint stronger.
        shrink_factor : float, optional
            Target length as a ratio of the original length. The accepted range
            is `shrink_factor - 0.05` to `shrink_factor + 0.05`. Default is
            `0.25`.

        Returns
        -------
        bool
            Native wrapper status for the constraint operation.
        """
        return self._solver.add_shrinking_edge_constraint(start_vertex, end_vertex, weight, shrink_factor)

    def add_circle_constraint(self, indices: Sequence[int], weight: float = 1.0) -> bool:
        """Add circle constraint to make vertices lie on a circle.

        Parameters
        ----------
        indices : list
            List of vertex indices.
        weight : float, optional
            Weight of the constraint, by default 1.0

        Returns
        -------
        bool
            True if the constraint was added successfully.
        """
        return self._solver.add_circle_constraint(indices, weight)

    def add_plane_constraint(self, indices: Sequence[int], weight: float = 1.0) -> bool:
        """Add a plane constraint to the solver.

        A plane constraint tries to keep points co-planar.
        This directly adds the constraint to the C++ solver.

        Parameters
        ----------
        indices : list
            List of vertex indices to constrain.
        weight : float, optional
            Weight of the constraint. Higher values make the constraint stronger.

        Returns
        -------
        bool
            Native wrapper status for the constraint operation.
        """
        return self._solver.add_plane_constraint(indices, weight)

    def add_bending_constraint(self, indices: Sequence[int], weight: float = 1.0, min_range: float = 1.0, max_range: float = 1.0) -> bool:
        """Add a bending constraint between two neighboring triangles.

        Parameters
        ----------
        indices : list
            List of 4 vertex indices in the specific order [id2, id0, id1, id3].
        weight : float, optional
            Weight of the constraint. Default is 1.0.
        min_range : float, optional
            Minimum bend factor relative to initial angle. Default is 1.0.
        max_range : float, optional
            Maximum bend factor relative to initial angle. Default is 1.0.

        Returns
        -------
        bool
            Native wrapper status for the constraint operation.
        """
        return self._solver.add_bending_constraint(indices, weight, min_range, max_range)

    def add_similarity_constraint(
        self,
        indices: Sequence[int],
        weight: float = 1.0,
        allow_scaling: bool = True,
        allow_rotation: bool = True,
        allow_translation: bool = True,
    ) -> bool:
        """Add similarity constraint to transform vertices to match a target shape.

        This is a low-level method that creates a similarity constraint. You must
        manually set the target shape using set_similarity_constraint_shape().
        For a higher-level method that automatically creates a regular polygon,
        use add_regular_polygon_constraint().

        Parameters
        ----------
        indices : list
            List of vertex indices.
        weight : float, optional
            Weight of the constraint, by default 1.0
        allow_scaling : bool, optional
            Whether to allow scaling, by default True
        allow_rotation : bool, optional
            Whether to allow rotation, by default True
        allow_translation : bool, optional
            Whether to allow translation, by default True

        Returns
        -------
        bool
            True if the constraint was added successfully.
        """
        return self._solver.add_similarity_constraint(indices, weight, allow_scaling, allow_rotation, allow_translation)

    def add_regular_polygon_constraint(self, indices: Sequence[int], weight: float = 1.0) -> bool:
        """Add constraint to make vertices form a regular polygon.

        This is a high-level method that automatically:
        1. Creates a regular polygon template in the face's plane
        2. Creates a similarity constraint to match the template

        Parameters
        ----------
        indices : list
            List of vertex indices of the polygon face.
        weight : float, optional
            Weight of the constraint, by default 1.0

        Returns
        -------
        bool
            True if the constraint was added successfully.
        """
        return self._solver.add_regular_polygon_constraint(indices, weight)

    def add_normal_force_with_faces(self, faces_flat: ArrayLike, face_sizes: ArrayLike, magnitude: float = 1.0) -> bool:
        """Add a normal force (inflation) using custom face topology.

        This applies forces along face normals, causing inflation or deflation
        depending on the magnitude's sign.

        Parameters
        ----------
        faces_flat : ndarray
            Flattened array of face vertex indices, where consecutive indices
            describe each face.
        face_sizes : ndarray
            Array indicating how many vertices are in each face.
        magnitude : float, optional
            Magnitude of the normal force. Positive values inflate,
            negative values deflate.

        Returns
        -------
        bool
            True if the force was added successfully.
        """

        faces_flat_array = np.asarray(faces_flat, dtype=np.int32)
        face_sizes_array = np.asarray(face_sizes, dtype=np.int32)
        return self._solver.add_normal_force_with_faces(faces_flat_array, face_sizes_array, magnitude)

    def add_vertex_force(self, index: int, force_x: float = 0.0, force_y: float = 0.0, force_z: float = 0.0) -> bool:
        """Add a vertex force to a specific point.

        Parameters
        ----------
        index : int
            Index of the vertex to apply force to.
        force_x : float, optional
            X component of the force vector. Default is 0.0.
        force_y : float, optional
            Y component of the force vector. Default is 0.0.
        force_z : float, optional
            Z component of the force vector. Default is 0.0.

        Returns
        -------
        bool
            Native wrapper status for the force operation.
        """
        return self._solver.add_vertex_force(force_x, force_y, force_z, index)

    def add_gravity_force(self, fx: float = 0.0, fy: float = 0.0, fz: float = -0.001) -> bool:
        """Add a gravity force to all vertices in the system.

        Parameters
        ----------
        fx : float, optional
            X component of the gravity force vector. Default is 0.0.
        fy : float, optional
            Y component of the gravity force vector. Default is 0.0.
        fz : float, optional
            Z component of the gravity force vector. Default is -0.001.

        Returns
        -------
        bool
            Native wrapper status for the force operation.
        """
        return self._solver.add_gravity_force(fx, fy, fz)

    def add_mesh_vertex_force(self, mesh: Mesh, force_x: float = 0.0, force_y: float = 0.0, force_z: float = 0.0, exclude_vertices: Sequence[int] | None = None) -> list[bool]:
        """Add vertex forces to all vertices of a COMPAS mesh.

        Parameters
        ----------
        mesh : Mesh
            The COMPAS mesh to add forces to.
        force_x : float, optional
            X component of the force vector. Default is 0.0.
        force_y : float, optional
            Y component of the force vector. Default is 0.0.
        force_z : float, optional
            Z component of the force vector. Default is 0.0.
        exclude_vertices : list, optional
            List of vertices to exclude from forces. Default is None.

        Returns
        -------
        list[bool]
            Native wrapper statuses for the force operations.
        """
        exclude_vertices = exclude_vertices or []
        force_ids: list[bool] = []

        for index, vertex in enumerate(mesh.vertices()):
            if vertex not in exclude_vertices:
                fid = self.add_vertex_force(index, force_x, force_y, force_z)
                force_ids.append(fid)

        return force_ids

    def add_shape_constraint(
        self,
        indices: Sequence[int],
        shape_type: str = "regular_polygon",
        weight: float = 1.0,
        allow_scaling: bool = True,
        allow_rotation: bool = True,
        allow_translation: bool = True,
        custom_points: Sequence[Sequence[float]] | None = None,
    ) -> bool:
        """Add a unified shape constraint with different shape types.

        This consolidates functionality of add_regular_polygon_constraint,
        add_similarity_constraint, and set_similarity_constraint_shape
        into a single unified method.

        Parameters
        ----------
        indices : list or ndarray
            List of vertex indices.
        shape_type : str, optional
            Type of shape: "regular_polygon", "similarity", or "custom", by default "regular_polygon"
        weight : float, optional
            Weight of the constraint, by default 1.0
        allow_scaling : bool, optional
            Whether to allow scaling transformations, by default True
        allow_rotation : bool, optional
            Whether to allow rotation transformations, by default True
        allow_translation : bool, optional
            Whether to allow translation transformations, by default True
        custom_points : list, optional
            Optional list of 3D points for custom shapes. Required when shape_type="custom".

        Returns
        -------
        bool
            Native wrapper status for the constraint operation.
        """
        if shape_type == "custom" and custom_points is None:
            raise ValueError("custom_points is required when shape_type='custom'")

        points_to_use: Sequence[Sequence[float]] = custom_points if custom_points is not None else ()

        return self._solver.add_shape_constraint(indices, shape_type, weight, allow_scaling, allow_rotation, allow_translation, points_to_use)
