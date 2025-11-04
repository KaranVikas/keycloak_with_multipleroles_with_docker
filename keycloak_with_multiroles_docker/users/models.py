from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
  USER_TYPE_CHOICES = (
    ('student', 'Student'),
    ('teacher', 'Teacher'),
    ('admin', 'Admin'),
 )

  user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
  phone = models.CharField(max_length=10, blank=True)

  #keycloak fields
  keycloak_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
  name = models.CharField(max_length=255, null=True, blank=True)

  # Fix the clash by adding related_name
  groups = models.ManyToManyField(
    'auth.Group',
    verbose_name='groups',
    blank=True,
    help_text='The groups this user belongs to.',
    related_name='custom_user_set',
    related_query_name='custom_user',
  )
  user_permissions = models.ManyToManyField(
    'auth.Permission',
    verbose_name='user permissions',
    blank=True,
    help_text='Specific permissions for this user.',
    related_name='custom_user_set',
    related_query_name='custom_user',
  )

  def __str__(self):
    return f"{self.username} ({self.user_type}) "

class StudentProfile(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
  grade = models.CharField(max_length=10)
  parent = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='children',
    limit_choices_to={'user_type': 'parent'},
  )

  def __str__(self):
    return f"{self.user.username} ({self.grade})"

class ParentProfile(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
  occupation = models.CharField(max_length=100, blank=True)

  def __str__(self):
    return f"{self.user.username} ({self.occupation})"
