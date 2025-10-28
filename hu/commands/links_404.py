"""Check for broken links (404s) in Hugo markdown files."""

import re
from pathlib import Path
from urllib.parse import urlparse

import click


def extract_links_from_markdown(content: str) -> list[str]:
    """Extract all links from markdown content.

    Handles both markdown links [text](url) and HTML links <a href="url">.
    """
    links = []

    # Markdown links: [text](url)
    md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    links.extend(re.findall(md_link_pattern, content))

    # HTML links: <a href="url">
    html_link_pattern = r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"'
    html_links = re.findall(html_link_pattern, content)
    links.extend([('', link) for link in html_links])

    return [link[1] for link in links if link[1]]


def is_internal_link(link: str) -> bool:
    """Check if a link is internal (relative or to local file)."""
    parsed = urlparse(link)
    # No scheme means relative link
    # Or scheme is file://
    return not parsed.scheme or parsed.scheme == 'file'


def check_internal_link(link: str, base_path: Path, hugo_root: Path) -> bool:
    """Check if an internal link exists.

    Args:
        link: The link to check
        base_path: The path of the markdown file containing the link
        hugo_root: The root of the Hugo project

    Returns:
        True if the link target exists, False otherwise
    """
    # Skip anchor-only links
    if link.startswith('#'):
        return True

    # Remove anchor if present
    link_without_anchor = link.split('#')[0]
    if not link_without_anchor:
        return True

    # Skip external links
    if not is_internal_link(link_without_anchor):
        return True

    # Remove query parameters
    link_without_query = link_without_anchor.split('?')[0]
    if not link_without_query:
        return True

    # Resolve the link relative to the base path
    if link_without_query.startswith('/'):
        # Absolute path from Hugo root
        target = hugo_root / link_without_query.lstrip('/')
    else:
        # Relative path
        target = (base_path.parent / link_without_query).resolve()

    return target.exists()


def find_broken_links(content_dir: Path, hugo_root: Path) -> dict[str, list[str]]:
    """Find all broken links in markdown files.

    Args:
        content_dir: Path to the Hugo content directory
        hugo_root: Path to the Hugo project root

    Returns:
        Dictionary mapping file paths to lists of broken links
    """
    broken_links = {}

    # Find all markdown files
    md_files = list(content_dir.rglob('*.md'))

    for md_file in md_files:
        content = md_file.read_text(encoding='utf-8')
        links = extract_links_from_markdown(content)

        file_broken_links = []
        for link in links:
            if is_internal_link(link) and not check_internal_link(link, md_file, hugo_root):
                file_broken_links.append(link)

        if file_broken_links:
            broken_links[str(md_file.relative_to(hugo_root))] = file_broken_links

    return broken_links


@click.command()
@click.option(
    '--content-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default='content',
    help='Path to Hugo content directory (default: content)'
)
@click.option(
    '--hugo-root',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default='.',
    help='Path to Hugo project root (default: current directory)'
)
def check_404_links(content_dir: Path, hugo_root: Path):
    """Find broken links in Hugo markdown files."""
    click.echo(f"Scanning for broken links in {content_dir}...")

    # Make paths absolute
    content_dir = content_dir.resolve()
    hugo_root = hugo_root.resolve()

    # If content_dir is relative, resolve it from hugo_root
    if not content_dir.is_absolute():
        content_dir = (hugo_root / content_dir).resolve()

    broken_links = find_broken_links(content_dir, hugo_root)

    if not broken_links:
        click.secho("✓ No broken links found!", fg='green')
        return

    click.secho(f"\n✗ Found broken links in {len(broken_links)} file(s):\n", fg='red')

    for file_path, links in broken_links.items():
        click.secho(f"{file_path}:", fg='yellow')
        for link in links:
            click.echo(f"  - {link}")
        click.echo()

    # Exit with error code if broken links found
    raise click.exceptions.Exit(1)
