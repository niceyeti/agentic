from agents.agentic.src.agentic.core.multi_agent_travel_workflow import chat_loop

if __name__ == "__main__":
    # FUTURE: in a real/clean application, load config here. This main func was
    # just to get moving. Config could be built and injected from this level,
    # though it could also be handled internally by 'workflows'. This project
    # doesn't have such a production lifecycle, but that's what would be needed
    # to productionize LangGraph, I just don't know those reqs yet.

    chat_loop()
