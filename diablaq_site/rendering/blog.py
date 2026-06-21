"""Blog page renderer — index, posts, and tag pages."""

from __future__ import annotations

from pathlib import Path


def render_blog_pages(
    env, out_dir, site_url, nav_projects, sorted_blog,
    _render_fn, _write_html_fn, _build_tags_index_fn, slugify_tag_fn,
) -> None:
    """Render blog index, posts, and tag pages."""
    _write_html_fn(
        out_dir / "blog" / "index.html",
        _render_fn(
            env, "blog_index.html",
            nav_projects=nav_projects, site_url=site_url,
            canonical_url=(site_url + "/blog/"),
            posts=sorted_blog,
        ),
    )
    for post in sorted_blog:
        _write_html_fn(
            out_dir / post.url.strip("/") / "index.html",
            _render_fn(
                env, "blog_post.html",
                nav_projects=nav_projects, site_url=site_url,
                canonical_url=(site_url + post.url),
                post=post,
                post_tags=[{"name": t, "url": f"/blog/tag/{slugify_tag_fn(t)}/"} for t in post.tags],
            ),
        )
    for tag, items in sorted(_build_tags_index_fn(sorted_blog).items(), key=lambda kv: kv[0].lower()):
        tag_slug = slugify_tag_fn(tag)
        _write_html_fn(
            out_dir / "blog" / "tag" / tag_slug / "index.html",
            _render_fn(
                env, "blog_index.html",
                nav_projects=nav_projects, site_url=site_url,
                canonical_url=(site_url + f"/blog/tag/{tag_slug}/"),
                posts=sorted(items, key=lambda p: p.date, reverse=True),
            ),
        )
