from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Company(models.Model):
    """
    Represents an employer or organization to which applications are submitted.
    Scoped strictly to each owner.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='companies',
    )
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_owner_company_name',
            )
        ]

    def __str__(self):
        return self.name


class ResumeVersion(models.Model):
    """
    Tracks tailored versions of a resume per user (plain text and role metadata).
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resume_versions',
    )
    label = models.CharField(max_length=120)
    target_role = models.CharField(max_length=120, blank=True)
    plain_text = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', 'label']

    def save(self, *args, **kwargs):
        # If this resume is set as default, ensure previous defaults for this user are unset
        if self.is_default and self.owner_id:
            ResumeVersion.objects.filter(owner=self.owner, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label}{' (Default)' if self.is_default else ''}"


class JobApplication(models.Model):
    """
    Core model tracking an individual job/internship application lifecycle.
    """
    class SourceChoices(models.TextChoices):
        CAMPUS = 'Campus', 'Campus'
        REFERRAL = 'Referral', 'Referral'
        LINKEDIN = 'LinkedIn', 'LinkedIn'
        CAREER_PORTAL = 'Career Portal', 'Career Portal'
        COLD_EMAIL = 'Cold Email', 'Cold Email'
        OTHER = 'Other', 'Other'

    class WorkModeChoices(models.TextChoices):
        REMOTE = 'Remote', 'Remote'
        HYBRID = 'Hybrid', 'Hybrid'
        ONSITE = 'Onsite', 'Onsite'

    class StatusChoices(models.TextChoices):
        SAVED = 'Saved', 'Saved'
        APPLIED = 'Applied', 'Applied'
        OA = 'OA', 'OA'
        TECHNICAL = 'Technical', 'Technical'
        HR = 'HR', 'HR'
        OFFER = 'Offer', 'Offer'
        REJECTED = 'Rejected', 'Rejected'
        WITHDRAWN = 'Withdrawn', 'Withdrawn'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications',
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='job_applications',
    )
    resume_version = models.ForeignKey(
        ResumeVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_applications',
    )
    role_title = models.CharField(max_length=200)
    job_url = models.URLField(blank=True)
    source = models.CharField(
        max_length=50,
        choices=SourceChoices.choices,
        default=SourceChoices.CAREER_PORTAL,
    )
    work_mode = models.CharField(
        max_length=20,
        choices=WorkModeChoices.choices,
        default=WorkModeChoices.ONSITE,
    )
    location = models.CharField(max_length=200, blank=True)
    expected_ctc_lpa = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected CTC in LPA (Lakhs Per Annum)",
    )
    status = models.CharField(
        max_length=30,
        choices=StatusChoices.choices,
        default=StatusChoices.SAVED,
    )
    applied_date = models.DateField(null=True, blank=True)
    next_action_date = models.DateField(null=True, blank=True)
    job_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', 'status'], name='idx_app_owner_status'),
            models.Index(fields=['owner', 'applied_date'], name='idx_app_owner_applied_date'),
        ]

    def __str__(self):
        return f"{self.role_title} at {self.company.name}"


class InterviewRound(models.Model):
    """
    Tracks sequential interview rounds (OA, DSA, System Design, HR, etc.) for an application.
    """
    class RoundTypeChoices(models.TextChoices):
        OA = 'OA', 'Online Assessment (OA)'
        DSA = 'DSA', 'Data Structures & Algorithms'
        SYSTEM_DESIGN = 'System Design', 'System Design'
        TECHNICAL = 'Technical', 'Technical Interview'
        MANAGERIAL = 'Managerial', 'Managerial'
        HR = 'HR', 'HR'
        OTHER = 'Other', 'Other'

    class RoundStatusChoices(models.TextChoices):
        SCHEDULED = 'Scheduled', 'Scheduled'
        COMPLETED = 'Completed', 'Completed'
        CLEARED = 'Cleared', 'Cleared'
        FAILED = 'Failed', 'Failed'
        CANCELLED = 'Cancelled', 'Cancelled'

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='interview_rounds',
    )
    round_number = models.PositiveIntegerField(default=1)
    round_type = models.CharField(
        max_length=50,
        choices=RoundTypeChoices.choices,
        default=RoundTypeChoices.TECHNICAL,
    )
    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=30,
        choices=RoundStatusChoices.choices,
        default=RoundStatusChoices.SCHEDULED,
    )
    interviewer_name = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    self_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Self performance rating from 1 to 5",
    )

    class Meta:
        ordering = ['round_number', 'scheduled_at']

    def __str__(self):
        return f"Round {self.round_number} ({self.get_round_type_display()}) - {self.application.role_title}"


class ApplicationNote(models.Model):
    """
    Free-form timestamped notes associated with a job application.
    """
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.application.company.name}"
