"""
Listing 10.9 - Complete Cognitive Agent with MCP

Assembles all modules (Listings 10.1-10.8) into a complete working system.
Connects the MCP memory server for long-term knowledge and uses Brave Search for
domain tools. Initializes the workspace and runs the cognitive loop on a
concrete query.

Includes metacognitive patterns from Listings 10.10-10.12: - Confidence gating
(prevents presenting uncertain results) - Stagnation detection (catches the
"broken record" failure mode) - Knowledge boundary awareness (knowing what you
don't know)
"""

import json
from agents import Runner

from .models import (
    GateDecision,
    CognitiveWorkspace,
    AttentionSignal,
    KnowledgeBoundary,
    StrategyType,
)

from .cognitive_agents import (
    perception_agent,
    evaluation_agent,
    memory_agent,
    execution_agent,
    planning_agent,
)

from .mcp import memory_server, search_server

# from dotenv import load_dotenv

# load_dotenv()


def check_confidence_gate(workspace: CognitiveWorkspace) -> GateDecision:
    """Confidence-gated execution (Listing 10.10)."""
    if workspace.confidence < 0.3:
        return GateDecision.SIGNAL_UNCERTAINTY

    if workspace.confidence < 0.6:
        if workspace.iteration_count < 3:
            return GateDecision.GATHER_MORE
        return GateDecision.SIGNAL_UNCERTAINTY

    if workspace.active_signal == AttentionSignal.CONTRADICTION:
        return GateDecision.GATHER_MORE

    if len(workspace.confidence_trend) >= 3:
        recent = workspace.confidence_trend[-3:]
        if all(recent[i] > recent[i + 1] for i in range(2)):
            return GateDecision.GATHER_MORE

    return GateDecision.PRESENT


def detect_stagnation(workspace: CognitiveWorkspace) -> bool:
    """Stagnation detection (Listing 10.11)."""
    if len(workspace.findings) < 2:
        return False

    last = workspace.findings[-1].content.lower().split()
    prev = workspace.findings[-2].content.lower().split()
    overlap = len(set(last) & set(prev)) / max(len(set(last)), 1)

    if overlap > 0.7:
        workspace.active_signal = AttentionSignal.STAGNATION
        workspace.signal_source = "content_overlap"
        return True

    if len(workspace.confidence_trend) >= 3:
        recent = workspace.confidence_trend[-3:]
        spread = max(recent) - min(recent)
        if spread < 0.05:
            workspace.active_signal = AttentionSignal.STAGNATION
            workspace.signal_source = "confidence_plateau"
            return True

    return False


def assess_knowledge_boundary(
    workspace: CognitiveWorkspace,
) -> KnowledgeBoundary:
    """Knowledge boundary awareness (Listing 10.12)."""
    signals = []

    if workspace.findings:
        avg_relevance = sum(f.relevance_score for f in workspace.findings) / len(
            workspace.findings
        )
        signals.append(avg_relevance)
    else:
        signals.append(0.0)

    if workspace.memory_hits:
        signals.append(0.8)
    else:
        signals.append(0.2)

    signals.append(workspace.confidence)

    avg_signal = sum(signals) / len(signals)

    if avg_signal > 0.6:
        return KnowledgeBoundary.WITHIN
    elif avg_signal > 0.3:
        return KnowledgeBoundary.EDGE
    else:
        workspace.active_signal = AttentionSignal.LOW_CONFIDENCE
        return KnowledgeBoundary.OUTSIDE


# ============================================================ ATTENTION MODULE
# (Listing 10.6)
# ============================================================


