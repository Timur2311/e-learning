from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import Course, Lesson

from .models import User


@receiver(post_save, sender=User)
def assign_instructor_permissions(sender, instance, created, **kwargs):
    if instance.role == User.Role.INSTRUCTOR:
        instructor_group, _ = Group.objects.get_or_create(name="Instructor")

        if instructor_group.permissions.count() == 0:
            course_ct = ContentType.objects.get_for_model(Course)
            lesson_ct = ContentType.objects.get_for_model(Lesson)
            perms = Permission.objects.filter(content_type=course_ct).filter(
                codename__in=["add_course", "change_course", "view_course"]
            )
            lesson_perms = Permission.objects.filter(content_type=lesson_ct).filter(
                codename__in=["add_lesson", "change_lesson", "view_lesson"]
            )

            instructor_group.permissions.add(*perms, *lesson_perms)

        if not instance.groups.filter(name="Instructor").exists():
            instance.groups.add(instructor_group)
