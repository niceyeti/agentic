from pydantic import BaseModel, Field
from enum import Enum


class TaskType(str, Enum):
    """TaskType is set by the Perception module to inform problem structure."""

    SIMPLE_LOOKUP = "simple_lookup"
    MULTI_STEP = "multi_step"
    CONTRADICTORY = "contradictory"
    AMBIGUOUS = "ambiguous"
    COMPOSITIONAL = "compositional"
    UNKNOWN = "unknown"


class TaskRepresentation(BaseModel):
    """TaskRepresentation encodes the user's query to determine its complexity
    and structure. This is the output of the Perception module."""

    task_type: TaskType
    extracted_entities: list[str] = Field(default_factory=list)
    complexity_estimate: float = 0.0
    ambiguities: list[str] = Field(default_factory=list)


class StrategyType(str, Enum):
    DIRECT = "direct"  # Direct execution for simple queries (System 1)
    DECOMPOSE = "decompose"  # Decompose into subtasks for multi-step problems
    EXPLORE = "explore"  # Explore to gather information before committing
    HYPOTHESIS_TEST = "hypothesis_test"  # Test competing hypotheses


class AttentionSignal(str, Enum):
    NONE = "none"
    LOW_CONFIDENCE = "low_confidence"
    STAGNATION = "stagnation"
    CONTRADICTION = "contradiction"
    KNOWLEDGE_GAP = "knowledge_gap"
    TASK_COMPLETE = "task_complete"


class Finding(BaseModel):
    content: str
    source: str
    relevance_score: float = 0.0
    quality_note: str = ""


class CognitiveWorkspace(BaseModel):
    # Task representation
    raw_query: str = ""
    task_type: TaskType = TaskType.UNKNOWN
    extracted_entities: list[str] = Field(default_factory=list)
    complexity_estimate: float = 0.0  # 0.0 (trivial) to 1.0 (highly complex)
    ambiguities: list[str] = Field(default_factory=list)

    # Active hypotheses
    current_strategy: StrategyType = StrategyType.DIRECT
    sub_goals: list[str] = Field(default_factory=list)
    alternative_strategies: list[str] = Field(default_factory=list)

    # Intermediate results
    findings: list[Finding] = Field(default_factory=list)
    memory_hits: list[str] = Field(default_factory=list)

    # Confidence state
    confidence: float = 0.5  # Starts neutral, moves toward 1.0 or 0.0
    confidence_trend: list[float] = Field(default_factory=list)

    # Execution history
    steps_taken: list[str] = Field(default_factory=list)
    failed_approaches: list[str] = Field(default_factory=list)
    iteration_count: int = 0

    # Attention signals
    active_signal: AttentionSignal = AttentionSignal.NONE
    signal_source: str = ""
