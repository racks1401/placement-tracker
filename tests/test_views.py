from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from tracker.forms import CompanyForm, JobApplicationForm
from tracker.models import ApplicationNote, Company, InterviewRound, JobApplication, ResumeVersion

User = get_user_model()


@pytest.fixture
def auth_client():
    user = User.objects.create_user(username='john', password='password123')
    client = Client()
    client.login(username='john', password='password123')
    return client, user


@pytest.fixture
def other_user():
    return User.objects.create_user(username='other', password='password123')


@pytest.mark.django_db
def test_unauthenticated_redirects_across_endpoints():
    """Unauthenticated access across all tracker routes must redirect to login."""
    client = Client()
    protected_urls = [
        reverse('tracker:dashboard'),
        reverse('tracker:application_list'),
        reverse('tracker:application_create'),
        reverse('tracker:company_list'),
        reverse('tracker:company_create'),
        reverse('tracker:resume_list'),
        reverse('tracker:resume_create'),
    ]

    for url in protected_urls:
        res = client.get(url)
        assert res.status_code == 302
        assert '/accounts/login/' in res.url


@pytest.mark.django_db
def test_job_application_form_dropdown_isolation_and_ctc_validation(auth_client, other_user):
    _, user = auth_client
    c_user = Company.objects.create(owner=user, name='Target Corp')
    c_other = Company.objects.create(owner=other_user, name='Hidden Corp')

    r_user = ResumeVersion.objects.create(owner=user, label='My Resume')
    r_other = ResumeVersion.objects.create(owner=other_user, label='Other Resume')

    form = JobApplicationForm(user=user)
    # Company dropdown must only show user's company
    company_choices = list(form.fields['company'].queryset)
    assert c_user in company_choices
    assert c_other not in company_choices

    # Resume dropdown must only show user's resume
    resume_choices = list(form.fields['resume_version'].queryset)
    assert r_user in resume_choices
    assert r_other not in resume_choices

    # Negative CTC validation
    form_invalid = JobApplicationForm(
        data={
            'company': c_user.pk,
            'role_title': 'Dev',
            'status': JobApplication.StatusChoices.APPLIED,
            'source': JobApplication.SourceChoices.CAREER_PORTAL,
            'work_mode': JobApplication.WorkModeChoices.ONSITE,
            'expected_ctc_lpa': '-5.0',
        },
        user=user,
    )
    assert not form_invalid.is_valid()
    assert 'expected_ctc_lpa' in form_invalid.errors


@pytest.mark.django_db
def test_company_form_unique_name_per_owner(auth_client, other_user):
    _, user = auth_client
    Company.objects.create(owner=user, name='Stripe')

    # Other user can use same name
    form_other = CompanyForm(data={'name': 'Stripe'}, user=other_user)
    assert form_other.is_valid()

    # Same user cannot duplicate company name
    form_dup = CompanyForm(data={'name': 'Stripe'}, user=user)
    assert not form_dup.is_valid()
    assert 'name' in form_dup.errors


@pytest.mark.django_db
def test_application_crud_lifecycle(auth_client):
    client, user = auth_client
    company = Company.objects.create(owner=user, name='Amazon')

    # 1. Create Application
    create_url = reverse('tracker:application_create')
    post_data = {
        'company': company.pk,
        'role_title': 'SDE I',
        'status': JobApplication.StatusChoices.APPLIED,
        'source': JobApplication.SourceChoices.CAMPUS,
        'work_mode': JobApplication.WorkModeChoices.HYBRID,
        'expected_ctc_lpa': '22.5',
        'applied_date': '2026-01-15',
    }
    response = client.post(create_url, post_data)
    assert response.status_code == 302
    app = JobApplication.objects.get(owner=user, role_title='SDE I')
    assert app.expected_ctc_lpa == Decimal('22.5')

    # 2. View List & Detail
    list_res = client.get(reverse('tracker:application_list'))
    assert list_res.status_code == 200
    assert b'SDE I' in list_res.content

    detail_res = client.get(reverse('tracker:application_detail', kwargs={'pk': app.pk}))
    assert detail_res.status_code == 200
    assert b'Amazon' in detail_res.content

    # 3. Update Application
    update_data = post_data.copy()
    update_data['status'] = JobApplication.StatusChoices.TECHNICAL
    update_res = client.post(reverse('tracker:application_update', kwargs={'pk': app.pk}), update_data)
    assert update_res.status_code == 302
    app.refresh_from_db()
    assert app.status == JobApplication.StatusChoices.TECHNICAL

    # 4. Delete Application
    del_res = client.post(reverse('tracker:application_delete', kwargs={'pk': app.pk}))
    assert del_res.status_code == 302
    assert not JobApplication.objects.filter(pk=app.pk).exists()


