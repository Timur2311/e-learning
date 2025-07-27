from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from courses.models import Course, Lesson
from users.serializers import UserSerializer


class CourseLessonCreateUpdateSerializer(serializers.Serializer):
    """
    Serializer for creating or updating lessons in a course.
    This serializer is used when creating or updating lessons within a course context.
    """

    id = serializers.IntegerField()
    is_active = serializers.BooleanField()


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = (
            "id",
            "title",
            "course",
            "description",
            "video_url",
            "content",
            "is_active",
        )

    def validate(self, attrs):
        instance = self.instance
        video_url = attrs.get("video_url", None)
        content = attrs.get("content", None)

        request = self.context.get("request")
        is_patch = request and request.method == "PATCH"
        if request.user.is_student:
            raise PermissionDenied
        if instance:
            if all([not video_url, not content]) and not is_patch:
                raise serializers.ValidationError(
                    "Either video_url or content must be provided."
                )
            if (
                instance.course.id != getattr(attrs.get("course"), "id", None)
                and instance.course.has_enrollments()
            ):
                raise serializers.ValidationError(
                    "You cannot change the course of a lesson that has enrollments."
                )
        return super().validate(attrs)


class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    lessons_count = serializers.IntegerField(default=0, read_only=True)
    is_enrolled = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "description",
            "instructor",
            "is_published",
            "lessons_count",
            "is_enrolled",
        )
        read_only_fields = ("is_published",)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied
        if not user.is_instructor:
            raise serializers.ValidationError(
                "You do not have permission to create or update courses."
            )
        attrs["instructor"] = user
        return attrs


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    lessons = CourseLessonCreateUpdateSerializer(
        many=True, required=False, write_only=True
    )

    class Meta:
        model = Course
        fields = ("id", "title", "description", "instructor", "is_published", "lessons")
        read_only_fields = ("is_published",)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        lessons = instance.lessons.filter(is_active=True)
        rep["lessons"] = LessonSerializer(instance=lessons, many=True).data
        return rep

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied
        if not user.is_instructor:
            raise serializers.ValidationError(
                "You do not have permission to create or update courses."
            )
        return attrs

    def update(self, instance, validated_data):
        lessons_data = validated_data.pop("lessons", [])
        instance = super().update(instance, validated_data)

        lesson_mapping = {lesson.id: lesson for lesson in instance.lessons.all()}
        updated_lessons = []

        for lesson_data in lessons_data:
            lesson_id = lesson_data.get("id")
            if lesson_id in lesson_mapping:
                lesson = lesson_mapping[lesson_id]
                for attr, value in lesson_data.items():
                    setattr(lesson, attr, value)
                updated_lessons.append(lesson)

        if updated_lessons:
            Lesson.objects.bulk_update(updated_lessons, ["is_active"])

        return instance
