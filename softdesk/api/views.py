from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework import mixins
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework.response import Response

from .models import Comment, Issue, Project, Contributor
from .permissions import (IsProjectOwnerOrContributorReadOnly,
                          IsIssueOwnerOrContributorReadOnly,
                          IsCommentOwnerOrContributorReadOnly)
from .serializers import CommentSerializer, IssueSerializer, UserSerializer, ContributorSerializer, ProjectSerializer


class CustomListMixin:
    def get(self, request, is_comment=False, *args, **kwargs):
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            user = Contributor.objects.get(project=project, user=request.user)
        except Project.DoesNotExist:
            return Response({"detail": f"Project with id '{self.kwargs['pk']}' doesn't exist."},
                            status=status.HTTP_404_NOT_FOUND)
        except Contributor.DoesNotExist:
            return Response({"detail": "You are not collaborate on this project."},
                            status=status.HTTP_404_NOT_FOUND)

        if is_comment:
            try:
                Issue.objects.get(id=self.kwargs['issue_id'])
            except Issue.DoesNotExist:
                return Response({"detail": f"Issue with id '{self.kwargs['issue_id']}' doesn't exist."})

        self.check_object_permissions(request, user)
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContributorList(CustomListMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsProjectOwnerOrContributorReadOnly]

    def get_queryset(self):
        return Contributor.objects.filter(project_id=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        try:
            new_contributor = User.objects.get(username=request.data['username'])
            project = Project.objects.get(id=self.kwargs['pk'])
        except Project.DoesNotExist:
            return Response({"detail": f"Project with id '{self.kwargs['pk']}' doesn't exist."},
                            status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"detail": f"Username '{request.data['username']}' doesn't exist."},
                            status=status.HTTP_404_NOT_FOUND)

        contributor = Contributor.objects.filter(user=new_contributor, project=project).exists()
        if contributor:
            return Response({'detail': f"{new_contributor.username} already contribute \
                            to the project '{project.title}'."},
                            status=status.HTTP_409_CONFLICT)

        try:
            user = Contributor.objects.get(project=project, user=request.user)
        except Contributor.DoesNotExist:
            return Response({"detail": "You are not collaborate on this project."},
                            status=status.HTTP_404_NOT_FOUND)

        contributor = Contributor(user=new_contributor, project=project, role='contributor')
        self.check_object_permissions(request, user)
        contributor.save()
        serializer = self.serializer_class(contributor)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ContributorDetail(mixins.DestroyModelMixin, generics.GenericAPIView):
    """
    Donner permissions de supprimé un collaborateur du projet
    """
    queryset = Contributor.objects.all()
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsProjectOwnerOrContributorReadOnly]

    def delete(self, request, *args, **kwargs):
        # Verifier si c'est bien fini, normalement oui
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            user = Contributor.objects.get(user=request.user, project=project)
            author = Contributor.objects.filter(project=project).filter(role='author')[0]
        except Contributor.DoesNotExist:
            return Response({"detail": "You are not collaborate on this project."},
                            status=status.HTTP_404_NOT_FOUND)

        except Project.DoesNotExist:
            return Response({'detail': "This project doesn't exist."},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            del_contributor = Contributor.objects.get(user_id=self.kwargs['user_id'], project_id=self.kwargs['pk'])
        except Contributor.DoesNotExist:
            return Response({"detail": "This contributor doesn't exist in this project."},
                            status=status.HTTP_404_NOT_FOUND)

        if user == author and author == del_contributor:
            return Response({"detail": "Can't delete the author of this project."})
        self.check_object_permissions(request, user)
        del_contributor.delete()
        return Response({'detail': 'contributor deleled successfully'}, status=status.HTTP_204_NO_CONTENT)


class UserRegister(mixins.CreateModelMixin, generics.GenericAPIView):
    """
    Register a new user. DONE
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ProjectList(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieve all project on the user logged, is DONE.
        """
        projects_id = Contributor.objects.filter(user=request.user, role='author').values_list('project_id', flat=True)
        projects = Project.objects.filter(id__in=projects_id)
        serializer = self.serializer_class(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        Create a project, is DONE.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        contributor = Contributor.objects.create(user=request.user, project=project)
        contributor.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsProjectOwnerOrContributorReadOnly]

    def get_project_or_error(self, request):
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            user = Contributor.objects.get(user=request.user, project=project)
        except Contributor.DoesNotExist:
            return Response({"detail": "You are not collaborate on this project."},
                            status=status.HTTP_404_NOT_FOUND)
        except Project.DoesNotExist:
            return Response({'detail': "This project doesn't exist."},
                            status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, user)
        return project

    def get(self, request, *args, **kwargs):
        project_or_error = self.get_project_or_error(request)
        if isinstance(project_or_error, Response):
            return project_or_error
        serializer = self.serializer_class(project_or_error)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        project_or_error = self.get_project_or_error(request)
        if isinstance(project_or_error, Response):
            return project_or_error
        serializer = self.serializer_class(project_or_error, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        project_or_error = self.get_project_or_error(request)
        if isinstance(project_or_error, Response):
            return project_or_error
        project_or_error.delete()
        return Response({'detail': 'project deleled successfully'}, status=status.HTTP_204_NO_CONTENT)


class IssueList(CustomListMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Issue.objects.filter(project_id=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            user = Contributor.objects.get(project=project, user=request.user)
        except Project.DoesNotExist:
            return Response({"detail": f"Project with id '{self.kwargs['pk']}' doesn't exist."},
                            status=status.HTTP_404_NOT_FOUND)
        except Contributor.DoesNotExist:
            return Response({"detail": "You are not collaborate on this project."},
                            status=status.HTTP_404_NOT_FOUND)

        print(request.data)
        if request.data['assigned']:
            try:
                assigned = User.objects.get(username=request.data['assigned'])
                Contributor.objects.get(user=assigned, project=project)
            except User.DoesNotExist:
                return Response({"detail": f"User with username '{request.data['assigned']}' doesn't exist. "},
                                status=status.HTTP_404_NOT_FOUND)
            except Contributor.DoesNotExist:
                return Response({"detail": "The assigned user doesn't contribute to the project."},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            assigned = request.user

        self.check_object_permissions(request, user)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(project=project, author=request.user, assigned=assigned)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IssueDetail(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  generics.GenericAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated, IsIssueOwnerOrContributorReadOnly]

    def get_issue_or_error(self, request):
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            Contributor.objects.get(user=request.user, project=project)
            issue = Issue.objects.get(id=self.kwargs['issue_id'], project=project)
        except Contributor.DoesNotExist:
            return Response({"detail": "You are not collaborate on this project."}, status=status.HTTP_404_NOT_FOUND)
        except Project.DoesNotExist:
            return Response({'detail': "This project doesn't exist."}, status=status.HTTP_404_NOT_FOUND)
        except Issue.DoesNotExist:
            return Response({"detail": "This issue doesn't exist."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, issue)
        return issue

    def get(self, request, *args, **kwargs):
        issue_or_error = self.get_issue_or_error(request)
        if isinstance(issue_or_error, Response):
            return issue_or_error
        serializer = self.serializer_class(issue_or_error)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        issue_or_error = self.get_issue_or_error(request)
        if isinstance(issue_or_error, Response):
            return issue_or_error
        if request.data['assigned']:
            try:
                assigned = User.objects.get(username=request.data['assigned'])
                project = Project.objects.get(id=self.kwargs['pk'])
                Contributor.objects.get(user=assigned, project=project)
            except User.DoesNotExist:
                return Response({"detail": f"User with username '{request.data['assigned']}' doesn't exist. "},
                                status=status.HTTP_404_NOT_FOUND)
            except Contributor.DoesNotExist:
                return Response({"detail": "The assigned user doesn't contribute to the project."},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            assigned = issue_or_error.assigned
        serializer = self.serializer_class(issue_or_error, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(assigned=assigned)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        issue_or_error = self.get_issue_or_error(request)
        if isinstance(issue_or_error, Response):
            return issue_or_error
        issue_or_error.delete()
        return Response({'detail': 'issue deleled successfully'}, status=status.HTTP_204_NO_CONTENT)


class CommentList(CustomListMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(issue_id=self.kwargs['issue_id'])

    def get(self, request, *args, **kwargs):
        return super().get(request, is_comment=True, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            user = Contributor.objects.get(project=project, user=request.user)
            issue = Issue.objects.get(project=project, id=self.kwargs['issue_id'])
        except Project.DoesNotExist:
            return Response({"detail": f"Project with id '{self.kwargs['pk']}' doesn't exist."},
                            status=status.HTTP_404_NOT_FOUND)
        except Contributor.DoesNotExist:
            return Response({"detail": "You are not collaborate on this project."},
                            status=status.HTTP_404_NOT_FOUND)
        except Issue.DoesNotExist:
            return Response({"detail": f"Issue with id '{self.kwargs['issue_id']}' doesn't exist."})

        self.check_object_permissions(request, user)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, issue=issue)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentOwnerOrContributorReadOnly]

    def get_comment_or_error(self, request):
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            Contributor.objects.get(user=request.user, project=project)
            issue = Issue.objects.get(id=self.kwargs['issue_id'], project=project)
            comment = Comment.objects.get(id=self.kwargs['comment_id'], issue=issue)
        except Contributor.DoesNotExist:
            return Response({"detail": "You are not collaborate on this project."}, status=status.HTTP_404_NOT_FOUND)
        except Project.DoesNotExist:
            return Response({'detail': "This project doesn't exist."}, status=status.HTTP_404_NOT_FOUND)
        except Issue.DoesNotExist:
            return Response({"detail": "This issue doesn't exist."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"detail": "This comment does't exist."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, comment)
        return comment

    def get(self, request, *args, **kwargs):
        comment_or_error = self.get_comment_or_error(request)
        if isinstance(comment_or_error, Response):
            return comment_or_error
        serializer = self.serializer_class(comment_or_error)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        comment_or_error = self.get_comment_or_error(request)
        if isinstance(comment_or_error, Response):
            return comment_or_error
        serializer = self.serializer_class(comment_or_error, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        comment_or_error = self.get_comment_or_error(request)
        if isinstance(comment_or_error, Response):
            return comment_or_error
        comment_or_error.delete()
        return Response({"detail": "comment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
