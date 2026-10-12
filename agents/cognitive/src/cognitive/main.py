import asyncio

from cognitive.cognitive_workflow import run_cognitive_loop


async def main():
    print("=" * 60)
    print("COGNITIVE AGENT ARCHITECTURE")
    print("=" * 60)

    # A query that a flat ReAct agent would get wrong:
    # The user already tried the standard fix, so the standard
    # answer is wrong by definition.
    query = (
        "A user reports that their deployment pipeline fails "
        "intermittently, but only during high-traffic periods. "
        "The standard fix (increasing timeout thresholds) was "
        "already applied and did not resolve the issue."
    )

    print(f"\nQuery: {query}\n")
    response = await run_cognitive_loop(
        query=query,
        max_iterations=10,
        confidence_threshold=0.8,
        max_cognitive_steps=5,
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
