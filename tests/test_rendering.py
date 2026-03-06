"""Tests for diablaq_site.rendering module — template rendering helpers."""

import pytest
from jinja2 import Environment, DictLoader, TemplateNotFound
from diablaq_site.rendering import render_template, abs_url


@pytest.fixture
def env():
    """Create a minimal Jinja2 Environment with in-memory templates."""
    templates = {
        "simple.html": "Hello {{ name }}!",
        "with_nav.html": "Projects: {{ nav_projects | length }}",
        "with_url.html": "URL: {{ abs_url('/test') }}",
        "full_context.html": "{{ title }} | Nav: {{ nav_projects | length }} | URL: {{ abs_url('/page') }}",
    }
    return Environment(loader=DictLoader(templates))


def test_render_template_basic_context(env):
    """Test render_template with basic context variables."""
    html = render_template(
        env, "simple.html", nav_projects=[], site_url="http://test", name="World"
    )
    assert html == "Hello World!"


def test_render_template_with_nav_projects(env):
    """Test render_template injects nav_projects into context."""
    projects = [{"title": "Project 1"}, {"title": "Project 2"}]
    html = render_template(env, "with_nav.html", nav_projects=projects, site_url="http://test")
    assert "Projects: 2" in html


def test_render_template_with_abs_url_function(env):
    """Test render_template provides abs_url as callable in context."""
    html = render_template(env, "with_url.html", nav_projects=[], site_url="http://example.com")
    assert html == "URL: http://example.com/test"


def test_render_template_full_context(env):
    """Test render_template combines nav_projects, abs_url, and custom context."""
    projects = [{"title": "P1"}, {"title": "P2"}, {"title": "P3"}]
    html = render_template(
        env,
        "full_context.html",
        nav_projects=projects,
        site_url="http://mysite.com",
        title="My Site",
    )
    assert "My Site" in html
    assert "Nav: 3" in html
    assert "URL: http://mysite.com/page" in html


def test_render_template_not_found(env):
    """Test render_template raises TemplateNotFound for missing template."""
    with pytest.raises(TemplateNotFound):
        render_template(env, "nonexistent.html", nav_projects=[], site_url="http://test")


def test_abs_url_basic(env):
    """Test abs_url function constructs correct absolute URLs."""
    url_fn = abs_url("http://example.com")
    assert url_fn("/page") == "http://example.com/page"


def test_abs_url_with_slash(env):
    """Test abs_url handles leading slashes in path."""
    url_fn = abs_url("http://example.com")
    result = url_fn("/path/to/page")
    assert result == "http://example.com/path/to/page"


def test_abs_url_without_leading_slash(env):
    """Test abs_url handles paths without leading slash."""
    url_fn = abs_url("http://example.com")
    result = url_fn("page")
    # Should normalize by ensuring slash is present
    assert result.startswith("http://example.com")
