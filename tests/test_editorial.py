import io
import json
import re
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from apps.editorial.forms import IdeaForm
from apps.editorial.models import (
    Article,
    Category,
    CategoryKind,
    Idea,
    PublicationStatus,
)

pytestmark = pytest.mark.django_db


def picture(name='idea.jpg'):
    output = io.BytesIO()
    Image.new('RGB', (900, 600), 'gray').save(output, format='JPEG')
    return SimpleUploadedFile(name, output.getvalue(), content_type='image/jpeg')


@pytest.fixture
def content():
    business = Category.objects.create(
        name='کافه', slug='cafe-test', kind=CategoryKind.BUSINESS
    )
    guide = Category.objects.create(
        name='راهنما', slug='guide-test', kind=CategoryKind.GUIDE
    )
    idea = Idea.objects.create(
        title='ایده تابلو کافه',
        category=business,
        image=picture(),
        image_alt='طرح نور کافه',
        description='ایده‌ای برای سردر کافه',
        meta_description='ایده تابلو کافه با نور و طراحی مفهومی',
        status=PublicationStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    article = Article.objects.create(
        title='راهنمای انتخاب تابلو',
        category=guide,
        image=picture('cover.jpg'),
        image_alt='نمونه نور تابلو',
        excerpt='چطور برای مغازه خود تابلو انتخاب کنیم؟',
        body=(
            'مقدمه مقاله.\n\n## هویت مغازه\n\nرنگ و خوانایی را بررسی کنید.'
            '\n\n## انتخاب متخصص\n\nنمونه‌کارها را ببینید.'
        ),
        meta_description='راهنمای انتخاب تابلو برای مغازه و بررسی نمونه‌کارهای متخصصان',
        status=PublicationStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    article.related_ideas.add(idea)
    return idea, article


def test_concept_gallery_does_not_require_vendor_or_executed_project(client, content):
    idea, _ = content
    response = client.get(reverse('editorial:ideas'))
    assert response.status_code == 200
    assert idea.title in response.content.decode()
    assert 'هوش مصنوعی' in response.content.decode()
    assert not hasattr(idea, 'vendor_id')


def test_draft_and_future_content_are_private(client, content):
    idea, article = content
    idea.status = PublicationStatus.DRAFT
    idea.save()
    article.published_at = timezone.now() + timedelta(days=1)
    article.save()
    assert client.get(idea.get_absolute_url()).status_code == 404
    assert client.get(article.get_absolute_url()).status_code == 404
    assert idea.title not in client.get(reverse('editorial:ideas')).content.decode()
    assert (
        article.title not in client.get(reverse('editorial:articles')).content.decode()
    )


def test_saved_concepts_can_start_a_request(client, content):
    idea, _ = content
    url = reverse('editorial:idea_save', kwargs={'pk': idea.pk})
    assert client.get(url).status_code == 405
    client.post(url, {'action': 'add'})
    client.post(url, {'action': 'add'})
    saved = client.get(reverse('editorial:saved'))
    assert list(saved.context['ideas']) == [idea]
    response = client.post(reverse('requests:from_board'))
    assert response.url == reverse('requests:wizard_need')
    assert idea.get_absolute_url() in client.session['request_wizard']['description']
    assert 'مفهومی' in client.session['request_wizard']['description']
    client.post(url, {'action': 'remove'})
    assert not client.get(reverse('editorial:saved')).context['ideas']


def test_publication_validation_and_safe_images(content):
    idea, _ = content
    idea.image_alt = ''
    with pytest.raises(ValidationError):
        idea.full_clean()
    form = IdeaForm(
        data={
            'title': 'عکس خراب',
            'category': idea.category_id,
            'source': 'ai',
            'style': 'modern',
            'status': 'draft',
        },
        files={
            'image': SimpleUploadedFile(
                'fake.jpg', b'not an image', content_type='image/jpeg'
            )
        },
    )
    assert not form.is_valid()
    assert 'image' in form.errors


def test_editor_requires_staff_and_model_permissions(client, user, content):
    client.force_login(user)
    assert client.get(reverse('editorial:manage')).status_code == 403
    assert (
        client.post(
            reverse('editorial:idea_create'), {'title': 'unauthorised'}
        ).status_code
        == 403
    )
    assert Idea.objects.count() == 1


def test_editor_upload_creates_independent_concept(client, staff_user, content):
    staff_user.is_superuser = True
    staff_user.save()
    client.force_login(staff_user)
    response = client.post(
        reverse('editorial:idea_create'),
        {
            'title': 'تابلو ساخته‌شده با هوش مصنوعی',
            'category': content[0].category_id,
            'image': picture('new.jpg'),
            'image_alt': 'طرح خیالی مغازه',
            'description': 'طرح برای الهام',
            'meta_description': 'طرح مفهومی برای الهام گرفتن مغازه‌ها',
            'source': 'ai',
            'style': 'modern',
            'status': 'published',
        },
    )
    assert response.status_code == 302
    idea = Idea.objects.get(title='تابلو ساخته‌شده با هوش مصنوعی')
    assert idea.created_by == staff_user
    assert idea.published_at is not None
    assert idea.thumbnail
    assert client.get(idea.get_absolute_url()).status_code == 200


def test_article_metadata_and_safe_structured_data(client, content):
    _, article = content
    article.seo_title = 'انتخاب تابلو مغازه'
    article.title = 'انتخاب تابلو </script><script>alert(1)</script>'
    article.save()
    response = client.get(article.get_absolute_url(), {'utm_source': 'campaign'})
    html = response.content.decode()
    assert 'انتخاب تابلو مغازه' in html
    assert (
        'utm_source' not in re.search(r'<link rel="canonical" href="([^"]+)"', html)[1]
    )
    data = [
        json.loads(raw)
        for raw in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S
        )
    ]
    article_data = next(obj for obj in data if obj.get('@type') == 'BlogPosting')
    assert article_data['headline'] == article.title
    assert article_data['datePublished']
    assert article_data['image'].startswith('http://testserver/')
    assert '</script><script>alert(1)</script>' not in html
    assert 'هویت مغازه' in html and 'انتخاب متخصص' in html


def test_sitemap_and_robots_include_public_content_only(client, content):
    idea, article = content
    sitemap = client.get(
        reverse('django.contrib.sitemaps.views.sitemap')
    ).content.decode()
    assert idea.get_absolute_url() in sitemap
    assert article.get_absolute_url() in sitemap
    assert '/request/' not in sitemap
    article.status = PublicationStatus.DRAFT
    article.save()
    assert article.get_absolute_url() not in client.get('/sitemap.xml').content.decode()
    robots = client.get('/robots.txt').content.decode()
    assert 'Sitemap: http://testserver/sitemap.xml' in robots


def test_filtered_and_private_pages_are_not_indexed(client, content):
    assert (
        'noindex'
        in client.get(reverse('editorial:ideas'), {'q': 'کافه'}).content.decode()
    )
    assert 'noindex' in client.get(reverse('editorial:saved')).content.decode()
    assert 'noindex' in client.get(reverse('requests:wizard_service')).content.decode()


def test_list_query_counts_are_constant(client, content):
    idea, article = content
    for route, model, obj in [
        ('editorial:ideas', Idea, idea),
        ('editorial:articles', Article, article),
    ]:
        with CaptureQueriesContext(connection) as few:
            client.get(reverse(route))
        for index in range(4):
            data = {
                'title': f'محتوا {index}',
                'slug': f'{route.split(":")[1]}-{index}',
                'category': obj.category,
                'image': picture(),
                'image_alt': 'تصویر',
                'status': 'published',
                'published_at': timezone.now(),
            }
            if model is Article:
                data |= {
                    'body': 'متن مقاله',
                    'excerpt': 'خلاصه',
                    'meta_description': 'توضیح مقاله',
                }
            else:
                data |= {'description': 'متن ایده', 'meta_description': 'توضیح ایده'}
            model.objects.create(**data)
        with CaptureQueriesContext(connection) as many:
            client.get(reverse(route))
        assert len(few) == len(many)


def test_category_filters_and_pagination_canonical(client, content):
    idea, _ = content
    category_url = reverse(
        'editorial:idea_category', kwargs={'category_slug': idea.category.slug}
    )
    assert idea.title in client.get(category_url).content.decode()
    assert not client.get(category_url, {'source': 'executed'}).context['ideas']
    html = client.get(
        category_url, {'page': '999999', 'utm_source': 'test'}
    ).content.decode()
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)[1]
    assert canonical == f'http://testserver{category_url}'
    assert client.get(reverse('portfolio:board')).status_code == 301
    assert client.get(reverse('portfolio:board')).url == reverse('editorial:ideas')


