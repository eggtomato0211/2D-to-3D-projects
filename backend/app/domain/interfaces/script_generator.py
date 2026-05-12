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
    """
    設計手順と確認事項から CadQuery スクリプトを生成するインターフェース（Step 2）
    """

    @abstractmethod
    def generate(
        self,
        steps: list[DesignStep],
        clarifications: list[Clarification],
    ) -> CadScript:
        """設計手順と確認事項から CadQuery スクリプトを生成する"""
        pass

    @abstractmethod
    def fix_script(self, script: CadScript, feedback: str) -> CadScript:
        """生成されたスクリプトに対してフィードバックを反映し、修正する（runtime error 用）"""
        pass

    @abstractmethod
    def modify_parameters(
        self,
        script: CadScript,
        old_parameters: list[ModelParameter],
        new_parameters: list[ModelParameter],
    ) -> CadScript:
        """パラメータの変更をスクリプトに反映する"""
        pass

    def correct_script(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str] = None,
        line_views: Optional[FourViewImage] = None,
        shaded_views: Optional[FourViewImage] = None,
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> CadScript:
        """
        生成済みスクリプト（構文的には正しい）と、検証で見つかった不一致リストを受け取り、
        不一致を解消するよう修正したスクリプトを返す（Phase 2-δ ループ用）。

        画像引数（§10.1）と過去 iter 履歴（§10.3）はオプション:
        - 画像: Verifier と同じ視覚情報を Corrector が参照することで、
                テキスト記述だけでは曖昧になる位置・寸法情報を補える
        - 履歴: 過去の試行と結果を Corrector に伝えることで、
                同じ失敗の繰り返しを抑制する

        既定実装は fix_script に整形済みフィードバックを渡すテキストオンリーのフォールバック。
        各 VLM 実装で画像対応・履歴対応の専用プロンプトに差し替えることを推奨。
        """
        feedback_lines = ["以下の不一致を解消するよう CadQuery スクリプトを修正してください。"]
        for d in discrepancies:
            feedback_lines.append(d.to_feedback_line())
        return self.fix_script(script, "\n".join(feedback_lines))
