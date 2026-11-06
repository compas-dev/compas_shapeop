from pathlib import Path

import tomllib


ROOT = Path(__file__).parents[1]
CMAKE_MINIMUM = "3.26"


def test_cmake_minimum_is_consistent():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    cmake_lists = (ROOT / "CMakeLists.txt").read_text()

    assert f"cmake_minimum_required(VERSION {CMAKE_MINIMUM}" in cmake_lists
    assert pyproject["tool"]["scikit-build"]["cmake"]["version"] == f">={CMAKE_MINIMUM}"
    assert f"cmake>={CMAKE_MINIMUM}" in pyproject["dependency-groups"]["build"]


def test_cibuildwheel_uses_pip_frontend():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    cibuildwheel = pyproject["tool"]["cibuildwheel"]

    assert cibuildwheel["build-frontend"] == "pip"
    assert cibuildwheel["test-requires"] == ["numpy>=1.26", "pytest>=8"]
