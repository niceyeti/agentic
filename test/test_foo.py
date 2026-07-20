import pytest
from langgraph.checkpoint.memory import MemorySaver

# from agentic.graph import app  # compiled graph

import asyncio

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph


@pytest.mark.asyncio
async def test_any_graph():

    builder = StateGraph(int)
    builder.add_node("add_one", lambda x: x + 1)
    builder.set_entry_point("add_one")
    builder.set_finish_point("add_one")

    memory = InMemorySaver()
    graph = builder.compile(checkpointer=memory)
    coro = graph.ainvoke(1, {"configurable": {"thread_id": "thread-1"}})
    # await asyncio.run(coro)
    assert (
        False
    ), "TODO: add aysnc graph test. Note that asyncio.run() is not allowed here, I'll have to evaluate."


# TODO: this test is a placeholder from an example until reqs are known.
def test_graph_pause_and_resume():
    memory = MemorySaver()
    # graph = app.compile(checkpointer=memory)
    config = {"configurable": {"thread_id": "test_1"}}

    # Run first part of the graph
    initial_state = {"messages": [{"role": "user", "content": "Proceed with purchase"}]}
    # await graph.ainvoke(initial_state, config)

    # # Verify paused state (if you have an interrupt_before node)
    # state = graph.get_state(config)
    # assert state.next == ("human_approval_node",)

    # # Resume graph execution
    # await graph.ainvoke(None, config)
    # final_state = graph.get_state(config)
    # assert final_state.values["status"] == "completed"
    assert False, "TODO: create tests"
