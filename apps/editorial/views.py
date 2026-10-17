from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.catalog.models import Service
from apps.common.seo import breadcrumbs, public_url
from apps.editorial.collections import (
    browser_reference_ids,
    import_browser_references,
    save_reference,
    saved_idea_ids,
    saved_ideas,
)
from apps.editorial.forms import ArticleForm, IdeaForm
from apps.editorial.models import (
    Article,
    Category,
    CategoryKind,
    Idea,
    IdeaSource,
    IdeaStyle,
)
from apps.editorial.selectors import (
    article_details,
    article_sections,
    published_articles,
    published_ideas,
)
from apps.editorial.services import save_content
from apps.portfolio.demo import attach_demo_image
from apps.portfolio.inspiration import board_ids, board_items


def _require_editor(request: HttpRequest, permission: str) -> None:
    if not request.user.is_staff or not request.user.has_perm(
        f'editorial.{permission}'
    ):
        raise PermissionDenied


def _idea_context(request: HttpRequest, idea: Idea) -> dict[str, object]:
    description = idea.meta_description or idea.description[:300]
    image_url = public_url(request, idea.image.url)
    schema = {
        '@context': 'https://schema.org',
        '@type': 'ImageObject',
        'name': idea.title,
        'description': idea.description,
        'contentUrl': image_url,
        'thumbnailUrl': public_url(request, idea.display_image_url),
        'caption': idea.image_alt,
        'url': public_url(request, idea.get_absolute_url()),
        'creditText': str(idea.get_source_display()),
    }
    return {
        'idea': idea,
        'saved_ids': saved_idea_ids(request),
        'SEO_TITLE': idea.seo_title or f'{idea.title} | ایده‌های تابلو',
        'SEO_DESCRIPTION': description,
        'SEO_IMAGE': image_url,
        'SEO_IMAGE_ALT': idea.image_alt,
        'image_schema': schema,
        'breadcrumb_schema': breadcrumbs(
            request,
            [
                (_('خانه'), '/'),
                (_('گالری الهام'), reverse('editorial:ideas')),
                (idea.title, idea.get_absolute_url()),
            ],
        ),
    }


def _article_context(request: HttpRequest, article: Article) -> dict[str, object]:
    author = (
        {'@type': 'Person', 'name': article.author_name}
        if article.author_name
        else {'@type': 'Organization', 'name': f'تحریریهٔ {settings.SITE_NAME}'}
    )
    schema = {
        '@context': 'https://schema.org',
        '@type': 'BlogPosting',
        'headline': article.title,
        'inLanguage': settings.LANGUAGE_CODE,
        'articleSection': article.category.name,
        'wordCount': len(article.body.split()),
        'description': article.meta_description or article.excerpt,
        'mainEntityOfPage': {
            '@type': 'WebPage',
            '@id': public_url(request, article.get_absolute_url()),
        },
        'author': author,
        'dateModified': article.updated_at.isoformat(),
    }
    if article.published_at:
        schema['datePublished'] = article.published_at.isoformat()
    if article.image:
        schema['image'] = public_url(request, article.image.url)
    schema['publisher'] = {
        '@type': 'Organization',
        'name': settings.SITE_NAME,
        'url': public_url(request, '/'),
    }
    sections = article_sections(article.body)
    return {
        'article': article,
        'author_display': article.author_name or f'تحریریهٔ {settings.SITE_NAME}',
        'saved_ids': saved_idea_ids(request),
        'sections': sections,
        'toc': [section for section in sections if section.heading],
        'SEO_TITLE': article.seo_title or f'{article.title} | مجلهٔ تابلو',
        'SEO_DESCRIPTION': article.meta_description or article.excerpt,
        'SEO_IMAGE': public_url(request, article.image.url) if article.image else '',
        'SEO_IMAGE_ALT': article.image_alt,
        'SEO_TYPE': 'article',
        'article_schema': schema,
        'breadcrumb_schema': breadcrumbs(
            request,
            [
                (_('خانه'), '/'),
                (_('مجلهٔ تابلو'), reverse('editorial:articles')),
                (article.title, article.get_absolute_url()),
            ],
        ),
    }


