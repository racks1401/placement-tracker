from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Company, JobApplication, ResumeVersion


@login_required
def dashboard_view(request):
    """
    Tenant-scoped dashboard view.
    Strictly filters records by owner=request.user.
    """
    user_applications = JobApplication.objects.filter(owner=request.user)
    user_companies = Company.objects.filter(owner=request.user)
    user_resumes = ResumeVersion.objects.filter(owner=request.user)

    context = {
        'total_applications': user_applications.count(),
        'total_companies': user_companies.count(),
        'total_resumes': user_resumes.count(),
    }
    return render(request, 'dashboard.html', context)
