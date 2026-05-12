"""4 視点（top / front / side / iso）から撮った PNG を保持する値オブジェクト。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FourViewImage:
    """4 視点 PNG バイト列。

    JIS B 0001 第三角法に準拠した視点を想定:
    - top:   +Z 方向から見下ろす（平面図）
    - front: -Y 方向から見る（正面図）
    - side:  +X 方向から見る（右側面図）
    - iso:   (+X, -Y, +Z) 方向からの等角投影
    """
    top: bytes
    front: bytes
    side: bytes
    iso: bytes

    def as_list(self) -> list[bytes]:
        """PNG のリスト形式で返す（順序: top, front, side, iso）。"""
        return [self.top, self.front, self.side, self.iso]
