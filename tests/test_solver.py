import math

import numpy as np
import pytest

from compas_shapeop.shapeop import Solver


def solve_target_problem() -> np.ndarray:
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    solver = Solver()
    solver.points = points
    solver.add_closeness_constraint(0, weight=1e5)
    solver.add_closeness_constraint_with_position(2, 1e5, 2.0, 1.0, 0.0)
    solver.add_edge_strain_constraint(0, 1, weight=1.0, min_range=0.9, max_range=1.1)
    solver.add_edge_strain_constraint(1, 2, weight=1.0, min_range=0.9, max_range=1.1)
    solver.init()
    solver.solve(50)
    result = solver.points
    assert result is not None
    return result.copy()


def test_points_require_n_by_three_shape():
    solver = Solver()

    with pytest.raises(ValueError, match=r"shape \(n, 3\)"):
        solver.points = np.zeros((3, 2))


def test_first_constraint_reports_success():
    solver = Solver()
    solver.points = np.array([[0.0, 0.0, 0.0]])

    assert solver.add_closeness_constraint(0)


def test_points_reassignment_resets_solver_and_preserves_exported_view():
    solver = Solver()
    solver.points = np.array([[0.0, 0.0, 0.0]])
    solver.add_closeness_constraint(0)
    solver.init()
    previous = solver.points
    assert previous is not None
    snapshot = previous.copy()

    solver.points = np.array([[1.0, 2.0, 3.0], [2.0, 2.0, 3.0]])

    assert solver.points is None
    assert not solver.is_initialized
    np.testing.assert_array_equal(previous, snapshot)

    solver.add_closeness_constraint(0)
    solver.add_closeness_constraint(1)
    solver.init()

    current = solver.points
    assert current is not None
    np.testing.assert_array_equal(current, [[1.0, 2.0, 3.0], [2.0, 2.0, 3.0]])
    assert not np.shares_memory(previous, current)


def test_shape_constraints_are_bound_and_solve():
    points = np.array([[0.0, 0.0, 0.0], [1.1, 0.0, 0.0], [1.0, 0.8, 0.0], [0.0, 1.0, 0.0]])

    for shape_type, custom_points in [
        ("regular_polygon", None),
        ("similarity", None),
        ("custom", [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]]),
    ]:
        solver = Solver()
        solver.points = points
        for index in range(len(points)):
            solver.add_closeness_constraint(index, weight=1.0)
        assert solver.add_shape_constraint([0, 1, 2, 3], shape_type=shape_type, custom_points=custom_points)
        solver.init()
        solver.solve(5)
        result = solver.points
        assert result is not None
        assert np.isfinite(result).all()


def test_shrink_factor_is_target_length_ratio():
    solver = Solver()
    solver.points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    solver.add_closeness_constraint(0, weight=1e5)
    solver.add_shrinking_edge_constraint(0, 1, weight=1e5, shrink_factor=0.25)
    solver.init()
    solver.solve(50)

    result = solver.points
    assert result is not None
    delta = result[1] - result[0]
    length_ratio = math.sqrt(sum(float(coordinate) ** 2 for coordinate in delta))
    assert 0.20 <= length_ratio <= 0.30 + 1e-12


def test_constraints_produce_finite_output_near_target():
    result = solve_target_problem()

    assert result.shape == (3, 3)
    assert np.isfinite(result).all()
    assert np.linalg.norm(result[2] - np.array([2.0, 1.0, 0.0])) < 1e-3
    assert np.linalg.norm(result[0]) < 1e-3


def test_solver_is_repeatable():
    first = solve_target_problem()
    second = solve_target_problem()

    np.testing.assert_allclose(first, second, rtol=0.0, atol=1e-12)


def test_dynamic_force_changes_points_and_remains_finite():
    solver = Solver()
    solver.points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    solver.add_closeness_constraint(0, weight=1e5)
    solver.add_vertex_force(2, force_z=0.01)
    solver.init(dynamic=True, damping=0.99, timestep=0.1)
    result = solver.points
    assert result is not None
    before = result.copy()

    solver.solve(20)

    assert np.isfinite(result).all()
    assert not np.array_equal(before, result)