def test_article_editor_preserves_live_slug_and_m2m(client, staff_user, content):
    staff_user.is_superuser = True
    staff_user.save()
    client.force_login(staff_user)
    idea, article = content
    response = client.post(
        reverse('editorial:article_create'),
        {
            'title': 'راهنمای تازه',
            'category': article.category_id,
            'excerpt': 'خلاصهٔ راهنمای تازه',
            'body': '## انتخاب سبک\n\nمتن راهنما.',
            'image': picture('guide.jpg'),
            'image_alt': 'تصویر راهنما',
            'meta_description': 'راهنمای انتخاب سبک تابلو',
            'status': 'published',
            'related_ideas': [idea.pk],
        },
    )
    assert response.status_code == 302
    created = Article.objects.get(title='راهنمای تازه')
    assert created.thumbnail and created.created_by == staff_user
    assert list(created.related_ideas.all()) == [idea]
    stable_url = created.get_absolute_url()
    response = client.post(
        reverse('editorial:article_edit', kwargs={'pk': created.pk}),
        {
            'title': 'عنوان اصلاح‌شده',
            'slug': 'changed-url',
            'category': article.category_id,
            'excerpt': created.excerpt,
            'body': created.body,
            'image_alt': created.image_alt,
            'meta_description': created.meta_description,
            'status': 'published',
            'related_ideas': [idea.pk],
        },
    )
    assert response.status_code == 302
    created.refresh_from_db()
    assert created.get_absolute_url() == stable_url
    assert client.get(stable_url).status_code == 200
    created.status = 'draft'
    created.save()
    preview = client.get(
        reverse('editorial:preview', kwargs={'kind': 'article', 'pk': created.pk})
    )
    assert preview.status_code == 200
    assert preview.headers['X-Robots-Tag'] == 'noindex, nofollow'
    assert client.get(stable_url).status_code == 404


