from django.db import models

from utils.models import BaseModel


class Enrollment(BaseModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="User",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Course",
    )


class LessonProgress(BaseModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="lesson_progresses",
        verbose_name="User",
    )
    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="progresses",
        verbose_name="Lesson",
    )
    completed = models.BooleanField(default=False, verbose_name="Completed")

    class Meta:
        unique_together = ("user", "lesson")
