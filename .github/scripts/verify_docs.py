"""Verify that generated documentation contains the canonical example."""

import argparse
from html.parser import HTMLParser
from pathlib import Path


class TextContentParser(HTMLParser):
    """Collect rendered text from an HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def rendered_text(page: Path) -> str:
    """Return concatenated text nodes from a rendered HTML page."""
    parser = TextContentParser()
    parser.feed(page.read_text())
    return "".join(parser.parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    args = parser.parse_args()

    expected = (
        "solver = Solver()",
        "solver.add_closeness_constraint(0, weight=1e5)",
        "solver.solve(50)",
    )
    pages = (
        args.site / "examples" / "solver" / "index.html",
        args.site / "tutorial" / "index.html",
    )

    for page in pages:
        content = rendered_text(page)
        missing = [text for text in expected if text not in content]
        if missing:
            raise SystemExit(f"Rendered page {page} is missing canonical example content: {missing}")
        if '--8<-- "docs/examples/solver.py"' in content:
            raise SystemExit(f"Rendered page {page} still contains the snippet directive")

    meshsolver_page = args.site / "reference" / "meshsolver" / "index.html"
    meshsolver_content = rendered_text(meshsolver_page)
    expected_defaults = (
        "Minimum allowed relative length. Default is 0.99.",
        "Maximum allowed relative length. Default is 1.01.",
        "Weight of the constraints. Default is 10.0.",
        "Weight of the constraints. Default is 1e3.",
        "Z component of the gravity force vector. Default is 0.01.",
        "Weight of the force. Default is 10.0.",
    )
    missing_defaults = [text for text in expected_defaults if text not in meshsolver_content]
    if missing_defaults:
        raise SystemExit(f"Rendered MeshSolver reference has incorrect defaults: {missing_defaults}")


if __name__ == "__main__":
    main()
