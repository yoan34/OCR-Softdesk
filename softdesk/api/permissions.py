from rest_framework import permissions


class IsObjectOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True if obj.author == request.user else False


class IsProjectOwnerOrContributorReadOnly(permissions.BasePermission):
    message = "You're not the author"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return True if obj.role == 'author' else False


class IsIssueOwnerOrContributorReadOnly(IsObjectOwnerOrReadOnly):
    message = "You're not author of this issue."


class IsCommentOwnerOrContributorReadOnly(IsObjectOwnerOrReadOnly):
    message = "You're not author of this comment."
