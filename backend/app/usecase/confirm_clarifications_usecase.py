from app.domain.entities.cad_model import CADModel
from app.domain.value_objects.clarification import Clarification
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.usecase.generate_script_usecase import GenerateScriptUseCase
from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.domain.interfaces.script_generator import IScriptGenerator
from loguru import logger

MAX_FIX_ATTEMPTS = 5


class ConfirmClarificationsUseCase:
    """
    ユーザーが確認事項に回答したら、それを保存して Step 2 & 3 を実行する。
    """

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        generate_script_usecase: GenerateScriptUseCase,
        execute_script_usecase: ExecuteScriptUseCase,
        script_generator: IScriptGenerator,
    ):
        self.cad_model_repo = cad_model_repo
        self.generate_script_usecase = generate_script_usecase
        self.execute_script_usecase = execute_script_usecase
        self.script_generator = script_generator

    def execute(self, model_id: str, responses: dict[str, str]) -> CADModel:
        """
        ユーザー回答を CADModel に保存し、Step 2 & 3 を実行する。

        Args:
            model_id: 処理対象の CADModel ID
            responses: {"clarification_1": "はい", "clarification_2": "C0.5 で良い", ...}

        Returns:
            生成された CADModel
        """
        logger.info(f"[ConfirmClarifications] ユーザー回答を処理中 (model_id={model_id})")

        # CADModel を取得
        cad_model = self.cad_model_repo.get_by_id(model_id)

        # ユーザー回答を clarifications に反映
        updated_clarifications = []
        for clarification in cad_model.clarifications:
            if clarification.id in responses:
                updated_clarifications.append(Clarification(
                    id=clarification.id,
                    question=clarification.question,
                    suggested_answer=clarification.suggested_answer,
                    user_response=responses[clarification.id]
                ))
            else:
                updated_clarifications.append(clarification)

        cad_model.clarifications = updated_clarifications
        cad_model.clarifications_confirmed = True
        self.cad_model_repo.update(cad_model)

        logger.info(f"[ConfirmClarifications] ユーザー回答を保存完了")

        # Step 1 の結果（DesignIntent）を再構築
        from app.domain.entities.design_intent import DesignIntent
        design_intent = DesignIntent(
            id=cad_model.id,
            blueprint_id=cad_model.blueprint_id,
            steps=cad_model.design_steps,  # 保存された手順を取得
            clarifications=cad_model.clarifications
        )

        # Step 1 時点の DesignIntent を再構築する
        # （ScriptGenerator への入力として steps が必要）
        # 既に cad_model に情報がないため、ここでは工夫が必要
        # 実装上、design_intent は generate_script_usecase でプロンプト生成に使用される
        # clarifications 情報をプロンプトに含める必要があるため、design_intent に詰める

        logger.info(f"[ConfirmClarifications] Step 2 スクリプト生成を開始")
        cad_script = self.generate_script_usecase.execute(model_id, design_intent)
        logger.info(f"[ConfirmClarifications] Step 2 スクリプト生成完了")

        # Step 3: CadQueryスクリプトを実行（失敗時はエラー修正ループ）
        logger.info(f"[ConfirmClarifications] Step 3 スクリプト実行を開始")
        cad_model = self.execute_script_usecase.execute(model_id, cad_script)

        for attempt in range(MAX_FIX_ATTEMPTS):
            if cad_model.error_message is None:
                logger.info(f"[ConfirmClarifications] Step 3 スクリプト実行成功")
                break

            logger.warning(
                f"[ConfirmClarifications] 実行失敗 "
                f"(試行 {attempt + 1}/{MAX_FIX_ATTEMPTS}): {cad_model.error_message}"
            )
            logger.info(f"[ConfirmClarifications] エラー修正ループ: スクリプト修正を開始")
            cad_script = self.script_generator.fix_script(
                cad_script, cad_model.error_message
            )
            logger.info(f"[ConfirmClarifications] 修正スクリプトで再実行")
            cad_model = self.execute_script_usecase.execute(model_id, cad_script)
        else:
            if cad_model.error_message is not None:
                logger.error(
                    f"[ConfirmClarifications] 最大リトライ回数({MAX_FIX_ATTEMPTS})"
                    f"を超過。修正失敗"
                )

        return cad_model
