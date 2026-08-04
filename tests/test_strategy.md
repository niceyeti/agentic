## Notes

See Lanham's book. I have a lot of questions about what needs to be tested in a
LangGraph app, especially since llm apps seem more and more like nano-services.

Lanham's book provides a good layering structure for LLM apps, proceeding from
the innermost layer to outermost. The testing strategy would map to each of
these layers, with whatever adjustments are needed:

1) persona: system/other prompts. Background and role, contextual attributes
   such as experience level, explicit operating constraints, etc.
2) tools and actions: 
3) reasoning and planning: reasoning/planning can be model-native (which may
   differ from one run to the next) or structured via patterns such as ReAct,
   Reflexion, chain-of-thought, etc.
4) knowledge and memory: state restoration. Lanham's sequential-thinking MCP
server provides a robust example of knowledge implementation.
    * knowledge: static, external information an agent draws on to do its work
      (documents, manuals, etc). Often lives in vector stores.
    * memory: dynamic, experiential information the agent builds through
      interaction. Past sessions, recorded observations, etc.
    * Both knowledge and memory are surfaced to the agent through RAG.
5) evaluation and feedback

The 

