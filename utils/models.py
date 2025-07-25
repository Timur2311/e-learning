from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        if hasattr(self, "name"):
            return self.name
        if hasattr(self, "title"):
            return self.title
        return str(getattr(self, "id") or super(BaseModel, self))
