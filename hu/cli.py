"""Main CLI entry point for hu."""

import click
from hu.commands import links_404
from hu.commands import svg as svg_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="hu")
def main():
    """Hugo utilities - Automate tasks for Hugo static site generator projects."""
    pass


# Register commands
# New simplified command name as requested: `hu 404`
main.add_command(links_404.check_404_links, name="404")
# Keep legacy alias for backward compatibility
main.add_command(links_404.check_404_links, name="404-links")
main.add_command(svg_cmd.svg, name="svg")


if __name__ == "__main__":
    main()
