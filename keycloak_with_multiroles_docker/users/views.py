from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView


class KeycloakConfigView(APIView):
  """
      Endpoint to provide keycloak configuration to frontend
  """
  permission_classes = [AllowAny]

  def get(self, request):
    return Response({
      'serverUrl': settings.KEYCLOAK_SERVER_URL,
      'realm': settings.KEYCLOAK_REALM,
      'clientId': settings.KEYCLOAK_CLIENT_ID,
    }, status=status.HTTP_200_OK
    )


class TokenValidationView(APIView):
  """
  Endpoint to validate token and return user info
  Frontend can call this after getting token from keycloak
  """

  permission_classes = [IsAuthenticated]

  def get(self, request):
    from keycloak_with_multiroles_docker.users.api.serializers import UserSerializer
    return Response({
      'valid': True,
      'user': UserSerializer(request.user).data
    }, status=status.HTTP_200_OK)
