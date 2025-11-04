from django.urls import path

from .api.views import (
  RegisterView,
  LoginView,
  LogoutView,
  CurrentUserView,
  ParentChildrenView,
  AllUsersView,
  UserDetailView
)
from .views import TokenValidationView, KeycloakConfigView

app_name = "users"
urlpatterns = [

  #   Keycloak Endpoints

  path('auth/keycloak/config/', KeycloakConfigView.as_view(), name='keycloak_config'),
  path('auth/validate/', TokenValidationView.as_view(), name='keycloak_token_validate'),

  #   Existing endpoints
  path('register/', RegisterView.as_view(), name='register'),
  path('login/', LoginView.as_view(), name='login'),
  path('logout/', LogoutView.as_view(), name='logout'),
  path('me/', CurrentUserView.as_view(), name='current_user'),
  path('parentchildren/', ParentChildrenView.as_view(), name='parent_children'),
  path('users/', AllUsersView.as_view(), name='all_users'),
  path('user/<int:pk>/', UserDetailView.as_view(), name='user_detail')
]
