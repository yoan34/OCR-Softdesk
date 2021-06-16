from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    TYPE_CHOICES = (
        ('back-end', 'Back-end'),
        ('front-end', 'Front-end'),
        ('ios', 'iOS'),
        ('android', 'Android')
    )
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    type = models.CharField(max_length=9, choices=TYPE_CHOICES, default='back-end')


class Contributor(models.Model):
    ROLE_CHOICES = (
        ('author', 'Author'),
        ('contributor', 'Contributor'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributors')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contributors')
    role = models.CharField(max_length=11, choices=ROLE_CHOICES, default='author')


class Issue(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    TAG_CHOICES = (
        ('bug', 'Bug'),
        ('improvement', 'Improvement'),
        ('task', 'Task'),
    )
    STATUS_CHOICES = (
        ('to do', 'To do'),
        ('in progress', 'In progress'),
        ('finished', 'Finished'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='issues', null=True)
    assigned = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default='medium')
    tag = models.CharField(max_length=11, choices=TAG_CHOICES, default='task')
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default='to do')
    created_time = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='comments', null=True)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    created_time = models.DateTimeField(auto_now_add=True)
