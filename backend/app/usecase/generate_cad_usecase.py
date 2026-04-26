from app.domain.entities.cad_model import CADModel
from app.usecase.analyze_blueprint_usecase import AnalyzeBlueprintUseCase
from app.usecase.generate_and_execute_script_usecase import GenerateAndExecuteScriptUseCase
from loguru import logger


class GenerateCadUseCase:
    """
    フルパイプライン: Step 1 (解析) → Step 2 (生成) → Step 3 (実行)。
    Step 1 の後に確認事項が残っていれば Step 2-3 はスキップし、ユーザー回答待ちで戻る。
    """

    def __init__(
        self,
        analyze_usecase: AnalyzeBlueprintUseCase,
        generate_and_execute_usecase: GenerateAndExecuteScriptUseCase,
    ):
        self.analyze_usecase = analyze_usecase
        self.generate_and_execute_usecase = generate_and_execute_usecase

    def execute(self, model_id: str) -> CADModel:
        logger.info(f"[Step 1] 図面解析を開始 (model_id={model_id})")
        cad_model = self.analyze_usecase.execute(model_id)
        logger.info(f"[Step 1] 図面解析完了 ({len(cad_model.design_steps)}ステップ)")
        for step in cad_model.design_steps:
            logger.info(f"[Step 1]   Step {step.step_number}: {step.instruction}")

        if cad_model.clarifications and not cad_model.clarifications_confirmed:
            logger.info(
                f"[Step 1] {len(cad_model.clarifications)} 件の確認事項が検出されました。"
                "ユーザー確認待機中..."
            )
            return cad_model

        return self.generate_and_execute_usecase.execute(model_id)
