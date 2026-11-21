from datetime import timedelta
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from tracker.models import Company, InterviewRound, JobApplication, ResumeVersion
from tracker.services import (
    filter_applications,
    get_companies_with_counts,
    get_dashboard_stats,
    get_resumes_with_counts,
    get_upcoming_interview_rounds,
)

User = get_user_model()


@pytest.fixture
def test_users():
    user1 = User.objects.create_user(username='candidate1', password='password123')
    user2 = User.objects.create_user(username='candidate2', password='password123')
    return user1, user2


@pytest.mark.django_db
def test_dashboard_stats_and_tenant_isolation(test_users):
    user1, user2 = test_users

    # Setup User 1 data
    c1 = Company.objects.create(owner=user1, name='Google', industry='Tech')
    c2 = Company.objects.create(owner=user1, name='Microsoft', industry='Tech')
    r1 = ResumeVersion.objects.create(owner=user1, label='Backend v1', is_default=True)

    app1 = JobApplication.objects.create(
        owner=user1,
        company=c1,
        resume_version=r1,
        role_title='Software Engineer',
        status=JobApplication.StatusChoices.APPLIED,
        expected_ctc_lpa=Decimal('24.00'),
    )
    app2 = JobApplication.objects.create(
        owner=user1,
        company=c2,
        resume_version=r1,
        role_title='DevOps Engineer',
        status=JobApplication.StatusChoices.TECHNICAL,
        expected_ctc_lpa=Decimal('28.00'),
    )
    app3 = JobApplication.objects.create(
        owner=user1,
        company=c1,
        resume_version=r1,
        role_title='SRE Intern',
        status=JobApplication.StatusChoices.OFFER,
        expected_ctc_lpa=Decimal('18.00'),
    )

    # User 2 data (should never leak into User 1 stats)
    c_user2 = Company.objects.create(owner=user2, name='Amazon', industry='Tech')
    JobApplication.objects.create(
        owner=user2,
        company=c_user2,
        role_title='QA Engineer',
        status=JobApplication.StatusChoices.OFFER,
        expected_ctc_lpa=Decimal('50.00'),
    )

    stats1 = get_dashboard_stats(user1)

    assert stats1['total_applications'] == 3
    assert stats1['active_applications_count'] == 2  # APPLIED + TECHNICAL
    assert stats1['offers_count'] == 1
    assert stats1['rejected_count'] == 0
    assert stats1['total_companies'] == 2
    assert stats1['total_resumes'] == 1
    assert stats1['avg_expected_ctc'] == Decimal('23.33')
    assert stats1['max_expected_ctc'] == Decimal('28.00')
    assert stats1['status_counts'][JobApplication.StatusChoices.APPLIED] == 1
    assert stats1['status_counts'][JobApplication.StatusChoices.TECHNICAL] == 1
    assert stats1['status_counts'][JobApplication.StatusChoices.OFFER] == 1
    assert stats1['status_counts'][JobApplication.StatusChoices.SAVED] == 0

    # Verify User 2 stats isolation
    stats2 = get_dashboard_stats(user2)
    assert stats2['total_applications'] == 1
    assert stats2['offers_count'] == 1
    assert stats2['max_expected_ctc'] == Decimal('50.00')


