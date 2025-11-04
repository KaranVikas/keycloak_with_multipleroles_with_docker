from rest_framework import serializers
from ..models import User, StudentProfile, ParentProfile

class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ['id','username', 'email', 'first_name', 'last_name', 'user_type', 'phone']
    read_only_fields = ['id']

class StudentProfileSerializer(serializers.ModelSerializer):
  parent_name = serializers.CharField(source='parent.username', read_only=True)
  class Meta:
    model = StudentProfile
    fields = ['user','grade','parent','parent_name']

class ParentProfileSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  children = serializers.SerializerMethodField()

  class Meta:
    model = ParentProfile
    fields = ['id','user','occupation','children']

  def get_children(self, obj):
    children = obj.children.all()
    return [{'id': child.user.id , 'username': child.user.username} for child in children]

class RegisterSerializer(serializers.ModelSerializer):

  password = serializers.CharField(write_only=True)
  parent_id = serializers.IntegerField(write_only=True, required=False)
  grade = serializers.CharField(write_only=True,  required=False)
  occupation = serializers.CharField(write_only=True,  required=False)

  class Meta:
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'password', 'user_type', 'phone', 'parent_id', 'grade', 'occupation']

  def create(self, validated_data):
    parent_id = validated_data.pop('parent_id', None)
    grade = validated_data.pop('grade', None)
    occupation = validated_data.pop('occupation', None)
    password = validated_data.pop('password')

    user = User.objects.create(**validated_data)
    user .set_password(password)
    user.save()

    # Create profile based on user type
    if user.user_type == 'student':
      parent = None
      if parent_id:
        parent = User.objects.filter(id=parent_id, user_type='parent').first()
      StudentProfile.objects.create(user=user, grade=grade or '', parent=parent)

    elif user.user_type == 'parent':
      ParentProfile.objects.create(user=user, occupation=occupation or '')

    return user
