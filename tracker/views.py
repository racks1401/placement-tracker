from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    ApplicationNoteForm,
    CompanyForm,
    InterviewRoundForm,
    JobApplicationForm,
    ResumeVersionForm,
)
from .mixins import get_owner_scoped_object_or_404
from .models import ApplicationNote, Company, InterviewRound, JobApplication, ResumeVersion
from .services import (
    filter_applications,
    get_companies_with_counts,
    get_dashboard_stats,
    get_resumes_with_counts,
)


# -----------------------------------------------------------------------------
# Dashboard View
# -----------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    """
    Renders the aggregated overview of the authenticated user's job pipeline.
    """
    context = get_dashboard_stats(request.user)
    return render(request, 'dashboard.html', context)


# -----------------------------------------------------------------------------
# JobApplication CRUD Views
# -----------------------------------------------------------------------------

@login_required
def application_list_view(request):
    """
    Displays the paginated, searchable, and filterable list of user's job applications.
    """
    applications_qs = filter_applications(request.user, request.GET)

    # Paginate by 10 items per page
    paginator = Paginator(applications_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter context for dropdowns
    context = {
        'page_obj': page_obj,
        'applications': page_obj.object_list,
        'total_count': paginator.count,
        'status_choices': JobApplication.StatusChoices.choices,
        'source_choices': JobApplication.SourceChoices.choices,
        'work_mode_choices': JobApplication.WorkModeChoices.choices,
        'selected_status': request.GET.get('status', ''),
        'selected_source': request.GET.get('source', ''),
        'selected_work_mode': request.GET.get('work_mode', ''),
        'selected_sort': request.GET.get('sort', 'updated_desc'),
        'search_query': request.GET.get('q', ''),
        'has_companies': Company.objects.filter(owner=request.user).exists(),
    }
    return render(request, 'tracker/application_list.html', context)


@login_required
def application_detail_view(request, pk):
    """
    Detailed view for a single application including its interview rounds timeline,
    notes, and inline quick-add forms.
    """
    application = get_owner_scoped_object_or_404(JobApplication, request.user, pk=pk)
    rounds = application.interview_rounds.all().order_by('round_number', 'scheduled_at')
    notes = application.notes.all().order_by('-created_at')

    # Next round number suggestion
    next_round_number = (rounds.last().round_number + 1) if rounds.exists() else 1

    round_form = InterviewRoundForm(initial={'round_number': next_round_number})
    note_form = ApplicationNoteForm()

    context = {
        'application': application,
        'rounds': rounds,
        'notes': notes,
        'round_form': round_form,
        'note_form': note_form,
    }
    return render(request, 'tracker/application_detail.html', context)


@login_required
def application_create_view(request):
    """
    Creates a new job application strictly owned by the current user.
    """
    has_companies = Company.objects.filter(owner=request.user).exists()
    if not has_companies:
        messages.warning(request, "Please add at least one company before creating an application.")
        return redirect('tracker:company_create')

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.owner = request.user
            application.save()
            messages.success(request, f'Application for "{application.role_title}" at {application.company.name} created!')
            return redirect('tracker:application_detail', pk=application.pk)
    else:
        # Pre-select company if passed in query param
        initial_data = {}
        company_id = request.GET.get('company')
        if company_id:
            initial_data['company'] = company_id
        form = JobApplicationForm(user=request.user, initial=initial_data)

    context = {
        'form': form,
        'title': 'Add New Job Application',
        'submit_text': 'Create Application',
        'cancel_url': reverse('tracker:application_list'),
    }
    return render(request, 'tracker/form_generic.html', context)


@login_required
def application_update_view(request, pk):
    """
    Edits an existing job application.
    """
    application = get_owner_scoped_object_or_404(JobApplication, request.user, pk=pk)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, instance=application, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Application for "{application.role_title}" updated successfully.')
            return redirect('tracker:application_detail', pk=application.pk)
    else:
        form = JobApplicationForm(instance=application, user=request.user)

    context = {
        'form': form,
        'title': f'Edit Application: {application.role_title} ({application.company.name})',
        'submit_text': 'Update Application',
        'cancel_url': reverse('tracker:application_detail', kwargs={'pk': application.pk}),
    }
    return render(request, 'tracker/form_generic.html', context)


@login_required
def application_delete_view(request, pk):
    """
    Deletes a job application and all associated interview rounds and notes.
    """
    application = get_owner_scoped_object_or_404(JobApplication, request.user, pk=pk)

    if request.method == 'POST':
        title = application.role_title
        company_name = application.company.name
        application.delete()
        messages.success(request, f'Application for "{title}" at {company_name} was deleted.')
        return redirect('tracker:application_list')

    context = {
        'item_type': 'Application',
        'item_title': f'{application.role_title} at {application.company.name}',
        'cancel_url': reverse('tracker:application_detail', kwargs={'pk': application.pk}),
    }
    return render(request, 'tracker/confirm_delete.html', context)


# -----------------------------------------------------------------------------
# Company CRUD Views
# -----------------------------------------------------------------------------

@login_required
def company_list_view(request):
    """
    Lists companies tracked by the authenticated user with search and application counts.
    """
    search_query = request.GET.get('q', '').strip()
    companies = get_companies_with_counts(request.user)

    if search_query:
        companies = companies.filter(name__icontains=search_query)

    context = {
        'companies': companies,
        'search_query': search_query,
    }
    return render(request, 'tracker/companies.html', context)


@login_required
def company_create_view(request):
    """
    Creates a new target company scoped to the authenticated user.
    """
    if request.method == 'POST':
        form = CompanyForm(request.POST, user=request.user)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            messages.success(request, f'Company "{company.name}" added successfully.')
            return redirect('tracker:company_list')
    else:
        form = CompanyForm(user=request.user)

    context = {
        'form': form,
        'title': 'Add Target Company',
        'submit_text': 'Save Company',
        'cancel_url': reverse('tracker:company_list'),
    }
    return render(request, 'tracker/form_generic.html', context)


@login_required
def company_update_view(request, pk):
    """
    Updates an existing company profile.
    """
    company = get_owner_scoped_object_or_404(Company, request.user, pk=pk)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Company "{company.name}" updated.')
            return redirect('tracker:company_list')
    else:
        form = CompanyForm(instance=company, user=request.user)

    context = {
        'form': form,
        'title': f'Edit Company: {company.name}',
        'submit_text': 'Update Company',
        'cancel_url': reverse('tracker:company_list'),
    }
    return render(request, 'tracker/form_generic.html', context)


@login_required
def company_delete_view(request, pk):
    """
    Deletes a company and cascades to its applications.
    """
    company = get_owner_scoped_object_or_404(Company, request.user, pk=pk)

    if request.method == 'POST':
        name = company.name
        company.delete()
        messages.success(request, f'Company "{name}" and all related applications were deleted.')
        return redirect('tracker:company_list')

    context = {
        'item_type': 'Company',
        'item_title': company.name,
        'extra_warning': 'Deleting this company will also delete all associated job applications and interview rounds!',
        'cancel_url': reverse('tracker:company_list'),
    }
    return render(request, 'tracker/confirm_delete.html', context)


# -----------------------------------------------------------------------------
# Resume Version CRUD Views
# -----------------------------------------------------------------------------

@login_required
def resume_list_view(request):
    """
    Displays the user's registered resume versions.
    """
    resumes = get_resumes_with_counts(request.user)
    context = {
        'resumes': resumes,
    }
    return render(request, 'tracker/resumes.html', context)


@login_required
def resume_create_view(request):
    """
    Registers a new tailored resume profile for the user.
    """
    if request.method == 'POST':
        form = ResumeVersionForm(request.POST, user=request.user)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.owner = request.user
            resume.save()
            messages.success(request, f'Resume version "{resume.label}" added.')
            return redirect('tracker:resume_list')
    else:
        form = ResumeVersionForm(user=request.user)

    context = {
        'form': form,
        'title': 'Add Resume Version',
        'submit_text': 'Save Resume Version',
        'cancel_url': reverse('tracker:resume_list'),
    }
    return render(request, 'tracker/form_generic.html', context)


@login_required
def resume_update_view(request, pk):
    """
    Updates an existing resume version profile.
    """
    resume = get_owner_scoped_object_or_404(ResumeVersion, request.user, pk=pk)

    if request.method == 'POST':
        form = ResumeVersionForm(request.POST, instance=resume, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Resume version "{resume.label}" updated.')
            return redirect('tracker:resume_list')
    else:
        form = ResumeVersionForm(instance=resume, user=request.user)

    context = {
        'form': form,
        'title': f'Edit Resume Version: {resume.label}',
        'submit_text': 'Update Resume Version',
        'cancel_url': reverse('tracker:resume_list'),
    }
    return render(request, 'tracker/form_generic.html', context)


@login_required
def resume_delete_view(request, pk):
    """
    Deletes a resume version.
    """
    resume = get_owner_scoped_object_or_404(ResumeVersion, request.user, pk=pk)

    if request.method == 'POST':
        label = resume.label
        resume.delete()
        messages.success(request, f'Resume version "{label}" was deleted.')
        return redirect('tracker:resume_list')

    context = {
        'item_type': 'Resume Version',
        'item_title': resume.label,
        'cancel_url': reverse('tracker:resume_list'),
    }
    return render(request, 'tracker/confirm_delete.html', context)


# -----------------------------------------------------------------------------
# InterviewRound Endpoints
# -----------------------------------------------------------------------------

@login_required
def round_create_view(request, app_pk):
    """
    Adds a new interview round to a job application owned by the user.
    """
    application = get_owner_scoped_object_or_404(JobApplication, request.user, pk=app_pk)

    if request.method == 'POST':
        form = InterviewRoundForm(request.POST)
        if form.is_valid():
            round_obj = form.save(commit=False)
            round_obj.application = application
            round_obj.save()
            messages.success(request, f'Round {round_obj.round_number} ({round_obj.get_round_type_display()}) scheduled.')
        else:
            messages.error(request, 'Failed to add round. Please correct the form errors.')
    return redirect('tracker:application_detail', pk=application.pk)


@login_required
def round_update_view(request, pk):
    """
    Edits an existing interview round.
    """
    round_obj = get_owner_scoped_object_or_404(InterviewRound, request.user, pk=pk)
    application = round_obj.application

    if request.method == 'POST':
        form = InterviewRoundForm(request.POST, instance=round_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Round {round_obj.round_number} updated.')
            return redirect('tracker:application_detail', pk=application.pk)
    else:
        form = InterviewRoundForm(instance=round_obj)

    context = {
        'form': form,
        'title': f'Edit Round {round_obj.round_number}: {application.role_title} at {application.company.name}',
        'submit_text': 'Update Round',
        'cancel_url': reverse('tracker:application_detail', kwargs={'pk': application.pk}),
    }
    return render(request, 'tracker/form_generic.html', context)


@login_required
def round_delete_view(request, pk):
    """
    Deletes an interview round.
    """
    round_obj = get_owner_scoped_object_or_404(InterviewRound, request.user, pk=pk)
    app_pk = round_obj.application.pk

    if request.method == 'POST':
        round_num = round_obj.round_number
        round_obj.delete()
        messages.success(request, f'Round {round_num} deleted.')
        return redirect('tracker:application_detail', pk=app_pk)

    context = {
        'item_type': 'Interview Round',
        'item_title': f'Round {round_obj.round_number} ({round_obj.get_round_type_display()})',
        'cancel_url': reverse('tracker:application_detail', kwargs={'pk': app_pk}),
    }
    return render(request, 'tracker/confirm_delete.html', context)


# -----------------------------------------------------------------------------
# ApplicationNote Endpoints
# -----------------------------------------------------------------------------

@login_required
def note_create_view(request, app_pk):
    """
    Adds a new note to a job application owned by the user.
    """
    application = get_owner_scoped_object_or_404(JobApplication, request.user, pk=app_pk)

    if request.method == 'POST':
        form = ApplicationNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.application = application
            note.save()
            messages.success(request, f'Note "{note.title}" added.')
        else:
            messages.error(request, 'Failed to add note. Please check errors.')
    return redirect('tracker:application_detail', pk=application.pk)


@login_required
def note_delete_view(request, pk):
    """
    Deletes an application note.
    """
    note = get_owner_scoped_object_or_404(ApplicationNote, request.user, pk=pk)
    app_pk = note.application.pk

    if request.method == 'POST':
        title = note.title
        note.delete()
        messages.success(request, f'Note "{title}" deleted.')
        return redirect('tracker:application_detail', pk=app_pk)

    context = {
        'item_type': 'Note',
        'item_title': note.title,
        'cancel_url': reverse('tracker:application_detail', kwargs={'pk': app_pk}),
    }
    return render(request, 'tracker/confirm_delete.html', context)
