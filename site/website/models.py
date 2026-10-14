from django.db import models
from django.utils import timezone


class ConsultRequest(models.Model):
    email = models.EmailField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    remote_addr = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=300, blank=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} · {self.created_at:%Y-%m-%d %H:%M}"
