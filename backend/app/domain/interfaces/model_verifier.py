from abc import ABC, abstractmethod
from ..entities.cad_model import CADModel
from ..value_objects.verification import VerificationResult


class IModelVerifier(ABC):
    """
    生成された 3D モデルと元の図面を比較検証するインターフェース（Step 5）
    """

    @abstractmethod
    def verify(self, cad_model: CADModel) -> VerificationResult:
        """元の図面と生成された CAD モデルを比較し、検証結果を返す"""
        pass
