from django.urls import path
from . import views

urlpatterns = [
    path('session/', views.session, name='auth_session'),
    path('sync/', views.sync, name='auth_sync'),
    path('update-profile/', views.update_profile, name='auth_update_profile'),
    path('delete-account/', views.delete_account, name='auth_delete_account'),
    path('check-email/', views.check_email, name='auth_check_email'),
]