@pytest.mark.django_db
def test_upcoming_interview_rounds_query(test_users):
    user1, user2 = test_users
    company = Company.objects.create(owner=user1, name='Meta')
    app = JobApplication.objects.create(
        owner=user1,
        company=company,
        role_title='Fullstack Engineer',
        status=JobApplication.StatusChoices.TECHNICAL,
    )

    now = timezone.now()

    # 1. Round in 3 days (Scheduled) -> SHOULD be returned
    r_valid = InterviewRound.objects.create(
        application=app,
        round_number=1,
        round_type=InterviewRound.RoundTypeChoices.DSA,
        scheduled_at=now + timedelta(days=3),
        status=InterviewRound.RoundStatusChoices.SCHEDULED,
    )

    # 2. Round in 2 days but already Completed -> SHOULD NOT be returned
    InterviewRound.objects.create(
        application=app,
        round_number=2,
        round_type=InterviewRound.RoundTypeChoices.OA,
        scheduled_at=now + timedelta(days=2),
        status=InterviewRound.RoundStatusChoices.COMPLETED,
    )

    # 3. Round in 15 days (outside 7-day window) -> SHOULD NOT be returned
    InterviewRound.objects.create(
        application=app,
        round_number=3,
        round_type=InterviewRound.RoundTypeChoices.SYSTEM_DESIGN,
        scheduled_at=now + timedelta(days=15),
        status=InterviewRound.RoundStatusChoices.SCHEDULED,
    )

    # 4. Round in past (yesterday) -> SHOULD NOT be returned
    InterviewRound.objects.create(
        application=app,
        round_number=4,
        round_type=InterviewRound.RoundTypeChoices.OA,
        scheduled_at=now - timedelta(days=1),
        status=InterviewRound.RoundStatusChoices.SCHEDULED,
    )

    upcoming = get_upcoming_interview_rounds(user1, days=7)
    assert upcoming.count() == 1
    assert upcoming.first().pk == r_valid.pk

    # User 2 should see 0 upcoming rounds
    assert get_upcoming_interview_rounds(user2, days=7).count() == 0


@pytest.mark.django_db
def test_filter_applications(test_users):
    user1, _ = test_users
    c_uber = Company.objects.create(owner=user1, name='Uber')
    c_netflix = Company.objects.create(owner=user1, name='Netflix')

    JobApplication.objects.create(
        owner=user1,
        company=c_uber,
        role_title='Backend Developer',
        source=JobApplication.SourceChoices.REFERRAL,
        work_mode=JobApplication.WorkModeChoices.REMOTE,
        status=JobApplication.StatusChoices.APPLIED,
        expected_ctc_lpa=Decimal('35.00'),
    )
    JobApplication.objects.create(
        owner=user1,
        company=c_netflix,
        role_title='Frontend Engineer',
        source=JobApplication.SourceChoices.LINKEDIN,
        work_mode=JobApplication.WorkModeChoices.HYBRID,
        status=JobApplication.StatusChoices.OA,
        expected_ctc_lpa=Decimal('42.00'),
    )

    # Filter by status
    res_status = filter_applications(user1, {'status': 'OA'})
    assert res_status.count() == 1
    assert res_status.first().company.name == 'Netflix'

    # Filter by source
    res_source = filter_applications(user1, {'source': 'Referral'})
    assert res_source.count() == 1
    assert res_source.first().company.name == 'Uber'

    # Filter by search query
    res_search = filter_applications(user1, {'q': 'Frontend'})
    assert res_search.count() == 1
    assert res_search.first().role_title == 'Frontend Engineer'

    # Filter by company search query
    res_search_company = filter_applications(user1, {'q': 'Uber'})
    assert res_search_company.count() == 1

    # Filter by CTC range
    res_ctc = filter_applications(user1, {'min_ctc': '40'})
    assert res_ctc.count() == 1
    assert res_ctc.first().company.name == 'Netflix'


@pytest.mark.django_db
def test_companies_and_resumes_with_counts(test_users):
    user1, _ = test_users
    c1 = Company.objects.create(owner=user1, name='Atlassian')
    c2 = Company.objects.create(owner=user1, name='Stripe')
    r1 = ResumeVersion.objects.create(owner=user1, label='SWE')

    JobApplication.objects.create(owner=user1, company=c1, resume_version=r1, role_title='SWE I')
    JobApplication.objects.create(owner=user1, company=c1, resume_version=r1, role_title='SWE II')

    companies = get_companies_with_counts(user1)
    comp_dict = {c.name: c.application_count for c in companies}
    assert comp_dict['Atlassian'] == 2
    assert comp_dict['Stripe'] == 0

    resumes = get_resumes_with_counts(user1)
    assert resumes.first().application_count == 2
