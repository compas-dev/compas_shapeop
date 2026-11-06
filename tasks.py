"""Thin Invoke aliases for the repository's canonical development commands."""

from invoke import task


@task
def test(context):
    """Run the test suite."""
    context.run("python -m pytest")


@task
def lint(context):
    """Run Ruff lint checks."""
    context.run("python -m ruff check .")


@task
def format(context, check=False):
    """Format Python sources, or check formatting with `--check`."""
    suffix = " --check" if check else ""
    context.run(f"python -m ruff format .{suffix}")


@task
def typecheck(context):
    """Run Pyright."""
    context.run("python -m pyright")


@task
def docs(context):
    """Build the documentation in strict mode."""
    context.run("python -m mkdocs build --strict")
    context.run("python .github/scripts/verify_docs.py site")


@task
def build(context):
    """Build the source and wheel distributions."""
    context.run("python -m build")


@task
def clean(context):
    """Remove generated build artifacts."""
    context.run("git clean -fdX build dist site")
