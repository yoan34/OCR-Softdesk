from django.contrib import admin
from .models import Comment, Issue, Project, Contributor


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'title')


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role')
    raw_id_fields = ('user',)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'assigned', 'priority', 'tag', 'created_time')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'issue', 'description', 'created_time')
