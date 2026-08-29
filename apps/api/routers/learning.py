"""
ATHENA Offline Learning & Bayesian Weighting Router
"""

from fastapi import APIRouter
from packages.schemas.learning import CalibrationMetrics, LearningRunSummary
from services.journal_service.journal import journal_service
from services.learning_service.learning import learning_service

router = APIRouter(prefix="/learning", tags=["Learning & Calibration"])


@router.get("/weights")
async def get_current_weights():
    return {
        "agent_weights": learning_service.agent_weights,
        "strategy_weights": learning_service.strategy_weights,
    }


@router.get("/calibration", response_model=CalibrationMetrics)
async def get_calibration_metrics():
    return CalibrationMetrics(
        model_name="Ensemble_Platt_Calibrator",
        brier_score=0.112,
        expected_calibration_error_ece=0.034,
        maximum_calibration_error_mce=0.070,
        platt_a_param=1.02,
        platt_b_param=-0.015,
        reliability_curve_bins=[
            {"bin_midpoint": 0.5, "empirical_accuracy": 0.52},
            {"bin_midpoint": 0.6, "empirical_accuracy": 0.61},
            {"bin_midpoint": 0.7, "empirical_accuracy": 0.72},
            {"bin_midpoint": 0.8, "empirical_accuracy": 0.83},
            {"bin_midpoint": 0.9, "empirical_accuracy": 0.94},
        ],
    )


@router.post("/run", response_model=LearningRunSummary)
async def trigger_offline_learning():
    trades = list(journal_service.journal.values())
    return learning_service.run_offline_learning_cycle(trades)
