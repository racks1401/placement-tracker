"""
Service layer for PlacementTracker.
Encapsulates business logic, dashboard aggregations, multi-criteria filtering,
and tenant-scoped queries.
"""

from datetime import timedelta
from decimal import Decimal
from django.db.models import Avg, Count, Max, Q
from django.utils import timezone

from .models import ApplicationNote, Company, InterviewRound, JobApplication, ResumeVersion


def get_upcoming_interview_rounds(user, days=7):
    """
    Retrieves interview rounds scheduled within the next N days (default 7)
    for job applications owned strictly by the specified user.
    """
    if not user.is_authenticated:
        return InterviewRound.objects.none()

    now = timezone.now()
    cutoff = now + timedelta(days=days)

    return (
        InterviewRound.objects.filter(
            application__owner=user,
            status=InterviewRound.RoundStatusChoices.SCHEDULED,
            scheduled_at__gte=now,
            scheduled_at__lte=cutoff,
        )
        .select_related('application', 'application__company')
        .order_by('scheduled_at')
    )


def filter_applications(user, filters=None):
    """
    Applies multi-criteria filtering, search, and sorting to a user's job applications.
    Strictly scoped to the authenticated user.
    """
    if not user.is_authenticated:
        return JobApplication.objects.none()

    qs = JobApplication.objects.filter(owner=user).select_related('company', 'resume_version')

    if not filters:
        return qs

    # 1. Status Filter
    status = filters.get('status')
    if status and status in JobApplication.StatusChoices.values:
        qs = qs.filter(status=status)

    # 2. Source Filter
    source = filters.get('source')
    if source and source in JobApplication.SourceChoices.values:
        qs = qs.filter(source=source)

    # 3. Work Mode Filter
    work_mode = filters.get('work_mode')
    if work_mode and work_mode in JobApplication.WorkModeChoices.values:
        qs = qs.filter(work_mode=work_mode)

    # 4. Company Filter
    company_id = filters.get('company_id') or filters.get('company')
    if company_id:
        try:
            qs = qs.filter(company_id=int(company_id))
        except (ValueError, TypeError):
            pass

    # 5. Search query across role, company name, location, and description
    search_query = filters.get('q') or filters.get('search')
    if search_query:
        search_query = search_query.strip()
        qs = qs.filter(
            Q(role_title__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(job_description__icontains=search_query)
        )

    # 6. CTC range filters
    min_ctc = filters.get('min_ctc')
    if min_ctc:
        try:
            qs = qs.filter(expected_ctc_lpa__gte=Decimal(str(min_ctc)))
        except (ValueError, TypeError):
            pass

    max_ctc = filters.get('max_ctc')
    if max_ctc:
        try:
            qs = qs.filter(expected_ctc_lpa__lte=Decimal(str(max_ctc)))
        except (ValueError, TypeError):
            pass

    # 7. Sorting / Ordering
    ordering_map = {
        'updated_desc': '-updated_at',
        'updated_asc': 'updated_at',
        'applied_desc': '-applied_date',
        'applied_asc': 'applied_date',
        'role_asc': 'role_title',
        'role_desc': '-role_title',
        'company_asc': 'company__name',
        'company_desc': '-company__name',
        'ctc_desc': '-expected_ctc_lpa',
        'ctc_asc': 'expected_ctc_lpa',
        'next_action_asc': 'next_action_date',
    }
    sort_by = filters.get('sort') or filters.get('ordering') or 'updated_desc'
    order_field = ordering_map.get(sort_by, '-updated_at')
    qs = qs.order_by(order_field)

    return qs


def get_dashboard_stats(user):
    """
    Computes dashboard metrics strictly for the given user:
    - Active stage breakdown
    - Status counts dictionary
    - Upcoming interview rounds within 7 days
    - CTC summary and recent applications
    """
    if not user.is_authenticated:
        return {
            'total_applications': 0,
            'active_applications_count': 0,
            'offers_count': 0,
            'rejected_count': 0,
            'status_counts': {},
            'upcoming_interviews': [],
            'upcoming_interviews_count': 0,
            'recent_applications': [],
            'total_companies': 0,
            'total_resumes': 0,
            'avg_expected_ctc': None,
            'max_expected_ctc': None,
        }

    user_applications = JobApplication.objects.filter(owner=user)
    total_applications = user_applications.count()

    # Aggregate counts by status
    db_status_counts = dict(
        user_applications.values('status')
        .annotate(count=Count('status'))
        .values_list('status', 'count')
    )
    # Ensure every valid choice exists in dictionary with at least 0
    status_counts = {
        choice.value: db_status_counts.get(choice.value, 0)
        for choice in JobApplication.StatusChoices
    }

    # Active stages: Applied, OA, Technical, HR
    active_stages = [
        JobApplication.StatusChoices.APPLIED,
        JobApplication.StatusChoices.OA,
        JobApplication.StatusChoices.TECHNICAL,
        JobApplication.StatusChoices.HR,
    ]
    active_applications_count = sum(status_counts.get(stage.value, 0) for stage in active_stages)
    offers_count = status_counts.get(JobApplication.StatusChoices.OFFER.value, 0)
    rejected_count = status_counts.get(JobApplication.StatusChoices.REJECTED.value, 0)

    # CTC calculations
    ctc_aggregates = user_applications.filter(
        expected_ctc_lpa__isnull=False
    ).aggregate(
        avg_ctc=Avg('expected_ctc_lpa'),
        max_ctc=Max('expected_ctc_lpa'),
    )
    avg_expected_ctc = (
        round(ctc_aggregates['avg_ctc'], 2) if ctc_aggregates['avg_ctc'] is not None else None
    )
    max_expected_ctc = ctc_aggregates['max_ctc']

    # Upcoming interviews within 7 days
    upcoming_interviews_qs = get_upcoming_interview_rounds(user, days=7)
    upcoming_interviews = list(upcoming_interviews_qs[:10])
    upcoming_interviews_count = upcoming_interviews_qs.count()

    # Recent applications (last 5 updated)
    recent_applications = list(
        user_applications.select_related('company', 'resume_version')
        .order_by('-updated_at')[:5]
    )

    total_companies = Company.objects.filter(owner=user).count()
    total_resumes = ResumeVersion.objects.filter(owner=user).count()

    return {
        'total_applications': total_applications,
        'active_applications_count': active_applications_count,
        'offers_count': offers_count,
        'rejected_count': rejected_count,
        'status_counts': status_counts,
        'upcoming_interviews': upcoming_interviews,
        'upcoming_interviews_count': upcoming_interviews_count,
        'recent_applications': recent_applications,
        'total_companies': total_companies,
        'total_resumes': total_resumes,
        'avg_expected_ctc': avg_expected_ctc,
        'max_expected_ctc': max_expected_ctc,
    }


def get_companies_with_counts(user):
    """
    Returns user's companies annotated with their application count.
    """
    if not user.is_authenticated:
        return Company.objects.none()

    return (
        Company.objects.filter(owner=user)
        .annotate(application_count=Count('job_applications'))
        .order_by('name')
    )


def get_resumes_with_counts(user):
    """
    Returns user's resume versions annotated with their application count.
    """
    if not user.is_authenticated:
        return ResumeVersion.objects.none()

    return (
        ResumeVersion.objects.filter(owner=user)
        .annotate(application_count=Count('job_applications'))
        .order_by('-is_default', 'label')
    )
