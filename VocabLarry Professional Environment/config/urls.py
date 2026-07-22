from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config.views import home, reading, writing, listening, speaking, verify_email, reset_password
from config.views_vocab import (
    vocab_browse, vocab_category, vocab_word_detail,
    vocab_quiz_setup, vocab_quiz_play,
    vocabulary_home, vocabulary_word_list,
)
from config.views_grammar import (
    grammar_browse, grammar_topic_detail, grammar_topic_quiz,
    grammar_test_setup, grammar_test_play,
    grammar_home, grammar_word,
)

urlpatterns = [
    path('', home, name='home'),

    path('vocabulary/', vocabulary_home, name='vocabulary_home'),
    path('vocabulary/category/', vocab_browse, name='vocabulary_category_list'),
    path('vocabulary/category/<slug:slug>/', vocab_category, name='vocabulary_category_detail'),
    path('vocabulary/word/', vocabulary_word_list, name='vocabulary_word_list'),
    path('vocabulary/word/<int:pk>/', vocab_word_detail, name='vocabulary_word_detail'),
    path('vocabulary/quiz/', vocab_quiz_setup, name='vocabulary_quiz_setup'),
    path('vocabulary/quiz/play/', vocab_quiz_play, name='vocabulary_quiz_play'),

    path('grammar/', grammar_home, name='grammar_home'),
    path('grammar/category/', grammar_browse, name='grammar_category_list'),
    path('grammar/category/<slug:slug>/', grammar_topic_detail, name='grammar_category_detail'),
    path('grammar/category/<slug:slug>/quiz/', grammar_topic_quiz, name='grammar_category_quiz'),
    path('grammar/word/', grammar_word, name='grammar_word'),
    path('grammar/quiz/', grammar_test_setup, name='grammar_quiz_setup'),
    path('grammar/quiz/play/', grammar_test_play, name='grammar_quiz_play'),

    path('reading/', reading, name='reading'),
    path('writing/', writing, name='writing'),
    path('listening/', listening, name='listening'),
    path('speaking/', speaking, name='speaking'),

    path('verify-email/<str:key>/', verify_email, name='verify_email'),
    path('reset-password/<str:key>/', reset_password, name='reset_password'),

    path('accounts/', include('allauth.urls')),
    path('_allauth/', include('allauth.headless.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
