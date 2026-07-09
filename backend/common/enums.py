"""Centralised enumerations (Django ``TextChoices``).

Every status/type constant used across modules lives here so the vocabulary
of the platform is defined exactly once. Framework-specific values (control
ids, weights, criteria) are NEVER enumerated here — those are configuration
(Rule 4). These enums describe *platform mechanics*, not governance content.
"""
from __future__ import annotations

from django.db import models


class ComplianceStatus(models.TextChoices):
    """The four permissible requirement verdicts. Produced by the LLM
    (classification only), never invented by Python."""

    PASS = "PASS", "Pass"
    PARTIAL = "PARTIAL", "Partial"
    FAIL = "FAIL", "Fail"
    CANNOT_DETERMINE = "CANNOT_DETERMINE", "Cannot Determine"


class AssessmentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class DocumentStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    PROCESSING = "PROCESSING", "Processing"
    PROCESSED = "PROCESSED", "Processed"
    FAILED = "FAILED", "Failed"


class DocumentType(models.TextChoices):
    """Supported governance document classes (see PROJECT INPUTS)."""

    AI_SYSTEM_DOC = "AI_SYSTEM_DOC", "AI System Documentation"
    MODEL_CARD = "MODEL_CARD", "Model Card"
    DATASHEET = "DATASHEET", "Datasheet"
    SECURITY_POLICY = "SECURITY_POLICY", "Security Policy"
    GOVERNANCE_POLICY = "GOVERNANCE_POLICY", "Governance Policy"
    RISK_ASSESSMENT = "RISK_ASSESSMENT", "Risk Assessment"
    DPIA = "DPIA", "Data Protection Impact Assessment"
    SOP = "SOP", "Standard Operating Procedure"
    TECHNICAL_PDF = "TECHNICAL_PDF", "Technical PDF"
    OTHER = "OTHER", "Other"


class ChunkType(models.TextChoices):
    RECURSIVE = "RECURSIVE", "Recursive"
    PAGE = "PAGE", "Page"
    TABLE = "TABLE", "Table"


class ScoreLevel(models.TextChoices):
    """Granularity of an AssessmentScore row. The scoring engine rolls
    requirement scores up through control, framework and overall levels."""

    REQUIREMENT = "REQUIREMENT", "Requirement"
    CONTROL = "CONTROL", "Control"
    FRAMEWORK = "FRAMEWORK", "Framework"
    OVERALL = "OVERALL", "Overall"


class RiskLevel(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class Priority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class RecommendationStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    RESOLVED = "RESOLVED", "Resolved"
    DISMISSED = "DISMISSED", "Dismissed"


class ReportFormat(models.TextChoices):
    PDF = "PDF", "PDF"
    JSON = "JSON", "JSON"


class ReportStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    GENERATED = "GENERATED", "Generated"
    FAILED = "FAILED", "Failed"


class UserRole(models.TextChoices):
    """Coarse RBAC roles. Enforcement is a later phase; the field exists now so
    the audit trail can attribute actions to a role from day one."""

    ADMIN = "ADMIN", "Administrator"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER", "Compliance Officer"
    AUDITOR = "AUDITOR", "Auditor"
    ML_ENGINEER = "ML_ENGINEER", "ML Engineer"
    VIEWER = "VIEWER", "Viewer"


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    UPLOAD = "UPLOAD", "Upload"
    PROCESS = "PROCESS", "Process"
    REPROCESS = "REPROCESS", "Reprocess"
    OVERRIDE = "OVERRIDE", "Human Override"
    EXPORT = "EXPORT", "Export"
    SYNC = "SYNC", "Framework Sync"
    LOGIN = "LOGIN", "Login"
    VIEW = "VIEW", "View"
