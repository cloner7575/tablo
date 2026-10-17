from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Prefetch, QuerySet

from apps.editorial.models import Article, Idea


@dataclass(frozen=True)
class ArticleSection:
    anchor: str
    heading: str
    paragraphs: list[str]


def published_ideas() -> QuerySet[Idea]:
    return Idea.objects.published().select_related('category', 'service')


def published_articles() -> QuerySet[Article]:
    return Article.objects.published().select_related('category', 'service')


def article_details() -> QuerySet[Article]:
    return published_articles().prefetch_related(
        Prefetch('related_ideas', queryset=published_ideas())
    )


def article_sections(body: str) -> list[ArticleSection]:
    sections = []
    heading = ''
    paragraphs = []
    paragraph = []
    for line in body.splitlines():
        if line.startswith('## '):
            if paragraph:
                paragraphs.append('\n'.join(paragraph))
                paragraph = []
            if heading or paragraphs:
                sections.append(
                    ArticleSection(f'section-{len(sections) + 1}', heading, paragraphs)
                )
            heading = line[3:].strip()
            paragraphs = []
        elif not line.strip():
            if paragraph:
                paragraphs.append('\n'.join(paragraph))
                paragraph = []
        else:
            paragraph.append(line)
    if paragraph:
        paragraphs.append('\n'.join(paragraph))
    if heading or paragraphs:
        sections.append(
            ArticleSection(f'section-{len(sections) + 1}', heading, paragraphs)
        )
    return sections
