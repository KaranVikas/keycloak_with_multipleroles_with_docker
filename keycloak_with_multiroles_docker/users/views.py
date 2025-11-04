from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


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
