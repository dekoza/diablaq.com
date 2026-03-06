"""Template rendering helpers — Jinja2 environment and context injection."""

from jinja2 import Environment


def _render(env: Environment, template_name: str, **ctx):
    """Internal renderer: fetch template and render with context."""
    template = env.get_template(template_name)
    return template.render(**ctx)


def abs_url(site_url: str):
    """Return a function that constructs absolute URLs from site_url.

    Args:
        site_url: Base URL (e.g., "http://example.com")

    Returns:
        Callable that takes a relative path and returns absolute URL.
    """

    def _abs_url_fn(path: str) -> str:
        # Normalize path: ensure leading slash
        path = "/" + path.lstrip("/")
        return f"{site_url}{path}" if site_url else path

    return _abs_url_fn


def render_template(env: Environment, template_name: str, *, nav_projects, site_url, **ctx) -> str:
    """Render a Jinja2 template with standard context injection.

    Args:
        env: Jinja2 Environment instance
        template_name: Name of the template to render
        nav_projects: Navigation projects list (injected into context)
        site_url: Base site URL for absolute URL construction
        **ctx: Additional context variables

    Returns:
        Rendered HTML string

    Raises:
        jinja2.TemplateNotFound: If template_name does not exist
    """
    # Build abs_url callable with site_url captured
    abs_url_fn = abs_url(site_url)

    # Combine standard context with user-provided context
    combined_context = {
        "nav_projects": nav_projects,
        "abs_url": abs_url_fn,
        **ctx,
    }

    return _render(env, template_name, **combined_context)