def route_attention(workspace: CognitiveWorkspace) -> str:
    """Read workspace signals and determine next module."""

    # System 1 fast path
    if (
        workspace.complexity_estimate < 0.3
        and workspace.memory_hits
        and workspace.active_signal == AttentionSignal.NONE
    ):
        return "FAST_RESPOND"

    # Signal-driven routing
    if workspace.active_signal == AttentionSignal.TASK_COMPLETE:
        return "RESPOND"

    if workspace.active_signal == AttentionSignal.STAGNATION:
        workspace.failed_approaches.append(workspace.current_strategy.value)
        return "META_PLAN"

    if workspace.active_signal == AttentionSignal.CONTRADICTION:
        workspace.current_strategy = StrategyType.HYPOTHESIS_TEST
        return "PLAN"

    if workspace.active_signal == AttentionSignal.LOW_CONFIDENCE:
        if workspace.confidence < 0.2:
            return "ESCALATE"
        return "PLAN"

    if workspace.active_signal == AttentionSignal.KNOWLEDGE_GAP:
        return "MEMORY"

    # Default cognitive cycle
    if not workspace.extracted_entities:
        return "PERCEIVE"
    if not workspace.sub_goals:
        return "PLAN"
    if (
        workspace.iteration_count == 0
        or workspace.active_signal == AttentionSignal.NONE
    ):
        return "EXECUTE"

    return "EVALUATE"


# ============================================================ WORKSPACE UPDATE
# HELPERS
# ============================================================


def update_workspace_perception(workspace, result):
    output = result.final_output
    workspace.task_type = output.task_type
    workspace.extracted_entities = output.extracted_entities
    workspace.complexity_estimate = output.complexity_estimate
    workspace.ambiguities = output.ambiguities
    workspace.steps_taken.append("PERCEIVE")
    print(
        f"  [Perception] Type={output.task_type.value}, "
        f"Complexity={output.complexity_estimate:.2f}, "
        f"Entities={output.extracted_entities}"
    )


def update_workspace_memory(workspace, result):
    output = result.final_output
    if isinstance(output, str) and output.strip():
        workspace.memory_hits.append(output)
    workspace.steps_taken.append("MEMORY")
    print(f"  [Memory] Hits={len(workspace.memory_hits)}")


def update_workspace_plan(workspace, result):
    output = result.final_output
    workspace.current_strategy = output.strategy_type
    workspace.sub_goals = output.sub_goals
    workspace.alternative_strategies = output.alternative_strategies
    workspace.steps_taken.append("PLAN")
    print(
        f"  [Planning] Strategy={output.strategy_type.value}, "
        f"Sub-goals={len(output.sub_goals)}"
    )
    for i, goal in enumerate(output.sub_goals, 1):
        print(f"    {i}. {goal}")


def update_workspace_execution(workspace, result):
    output = result.final_output
    workspace.findings.append(output)
    if workspace.sub_goals:
        completed_goal = workspace.sub_goals.pop(0)
        print(f"  [Execution] Completed: {completed_goal}")
    print(
        f"  [Execution] Found: {output.content[:100]}... "
        f"(relevance={output.relevance_score:.2f})"
    )

    # Run stagnation detection after each execution
    detect_stagnation(workspace)


def update_workspace_evaluation(workspace, result):
    output = result.final_output
    workspace.confidence = max(
        0.0, min(1.0, workspace.confidence + output.confidence_delta)
    )
    workspace.confidence_trend.append(workspace.confidence)

    if output.contradictions:
        for c in output.contradictions:
            print(f"  [Evaluation] Contradiction: {c}")

    if not output.consistency_check:
        workspace.active_signal = AttentionSignal.CONTRADICTION
        workspace.signal_source = "evaluation"

    if output.recommendation == "REPLAN":
        workspace.active_signal = AttentionSignal.STAGNATION
        workspace.signal_source = "evaluation"
    elif output.recommendation == "ESCALATE":
        workspace.active_signal = AttentionSignal.LOW_CONFIDENCE
        workspace.signal_source = "evaluation"
    elif output.recommendation == "TERMINATE":
        workspace.active_signal = AttentionSignal.TASK_COMPLETE
        workspace.signal_source = "evaluation"

    workspace.steps_taken.append("EVALUATE")
    print(
        f"  [Evaluation] Confidence={workspace.confidence:.2f}, "
        f"Recommendation={output.recommendation}, "
        f"Progress: {output.progress_assessment[:80]}"
    )

    # Assess knowledge boundary after evaluation
    boundary = assess_knowledge_boundary(workspace)
    if boundary != KnowledgeBoundary.WITHIN:
        print(f"  [Boundary] Operating at: {boundary.value}")


