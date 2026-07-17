from django.urls import path
from . import views, write_views

urlpatterns = [
    path('words/', views.words, name='api_words'),
    path('words/<int:pk>/', write_views.word_detail, name='api_word_detail'),
    path('categories/', views.categories, name='api_categories'),
    path('categories/<int:pk>/', write_views.category_detail, name='api_category_detail'),
    path('cefr-levels/', views.cefr_levels, name='api_cefr_levels'),
    path('grammar/', views.grammar, name='api_grammar'),
    path('grammar/topics/', write_views.grammar_topic_create, name='api_grammar_topic_create'),
    path('grammar/topics/<int:pk>/', write_views.grammar_topic_detail, name='api_grammar_topic_detail'),
    path('grammar/blocks/', write_views.grammar_block_create, name='api_grammar_block_create'),
    path('grammar/blocks/<int:pk>/', write_views.grammar_block_detail, name='api_grammar_block_detail'),
    path('grammar/questions/', write_views.grammar_question_create, name='api_grammar_question_create'),
    path('grammar/questions/<int:pk>/', write_views.grammar_question_detail, name='api_grammar_question_detail'),
]
