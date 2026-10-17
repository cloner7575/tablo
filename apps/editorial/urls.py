from django.urls import path

from apps.editorial import views

app_name = 'editorial'

urlpatterns = [
    path('inspiration/', views.ideas, name='ideas'),
    path(
        'inspiration/category/<uslug:category_slug>/', views.ideas, name='idea_category'
    ),
    path('inspiration/saved/sync/', views.sync_saved, name='sync_saved'),
    path('inspiration/saved/', views.saved, name='saved'),
    path('inspiration/manage/', views.manage, name='manage'),
    path('inspiration/manage/ideas/new/', views.idea_create, name='idea_create'),
    path('inspiration/manage/ideas/<int:pk>/', views.idea_edit, name='idea_edit'),
    path(
        'inspiration/manage/articles/new/', views.article_create, name='article_create'
    ),
    path(
        'inspiration/manage/articles/<int:pk>/', views.article_edit, name='article_edit'
    ),
    path(
        'inspiration/manage/<str:kind>/<int:pk>/preview/', views.preview, name='preview'
    ),
    path('inspiration/save/<int:pk>/', views.idea_save, name='idea_save'),
    path('inspiration/<uslug:slug>/request/', views.idea_request, name='idea_request'),
    path('inspiration/<uslug:slug>/', views.idea_detail, name='idea'),
    path('articles/', views.articles, name='articles'),
    path(
        'articles/category/<uslug:category_slug>/',
        views.articles,
        name='article_category',
    ),
    path('articles/<uslug:slug>/', views.article_detail, name='article'),
]
