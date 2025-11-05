from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from keycloak_with_multiroles_docker.users.api.serializers import (
  UserSerializer
)
from keycloak_with_multiroles_docker.users.models import User, StudentProfile
from ..permissions import IsParent, IsAdmin


# Create your views here.

# class RegisterView(APIView):
#   permission_classes = [AllowAny]
#
#   def post(self, request):
#     serializer = RegisterSerializer(data=request.data)
#     if serializer.is_valid():
#       user = serializer.save()
#       return Response({
#         'message':'User registered successfully',
#         'user': UserSerializer(user).data
#         }, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class LoginView(APIView):
#   permission_classes = [AllowAny]
#
#   def post(self, request):
#     username = request.data.get('username')
#     password = request.data.get('password')
#     user = authenticate(request, username=username, password=password)
#
#     if user is not None:
#       login(request, user)
#       return Response({
#         'message':'User logged in successfully',
#         'user': UserSerializer(user).data
#         }, status=status.HTTP_200_OK)
#
#     return Response({
#       'message':'Invalid credentials'
#       }, status=status.HTTP_401_UNAUTHORIZED)
#
# class LogoutView(APIView):
#   permission_classes = [IsAuthenticated]
#
#   def post(self, request):
#     logout(request)
#     return Response({
#       'message':'User logged out successfully'
#       }, status=status.HTTP_200_OK)

class CurrentUserView(APIView):
  """
      Works for both Django session users and Keycloak JWT users
  """
  permission_classes = [IsAuthenticated]

  def get(self, request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


class ParentChildrenView(APIView):
  permission_classes = [IsAuthenticated, IsParent]

  def get(self, request):
    # Get StudentProfile objects where parent is the current user
    children_profiles = StudentProfile.objects.filter(parent=request.user)
    children_users = [profile.user for profile in children_profiles]
    serializer = UserSerializer(children_users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class AllUsersView(APIView):
  permission_classes = [IsAuthenticated, IsAdmin]

  def get(self, request):
    """ Admin can view all users"""
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailView(APIView):
  permission_classes = [IsAuthenticated, IsAdmin]

  def get(self, request, pk):
    """ Admin can view specific user details. """
    try:
      user = User.objects.get(pk=pk)
      serializer = UserSerializer(user)
      return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
      return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

  def delete(self, request, pk):
    """ Admin can delete a user. """
    try:
      user = User.objects.get(pk=pk)
      user.delete()
      return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
      return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
