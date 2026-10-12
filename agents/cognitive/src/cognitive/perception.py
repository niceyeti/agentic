from agents import Agent

from .models import TaskRepresentation

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