@pytest.mark.django_db
def test_cross_tenant_404_protection_on_crud_views(auth_client, other_user):
    client, user = auth_client

    # Other user creates an application, company, resume
    other_company = Company.objects.create(owner=other_user, name='OtherCo')
    other_app = JobApplication.objects.create(
        owner=other_user,
        company=other_company,
        role_title='Secret Role',
    )
    other_resume = ResumeVersion.objects.create(owner=other_user, label='Confidential Resume')

    # Logged-in user tries to view, edit, delete other user's application -> 404
    assert client.get(reverse('tracker:application_detail', kwargs={'pk': other_app.pk})).status_code == 404
    assert client.get(reverse('tracker:application_update', kwargs={'pk': other_app.pk})).status_code == 404
    assert client.post(reverse('tracker:application_delete', kwargs={'pk': other_app.pk})).status_code == 404

    # Other user's company and resume -> 404
    assert client.get(reverse('tracker:company_update', kwargs={'pk': other_company.pk})).status_code == 404
    assert client.post(reverse('tracker:company_delete', kwargs={'pk': other_company.pk})).status_code == 404
    assert client.get(reverse('tracker:resume_update', kwargs={'pk': other_resume.pk})).status_code == 404
    assert client.post(reverse('tracker:resume_delete', kwargs={'pk': other_resume.pk})).status_code == 404


@pytest.mark.django_db
def test_rounds_and_notes_endpoints(auth_client, other_user):
    client, user = auth_client
    company = Company.objects.create(owner=user, name='Google')
    app = JobApplication.objects.create(owner=user, company=company, role_title='L4 SWE')

    # Add Round
    round_data = {
        'round_number': 1,
        'round_type': InterviewRound.RoundTypeChoices.DSA,
        'scheduled_at': '2026-03-01T10:00',
        'status': InterviewRound.RoundStatusChoices.SCHEDULED,
        'interviewer_name': 'Sarah',
        'notes': 'Tree questions',
        'self_rating': 4,
    }
    r_post = client.post(reverse('tracker:round_create', kwargs={'app_pk': app.pk}), round_data)
    assert r_post.status_code == 302
    assert app.interview_rounds.count() == 1
    round_obj = app.interview_rounds.first()
    assert round_obj.interviewer_name == 'Sarah'
    assert round_obj.self_rating == 4

    # Add Note
    note_data = {
        'title': 'Salary Discussion',
        'body': 'Offered standard band.',
    }
    n_post = client.post(reverse('tracker:note_create', kwargs={'app_pk': app.pk}), note_data)
    assert n_post.status_code == 302
    assert app.notes.count() == 1
    note_obj = app.notes.first()
    assert note_obj.title == 'Salary Discussion'

    # Other user cannot add round to or delete this round/note -> 404
    other_client = Client()
    other_client.login(username='other', password='password123')
    assert other_client.post(reverse('tracker:round_create', kwargs={'app_pk': app.pk}), round_data).status_code == 404
    assert other_client.post(reverse('tracker:round_delete', kwargs={'pk': round_obj.pk})).status_code == 404
    assert other_client.post(reverse('tracker:note_delete', kwargs={'pk': note_obj.pk})).status_code == 404


