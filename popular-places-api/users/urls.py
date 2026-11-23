from django.urls import path
from .views import RegisterView, LogoutView, LoginView, CsrfView, MeView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('login/', LoginView.as_view()),
    path('csrf/', CsrfView.as_view()),
    path('me/', MeView.as_view())
]