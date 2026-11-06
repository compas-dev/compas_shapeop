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
        parser = TextContentParser()
        parser.feed(page.read_text())
        content = "".join(parser.parts)
        missing = [text for text in expected if text not in content]
        if missing:
            raise SystemExit(f"Rendered page {page} is missing canonical example content: {missing}")
        if '--8<-- "docs/examples/solver.py"' in content:
            raise SystemExit(f"Rendered page {page} still contains the snippet directive")


if __name__ == "__main__":
    main()
