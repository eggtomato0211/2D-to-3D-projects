from abc import ABC, abstractmethod
from typing import Optional

from ..value_objects.cad_script import CadScript
from ..value_objects.clarification import Clarification
from ..value_objects.design_step import DesignStep
from ..value_objects.discrepancy import Discrepancy
from ..value_objects.four_view_image import FourViewImage
from ..value_objects.iteration_attempt import IterationAttempt
from ..value_objects.model_parameter import ModelParameter


class IScriptGenerator(ABC):
    """設計手順から CadQuery スクリプトを生成するインターフェース。"""

    @abstractmethod
    def generate(
        self,
        steps: list[DesignStep],
        clarifications: list[Clarification],
    ) -> CadScript:
        """設計手順と確認事項から CadQuery スクリプトを生成する。"""
        ...

    @abstractmethod
    def fix_script(self, script: CadScript, feedback: str) -> CadScript:
        """ランタイムエラー文字列を元にスクリプトを修正する。"""
        ...

    @abstractmethod
    def modify_parameters(
        self,
        script: CadScript,
        old_parameters: list[ModelParameter],
        new_parameters: list[ModelParameter],
    ) -> CadScript:
        """パラメータ変更をスクリプトに反映する。"""
        ...

    @abstractmethod
    def edit_script(self, script: CadScript, instruction: str) -> CadScript:
        """ユーザーの自然言語指示でスクリプトを編集する（チャット型対話用）。

        既存スクリプトを最小変更で目的の修正を反映させる。
        """
        ...

    @abstractmethod
    def correct_script(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str] = None,
        line_views: Optional[FourViewImage] = None,
        shaded_views: Optional[FourViewImage] = None,
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> CadScript:
        """構文は正しいが図面と合わないスクリプトに対し、不一致を解消する。

        Vision 対応の実装は元 2D 図面と生成モデルの 4 視点画像を入力として受け取り、
        過去の試行履歴を見て同じ失敗を繰り返さないようにする。
        画像対応していない実装はテキスト記述のみで修正してよい。
        """
        ...
