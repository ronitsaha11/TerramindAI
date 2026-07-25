import abc
import logging

from src.analytics.models import AnalysisRequest, AnalysisResult

logger = logging.getLogger(__name__)


class AnalyticsEngine(abc.ABC):
    """
    Abstract orchestrator for the Earth Intelligence Engine.
    Implementations of this engine are responsible for scheduling and executing
    geospatial analytic jobs (like NDVI, NDWI, or custom AI inference).
    """

    @abc.abstractmethod
    async def submit_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Submit a new analysis request to the engine.
        Depending on the implementation, this might process synchronously
        or dispatch to a task queue and return a PENDING status.
        """
        pass

    @abc.abstractmethod
    async def get_analysis_status(self, analysis_id: str) -> AnalysisResult:
        """
        Retrieve the current status and result of a previously submitted analysis.
        """
        pass