# ============================================================ FORMAT HELPERS
# ============================================================


def format_memory_query(workspace: CognitiveWorkspace) -> str:
    return (
        f"Search for past experience related to these entities: "
        f"{workspace.extracted_entities}. "
        f"Task type: {workspace.task_type.value}. "
        f"Query: {workspace.raw_query}"
    )


def format_planning_input(workspace: CognitiveWorkspace) -> str:
    return json.dumps(
        {
            "task_type": workspace.task_type.value,
            "entities": workspace.extracted_entities,
            "complexity": workspace.complexity_estimate,
            "ambiguities": workspace.ambiguities,
            "memory_hits": workspace.memory_hits,
            "failed_approaches": workspace.failed_approaches,
        }
    )


def format_execution_input(workspace: CognitiveWorkspace) -> str:
    current_goal = (
        workspace.sub_goals[0] if workspace.sub_goals else workspace.raw_query
    )
    return json.dumps(
        {
            "sub_goal": current_goal,
            "context": {
                "task": workspace.raw_query,
                "strategy": workspace.current_strategy.value,
                "prior_findings": [f.content[:100] for f in workspace.findings[-3:]],
            },
        }
    )


def format_evaluation_input(workspace: CognitiveWorkspace) -> str:
    return json.dumps(
        {
            "task": workspace.raw_query,
            "current_strategy": workspace.current_strategy.value,
            "latest_finding": (
                workspace.findings[-1].model_dump() if workspace.findings else None
            ),
            "all_findings_count": len(workspace.findings),
            "confidence": workspace.confidence,
            "confidence_trend": workspace.confidence_trend[-5:],
            "steps_taken": workspace.steps_taken[-5:],
            "remaining_sub_goals": workspace.sub_goals,
        }
    )


# ============================================================ RESPONSE BUILDERS
# ============================================================


def build_response(workspace: CognitiveWorkspace) -> str:
    findings_text = "\n".join(
        f"  - {f.content[:200]} (source: {f.source}, "
        f"relevance: {f.relevance_score:.2f})"
        for f in workspace.findings
    )

    gate = check_confidence_gate(workspace)
    boundary = assess_knowledge_boundary(workspace)

    return (
        f"\n{'='*60}\n"
        f"COGNITIVE AGENT RESPONSE\n"
        f"{'='*60}\n"
        f"Query: {workspace.raw_query}\n\n"
        f"Strategy Used: {workspace.current_strategy.value}\n"
        f"Task Type: {workspace.task_type.value}\n"
        f"Final Confidence: {workspace.confidence:.2f}\n"
        f"Confidence Gate: {gate.value}\n"
        f"Knowledge Boundary: {boundary.value}\n"
        f"Total Steps: {len(workspace.steps_taken)}\n"
        f"Iterations: {workspace.iteration_count + 1}\n\n"
        f"Findings:\n{findings_text}\n\n"
        f"Failed Approaches: {workspace.failed_approaches or 'None'}\n"
        f"Confidence Trend: {[f'{c:.2f}' for c in workspace.confidence_trend]}\n"
    )


def build_uncertain_response(workspace: CognitiveWorkspace) -> str:
    return (
        f"\n{'='*60}\n"
        f"COGNITIVE AGENT RESPONSE (LOW CONFIDENCE)\n"
        f"{'='*60}\n"
        f"Query: {workspace.raw_query}\n\n"
        f"WARNING: The agent could not resolve this with sufficient "
        f"certainty (confidence={workspace.confidence:.2f}).\n\n"
        f"Partial findings:\n"
        + "\n".join(f"  - {f.content[:200]}" for f in workspace.findings)
        + f"\n\nFailed approaches: {workspace.failed_approaches}\n"
        f"Steps taken: {workspace.steps_taken}\n\n"
        f"Recommendation: This query may require human expertise "
        f"or additional data sources.\n"
    )


# ============================================================ EXPERIENCE
# RECORDING
# ============================================================


