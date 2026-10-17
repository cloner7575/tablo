from django.contrib import admin
from django.http import HttpRequest

from apps.editorial.forms import ArticleForm, IdeaForm
from apps.editorial.models import Article, Category, Idea


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'is_active', 'sort_order')
    list_filter = ('kind', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    form = IdeaForm
    list_display = ('title', 'category', 'source', 'style', 'status', 'is_featured')
    list_filter = ('status', 'category', 'source', 'style')
    search_fields = ('title', 'description', 'slug')
    list_select_related = ('category', 'service', 'created_by')
    readonly_fields = (
        'published_at',
        'created_at',
        'updated_at',
        'thumbnail',
        'created_by',
    )
    list_per_page = 30

    def save_model(
        self, request: HttpRequest, obj: Idea, form: IdeaForm, change: bool
    ) -> None:
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleForm
    list_display = ('title', 'category', 'status', 'published_at', 'is_featured')
    list_filter = ('status', 'category')
    search_fields = ('title', 'body', 'slug')
    list_select_related = ('category', 'service', 'created_by')
    readonly_fields = (
        'published_at',
        'created_at',
        'updated_at',
        'thumbnail',
        'created_by',
    )
    list_per_page = 30

    def save_model(
        self, request: HttpRequest, obj: Article, form: ArticleForm, change: bool
    ) -> None:
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
