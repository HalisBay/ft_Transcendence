from django.urls import path, re_path
from django.views.generic import TemplateView
from django.conf import settings
from . import views
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.index_page, name="index"),
    path("home", views.home_page, name="home"),
    path("register", views.register_user, name="register"),
    path("login", views.login_user, name="login"),
    path("activate/<str:uidb64>/<str:token>/", views.activate_user, name="activate_user"),
    path("verify", views.verify_page, name="verify_page"),
    path("user", views.user_page, name="user"),
    path("logout", views.logout_page, name="logout"),
    path("notverified", views.verify_fail, name="not_verified"),
    path("user/activate2fa", views.activate_2fa, name="user_2fa"),
    path("user/update", views.update, name="update"),
    path("user/update_user", views.update_user, name="update_user"),
    path("user/delete", views.delete_all, name="delete"),
    path("anonymize_account", views.anonymize_account, name="anonymize_account"),
    path("gdpr", views.gdpr_page, name="gdpr"),
    path("about", views.about_page, name="about"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
