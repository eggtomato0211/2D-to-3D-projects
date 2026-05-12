from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..value_objects.cad_script import CadScript
from ..value_objects.model_parameter import ModelParameter
from ..value_objects.clarification import Clarification
from ..value_objects.design_step import DesignStep
from ..value_objects.verification_snapshot import VerificationSnapshot

class GenerationStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"      # Step 1 実行中
    GENERATING = "generating"    # Step 2 実行中
    EXECUTING = "executing"      # Step 3 実行中
    RENDERING = "rendering"      # Step 4 実行中
    VERIFYING = "verifying"      # Step 5 実行中
    SUCCESS = "success"
    FAILED = "failed"
@dataclass
class CADModel:
    """
    生成された3Dモデルの管理情報を表すエンティティ。
    ステータス遷移（PENDING→SUCCESS/FAILED）を持ち、成果物のパスやエラー情報を保持する。
    確認事項（Clarification）を保持し、ユーザーからの確認待機を管理する。
    """
    id: str
    blueprint_id: str
    status: GenerationStatus
    stl_path: Optional[str] = None
    step_path: Optional[str] = None  # Phase 2 線画レンダ用
    error_message: Optional[str] = None
    parameters: list[ModelParameter] = field(default_factory=list)
    cad_script: Optional[CadScript] = None
    clarifications: list[Clarification] = field(default_factory=list)
    clarifications_confirmed: bool = False
    design_steps: list[DesignStep] = field(default_factory=list)
    verification_history: list[VerificationSnapshot] = field(default_factory=list)
