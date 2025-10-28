"""Main CLI entry point for hu."""

import click
from hu.commands import links_404


@click.group()
@click.version_option(version="0.1.0", prog_name="hu")
def main():
    """Hugo utilities - Automate tasks for Hugo static site generator projects."""
    pass


# Register commands
main.add_command(links_404.check_404_links, name="404-links")


if __name__ == "__main__":
    main()
