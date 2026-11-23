"""
@description: Package entry point for ``python -m open_run_lab``.
"""

from open_run_lab.cli import cli


def main() -> None:
    cli(prog_name="python -m open_run_lab")


if __name__ == "__main__":
    main()
