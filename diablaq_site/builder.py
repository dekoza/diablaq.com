from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import frontmatter
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown


@dataclass(frozen=True)
class Edition:
    url: str
    title: str
    project_slug: str
    release: str | None
    release_date: date
    is_new: bool
    is_announcement: bool
    presale_url: str | None
    legacy_anchor: str | None
    html_body: str


@dataclass(frozen=True)
class Project:
    slug: str
    title: str
    line: str
    summary: str | None
    legacy_path: str | None
    url: str
    html_body: str


@dataclass(frozen=True)
class Person:
    slug: str
    name: str
    html_bio: str


def _parse_date(value: str, *, source_path: Path) -> date:
    try:
        yyyy, mm, dd = value.split("-")
        return date(int(yyyy), int(mm), int(dd))
    except Exception as exc:  # noqa: BLE001 - want a clear error
        raise ValueError(
            f"Nieprawidłowe release_date={value!r} w {source_path}. Oczekiwany format YYYY-MM-DD."
        ) from exc


def _read_markdown_file(path: Path) -> tuple[dict, str]:
    post = frontmatter.load(path)
    meta = dict(post.metadata or {})
    body_md = post.content or ""
    body_html = markdown(body_md, extensions=["extra", "sane_lists"])
    return meta, body_html


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _write_html(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def _render(env: Environment, template_name: str, **ctx):
    template = env.get_template(template_name)
    return template.render(**ctx)


def build_site(*, root: Path, out_dir: Path) -> None:
    templates_dir = root / "templates"
    content_dir = root / "content"

    if not templates_dir.exists():
        raise FileNotFoundError(f"Brak katalogu templates/: {templates_dir}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # --- load content
    projects: list[Project] = []
    editions: list[Edition] = []
    people: list[Person] = []

    # Projects (content/projects/<slug>/project.md)
    projects_root = content_dir / "projects"
    for project_dir in sorted(projects_root.glob("*/")):
        project_md = project_dir / "project.md"
        if not project_md.exists():
            continue

        meta, body_html = _read_markdown_file(project_md)
        slug = project_dir.name
        title = str(meta.get("title") or slug)
        line = str(meta.get("line") or "diablaq")
        summary = meta.get("summary")
        legacy_path = meta.get("legacy_path")
        url = f"/{slug}/"

        projects.append(
            Project(
                slug=slug,
                title=title,
                line=line,
                summary=summary,
                legacy_path=legacy_path,
                url=url,
                html_body=body_html,
            )
        )

        # Editions (content/projects/<slug>/editions/*.md)
        for edition_md in sorted((project_dir / "editions").glob("*.md")):
            emeta, ebody_html = _read_markdown_file(edition_md)

            if "release_date" not in emeta:
                raise ValueError(f"Brak release_date w {edition_md}")

            is_new = bool(emeta.get("is_new", False))
            is_announcement = bool(emeta.get("is_announcement", False))
            if is_new and is_announcement:
                raise ValueError(
                    f"Pozycja nie może mieć jednocześnie is_new i is_announcement: {edition_md}"
                )

            release_date = _parse_date(str(emeta["release_date"]), source_path=edition_md)
            ed_slug = edition_md.stem
            url = f"/{line}/{slug}/{ed_slug}/" if line in {"mecenat", "studio"} else f"/{slug}/{ed_slug}/"

            editions.append(
                Edition(
                    url=url,
                    title=str(emeta.get("title") or ed_slug),
                    project_slug=slug,
                    release=str(emeta.get("release") or "") or None,
                    release_date=release_date,
                    is_new=is_new,
                    is_announcement=is_announcement,
                    presale_url=emeta.get("presale_url"),
                    legacy_anchor=emeta.get("legacy_anchor"),
                    html_body=ebody_html,
                )
            )

    # People (content/people/*.md)
    people_root = content_dir / "people"
    for person_md in sorted(people_root.glob("*.md")):
        meta, body_html = _read_markdown_file(person_md)
        slug = person_md.stem
        name = str(meta.get("name") or slug)
        people.append(Person(slug=slug, name=name, html_bio=body_html))

    # --- derived lists
    new_editions = sorted(
        [e for e in editions if e.is_new], key=lambda e: e.release_date, reverse=True
    )
    announcements = sorted(
        [e for e in editions if e.is_announcement], key=lambda e: e.release_date, reverse=True
    )

    # --- render pages
    # Home
    html = _render(
        env,
        "home.html",
        projects=projects,
        new_editions=new_editions[:12],
        announcements=announcements[:12],
    )
    _write_html(out_dir / "index.html", html)

    # Listing pages
    html = _render(env, "listing.html", title="Nowości", items=new_editions)
    _write_html(out_dir / "nowe" / "index.html", html)

    html = _render(env, "listing.html", title="Zapowiedzi", items=announcements)
    _write_html(out_dir / "zapowiedzi" / "index.html", html)

    # People
    html = _render(env, "people_index.html", people=people)
    _write_html(out_dir / "ludzie" / "index.html", html)

    for p in people:
        html = _render(env, "person.html", person=p)
        _write_html(out_dir / "ludzie" / p.slug / "index.html", html)

        # legacy alias: /<slug>/ for people is handled later per explicit mapping.

    # Projects and editions pages
    for pr in projects:
        # legacy series page at /<slug>/
        pr_editions = [e for e in editions if e.project_slug == pr.slug]
        pr_editions_sorted = sorted(pr_editions, key=lambda e: e.release_date, reverse=True)

        html = _render(env, "project.html", project=pr, editions=pr_editions_sorted)
        _write_html(out_dir / pr.slug / "index.html", html)

        for e in pr_editions_sorted:
            # canonical edition page
            html = _render(env, "edition.html", edition=e, project=pr)
            out_path = out_dir / e.url.strip("/") / "index.html"
            _write_html(out_path, html)

    # Special legacy alias rules (minimal): /zvyrke/ -> /ludzie/zvyrke/
    # We implement as a lightweight redirect page for now.
    zv = next((p for p in people if p.slug == "zvyrke"), None)
    if zv is not None:
        html = _render(env, "redirect.html", to_url=f"/ludzie/{zv.slug}/")
        _write_html(out_dir / "zvyrke" / "index.html", html)

    # --- copy static assets
    _copy_tree(root / "img", out_dir / "img")
    _copy_tree(root / "css", out_dir / "css")

    for file_name in ["CNAME", ".nojekyll"]:
        src = root / file_name
        if src.exists():
            shutil.copy2(src, out_dir / file_name)

