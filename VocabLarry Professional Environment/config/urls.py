from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config.views import home
from config.views_vocab import (
    vocab_browse, vocab_category, vocab_word_detail,
    vocab_quiz_setup, vocab_quiz_play,
)

urlpatterns = [
    path('', home, name='home'),
    path('vocab/', vocab_browse, name='vocab_browse'),
    path('vocab/category/<slug:slug>/', vocab_category, name='vocab_category'),
    path('vocab/word/<int:pk>/', vocab_word_detail, name='vocab_word_detail'),
    path('vocab/quiz/', vocab_quiz_setup, name='vocab_quiz_setup'),
    path('vocab/quiz/play/', vocab_quiz_play, name='vocab_quiz_play'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
