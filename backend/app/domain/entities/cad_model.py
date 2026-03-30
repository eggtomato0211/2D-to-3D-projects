from dataclasses import dataclass
from enum import Enum
from typing import Optional

class GenerationStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"

@dataclass
class CADModel:
    """
    生成された3Dモデルの管理情報を表すエンティティ。
    ステータス遷移（PENDING→SUCCESS/FAILED）を持ち、成果物のパスやエラー情報を保持する。
    """
    id: str
    blueprint_id: str
    status: GenerationStatus
    stl_path: Optional[str] = None
    error_message: Optional[str] = None
