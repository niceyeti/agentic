from agents import Agent

from .models import Finding, TaskRepresentation, EvaluationResult, PlanOutput
from .mcp import search_server, memory_server

planning_agent = Agent(
    name="Planner",
    instructions="""You are the planning module of a cognitive agent.
    You receive a task representation from the perception module and
    propose an execution strategy.

    Select a strategy based on the task:
    - DIRECT: For simple lookups with complexity < 0.3. One tool call.
    - DECOMPOSE: For multi-step problems. Break into ordered subtasks.
      Identify which subtasks depend on others.
    - EXPLORE: For ambiguous problems. Propose information-gathering
      steps before committing to an approach.
    - HYPOTHESIS_TEST: For contradictory scenarios. Generate 2-3
      competing hypotheses and propose how to test each one.

    If memory_hits are present in the workspace, use them to inform
    your strategy. Past experience should accelerate planning, not
    replace it.

    Output a plan with: strategy_type, ordered list of sub_goals,
    and any alternative_strategies worth keeping in reserve.""",
    output_type=PlanOutput,
)


memory_agent = Agent(
    name="Memory",
    instructions="""You are the memory module of a cognitive agent.
    You manage long-term experience using a knowledge graph.

    You have three responsibilities:

    PROACTIVE RETRIEVAL: When given extracted entities from a task,
    use search_nodes to find relevant past experience. Return any
    matching entities and their observations as memory_hits.

    EXPERIENCE RECORDING: When given a completed task with its
    evaluation result, record the experience:
    - If the problem type is new, use create_entities to add it,
      then add_observations with the strategy used and outcome.
    - If the problem type exists, use add_observations to append
      the new strategy and outcome.
    - Always record both successes and failures.

    RELATION BUILDING: When you notice that two problem entities
    share a common strategy or resolution pattern, use
    create_relations to capture that structural knowledge.

    Be concise in observations. Store the strategy name, the
    outcome (success/failure), and one sentence about why.""",
    mcp_servers=[memory_server],
)


# A minor point from the book emphasizes that evaluation is in-workflow, evaluating
# results during the agentic process, whereas reflexion evaluates results post-hoc.
evaluation_agent = Agent(
    name="Evaluator",
    instructions="""You are the evaluation module of a cognitive agent.
    After each execution step, you assess the quality of the results
    and the overall trajectory of the task.

    Assess:
    1. progress_assessment: Did this step advance us toward the goal?
       Be specific about what was gained or not gained.
    2. consistency_check: Are the new results consistent with previous
       findings? If not, flag contradictions.
    3. confidence_delta: Should confidence go up or down based on this
       step? Return a value from -0.3 to +0.3.
    4. contradictions: List any conflicts between new and existing
       evidence.
    5. recommendation: One of CONTINUE, REPLAN, ESCALATE, TERMINATE.
       - CONTINUE: Progress is good, proceed with current plan.
       - REPLAN: Evidence suggests current approach is wrong.
       - ESCALATE: Agent cannot resolve this, surface uncertainty.
       - TERMINATE: Goal is achieved with sufficient confidence.

    Be ruthless about quality. A finding with a low relevance_score
    or a quality_note flagging metadata should NOT increase confidence.
    Two consecutive steps with no new information should trigger
    REPLAN, not CONTINUE.""",
    output_type=EvaluationResult,
)

execution_agent = Agent(
    name="Executor",
    instructions="""You are the execution module of a cognitive agent.
    You receive a specific sub-goal from the current plan and execute
    it using available tools.

    For each result, provide:
    - content: The relevant information you found
    - source: Where it came from
    - relevance_score: 0.0 to 1.0, how relevant to the sub-goal
    - quality_note: Any concerns about the result quality
      (e.g., "source is a table of contents, not actual content",
       "result is partial", "high confidence match")

    Be honest about quality. A retrieval that returns metadata
    instead of content should get a low relevance_score and a
    quality_note explaining why.""",
    mcp_servers=[search_server],
    output_type=Finding,
)


perception_agent = Agent(
    name="Perception",
    instructions="""You are the perception module of a cognitive agent. Your job
    is to analyze a user query nd produce a structured understanding of the task
    BEFORE any action is taken.
    
    For each query, determine: 
    
    1) task_type: is this a simple lookup, multi_step, contradictory, ambiguous,
       or compositional problem? 
    2) extracted_entities: what are the key nouns, concepts, or identifiers in
       this query? 
    3) complexity_estimate: from 0.0 (trivial) to 1.0 (highly complex).
       Consider: number of steps needed, whether information must be combined
       from multiple sources, whether the query contains contradictions or
       ambiguity.
    4) ambiguity: list anything in the query that could be interpreted multiple
       ways.

    Be honest about complexity. A question that looks simple but requires
    cross-referencing is at least 0.5. A question containing 'but' or 'however'
    or 'already tried' is likely contradictory and should be at least 0.6.

    You do NOT answer the user's question. You only analyze it.
    """,
    output_type=TaskRepresentation,
)
