import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from tracker.models import Company, InterviewRound, JobApplication, ResumeVersion

User = get_user_model()


@pytest.mark.django_db
def test_seed_data_command_is_idempotent():
    """
    Verifies running seed_data once populates the exact expected counts,
    and running it a second time creates 0 duplicate records.
    """
    # First execution
    call_command('seed_data')

    users_count = User.objects.filter(username__in=['alex_dev', 'priya_swe']).count()
    companies_count = Company.objects.filter(owner__username__in=['alex_dev', 'priya_swe']).count()
    resumes_count = ResumeVersion.objects.filter(owner__username__in=['alex_dev', 'priya_swe']).count()
    applications_count = JobApplication.objects.filter(owner__username__in=['alex_dev', 'priya_swe']).count()
    rounds_count = InterviewRound.objects.filter(application__owner__username__in=['alex_dev', 'priya_swe']).count()

    assert users_count == 2
    assert companies_count == 10
    assert resumes_count == 4
    assert applications_count == 24
    assert rounds_count == 18

    # Second execution (Idempotency test)
    call_command('seed_data')

    assert User.objects.filter(username__in=['alex_dev', 'priya_swe']).count() == 2
    assert Company.objects.filter(owner__username__in=['alex_dev', 'priya_swe']).count() == 10
    assert ResumeVersion.objects.filter(owner__username__in=['alex_dev', 'priya_swe']).count() == 4
    assert JobApplication.objects.filter(owner__username__in=['alex_dev', 'priya_swe']).count() == 24
    assert InterviewRound.objects.filter(application__owner__username__in=['alex_dev', 'priya_swe']).count() == 18
