from app.domain.entities.cad_model import CADModel
from app.domain.value_objects.clarification import Clarification, ClarificationAnswer
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.usecase.generate_and_execute_script_usecase import GenerateAndExecuteScriptUseCase
from loguru import logger


class ConfirmClarificationsUseCase:
    """
    ユーザーが確認事項に回答したら、それを CADModel に反映してパイプラインを再開する
    （Step 2 & 3 を実行）。
    """

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        generate_and_execute_usecase: GenerateAndExecuteScriptUseCase,
    ):
        self.cad_model_repo = cad_model_repo
        self.generate_and_execute_usecase = generate_and_execute_usecase

    def execute(
        self, model_id: str, responses: dict[str, ClarificationAnswer]
    ) -> CADModel:
        """
        ユーザー回答を CADModel に保存し、Step 2 & 3 を実行する。

        Args:
            model_id: 処理対象の CADModel ID
            responses: {"clarification_1": YesAnswer(),
                        "clarification_2": CustomAnswer(text="C0.5 で良い"), ...}

        Returns:
            生成された CADModel
        """
        logger.info(f"[ConfirmClarifications] ユーザー回答を処理中 (model_id={model_id})")

        cad_model = self.cad_model_repo.get_by_id(model_id)

        updated_clarifications = []
        for clarification in cad_model.clarifications:
            if clarification.id in responses:
                updated_clarifications.append(Clarification(
                    id=clarification.id,
                    question=clarification.question,
                    candidates=clarification.candidates,
                    user_response=responses[clarification.id],
                ))
            else:
                updated_clarifications.append(clarification)

        cad_model.clarifications = updated_clarifications
        cad_model.clarifications_confirmed = True
        self.cad_model_repo.save(cad_model)

        logger.info("[ConfirmClarifications] ユーザー回答を保存完了")

        return self.generate_and_execute_usecase.execute(model_id)
