from django.db import models

class FacebookSession(models.Model):
    """
    Stores session information for a Facebook account to allow re-logging in
    without credentials.
    """
    account_id = models.CharField(max_length=100, unique=True, help_text="A unique identifier for the Facebook account, e.g., username or email.")
    cookies = models.JSONField(help_text="The cookies required for session authentication.")
    f_value = models.CharField(max_length=255, help_text="The 'f' value extracted from Facebook's scripts, used in some API calls.")
    last_used = models.DateTimeField(auto_now=True, help_text="Timestamp of the last time the session was used.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Facebook Session for {self.account_id}"

