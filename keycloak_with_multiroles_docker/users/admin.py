from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, ParentProfile

# Register your models here.
class UserAdmin(BaseUserAdmin):
  list_display = ['email', 'username', 'user_type','is_staff']
  list_filter = ['user_type', 'is_staff', 'is_superuser']
  fieldsets = BaseUserAdmin.fieldsets + (
  ('Custom Fields', {'fields': ('phone','user_type')}),
  )
  add_fieldsets = BaseUserAdmin.add_fieldsets + (
    ('Custom Fields' ,{'fields': ('user_type', 'phone')})
  )

admin.site.register(User, UserAdmin)
admin.site.register(StudentProfile)
admin.site.register(ParentProfile)
