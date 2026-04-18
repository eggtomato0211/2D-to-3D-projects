from app.usecase.analyze_blueprint_usecase import AnalyzeBlueprintUseCase
from app.usecase.generate_script_usecase import GenerateScriptUseCase
from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.domain.interfaces.script_generator import IScriptGenerator
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from loguru import logger

MAX_FIX_ATTEMPTS = 5


class GenerateCadUseCase:
    def __init__(
        self,
        analyze_usecase: AnalyzeBlueprintUseCase,
        generate_script_usecase: GenerateScriptUseCase,
        execute_script_usecase: ExecuteScriptUseCase,
        script_generator: IScriptGenerator,
        cad_model_repo: ICADModelRepository,
    ):
        self.analyze_usecase = analyze_usecase
        self.generate_script_usecase = generate_script_usecase
        self.execute_script_usecase = execute_script_usecase
        self.script_generator = script_generator
        self.cad_model_repo = cad_model_repo

    def execute(self, model_id: str):
        # Step 1: 図面を解析して設計意図を生成
        logger.info(f"[Step 1] 図面解析を開始 (model_id={model_id})")
        design_intent = self.analyze_usecase.execute(model_id)
        logger.info(f"[Step 1] 図面解析完了 ({len(design_intent.steps)}ステップ)")
        for step in design_intent.steps:
            logger.info(f"[Step 1]   Step {step.step_number}: {step.instruction}")

        # Step 1 後: 確認事項がある場合は一旦停止
        cad_model = self.cad_model_repo.get_by_id(model_id)
        if cad_model.clarifications and not cad_model.clarifications_confirmed:
            logger.info(
                f"[Step 1] {len(cad_model.clarifications)} 件の確認事項が検出されました。"
                f"ユーザー確認待機中..."
            )
            return cad_model

        # Step 2: 設計意図からCadQueryスクリプトを生成
        logger.info("[Step 2] スクリプト生成を開始")
        cad_script = self.generate_script_usecase.execute(model_id, design_intent)
        logger.info("[Step 2] スクリプト生成完了")

        # Step 3: CadQueryスクリプトを実行（失敗時はエラー修正ループ）
        logger.info("[Step 3] スクリプト実行を開始")
        cad_model = self.execute_script_usecase.execute(model_id, cad_script)

        for attempt in range(MAX_FIX_ATTEMPTS):
            if cad_model.error_message is None:
                logger.info("[Step 3] スクリプト実行成功")
                break

            logger.warning(f"[Step 3] 実行失敗 (試行 {attempt + 1}/{MAX_FIX_ATTEMPTS}): {cad_model.error_message}")
            logger.info(f"[Step 3] エラー修正ループ: スクリプト修正を開始")
            cad_script = self.script_generator.fix_script(
                cad_script, cad_model.error_message
            )
            logger.info(f"[Step 3] 修正スクリプトで再実行")
            cad_model = self.execute_script_usecase.execute(model_id, cad_script)
        else:
            if cad_model.error_message is not None:
                logger.error(f"[Step 3] 最大リトライ回数({MAX_FIX_ATTEMPTS})を超過。修正失敗")

        return cad_model