@require_GET
def ideas(request: HttpRequest, category_slug: str = '') -> HttpResponse:
    query = request.GET.get('q', '').strip()[:80]
    selected_style = request.GET.get('style', '')[:20]
    selected_source = request.GET.get('source', '')[:20]
    service_slug = request.GET.get('service', '')[:140]
    category = (
        get_object_or_404(
            Category, slug=category_slug, kind=CategoryKind.BUSINESS, is_active=True
        )
        if category_slug
        else None
    )
    items = published_ideas()
    if category:
        items = items.filter(category=category)
    if query:
        items = items.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(design_notes__icontains=query)
        )
    if selected_style:
        items = items.filter(style=selected_style)
    if selected_source:
        items = items.filter(source=selected_source)
    if service_slug:
        items = items.filter(service__slug=service_slug)
    page = Paginator(items, 12).get_page(request.GET.get('page'))
    page_items = list(page)
    params = request.GET.copy()
    params.pop('page', None)
    return render(
        request,
        'pages/editorial/ideas.html',
        {
            'page_obj': page,
            'ideas': page_items,
            'featured': page_items[0] if page_items else None,
            'CANONICAL_URL': public_url(
                request,
                request.path + (f'?page={page.number}' if page.number > 1 else ''),
            ),
            'categories': Category.objects.filter(
                kind=CategoryKind.BUSINESS, is_active=True
            ),
            'category': category,
            'query': query,
            'styles': IdeaStyle.choices,
            'sources': IdeaSource.choices,
            'services': Service.objects.filter(is_active=True),
            'selected_style': selected_style,
            'selected_source': selected_source,
            'selected_service': service_slug,
            'saved_ids': saved_idea_ids(request),
            'filter_query': params.urlencode(),
            'SEO_TITLE': f'ایده تابلو برای {category.name}'
            if category
            else 'ایده‌های تابلو برای مغازه‌ها',
            'SEO_DESCRIPTION': category.description
            if category and category.description
            else (
                'ایده‌های تصویری تابلو برای کافه، فروشگاه و کسب‌وکارها؛ '
                'طرح‌های هوش مصنوعی و مفهومی را ببینید و مرجع پروژهٔ خود را پیدا کنید.'
            ),
        },
    )


@require_GET
def idea_detail(request: HttpRequest, slug: str) -> HttpResponse:
    idea = get_object_or_404(published_ideas(), slug=slug)
    context = _idea_context(request, idea)
    context['related'] = (
        published_ideas().filter(category=idea.category).exclude(pk=idea.pk)[:4]
    )
    context['articles'] = published_articles().filter(related_ideas=idea)[:3]
    return render(request, 'pages/editorial/idea.html', context)


@require_GET
def articles(request: HttpRequest, category_slug: str = '') -> HttpResponse:
    query = request.GET.get('q', '').strip()[:80]
    category = (
        get_object_or_404(
            Category, slug=category_slug, kind=CategoryKind.GUIDE, is_active=True
        )
        if category_slug
        else None
    )
    queryset = published_articles()
    if category:
        queryset = queryset.filter(category=category)
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(body__icontains=query)
        )
    page = Paginator(queryset, 9).get_page(request.GET.get('page'))
    items = list(page)
    params = request.GET.copy()
    params.pop('page', None)
    return render(
        request,
        'pages/editorial/articles.html',
        {
            'page_obj': page,
            'articles': items,
            'featured': items[0] if items else None,
            'CANONICAL_URL': public_url(
                request,
                request.path + (f'?page={page.number}' if page.number > 1 else ''),
            ),
            'categories': Category.objects.filter(
                kind=CategoryKind.GUIDE, is_active=True
            ),
            'category': category,
            'query': query,
            'filter_query': params.urlencode(),
            'SEO_TITLE': f'{category.name} | مجلهٔ تابلو'
            if category
            else 'مجلهٔ تابلو؛ راهنمای انتخاب و طراحی تابلو مغازه',
            'SEO_DESCRIPTION': category.description
            if category and category.description
            else (
                'راهنماهای انتخاب تابلو، طراحی سردر، نورپردازی و همکاری با متخصصان؛ '
                'تصمیم‌های روشن‌تر برای مغازهٔ شما.'
            ),
        },
    )


@require_GET
def article_detail(request: HttpRequest, slug: str) -> HttpResponse:
    article = get_object_or_404(article_details(), slug=slug)
    context = _article_context(request, article)
    context['related'] = (
        published_articles()
        .filter(category=article.category)
        .exclude(pk=article.pk)[:3]
    )
    return render(request, 'pages/editorial/article.html', context)


@never_cache
@require_GET
def saved(request: HttpRequest) -> HttpResponse:
    projects = list(board_items(request))
    for project in projects:
        attach_demo_image(project)
    return render(
        request,
        'pages/editorial/saved.html',
        {
            'ideas': list(saved_ideas(request)),
            'items': projects,
            'saved_ids': saved_idea_ids(request),
            'portfolio_saved_ids': board_ids(request),
            'browser_saves': bool(
                browser_reference_ids(request, 'idea')
                or browser_reference_ids(request, 'portfolio_item')
            ),
            'customer_panel_active': 'saved',
        },
    )


