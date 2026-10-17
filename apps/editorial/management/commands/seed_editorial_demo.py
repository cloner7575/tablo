"""Optional local preview content. Never runs as part of migrations."""

import json
from argparse import ArgumentParser
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import Service
from apps.editorial.forms import ArticleForm, IdeaForm
from apps.editorial.models import Article, Category, Idea


class Command(BaseCommand):
    help = (
        'Add illustrative local gallery and original starter guides (draft by default).'
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            '--publish', action='store_true', help='Publish only on a local preview.'
        )

    def handle(self, *args: object, **options: object) -> None:
        if not settings.DEBUG:
            raise CommandError('Demo content is only available with DEBUG enabled.')
        data_path = Path(__file__).parents[2] / 'demo_content.json'
        content = json.loads(data_path.read_text(encoding='utf-8'))
        status = 'published' if options['publish'] else 'draft'
        root = Path(settings.BASE_DIR) / 'static' / 'img' / 'demo'
        for (
            slug,
            title,
            category,
            style,
            service,
            filename,
            description,
            notes,
        ) in content['ideas']:
            if Idea.objects.filter(slug=slug).exists():
                continue
            form = IdeaForm(
                data={
                    'slug': slug,
                    'title': title,
                    'category': Category.objects.get(slug=category).pk,
                    'style': style,
                    'source': 'ai',
                    'description': description,
                    'design_notes': notes,
                    'image_alt': title,
                    'meta_description': description,
                    'seo_title': title,
                    'service': Service.objects.filter(slug=service)
                    .values_list('pk', flat=True)
                    .first()
                    or '',
                    'status': status,
                    'is_featured': slug == 'cafe-warm',
                },
                files={
                    'image': SimpleUploadedFile(
                        filename,
                        (root / filename).read_bytes(),
                        content_type='image/png',
                    )
                },
            )
            if not form.is_valid():
                raise CommandError(str(form.errors))
            form.save()
        for slug, title, category, filename, excerpt, body in content['articles']:
            if Article.objects.filter(slug=slug).exists():
                continue
            form = ArticleForm(
                data={
                    'slug': slug,
                    'title': title,
                    'category': Category.objects.get(slug=category).pk,
                    'excerpt': excerpt,
                    'body': body,
                    'image_alt': title,
                    'image_caption': 'تصویر مفهومی برای همراهی با راهنما؛ '
                    'نمونهٔ پروژهٔ اجراشده نیست.',
                    'meta_description': excerpt,
                    'seo_title': title,
                    'status': status,
                    'is_featured': slug == 'choose-shop-sign',
                    'related_ideas': list(
                        Idea.objects.published().values_list('pk', flat=True)[:3]
                    ),
                },
                files={
                    'image': SimpleUploadedFile(
                        filename,
                        (root / filename).read_bytes(),
                        content_type='image/png',
                    )
                },
            )
            if not form.is_valid():
                raise CommandError(str(form.errors))
            form.save()
        self.stdout.write(
            self.style.SUCCESS(
                'Local gallery and guides ready. Existing content preserved.'
            )
        )
