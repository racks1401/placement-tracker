from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .services import get_dashboard_stats


@login_required
def dashboard_view(request):
    """
    Tenant-scoped dashboard view.
    Populated using the aggregation service layer.
    """
    context = get_dashboard_stats(request.user)
    return render(request, 'dashboard.html', context)
