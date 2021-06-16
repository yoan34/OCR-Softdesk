from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Comment, Issue, Project, Contributor


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'password2']
        extra_kwargs = {'first_name': {'default': ''},
                        'last_name': {'default': ''},
                        'email': {'default': ''}}

    def save(self):
        password = self.validated_data['password']
        password2 = self.validated_data.popitem('password2')[1]
        user = User(**self.validated_data)

        if password != password2:
            raise serializers.ValidationError({'password': 'Passwords nuch match.'})
        user.set_password(password)
        user.save()
        return user


class ContributorSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False, read_only=True)

    class Meta:
        model = Contributor
        fields = ['user', 'id', 'user_id', 'role']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_representation = representation.pop('user')
        for key in user_representation:
            representation[key] = user_representation[key]
        return representation

    def to_internal_value(self, data):
        profile_internal = {}
        for key in UserSerializer.Meta.fields:
            if key in data:
                profile_internal[key] = data.pop(key)
        internal = super().to_internal_value(data)
        internal['profile'] = profile_internal
        return internal

    def update(self, instance, validate_data):
        user_data = validate_data.pop('user')
        super().update(instance, validate_data)
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ['id', 'author', 'description', 'created_time']


class IssueSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    author = UserSerializer(required=False)
    assigned = UserSerializer(required=False)

    class Meta:
        model = Issue
        fields = ['id', 'author', 'assigned', 'title', 'description', 'priority', 'tag', 'status',
                  'created_time', 'comments']
        extra_kwargs = {'author': {'default': ''},
                        'assigned': {'default': ''}}


class ProjectSerializer(serializers.ModelSerializer):
    contributors = ContributorSerializer(many=True, read_only=True)
    issues = IssueSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'type', 'contributors', 'issues']
