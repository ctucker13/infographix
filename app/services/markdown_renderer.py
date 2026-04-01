from __future__ import annotations

from functools import lru_cache

from markdown_it import MarkdownIt
try:
    from markdown_it.extensions.tasklists import tasklists_plugin
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    tasklists_plugin = None
from markupsafe import Markup


@lru_cache(maxsize=1)
def _markdown() -> MarkdownIt:
    """Configure a safe markdown renderer once."""
    md = MarkdownIt("commonmark", {"html": False, "linkify": True, "breaks": True})
    md.enable("table").enable("strikethrough")
    if tasklists_plugin is not None:
        md.use(tasklists_plugin, enabled=True, label=True)
    return md


def render_markdown(value: str | None) -> Markup:
    """Render markdown content into safe HTML for templates."""
    if not value:
        return Markup("")
    html = _markdown().render(value)
    return Markup(html)
