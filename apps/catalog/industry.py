"""Reviewed, offline source data. Browsing and media retrieval never run on requests."""

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict, cast


class ProviderReference(TypedDict):
    key: str
    name: str
    website: str
    city_slug: str
    city_name: str
    image: str
    services: list[str]
    description: str


class ServiceContent(TypedDict):
    slug: str
    title: str
    description: str
    suitable_for: str
    materials: str
    image: str
    source_name: str
    source_url: str
    faq: list[dict[str, str]]


class ProjectContent(TypedDict):
    slug: str
    title: str
    description: str
    service: str
    image: str
    source_name: str
    source_url: str
    source_image_url: str


class IndustryContent(TypedDict):
    checked_on: str
    providers: list[ProviderReference]
    services: list[ServiceContent]
    projects: list[ProjectContent]


@lru_cache(maxsize=1)
def industry_content() -> IndustryContent:
    return cast(
        IndustryContent,
        json.loads(Path(__file__).with_name("industry_content.json").read_text()),
    )


def industry_providers(
    *, query: str = "", city_slug: str = "", service_slug: str = ""
) -> list[ProviderReference]:
    return [
        provider
        for provider in industry_content()["providers"]
        if (not query or query in provider["name"] or query in provider["description"])
        and (not city_slug or city_slug == provider["city_slug"])
        and (not service_slug or service_slug in provider["services"])
    ]
