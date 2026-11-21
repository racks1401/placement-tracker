from django.contrib import admin
from .models import ApplicationNote, Company, InterviewRound, JobApplication, ResumeVersion


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'industry', 'location', 'created_at')
    search_fields = ('name', 'industry', 'location', 'owner__username')
    list_filter = ('industry', 'created_at')


@admin.register(ResumeVersion)
class ResumeVersionAdmin(admin.ModelAdmin):
    list_display = ('label', 'owner', 'target_role', 'is_default', 'created_at')
    search_fields = ('label', 'target_role', 'owner__username')
    list_filter = ('is_default', 'created_at')


class InterviewRoundInline(admin.TabularInline):
    model = InterviewRound
    extra = 0


class ApplicationNoteInline(admin.TabularInline):
    model = ApplicationNote
    extra = 0


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('role_title', 'company', 'owner', 'status', 'source', 'work_mode', 'applied_date', 'updated_at')
    search_fields = ('role_title', 'company__name', 'owner__username')
    list_filter = ('status', 'source', 'work_mode', 'applied_date')
    inlines = [InterviewRoundInline, ApplicationNoteInline]


@admin.register(InterviewRound)
class InterviewRoundAdmin(admin.ModelAdmin):
    list_display = ('application', 'round_number', 'round_type', 'status', 'scheduled_at', 'self_rating')
    list_filter = ('round_type', 'status', 'scheduled_at')
    search_fields = ('application__role_title', 'application__company__name', 'interviewer_name')


@admin.register(ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'application', 'created_at')
    search_fields = ('title', 'body', 'application__role_title')
