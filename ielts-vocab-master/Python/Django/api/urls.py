from django.urls import path
from . import views

urlpatterns = [
    path('words/', views.words, name='api_words'),
    path('categories/', views.categories, name='api_categories'),
    path('cefr-levels/', views.cefr_levels, name='api_cefr_levels'),
    path('grammar/', views.grammar, name='api_grammar'),
]
