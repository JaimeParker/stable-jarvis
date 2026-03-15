from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import feedparser


CONFERENCE_PATTERN = re.compile(
    r"\b("
    r"CVPR|ICCV|ECCV|NeurIPS|NIPS|ICLR|ICML|AAAI|IJCAI|ACL|EMNLP|NAACL|COLING|"
    r"KDD|WWW|The\s*Web\s*Conference|WSDM|SIGIR|SIGGRAPH(?:\s*Asia)?|ICME|ICASSP|WACV|"
    r"ACM\s*MM|MM|MICCAI|ISBI|CoRL|RSS|IROS|ICRA"
    r")\b(?:\s*20\d{2})?",
    flags=re.IGNORECASE,
)
ROLE_PATTERN = re.compile(
    r"\b(Oral(?:\s*Presentation)?|Spotlight|Poster|Highlight|Long|Short|Best\s*Paper|Honorable\s*Mention)\b",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r'https?://[^\s)\]>\'\"]+', re.IGNORECASE)
TRAILING_CHARS = '.,;:?!)]}>\'"'
CODE_HOSTS = (
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "codeberg.org",
    "gitee.com",
    "huggingface.co",
    "sourceforge.net",
    "sr.ht",
    "git.sr.ht",
)


@dataclass(slots=True)
class ParsedArxivEntry:
    entry_id: str | None
    arxiv_id: str | None
    title: str
    authors: list[str] = field(default_factory=list)
    primary_category: str | None = None
    categories: list[str] = field(default_factory=list)
    published: str | None = None
    updated: str | None = None
    comments: str | None = None
    journal_ref: str | None = None
    venue_inferred: str | None = None
    summary: str | None = None
    html_url: str | None = None
    pdf_url: str | None = None
    code_urls: list[str] = field(default_factory=list)
    project_urls: list[str] = field(default_factory=list)
    other_urls: list[str] = field(default_factory=list)


def _clean_url(url: str) -> str:
    cleaned = url
    while cleaned and cleaned[-1] in TRAILING_CHARS:
        cleaned = cleaned[:-1]
    return cleaned


def _host_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return ""
    return host[4:] if host.startswith("www.") else host


def _deduplicate(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(item)
    return ordered


def _is_code_host(host: str) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in CODE_HOSTS)


def _is_project_like(url: str, host: str) -> bool:
    if re.search(r"\.(?:io|ai|ml)$", host):
        return True
    if "sites.google.com" in host:
        return True
    if any(marker in host for marker in (".cs.", ".vision.", ".ee.", ".cv.", ".ml.")):
        return True
    return bool(re.search(r"/(project|projects|page|pages|people|lab|group|research|paper|papers)(/|$)", url, re.IGNORECASE))


def extract_venue_info(text: str) -> str | None:
    match = CONFERENCE_PATTERN.search(text or "")
    if not match:
        return None
    conference = match.group(0).strip()
    role_match = ROLE_PATTERN.search(text or "")
    role = role_match.group(0).strip() if role_match else None
    return f"{conference}{(' ' + role) if role else ''}"


def extract_urls(text: str) -> dict[str, list[str]]:
    raw_urls = URL_PATTERN.findall(text or "")
    cleaned_urls = [_clean_url(url) for url in raw_urls if url]
    code_urls: list[str] = []
    project_urls: list[str] = []
    other_urls: list[str] = []
    for url in cleaned_urls:
        host = _host_of(url)
        if not host:
            continue
        if _is_code_host(host):
            code_urls.append(url)
        elif _is_project_like(url, host):
            project_urls.append(url)
        else:
            other_urls.append(url)
    return {
        "all_urls": _deduplicate(cleaned_urls),
        "code_urls": _deduplicate(code_urls),
        "project_urls": _deduplicate(project_urls),
        "other_urls": _deduplicate(other_urls),
    }


def _extract_arxiv_id(entry_id: str | None) -> str | None:
    if not entry_id:
        return None
    if "/abs/" in entry_id:
        return entry_id.rsplit("/abs/", 1)[-1]
    if entry_id.startswith("http"):
        return entry_id.rstrip("/").split("/")[-1]
    return entry_id


def parse_feed(xml_text: str) -> list[ParsedArxivEntry]:
    feed = feedparser.parse(xml_text)
    items: list[ParsedArxivEntry] = []
    for entry in feed.entries:
        title = (entry.title or "").replace("\n", " ").strip()
        authors = [author.get("name", "") for author in entry.get("authors", [])] if "authors" in entry else []
        html_url = None
        pdf_url = None
        for link in entry.get("links", []):
            if link.get("rel") == "alternate":
                html_url = link.get("href")
            if link.get("title", "").lower() == "pdf" or link.get("type") == "application/pdf":
                pdf_url = link.get("href")
        comments = getattr(entry, "arxiv_comment", None) or ""
        journal_ref = getattr(entry, "arxiv_journal_ref", None)
        primary_category = getattr(getattr(entry, "arxiv_primary_category", {}), "term", None) or None
        categories = [tag.get("term") for tag in entry.get("tags", []) if tag.get("term")]
        venue = extract_venue_info(f"{comments or ''} {journal_ref or ''}")
        url_info = extract_urls(f"{comments or ''}\n{getattr(entry, 'summary', '')}")
        entry_id = entry.get("id")
        items.append(
            ParsedArxivEntry(
                entry_id=entry_id,
                arxiv_id=_extract_arxiv_id(entry_id),
                title=title,
                authors=authors,
                primary_category=primary_category,
                categories=categories,
                published=entry.get("published"),
                updated=entry.get("updated"),
                comments=comments,
                journal_ref=journal_ref,
                venue_inferred=venue,
                summary=getattr(entry, "summary", ""),
                html_url=html_url,
                pdf_url=pdf_url,
                code_urls=url_info["code_urls"],
                project_urls=url_info["project_urls"],
                other_urls=url_info["other_urls"],
            )
        )
    return items
