from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from api import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('signin/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('signup/', views.UserRegister.as_view()),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('projects/', views.ProjectList.as_view()),
    path('projects/<int:pk>', views.ProjectDetail.as_view()),
    path('projects/<int:pk>/users/', views.ContributorList.as_view()),
    path('projects/<int:pk>/users/<int:user_id>', views.ContributorDetail.as_view()),
    path('projects/<int:pk>/issues/', views.IssueList.as_view()),
    path('projects/<int:pk>/issues/<int:issue_id>', views.IssueDetail.as_view()),
    path('projects/<int:pk>/issues/<int:issue_id>/comments/', views.CommentList.as_view()),
    path('projects/<int:pk>/issues/<int:issue_id>/comments/<int:comment_id>', views.CommentDetail.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
