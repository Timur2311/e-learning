# courses/admin.py
from django.contrib import admin

from .models import Course, Lesson


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    fields = ("title", "description", "video_url", "is_active", "content")
    show_change_link = True


class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "is_published", "has_enrollments_display")
    list_filter = ("is_published",)
    search_fields = ("title", "description", "instructor__username")
    inlines = [LessonInline]
    readonly_fields = ("has_enrollments_display",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.is_instructor:
            return qs.filter(instructor=request.user)
        return qs.none()

    def has_enrollments_display(self, obj):
        return obj.has_enrollments()

    has_enrollments_display.boolean = True
    has_enrollments_display.short_description = "Has Enrollments"


class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "is_active")
    list_filter = ("is_active", "course")
    search_fields = ("title", "description", "course__title")


admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