@pytest.mark.django_db
def test_application_list_view_filtering_and_search(auth_client):
    client, user = auth_client
    c1 = Company.objects.create(owner=user, name='Adobe')
    c2 = Company.objects.create(owner=user, name='Salesforce')

    JobApplication.objects.create(
        owner=user,
        company=c1,
        role_title='Platform Engineer',
        status=JobApplication.StatusChoices.APPLIED,
        source=JobApplication.SourceChoices.REFERRAL,
    )
    JobApplication.objects.create(
        owner=user,
        company=c2,
        role_title='Security Architect',
        status=JobApplication.StatusChoices.OFFER,
        source=JobApplication.SourceChoices.LINKEDIN,
    )

    # Filter by status
    res_status = client.get(reverse('tracker:application_list'), {'status': 'Applied'})
    assert res_status.status_code == 200
    assert len(res_status.context['applications']) == 1
    assert res_status.context['applications'][0].role_title == 'Platform Engineer'

    # Filter by search query
    res_search = client.get(reverse('tracker:application_list'), {'q': 'Security'})
    assert res_search.status_code == 200
    assert len(res_search.context['applications']) == 1
    assert res_search.context['applications'][0].role_title == 'Security Architect'


@pytest.mark.django_db
def test_dashboard_view_metric_accuracy(auth_client):
    client, user = auth_client
    comp = Company.objects.create(owner=user, name='Oracle')
    JobApplication.objects.create(
        owner=user,
        company=comp,
        role_title='Cloud SWE',
        status=JobApplication.StatusChoices.OFFER,
        expected_ctc_lpa=Decimal('28.00'),
    )

    response = client.get(reverse('tracker:dashboard'))
    assert response.status_code == 200
    assert response.context['total_applications'] == 1
    assert response.context['offers_count'] == 1
    assert response.context['total_companies'] == 1
    assert response.context['avg_expected_ctc'] == Decimal('28.00')


@pytest.mark.django_db
def test_company_and_resume_crud_views(auth_client):
    client, user = auth_client

    # Create Company
    res_c_create = client.post(reverse('tracker:company_create'), {
        'name': 'Databricks',
        'industry': 'AI / Big Data',
        'location': 'San Francisco',
        'website': 'https://databricks.com',
        'notes': 'Great engineering culture',
    })
    assert res_c_create.status_code == 302
    company = Company.objects.get(owner=user, name='Databricks')

    # Update Company
    res_c_update = client.post(reverse('tracker:company_update', kwargs={'pk': company.pk}), {
        'name': 'Databricks Inc',
        'industry': 'AI / Big Data',
        'location': 'San Francisco, CA',
        'website': 'https://databricks.com',
        'notes': 'Updated notes',
    })
    assert res_c_update.status_code == 302
    company.refresh_from_db()
    assert company.name == 'Databricks Inc'

    # Create Resume
    res_r_create = client.post(reverse('tracker:resume_create'), {
        'label': 'ML Ops v1',
        'target_role': 'Machine Learning Engineer',
        'plain_text': 'PyTorch, MLflow, Ray experience',
        'is_default': True,
    })
    assert res_r_create.status_code == 302
    resume = ResumeVersion.objects.get(owner=user, label='ML Ops v1')
    assert resume.is_default is True

    # Delete Resume
    res_r_del = client.post(reverse('tracker:resume_delete', kwargs={'pk': resume.pk}))
    assert res_r_del.status_code == 302
    assert not ResumeVersion.objects.filter(pk=resume.pk).exists()

    # Delete Company
    res_c_del = client.post(reverse('tracker:company_delete', kwargs={'pk': company.pk}))
    assert res_c_del.status_code == 302
    assert not Company.objects.filter(pk=company.pk).exists()
