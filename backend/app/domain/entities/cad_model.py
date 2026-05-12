from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..value_objects.cad_script import CadScript
from ..value_objects.clarification import Clarification
from ..value_objects.design_step import DesignStep
from ..value_objects.iteration_attempt import IterationAttempt
from ..value_objects.model_parameter import ModelParameter
from ..value_objects.verification import VerificationResult


class GenerationStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"      # Step 1
    GENERATING = "generating"    # Step 2
    EXECUTING = "executing"      # Step 3
    RENDERING = "rendering"      # Step 4
    VERIFYING = "verifying"      # Step 5
    CORRECTING = "correcting"    # Step 6 (Phase 2 ループ修正)
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class CADModel:
    """生成された 3D モデルの管理情報を表すエンティティ。

    Phase 1 のスクリプト生成 + Phase 2 の verify-correct ループに渡って
    状態を保持する。design_steps / clarifications / iteration_history は
    パイプライン進行に合わせて埋まる。
    """
    id: str
    blueprint_id: str
    status: GenerationStatus
    stl_path: Optional[str] = None
    step_path: Optional[str] = None
    error_message: Optional[str] = None
    parameters: list[ModelParameter] = field(default_factory=list)
    cad_script: Optional[CadScript] = None
    clarifications: list[Clarification] = field(default_factory=list)
    clarifications_confirmed: bool = False
    design_steps: list[DesignStep] = field(default_factory=list)
    verification_result: Optional[VerificationResult] = None
    iteration_history: list[IterationAttempt] = field(default_factory=list)
    model_provider_id: Optional[str] = None  # 生成に使った VLM の ID
