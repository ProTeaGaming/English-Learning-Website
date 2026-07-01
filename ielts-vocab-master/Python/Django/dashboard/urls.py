from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard_index'),
    path('words/', views.word_list, name='dashboard_word_list'),
    path('words/add/', views.word_add, name='dashboard_word_add'),
    path('words/<int:pk>/edit/', views.word_edit, name='dashboard_word_edit'),
    path('words/<int:pk>/delete/', views.word_delete, name='dashboard_word_delete'),
    path('categories/', views.category_list, name='dashboard_category_list'),
    path('categories/add/', views.category_add, name='dashboard_category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='dashboard_category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='dashboard_category_delete'),
    path('colors/', views.color_list, name='dashboard_color_list'),
    path('colors/add/', views.color_form, name='dashboard_color_add'),
    path('colors/<int:pk>/edit/', views.color_form, name='dashboard_color_edit'),
    path('cefr-levels/', views.cefr_list, name='dashboard_cefr_list'),
    path('users/', views.user_list, name='dashboard_user_list'),
    path('users/<int:pk>/', views.user_detail, name='dashboard_user_detail'),
]
