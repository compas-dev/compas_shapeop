import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
VERIFIER = ROOT / ".github" / "scripts" / "verify_wheel.py"


def make_wheel(
    tmp_path: Path,
    *,
    platform_tag: str = "macosx_11_0_arm64",
    wheel_tags: tuple[str, ...] | None = None,
    requires_python: str = ">=3.12",
    requires_numpy: bool = True,
) -> Path:
    wheel = tmp_path / f"compas_shapeop-0.1.2-cp312-abi3-{platform_tag}.whl"
    dist_info = "compas_shapeop-0.1.2.dist-info"
    wheel_tags = wheel_tags or tuple(f"cp312-abi3-{platform}" for platform in platform_tag.split("."))
    wheel_tag_headers = "".join(f"Tag: {tag}\n" for tag in wheel_tags)
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
            f"Wheel-Version: 1.0\nRoot-Is-Purelib: false\n{wheel_tag_headers}",
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
    result = run_verifier(make_wheel(tmp_path, wheel_tags=("cp313-abi3-macosx_11_0_arm64",)))

    assert result.returncode != 0
    assert "tag set" in result.stderr


def test_wheel_verifier_rejects_platform_tag_mismatch(tmp_path: Path):
    result = run_verifier(make_wheel(tmp_path, wheel_tags=("cp312-abi3-manylinux_2_28_x86_64",)))

    assert result.returncode != 0
    assert "tag set" in result.stderr


def test_wheel_verifier_accepts_compressed_platform_tags(tmp_path: Path):
    platform_tag = "manylinux_2_27_x86_64.manylinux_2_28_x86_64"

    result = run_verifier(make_wheel(tmp_path, platform_tag=platform_tag))

    assert result.returncode == 0, result.stderr


def test_wheel_verifier_rejects_missing_compressed_tag(tmp_path: Path):
    platform_tag = "manylinux_2_27_x86_64.manylinux_2_28_x86_64"
    result = run_verifier(
        make_wheel(
            tmp_path,
            platform_tag=platform_tag,
            wheel_tags=("cp312-abi3-manylinux_2_28_x86_64",),
        )
    )

    assert result.returncode != 0
    assert "missing=" in result.stderr


def test_wheel_verifier_rejects_extra_tag(tmp_path: Path):
    result = run_verifier(
        make_wheel(
            tmp_path,
            wheel_tags=(
                "cp312-abi3-macosx_11_0_arm64",
                "cp312-abi3-macosx_12_0_arm64",
            ),
        )
    )

    assert result.returncode != 0
    assert "extra=" in result.stderr


def test_wheel_verifier_rejects_any_platform_for_native_wheel(tmp_path: Path):
    result = run_verifier(make_wheel(tmp_path, platform_tag="any"))

    assert result.returncode != 0
    assert "must not be 'any'" in result.stderr


def test_wheel_verifier_rejects_incorrect_filename_tag(tmp_path: Path):
    wheel = make_wheel(tmp_path)
    incorrect = wheel.with_name("compas_shapeop-0.1.2-cp313-abi3-macosx_11_0_arm64.whl")
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
