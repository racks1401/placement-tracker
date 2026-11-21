from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404


class OwnerRequiredMixin(LoginRequiredMixin):
    """
    Ensures the user is authenticated and restricts the queryset strictly to objects
    owned by the logged-in user. Any attempt to access another user's object returns a 404.
    """
    owner_field = 'owner'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.none()
        filter_kwargs = {self.owner_field: self.request.user}
        return qs.filter(**filter_kwargs)


class ApplicationChildOwnerMixin(LoginRequiredMixin):
    """
    For child models of JobApplication (InterviewRound, ApplicationNote).
    Restricts queries strictly to records whose parent application belongs to request.user.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.none()
        return qs.filter(application__owner=self.request.user)


def get_owner_scoped_object_or_404(model_class, user, **kwargs):
    """
    Helper function for function-based views to fetch an object strictly owned by the user,
    or raise Http404 to prevent primary key enumeration/probing.
    """
    if not user.is_authenticated:
        raise Http404(f"No {model_class.__name__} matches the given query.")
    try:
        if hasattr(model_class, 'owner'):
            return model_class.objects.get(owner=user, **kwargs)
        elif hasattr(model_class, 'application'):
            return model_class.objects.get(application__owner=user, **kwargs)
        else:
            return model_class.objects.get(**kwargs)
    except model_class.DoesNotExist:
        raise Http404(f"No {model_class.__name__} matches the given query.")
