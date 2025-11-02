"""Main CLI entry point for hu."""

import click
from hu.commands import svg as svg_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="hu")
def main():
    """Hugo utilities - Automate tasks for Hugo static site generator projects."""
    pass


# Register commands
main.add_command(svg_cmd.svg, name="svg")


if __name__ == "__main__":
    main()
