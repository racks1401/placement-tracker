import pytest
from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import Client
from django.urls import reverse

from tracker.mixins import get_owner_scoped_object_or_404
from tracker.models import Company, JobApplication

User = get_user_model()


@pytest.mark.django_db
def test_unauthenticated_redirect():
    """Unauthenticated access to protected dashboard redirects to login."""
    client = Client()
    response = client.get(reverse('tracker:dashboard'))
    assert response.status_code == 302
    assert '/accounts/login/' in response.url


@pytest.mark.django_db
def test_user_registration_and_login():
    """Test user registration, login, and profile access."""
    client = Client()

    # Register
    reg_data = {
        'username': 'alice',
        'email': 'alice@example.com',
        'first_name': 'Alice',
        'last_name': 'Smith',
        'password': 'SecurePassword123!',
        'password_confirm': 'SecurePassword123!',
    }
    response = client.post(reverse('accounts:register'), reg_data)
    assert response.status_code == 302
    assert response.url == reverse('tracker:dashboard')

    # Verify user created in DB
    user = User.objects.get(username='alice')
    assert user.check_password('SecurePassword123!')
    assert user.email == 'alice@example.com'

    # Verify session is active
    dash_response = client.get(reverse('tracker:dashboard'))
    assert dash_response.status_code == 200
    assert b'Alice' in dash_response.content or b'alice' in dash_response.content

    # Logout
    logout_response = client.post(reverse('accounts:logout'))
    assert logout_response.status_code == 302

    # Should redirect to login now
    dash_after_logout = client.get(reverse('tracker:dashboard'))
    assert dash_after_logout.status_code == 302


@pytest.mark.django_db
def test_strict_tenant_scoping_isolation():
    """Verify User B cannot access or inspect records belonging to User A."""
    user_a = User.objects.create_user(username='usera', password='passwordA123')
    user_b = User.objects.create_user(username='userb', password='passwordB123')

    # User A creates a company and application
    company_a = Company.objects.create(owner=user_a, name='Acme Corp')
    app_a = JobApplication.objects.create(
        owner=user_a,
        company=company_a,
        role_title='Software Engineer',
    )

    # Scoping check: User A can fetch their own object
    obj_a = get_owner_scoped_object_or_404(JobApplication, user_a, pk=app_a.pk)
    assert obj_a.pk == app_a.pk

    # Scoping check: User B trying to fetch User A's object raises Http404 (preventing PK guessing)
    with pytest.raises(Http404):
        get_owner_scoped_object_or_404(JobApplication, user_b, pk=app_a.pk)

    with pytest.raises(Http404):
        get_owner_scoped_object_or_404(Company, user_b, pk=company_a.pk)
