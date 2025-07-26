from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CourseModelViewSet, LessonViewSet

router = DefaultRouter()
router.register(r"lessons", LessonViewSet, basename="lesson")
router.register(r"", CourseModelViewSet, basename="course")

urlpatterns = [
    path("", include(router.urls), name="course-list-create"),
]
