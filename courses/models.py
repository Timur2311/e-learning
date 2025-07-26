from django.db import models

from utils.models import BaseModel


class Course(BaseModel):
    title = models.CharField(max_length=255, verbose_name="Course Title")
    description = models.TextField(verbose_name="Course Description")
    instructor = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Instructor",
    )
    is_published = models.BooleanField(default=False, verbose_name="Is Published")

    def create_enrollment(self, user):
        from enrollments.models import Enrollment

        enrollment = Enrollment.objects.create(course=self, user=user)
        return enrollment

    def is_enrolled(self, user):
        """
        Check if a user is enrolled in this course.
        """
        return self.enrollments.filter(user=user).exists()

    def has_enrollments(self):
        """
        Check if the course has any enrollments.
        """
        return self.enrollments.exists()


class Lesson(BaseModel):
    title = models.CharField(max_length=255, verbose_name="Lesson Title")
    description = models.TextField(verbose_name="Lesson Description")
    video_url = models.URLField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Course",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    # TODO: validation for content ot URL exists, maybe just displaying not uploaded yet
    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title
