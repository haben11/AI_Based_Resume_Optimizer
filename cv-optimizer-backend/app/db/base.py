# Import all the models, so that Base has them before being
# imported by Alembic or used to create tables
from app.db.session import Base  # noqa
from app.models.user import User  # noqa
from app.models.resume import Resume, OptimizationHistory  # noqa
from app.models.structured_resume import (  # noqa
    StructuredResume,
    ResumeSection,
    BulletPoint,
    OptimizationRequest,
    ResumeVersion,
    AISuggestion
)
from app.models.knowledge_base import (  # noqa
    ATSKeyword,
    IndustrySkill,
    JobTitleData,
    ActionVerb,
    IndustryMetric,
    CompanyData,
    CertificationData,
    EducationData
)
from app.models.semantic_cache import (  # noqa
    SemanticCacheEntry,
    CacheStatistics
)
from app.models.refresh_token import RefreshToken  # noqa