@require_POST
def idea_save(request: HttpRequest, pk: int) -> HttpResponse:
    idea = get_object_or_404(published_ideas(), pk=pk)
    action = request.POST.get('action', 'add')
    if action not in {'add', 'remove'}:
        return HttpResponse(_('عملیات ذخیره معتبر نیست.'), status=400)
    stored = save_reference(request, kind="idea", pk=idea.pk, action=action)
    messages.success(request, _("ذخیره‌ها به‌روز شدند.")) if stored else messages.info(
        request, _("۲۴ تصویر ذخیره دارید؛ ابتدا یکی را حذف کنید.")
    )
    if request.POST.get('destination') == 'detail':
        return redirect(idea.get_absolute_url())
    return redirect('editorial:saved')


@require_POST
def idea_request(request: HttpRequest, slug: str) -> HttpResponse:
    idea = get_object_or_404(published_ideas(), slug=slug)
    request.session['request_wizard'] = {
        'compact': True,
        'description': (
            f'مرجع {idea.get_source_display()}: {idea.title}\n'
            f'{public_url(request, idea.get_absolute_url())}\n{idea.description}'
        ),
        'service_id': idea.service_id
        if idea.service and idea.service.is_active
        else None,
    }
    messages.success(
        request, _('ایده به درخواست پروژه اضافه شد؛ مشخصات اجرا را تکمیل کنید.')
    )
    return redirect('requests:wizard_need')


@login_required
@never_cache
@require_GET
def manage(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff or not (
        request.user.has_perm('editorial.view_idea')
        or request.user.has_perm('editorial.view_article')
    ):
        raise PermissionDenied
    ideas_page = Paginator(
        Idea.objects.select_related('category').order_by('-updated_at')
        if request.user.has_perm('editorial.view_idea')
        else Idea.objects.none(),
        20,
    ).get_page(request.GET.get('ideas_page'))
    articles_page = Paginator(
        Article.objects.select_related('category').order_by('-updated_at')
        if request.user.has_perm('editorial.view_article')
        else Article.objects.none(),
        20,
    ).get_page(request.GET.get('articles_page'))
    return render(
        request,
        'pages/editorial/manage.html',
        {'ideas': ideas_page, 'articles': articles_page},
    )


def _content_editor(
    request: HttpRequest, kind: str, pk: int | None = None
) -> HttpResponse:
    model = Idea if kind == 'idea' else Article
    form_class = IdeaForm if kind == 'idea' else ArticleForm
    _require_editor(request, f'{"change" if pk else "add"}_{kind}')
    instance = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None,
        instance=instance,
    )
    if request.method == 'POST' and form.is_valid():
        item = save_content(form=form, actor=request.user)
        messages.success(request, _('محتوا ذخیره شد.'))
        if request.user.has_perm(f'editorial.change_{kind}'):
            return redirect(f'editorial:{kind}_edit', pk=item.pk)
        return redirect(f'editorial:{kind}_create')
    return render(
        request,
        'pages/editorial/editor.html',
        {'form': form, 'kind': kind, 'item': instance},
        status=400 if form.is_bound else 200,
    )


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def idea_create(request: HttpRequest) -> HttpResponse:
    return _content_editor(request, 'idea')


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def idea_edit(request: HttpRequest, pk: int) -> HttpResponse:
    return _content_editor(request, 'idea', pk)


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def article_create(request: HttpRequest) -> HttpResponse:
    return _content_editor(request, 'article')


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def article_edit(request: HttpRequest, pk: int) -> HttpResponse:
    return _content_editor(request, 'article', pk)


@login_required
@never_cache
@require_GET
def preview(request: HttpRequest, kind: str, pk: int) -> HttpResponse:
    if kind not in {'idea', 'article'}:
        raise PermissionDenied
    _require_editor(request, f'view_{kind}')
    item = get_object_or_404(
        Idea.objects.select_related('category', 'service')
        if kind == 'idea'
        else Article.objects.select_related('category', 'service').prefetch_related(
            Prefetch('related_ideas', queryset=published_ideas())
        ),
        pk=pk,
    )
    context = (
        _idea_context(request, item)
        if kind == 'idea'
        else _article_context(request, item)
    )
    context |= {'PAGE_NOINDEX': True, 'is_preview': True}
    response = render(request, f'pages/editorial/{kind}.html', context)
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response


@login_required
@require_POST
def sync_saved(request: HttpRequest) -> HttpResponse:
    pending = import_browser_references(request)
    if pending:
        messages.info(
            request,
            _(
                "بعضی ذخیره‌ها منتقل نشدند؛ ظرفیت حساب پر است. "
                "ابتدا چند تصویر را حذف کنید."
            ),
        )
        return redirect("editorial:saved")
    messages.success(
        request,
        _("ذخیره‌ها به حساب منتقل شدند؛ در دستگاه‌های دیگر هم در دسترس‌اند."),
    )
    return redirect("editorial:saved")
