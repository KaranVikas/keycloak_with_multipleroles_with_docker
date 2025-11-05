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
      'serverUrl': settings.KEYCLOAK_SERVER,
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


class KeycloakSyncUserView(APIView):
  """
    Endpoint to sync user from keycloak to Django database
    Called after user registers/logs in via keycloak
  """

  permission_classes = [IsAuthenticated]

  def post(self, request):
    from keycloak_with_multiroles_docker.users.api.serializers import UserSerializer

    user = request.user
    # User is already created/updated by the authentication backend
    # just return the user data
    return Response({
      'valid': True,
      'user': UserSerializer(user).data,
      'message': 'User synced successfully'
    }, status=status.HTTP_200_OK)
