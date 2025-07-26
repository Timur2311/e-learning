from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Case, Count, Value, When
from django_filters import rest_framework as filters
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .filters import CourseFilter
from .models import Course, Lesson
from .serializers import (CourseDetailSerializer, CourseSerializer,
                          LessonSerializer)

User = get_user_model()


class CourseModelViewSet(viewsets.ModelViewSet):
    model = Course
    queryset = Course.objects.filter(is_published=True).prefetch_related("enrollments")
    serializer_class = CourseSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CourseFilter

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

        if user.is_authenticated and user.is_student:
            queryset = queryset.annotate(
                is_enrolled=Case(
                    When(enrollments__user=user, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        course = self.get_object()
        if not user.is_authenticated:
            raise serializers.ValidationError(
                "You must be authenticated to see course details."
            )
        is_enrolled = course.get_is_enrolled(user)
        if user.is_authenticated and not user.is_instructor and not is_enrolled:
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                description="ID of the user to calculate progress for",
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            )
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        operation_id="getCourseProgress",
    )
    @action(detail=True, methods=["get"])
    def get_progress(self, request, pk=None):
        from django.shortcuts import get_object_or_404

        from enrollments.models import LessonProgress

        user_id = request.GET.get("user_id")
        if user_id is None:
            raise serializers.ValidationError("user_id parameter is required.")
        user = get_object_or_404(User, pk=user_id)

        course = self.get_object()
        lessons_count = course.lessons.count()
        completed_lessons = LessonProgress.objects.filter(
            user=user, lesson__course=course, completed=True
        ).count()
        progress = (completed_lessons / lessons_count) * 100 if lessons_count > 0 else 0
        return Response(
            {
                "progress": progress,
                "completed_lessons": completed_lessons,
                "lessons_count": lessons_count,
            }
        )


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

    @action(detail=True, methods=["post"])
    def mark_as_completed(self, request, pk=None):
        from enrollments.models import LessonProgress

        LessonProgress.objects.update_or_create(
            user=request.user,
            lesson=self.get_object(),
            defaults={"completed": True},
        )
        return Response({"status": "lesson completed"})
