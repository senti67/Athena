"""Athena Agent Service Package"""

from .base import BaseAgent
from .llm_gateway import LLMGateway, llm_gateway
from .orchestrator import AgentOrchestrator, agent_orchestrator
from .agents import (
    TechnicalAgent,
    QuantAgent,
    FundamentalAgent,
    SentimentNewsAgent,
    MacroAgent,
    MicrostructureAgent,
    # Legacy aliases
    SentimentAgent,
    ResearchAgent,
    OptionsAgent,
    CrossAssetAgent,
    PatternDiscoveryAgent,
    SimulationAgent,
    ComplianceAgent,
    CostAnalysisAgent,
    DataQualityAgent,
)
from .analyzers import (
    CrossAssetAnalyzer,
    OptionsAnalyzer,
    PatternAnalyzer,
    RiskSimulation,
)

DataQualityAgentWrapper = TechnicalAgent

__all__ = [
    "BaseAgent",
    "LLMGateway",
    "llm_gateway",
    "AgentOrchestrator",
    "agent_orchestrator",
    "TechnicalAgent",
    "QuantAgent",
    "FundamentalAgent",
    "SentimentNewsAgent",
    "MacroAgent",
    "MicrostructureAgent",
    "SentimentAgent",
    "ResearchAgent",
    "OptionsAgent",
    "CrossAssetAgent",
    "PatternDiscoveryAgent",
    "SimulationAgent",
    "DataQualityAgent",
    "DataQualityAgentWrapper",
    "ComplianceAgent",
    "CostAnalysisAgent",
    "CrossAssetAnalyzer",
    "OptionsAnalyzer",
    "PatternAnalyzer",
    "RiskSimulation",
]
