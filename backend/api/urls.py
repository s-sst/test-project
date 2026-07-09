"""Public API surface — single source of truth for every route.

Concentrating the URL contract here (rather than scattering it across app
``urls.py`` files) makes it trivial to see, review and preserve the API shape
across phases (Rule 7: maintain backward compatibility).
"""
from __future__ import annotations

from django.urls import include, path

from assessments.views import (
    AssessmentDetailView,
    HistoryView,
    ProcessView,
    ReprocessView,
)
from audit_logs.views import AuditLogListView
from dashboard.views import DashboardView
from documents.views import DocumentDetailView, DocumentListView, DocumentUploadView
from frameworks.views import FrameworkDetailView, FrameworkListView
from reports.views import ReportCreateView, ReportDetailView, ReportDownloadView
from scoring.views import ScoreOverrideView

from .views import HealthView, RootView

urlpatterns = [
    path("", RootView.as_view(), name="api-root"),
    path("health", HealthView.as_view(), name="health"),
    # --- Documents / ingestion ---
    path("upload", DocumentUploadView.as_view(), name="upload"),
    path("documents", DocumentListView.as_view(), name="document-list"),
    path("documents/<uuid:pk>", DocumentDetailView.as_view(), name="document-detail"),
    # --- Frameworks ---
    path("frameworks", FrameworkListView.as_view(), name="framework-list"),
    path("framework/<slug:framework_id>", FrameworkDetailView.as_view(), name="framework-detail"),
    # --- Assessments ---
    path("process", ProcessView.as_view(), name="process"),
    path("reprocess", ReprocessView.as_view(), name="reprocess"),
    path("history", HistoryView.as_view(), name="history"),
    path("assessment/<uuid:assessment_id>", AssessmentDetailView.as_view(), name="assessment-detail"),
    # --- Reports & dashboard ---
    path("report", ReportCreateView.as_view(), name="report-create"),
    path("report/<uuid:report_id>", ReportDetailView.as_view(), name="report-detail"),
    path("report/<uuid:report_id>/download", ReportDownloadView.as_view(), name="report-download"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    # --- Human oversight ---
    path("score/<uuid:score_id>/override", ScoreOverrideView.as_view(), name="score-override"),
    # --- Audit ---
    path("audit-logs", AuditLogListView.as_view(), name="audit-log-list"),
    # --- Auth ---
    path("auth/", include("authentication.urls")),
]
