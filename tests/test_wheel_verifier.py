import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
VERIFIER = ROOT / ".github" / "scripts" / "verify_wheel.py"


def make_wheel(tmp_path: Path, *, tag: str = "cp312-abi3-any", requires_python: str = ">=3.12", requires_numpy: bool = True) -> Path:
    wheel = tmp_path / "compas_shapeop-0.1.2-cp312-abi3-any.whl"
    dist_info = "compas_shapeop-0.1.2.dist-info"
    requires_dist = "Requires-Dist: compas<4,>=3\n"
    if requires_numpy:
        requires_dist += "Requires-Dist: numpy>=1.26\n"

    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("compas_shapeop/py.typed", "")
        archive.writestr("compas_shapeop/_shapeop.pyi", "")
        archive.writestr("compas_shapeop/_shapeop.abi3.so", "")
        archive.writestr(f"{dist_info}/licenses/LICENSE", "")
        archive.writestr(f"{dist_info}/licenses/LICENSE.shapeop", "")
        archive.writestr(f"{dist_info}/licenses/THIRD_PARTY_NOTICES.md", "")
        archive.writestr(
            f"{dist_info}/WHEEL",
            f"Wheel-Version: 1.0\nRoot-Is-Purelib: false\nTag: {tag}\n",
        )
        archive.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.4\nName: compas_shapeop\nVersion: 0.1.2\nRequires-Python: {requires_python}\n{requires_dist}",
        )
    return wheel


def run_verifier(wheel: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), str(wheel)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_wheel_verifier_accepts_expected_contract(tmp_path: Path):
    result = run_verifier(make_wheel(tmp_path))

    assert result.returncode == 0, result.stderr


def test_wheel_verifier_rejects_inconsistent_wheel_tag(tmp_path: Path):
    result = run_verifier(make_wheel(tmp_path, tag="cp313-abi3-any"))

    assert result.returncode != 0
    assert "cp312-abi3" in result.stderr


def test_wheel_verifier_rejects_incorrect_filename_tag(tmp_path: Path):
    wheel = make_wheel(tmp_path)
    incorrect = wheel.with_name("compas_shapeop-0.1.2-cp313-abi3-any.whl")
    wheel.rename(incorrect)

    result = run_verifier(incorrect)

    assert result.returncode != 0
    assert "cp312-abi3" in result.stderr


def test_wheel_verifier_rejects_incorrect_python_requirement(tmp_path: Path):
    result = run_verifier(make_wheel(tmp_path, requires_python=">=3.11"))

    assert result.returncode != 0
    assert "Requires-Python" in result.stderr


def test_wheel_verifier_rejects_missing_runtime_dependency(tmp_path: Path):
    result = run_verifier(make_wheel(tmp_path, requires_numpy=False))

    assert result.returncode != 0
    assert "numpy>=1.26" in result.stderr