async def record_experience(workspace: CognitiveWorkspace):
    """Record the task outcome in the memory knowledge graph."""
    summary = (
        f"Record this completed task in the knowledge graph:\n"
        f"Task: {workspace.raw_query}\n"
        f"Type: {workspace.task_type.value}\n"
        f"Strategy used: {workspace.current_strategy.value}\n"
        f"Final confidence: {workspace.confidence:.2f}\n"
        f"Steps taken: {len(workspace.steps_taken)}\n"
        f"Failed approaches: {workspace.failed_approaches}\n"
        f"Key entities: {workspace.extracted_entities}"
    )
    try:
        await Runner.run(memory_agent, input=summary)
        print(
            f"  [Memory] Experience recorded: "
            f"{workspace.task_type.value} -> "
            f"{workspace.current_strategy.value} "
            f"(confidence={workspace.confidence:.2f})"
        )
    except Exception as e:
        print(f"  [Memory] Failed to record experience: {e}")


# ============================================================ THE COGNITIVE
# LOOP (Listing 10.8)
# ============================================================


async def run_cognitive_loop(
    query: str,
    max_iterations: int = 10,
    confidence_threshold: float = 0.8,
    max_cognitive_steps: int = 5,
):
    """Run the full cognitive agent loop on a query.

    The outer loop (agentic loop from Chapter 9) handles iteration and
    convergence. The inner loop (cognitive cycle) handles attention routing and
    module execution within each iteration.
    """
    workspace = CognitiveWorkspace(raw_query=query)

    async with memory_server, search_server:
        for i in range(max_iterations):
            workspace.iteration_count = i
            print(f"\n{'─'*40}")
            print(f"Iteration {i + 1} / {max_iterations}")
            print(f"{'─'*40}")

            # Inner cognitive cycle
            for step in range(max_cognitive_steps):
                next_module = route_attention(workspace)
                print(f"\n  [{step + 1}] Routing -> {next_module}")

                if next_module == "FAST_RESPOND":
                    print("  [Fast Path] Responding from memory")
                    return build_response(workspace)

                if next_module == "RESPOND":
                    # Apply confidence gate before presenting
                    gate = check_confidence_gate(workspace)
                    if gate == GateDecision.SIGNAL_UNCERTAINTY:
                        return build_uncertain_response(workspace)
                    return build_response(workspace)

                if next_module == "ESCALATE":
                    return build_uncertain_response(workspace)

                if next_module == "PERCEIVE":
                    result = await Runner.run(
                        perception_agent, input=workspace.raw_query
                    )
                    update_workspace_perception(workspace, result)

                elif next_module == "MEMORY":
                    result = await Runner.run(
                        memory_agent, input=format_memory_query(workspace)
                    )
                    update_workspace_memory(workspace, result)

                elif next_module in ("PLAN", "META_PLAN"):
                    if next_module == "META_PLAN":
                        print(
                            "  [Meta-Plan] Previous strategy failed, "
                            "trying alternative"
                        )
                    result = await Runner.run(
                        planning_agent, input=format_planning_input(workspace)
                    )
                    update_workspace_plan(workspace, result)

                elif next_module == "EXECUTE":
                    result = await Runner.run(
                        execution_agent, input=format_execution_input(workspace)
                    )
                    update_workspace_execution(workspace, result)

                elif next_module == "EVALUATE":
                    result = await Runner.run(
                        evaluation_agent, input=format_evaluation_input(workspace)
                    )
                    update_workspace_evaluation(workspace, result)

                    if workspace.active_signal == AttentionSignal.TASK_COMPLETE:
                        break

                # Reset signal after processing to prevent loops
                if workspace.active_signal not in (
                    AttentionSignal.STAGNATION,
                    AttentionSignal.CONTRADICTION,
                    AttentionSignal.LOW_CONFIDENCE,
                ):
                    workspace.active_signal = AttentionSignal.NONE

            # Check convergence at the agentic loop level
            if workspace.confidence >= confidence_threshold:
                print(f"\nConverged at confidence " f"{workspace.confidence:.2f}")
                break

        # Record experience in memory after completion
        await record_experience(workspace)

        # Final confidence gate check
        gate = check_confidence_gate(workspace)
        if gate == GateDecision.SIGNAL_UNCERTAINTY:
            return build_uncertain_response(workspace)
        return build_response(workspace)
