"""One set of lighting edits per shared scene, with no request-time I/O."""

from django.conf import settings
from django.templatetags.static import static

PHASES = ('morning', 'day', 'sunset', 'night')
SCENE_SOURCES = {
    'img/landing-signature-v1.webp': 'signature',
    'img/landing-wayfinding-v1.webp': 'wayfinding',
    'img/landing-boutique-v1.webp': 'boutique',
    'img/landing-restaurant-v1.webp': 'restaurant',
    'img/landing-office-v1.webp': 'office',
    'img/demo/portfolio-cafe.png': 'cafe',
    'img/demo/portfolio-boutique.png': 'boutique',
    'img/demo/portfolio-office.png': 'office',
    'img/demo/portfolio-restaurant.png': 'restaurant',
    'img/demo/service-chalnium.png': 'chalnium',
    'img/demo/service-neon.png': 'neon',
    'img/demo/service-led.png': 'led',
    'img/demo/service-steel.png': 'steel',
    'img/demo/service-composite.png': 'composite',
    'img/demo/service-flexi.png': 'flexi',
    'img/demo/workshop-banner.png': 'workshop',
    'img/references/novin-gerad.webp': 'reference-gerad',
    'img/references/namatabesh-vozara.webp': 'reference-vozara',
    'img/references/rangin-national-jewels.webp': 'reference-jewels',
    'img/references/doral-chalnium.webp': 'reference-doral',
    'img/references/diba-office.webp': 'reference-diba',
    'img/references/novinlight-lasvegas.webp': 'reference-lasvegas',
}


def scene_variants(source: str) -> dict[str, str]:
    """Only registered site photographs have generated lighting variants."""
    # The importer copies bundled references to this exact media directory.
    # Resolve that namespace only; an unrelated upload with the same basename
    # must never inherit a reference photograph's lighting edits.
    reference_prefix = f'{settings.MEDIA_URL}industry/references/'
    if source.startswith(reference_prefix):
        source = f'img/references/{source.removeprefix(reference_prefix)}'
    slug = SCENE_SOURCES.get(source)
    if not slug:
        return {}
    return {phase: static(f'img/daylight/{slug}-{phase}.webp') for phase in PHASES}


def scene_source(source: str) -> str:
    """Resolve logical static paths; preserve uploaded and external URLs."""
    return static(source) if source.startswith('img/') else source
