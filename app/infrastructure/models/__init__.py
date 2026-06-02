"""
app/infrastructure/models/__init__.py

Alembic autogenerate 가 모든 테이블을 인식하도록 모든 ORM 모델을 import 한다.
"""

# ── User 도메인 ──────────────────────────────────────────────
from app.infrastructure.models.user_model import (
    ProviderType,
    UserModel,
    UserAuthProviderModel,
    UserResidenceModel,
    UserSettingModel,
    VerificationStatus,
)

# ── Disaster 도메인 ──────────────────────────────────────────
from app.infrastructure.models.disaster_model import (
    AftershockFeeling,
    AvailableTime,
    DisasterImpactModel,
    DisasterTypeModel,
    EarthquakeImpactModel,
    FireDamageScope,
    FireImpactModel,
    FloodImpactModel,
    FloodLevel,
    InjuryLevel,
    RegistrationStatus,
    ResidenceStatus,
    SafetyStatus,
    SmokeInhalation,
    TyphoonImpactModel,
    UserDisasterModel,
    WaterDrainStatus,
)

# ── Recovery 도메인 ──────────────────────────────────────────
from app.infrastructure.models.recovery_model import (
    DailyStatusCheckModel,
    RecoveryFeatureModel,
    RecoveryOutputModel,
    RecoveryStageMasterModel,
)

# ── Checklist 도메인 ─────────────────────────────────────────
from app.infrastructure.models.checklist_model import (
    ArchiveFileModel,
    ArchiveItemModel,
    ChecklistItemModel,
)

# ── Community 도메인 ─────────────────────────────────────────
from app.infrastructure.models.community_model import (
    CommunityCategoryModel,
    CommunityPostAttachmentModel,
    CommunityPostLinkModel,
    CommunityPostModel,
    CommunityProfileModel,
)

__all__ = [
    # ── User models ──────────────────────────────────────────
    "UserModel",
    "UserAuthProviderModel",
    "UserResidenceModel",
    "UserSettingModel",
    # ── User enums ───────────────────────────────────────────
    "VerificationStatus",
    "ProviderType",
    # ── Disaster models ──────────────────────────────────────
    "DisasterTypeModel",
    "UserDisasterModel",
    "DisasterImpactModel",
    "EarthquakeImpactModel",
    "TyphoonImpactModel",
    "FireImpactModel",
    "FloodImpactModel",
    # ── Disaster enums ───────────────────────────────────────
    "RegistrationStatus",
    "SafetyStatus",
    "ResidenceStatus",
    "InjuryLevel",
    "AftershockFeeling",
    "FireDamageScope",
    "SmokeInhalation",
    "FloodLevel",
    "WaterDrainStatus",
    "AvailableTime",
    # ── Recovery models ──────────────────────────────────────
    "RecoveryStageMasterModel",
    "RecoveryOutputModel",
    "RecoveryFeatureModel",
    "DailyStatusCheckModel",
    # ── Checklist models ─────────────────────────────────────
    "ChecklistItemModel",
    "ArchiveItemModel",
    "ArchiveFileModel",
    # ── Community models ─────────────────────────────────────
    "CommunityProfileModel",
    "CommunityCategoryModel",
    "CommunityPostModel",
    "CommunityPostLinkModel",
    "CommunityPostAttachmentModel",
]