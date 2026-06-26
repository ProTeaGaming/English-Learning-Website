from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard_index'),
    path('words/', views.word_list, name='dashboard_word_list'),
    path('words/add/', views.word_add, name='dashboard_word_add'),
    path('words/<int:pk>/edit/', views.word_edit, name='dashboard_word_edit'),
    path('words/<int:pk>/delete/', views.word_delete, name='dashboard_word_delete'),
]
