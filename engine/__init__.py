"""Pinned PROWRAP v1.3 calculation engine package."""
import sys

from . import prowrap_materials as _prowrap_materials

# The accepted v1.3 optimizer is byte-for-byte pinned from the standalone
# engine, where material modules are imported from the repository root.
sys.modules.setdefault("prowrap_materials", _prowrap_materials)

from .corrosion_defects import (
    ACTUAL_DEFECT_LENGTH,
    DEFECT_LENGTH_BASES,
    ENTER_MANUALLY,
    INDEPENDENT_DEFECTS,
    CorrosionAssessmentPlan,
    IndividualCorrosionDefect,
    build_corrosion_assessment_plan,
)

__all__ = [
    "ACTUAL_DEFECT_LENGTH",
    "DEFECT_LENGTH_BASES",
    "ENTER_MANUALLY",
    "INDEPENDENT_DEFECTS",
    "CorrosionAssessmentPlan",
    "IndividualCorrosionDefect",
    "build_corrosion_assessment_plan",
]
