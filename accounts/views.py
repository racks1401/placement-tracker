from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import UserLoginForm, UserProfileForm, UserRegistrationForm


def register_view(request):
    """
    Handles new user account registration and logs them in immediately upon success.
    """
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f'Welcome to PlacementTracker, {user.username}! Your account has been created.')
            return redirect('tracker:dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Handles user login using standard Django session authentication.
    """
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')

    redirect_to = request.POST.get('next', request.GET.get('next', ''))

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            # Ensure safe redirection
            if redirect_to and url_has_allowed_host_and_scheme(redirect_to, allowed_hosts={request.get_host()}):
                return redirect(redirect_to)
            return redirect('tracker:dashboard')
    else:
        form = UserLoginForm(request)

    return render(request, 'accounts/login.html', {'form': form, 'next': redirect_to})


def logout_view(request):
    """
    Logs out the current authenticated user and redirects to login page.
    Supports both POST and GET for clean UX.
    """
    if request.user.is_authenticated:
        auth_logout(request)
        messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """
    Allows the authenticated user to view and update basic preferences and profile details.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile preferences have been updated.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})
