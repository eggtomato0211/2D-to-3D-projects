from dataclasses import dataclass, field
from enum import Enum


class ParameterType(Enum):
    """パラメータの種別"""
    LENGTH = "length"        # 直線エッジの長さ
    RADIUS = "radius"        # 円弧・円筒の半径
    BOUNDING_X = "bounding_x"  # バウンディングボックス X寸法
    BOUNDING_Y = "bounding_y"  # バウンディングボックス Y寸法
    BOUNDING_Z = "bounding_z"  # バウンディングボックス Z寸法


@dataclass(frozen=True)
class ModelParameter:
    """
    3Dモデルから抽出された寸法パラメータ。

    Attributes:
        name: パラメータの表示名（例: "上面 X方向エッジ", "中央の穴"）
        value: 数値（mm単位）
        parameter_type: パラメータの種別
        edge_points: エッジの3D座標リスト [[x,y,z], ...] - ハイライト描画用
    """
    name: str
    value: float
    parameter_type: ParameterType
    edge_points: list[list[float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name は空にできません")
        if self.value < 0:
            raise ValueError("value は0以上である必要があります")
