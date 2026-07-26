import logging
import time
import uuid

from src.ai.base import (
    AbstractInferenceProvider,
    AbstractPostprocessor,
    AbstractPreprocessor,
)
from src.ai.exceptions import (
    AIException,
    InferenceExecutionError,
    InferenceValidationError,
)
from src.ai.manager import ModelManager
from src.ai.models import InferenceRequest, InferenceResult, PredictionMetadata

logger = logging.getLogger(__name__)


class AIInferenceService(AbstractInferenceProvider):
    """
    Orchestrates the end-to-end AI inference workflow.
    Coordinates preprocessing, model execution, and postprocessing.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        preprocessor: AbstractPreprocessor,
        postprocessor: AbstractPostprocessor,
    ) -> None:
        """
        Initialize the AI Inference Service.

        Args:
            model_manager: Manager for retrieving and caching AI models.
            preprocessor: Component for preparing input data.
            postprocessor: Component for formatting model outputs.
        """
        self._model_manager = model_manager
        self._preprocessor = preprocessor
        self._postprocessor = postprocessor

    async def execute_inference(self, request: InferenceRequest) -> InferenceResult:
        """
        Execute the full inference pipeline.

        Args:
            request: The inference request payload.

        Returns:
            The final standardized inference result.

        Raises:
            ModelNotFoundError: If the requested model is not available.
            InferenceValidationError: If the request is invalid.
            InferenceExecutionError: If any step of the pipeline fails unexpectedly.
        """
        start_time = time.perf_counter()

        try:
            # 1. Validate request
            if "raw_data" not in request.parameters:
                raise InferenceValidationError(
                    "Missing 'raw_data' in request parameters."
                )
            raw_data = request.parameters["raw_data"]

            # 2. Preprocess
            tensor_input = self._preprocessor.preprocess(request, raw_data)

            # 3. Retrieve model
            model = self._model_manager.get_model(request.model_id)

            # 4. Execute inference
            model_output = model.predict(
                preprocessed_data=tensor_input, parameters=request.parameters
            )

            # 5. Postprocess
            postprocessed_data = self._postprocessor.postprocess(request, model_output)

            # 6. Construct InferenceResult
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # The prompt requested "model identifier" and "timestamp if supported"
            # We will populate these inside result_data to ensure extensibility
            postprocessed_data["model_id"] = request.model_id
            postprocessed_data["timestamp"] = time.time()

            metadata = PredictionMetadata(
                confidence_score=None,
                execution_time_ms=duration_ms,
                model_version=model.metadata.version,
            )

            # Use generated UUID for request_id since not in InferenceRequest
            result = InferenceResult(
                request_id=uuid.uuid4(),
                prediction_metadata=metadata,
                result_data=postprocessed_data,
            )

            return result

        except AIException:
            # Known TerraMind AI exceptions should be re-raised transparently
            raise
        except Exception as e:
            # Translate framework/unexpected exceptions into TerraMind AI exceptions
            logger.error(f"Unexpected error during inference orchestration: {e}")
            raise InferenceExecutionError(
                f"Unexpected error during inference orchestration: {e}"
            ) from e
