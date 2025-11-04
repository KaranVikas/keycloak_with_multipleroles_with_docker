from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
  """
    Permission to check for student users
  """
  def has_permission(self, request, view):
    return request.user.is_authenticated and request.user.user_type == 'student'

class IsParent(BasePermission):
  """ Permission to check for parent users """
  def has_permission(self, request, view):
    return request.user.is_authenticated and request.user.user_type == 'parent'

class IsAdmin(BasePermission):
  """ Permission to check for admin users """
  def has_permission(self, request, view):
    return request.user.is_authenticated and request.user.user_type == 'admin'

class IsOwnerOrParent(BasePermission):
  """ Allow students to access their own todos."""

  def has_object_permission(self, request, view, obj):
    user = request.user

    # admin can access everything
    if user.user_type == 'admin':
      return True

    # student can only access their own todos
    if user.user_type == 'student':
      return obj.student == user

    # parent can access all their children's todos
    if user.user_type == 'parent':
      children_ids = user.children.values_list('user_id', flat=True)
      return obj.student_id in children_ids or obj.user == user

    return False
