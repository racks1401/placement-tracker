from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError

from .models import ApplicationNote, Company, InterviewRound, JobApplication, ResumeVersion


class JobApplicationForm(forms.ModelForm):
    """
    Form for creating and editing job applications.
    Strictly filters Company and ResumeVersion foreign key dropdowns to the logged-in user.
    """
    applied_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        help_text='Date you submitted the application',
    )
    next_action_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        help_text='Next follow-up, test deadline, or interview date',
    )
    job_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Job description or requirements'}),
    )

    class Meta:
        model = JobApplication
        fields = [
            'company',
            'role_title',
            'resume_version',
            'status',
            'source',
            'work_mode',
            'location',
            'expected_ctc_lpa',
            'applied_date',
            'next_action_date',
            'job_url',
            'job_description',
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-input'}),
            'resume_version': forms.Select(attrs={'class': 'form-input'}),
            'role_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Software Development Engineer'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'source': forms.Select(attrs={'class': 'form-input'}),
            'work_mode': forms.Select(attrs={'class': 'form-input'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Bengaluru, India or Remote'}),
            'expected_ctc_lpa': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 18.5'}),
            'job_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://careers.example.com/job/123'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.user = user
            # Tenant-scoped dropdowns
            self.fields['company'].queryset = Company.objects.filter(owner=user).order_by('name')
            self.fields['resume_version'].queryset = ResumeVersion.objects.filter(owner=user).order_by('-is_default', 'label')
            self.fields['company'].empty_label = 'Select a company...'
            self.fields['resume_version'].empty_label = 'Select a resume version (optional)...'

    def clean_expected_ctc_lpa(self):
        ctc = self.cleaned_data.get('expected_ctc_lpa')
        if ctc is not None and ctc < Decimal('0.00'):
            raise ValidationError("Expected CTC cannot be negative.")
        return ctc


class CompanyForm(forms.ModelForm):
    """
    Form for creating and editing target employers.
    Enforces tenant-scoped unique name validation.
    """
    class Meta:
        model = Company
        fields = ['name', 'website', 'industry', 'location', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Company name (e.g. Google)'}),
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://company.com'}),
            'industry': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. FinTech, SaaS, E-Commerce'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Headquarters or office location'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Hiring process notes, campus tier, referral contact'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if self.user:
            qs = Company.objects.filter(owner=self.user, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("You already have a company registered with this name.")
        return name


class ResumeVersionForm(forms.ModelForm):
    """
    Form for registering resume profiles and tailored versions.
    """
    class Meta:
        model = ResumeVersion
        fields = ['label', 'target_role', 'plain_text', 'notes', 'is_default']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Backend Go/Python v2'}),
            'target_role': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Backend Software Engineer'}),
            'plain_text': forms.Textarea(attrs={'class': 'form-input font-mono', 'rows': 6, 'placeholder': 'Paste plain text resume summary or highlights'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Tailored highlights, keywords included, projects featured'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user


class InterviewRoundForm(forms.ModelForm):
    """
    Form for scheduling and recording interview rounds.
    """
    scheduled_at = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-input'},
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        help_text='Scheduled date and time',
    )

    class Meta:
        model = InterviewRound
        fields = [
            'round_number',
            'round_type',
            'scheduled_at',
            'status',
            'interviewer_name',
            'notes',
            'self_rating',
        ]
        widgets = {
            'round_number': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'round_type': forms.Select(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'interviewer_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Interviewer name or panel'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Questions asked, LeetCode topics, feedback'}),
            'self_rating': forms.Select(
                choices=[('', 'Select rating (1-5)...')] + [(i, f'{i} - {"Poor" if i==1 else "Average" if i==3 else "Excellent" if i==5 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-input'}
            ),
        }

    def clean_round_number(self):
        num = self.cleaned_data.get('round_number')
        if num is not None and num < 1:
            raise ValidationError("Round number must be 1 or greater.")
        return num


class ApplicationNoteForm(forms.ModelForm):
    """
    Form for adding free-form notes to a job application.
    """
    class Meta:
        model = ApplicationNote
        fields = ['title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Note title (e.g. HR Follow-up call)'}),
            'body': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Write your notes, salary discussion, impressions...'}),
        }
