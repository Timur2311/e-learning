import django_filters

from .models import Course


class CourseFilter(django_filters.FilterSet):
    enrolled = django_filters.BooleanFilter(
        method="get_enrolled_courses", label="Enrolled courses"
    )

    class Meta:
        model = Course
        fields = ["is_published", "enrolled"]

    def get_enrolled_courses(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and user.is_student and value:
            queryset = queryset.filter(enrollments__user=user).distinct()
        return queryset
