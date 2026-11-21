from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from tracker.models import ApplicationNote, Company, InterviewRound, JobApplication, ResumeVersion

User = get_user_model()


@pytest.fixture
def users():
    user1 = User.objects.create_user(username='model_user1', password='password123')
    user2 = User.objects.create_user(username='model_user2', password='password123')
    return user1, user2


@pytest.mark.django_db
def test_company_model_constraints_and_str(users):
    u1, u2 = users
    comp1 = Company.objects.create(owner=u1, name='Google', industry='Tech', location='Mountain View')
    assert str(comp1) == 'Google'

    # Same user cannot create duplicate company name (IntegrityError)
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            Company.objects.create(owner=u1, name='Google')

    # Different user CAN create company with same name
    comp_u2 = Company.objects.create(owner=u2, name='Google')
    assert comp_u2.pk != comp1.pk


@pytest.mark.django_db
def test_resume_version_default_flag_logic(users):
    u1, u2 = users

    # User 1 creates first default resume
    r1 = ResumeVersion.objects.create(owner=u1, label='Backend v1', is_default=True)
    assert r1.is_default is True
    assert 'Default' in str(r1)

    # User 2 creates default resume
    r_u2 = ResumeVersion.objects.create(owner=u2, label='Frontend v1', is_default=True)
    assert r_u2.is_default is True

    # User 1 creates second default resume -> r1 must be updated to is_default=False
    r2 = ResumeVersion.objects.create(owner=u1, label='Fullstack v2', is_default=True)
    r1.refresh_from_db()
    r_u2.refresh_from_db()

    assert r2.is_default is True
    assert r1.is_default is False
    # User 2's default resume must remain unaffected
    assert r_u2.is_default is True


@pytest.mark.django_db
def test_job_application_indexes_and_str(users):
    u1, _ = users
    comp = Company.objects.create(owner=u1, name='Meta')
    app = JobApplication.objects.create(
        owner=u1,
        company=comp,
        role_title='Production Engineer',
        expected_ctc_lpa=Decimal('35.00'),
    )

    assert str(app) == 'Production Engineer at Meta'
    assert app.status == JobApplication.StatusChoices.SAVED
    assert app.source == JobApplication.SourceChoices.CAREER_PORTAL
    assert app.work_mode == JobApplication.WorkModeChoices.ONSITE

    # Verify required compound indexes are explicitly defined
    index_names = [idx.name for idx in JobApplication._meta.indexes]
    assert 'idx_app_owner_status' in index_names
    assert 'idx_app_owner_applied_date' in index_names


@pytest.mark.django_db
def test_interview_round_rating_validation_and_cascade(users):
    u1, _ = users
    comp = Company.objects.create(owner=u1, name='Netflix')
    app = JobApplication.objects.create(owner=u1, company=comp, role_title='SRE')

    # Valid rating (1 to 5)
    round_valid = InterviewRound(
        application=app,
        round_number=1,
        round_type=InterviewRound.RoundTypeChoices.DSA,
        scheduled_at=timezone.now(),
        self_rating=5,
    )
    round_valid.full_clean()
    round_valid.save()
    assert 'Round 1' in str(round_valid)

    # Invalid rating > 5 raises ValidationError on full_clean
    round_invalid_high = InterviewRound(
        application=app,
        round_number=2,
        round_type=InterviewRound.RoundTypeChoices.TECHNICAL,
        scheduled_at=timezone.now(),
        self_rating=6,
    )
    with pytest.raises(ValidationError):
        round_invalid_high.full_clean()

    # Invalid rating < 1 raises ValidationError on full_clean
    round_invalid_low = InterviewRound(
        application=app,
        round_number=3,
        round_type=InterviewRound.RoundTypeChoices.HR,
        scheduled_at=timezone.now(),
        self_rating=0,
    )
    with pytest.raises(ValidationError):
        round_invalid_low.full_clean()


@pytest.mark.django_db
def test_cascade_and_set_null_behaviors(users):
    u1, _ = users
    comp = Company.objects.create(owner=u1, name='Apple')
    resume = ResumeVersion.objects.create(owner=u1, label='iOS Dev')
    app = JobApplication.objects.create(
        owner=u1,
        company=comp,
        resume_version=resume,
        role_title='iOS Engineer',
    )
    InterviewRound.objects.create(
        application=app,
        round_number=1,
        scheduled_at=timezone.now(),
    )
    note = ApplicationNote.objects.create(
        application=app,
        title='Initial Screening',
        body='Recruiter call went well.',
    )
    assert 'Apple' in str(note)

    # 1. Deleting ResumeVersion sets resume_version=None on JobApplication (SET_NULL)
    resume.delete()
    app.refresh_from_db()
    assert app.resume_version is None

    # 2. Deleting Company cascades and deletes JobApplication, Rounds, and Notes
    comp.delete()
    assert not JobApplication.objects.filter(pk=app.pk).exists()
    assert not InterviewRound.objects.filter(application_id=app.pk).exists()
    assert not ApplicationNote.objects.filter(application_id=app.pk).exists()