def test_staff_content_permissions_are_separate(client, staff_user, content):
    from django.contrib.auth.models import Permission

    idea, article = content
    staff_user.user_permissions.add(
        Permission.objects.get(
            codename='view_idea', content_type__app_label='editorial'
        )
    )
    client.force_login(staff_user)
    response = client.get(reverse('editorial:manage'))
    assert response.status_code == 200
    assert idea.title in response.content.decode()
    assert article.title not in response.content.decode()
    assert (
        client.get(
            reverse('editorial:article_edit', kwargs={'pk': article.pk})
        ).status_code
        == 403
    )
    assert (
        client.get(reverse('editorial:idea_edit', kwargs={'pk': idea.pk})).status_code
        == 403
    )


def test_public_article_hides_unpublished_related_ideas(client, content):
    idea, article = content
    idea.status = 'draft'
    idea.save()
    response = client.get(article.get_absolute_url())
    assert idea.title not in response.content.decode()


def test_configured_public_origin_is_used_consistently(client, settings, content):
    settings.PUBLIC_SITE_URL = 'https://sign.example'
    idea, article = content
    response = client.get(article.get_absolute_url(), {'utm_source': 'test'})
    assert (
        f'href="https://sign.example{article.get_absolute_url()}"'
        in response.content.decode()
    )
    assert 'https://sign.example/media/articles/' in response.content.decode()
    assert (
        f'https://sign.example{idea.get_absolute_url()}'
        in client.get('/sitemap.xml').content.decode()
    )
    assert (
        'Sitemap: https://sign.example/sitemap.xml'
        in client.get('/robots.txt').content.decode()
    )


def test_save_handles_invalid_session_and_requires_csrf(client, content):
    from django.test import Client

    idea, _ = content
    session = client.session
    session['inspiration_ideas'] = ['invalid', None, idea.pk, idea.pk]
    session.save()
    assert list(client.get(reverse('editorial:saved')).context['ideas']) == [idea]
    url = reverse('editorial:idea_save', kwargs={'pk': idea.pk})
    assert Client(enforce_csrf_checks=True).post(url).status_code == 403
    assert client.post(url, {'action': 'unknown'}).status_code == 400


def test_gallery_capacity_and_related_article_saved_state(client, content):
    idea, article = content
    ids = [idea.pk]
    for index in range(24):
        other = Idea.objects.create(
            title=f'ایدهٔ {index}',
            category=idea.category,
            image=idea.image.name,
            image_alt='تصویر مرجع',
            description='شرح',
            meta_description='توضیح',
            status='published',
        )
        if index < 23:
            ids.append(other.pk)
    session = client.session
    session['inspiration_ideas'] = ids
    session.save()
    client.post(reverse('editorial:idea_save', kwargs={'pk': other.pk}))
    assert len(client.session['inspiration_ideas']) == 24
    assert other.pk not in client.session['inspiration_ideas']
    html = client.get(article.get_absolute_url()).content.decode()
    assert f'حذف {idea.title} از ذخیره‌ها' in html


def test_editor_invalid_post_keeps_errors_and_draft_article_can_preview(
    client, staff_user, content
):
    staff_user.is_superuser = True
    staff_user.save()
    client.force_login(staff_user)
    response = client.post(
        reverse('editorial:article_create'),
        {
            'title': 'مقاله بدون عکس',
            'category': content[1].category_id,
            'excerpt': 'خلاصه',
            'body': 'متن',
            'status': 'published',
        },
    )
    assert response.status_code == 400
    assert 'image' in response.context['form'].errors
    assert not Article.objects.filter(title='مقاله بدون عکس').exists()
    response = client.post(
        reverse('editorial:article_create'),
        {
            'title': 'پیش‌نویس بدون عکس',
            'category': content[1].category_id,
            'status': 'draft',
        },
    )
    assert response.status_code == 302
    draft = Article.objects.get(title='پیش‌نویس بدون عکس')
    assert (
        client.get(
            reverse('editorial:preview', kwargs={'kind': 'article', 'pk': draft.pk})
        ).status_code
        == 200
    )
    assert client.get(draft.get_absolute_url()).status_code == 404
