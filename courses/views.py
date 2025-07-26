from django.db.models import Count
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Course, Lesson
from .serializers import CourseDetailSerializer, CourseSerializer, LessonSerializer


class CourseModelViewSet(viewsets.ModelViewSet):
    model = Course
    queryset = Course.objects.filter(is_published=True)
    serializer_class = CourseSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_serializer_class(self):
        if self.action in ["retrieve", "update", "partial_update"]:
            return CourseDetailSerializer
        return CourseSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.is_instructor:
            return Course.objects.filter(instructor=user).annotate(
                lessons_count=Count("lessons", distinct=True)
            )
        queryset = queryset.annotate(lessons_count=Count("lessons", distinct=True))
        return queryset

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        course = self.get_object()
        if not user.is_authenticated:
            raise serializers.ValidationError(
                "You must be authenticated to see course details."
            )
        if (
            user.is_authenticated
            and not user.is_instructor
            and not course.is_enrolled(user)
        ):
            raise serializers.ValidationError(
                "To see course details you must be enroll it."
            )
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        # in future we can add some custom logic maybe
        course = self.get_object()
        if not course.lessons.exists():
            raise serializers.ValidationError(
                "You can not publish course without lessons."
            )
        course.is_published = True
        course.save()
        return Response({"status": "course published"})

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        if not user.is_authenticated:
            raise serializers.ValidationError("You must be authenticated to enroll.")
        if user.is_authenticated and not user.is_student:
            raise serializers.ValidationError(
                "You must be a student to enroll in a course."
            )
        course.create_enrollment(request.user)
        return Response({"status": "enrollment created"})


class LessonViewSet(viewsets.ModelViewSet):
    model = Lesson
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_student:
            queryset = queryset.filter(
                is_active=True, course__enrollments__user=user
            ).distinct()
        if user.is_instructor:
            queryset = queryset.filter(course__instructor=user)
        return queryset

    def perform_create(self, serializer):
        if not self.request.user.is_instructor:
            raise PermissionDenied
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        if not self.request.user.is_instructor:
            raise PermissionDenied
        return super().perform_update(serializer)
