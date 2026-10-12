import os
import pytest

from agents import Runner, set_default_openai_client
from openai import AsyncOpenAI

from cognitive.agents import evaluation_agent
from cognitive.util.util import load_from_cred_dict
from cognitive.models import CognitiveWorkspace


# This is merely a manual test, requiring user input.
@pytest.mark.skipif(
    "EVALUATION" not in os.environ,
    reason="Skipping evaluation agent test. Set EVALUATION environment var to run.",
)
def test_perception_agent():

    print("""
This main driver is purely for testing the evaluation module in isolation,
per the book's exercises:

'Feed the evaluation module three workspace states: one with high-quality
findings, one with contradictory findings, and one with low-confidence
results. Verify that the module returns CONTINUE, REPLACE, and ESCALATE
respectively.'

""")

    api_cred = load_from_cred_dict(".cred", key="openai")
    custom_client = AsyncOpenAI(api_key=api_cred.get_secret_value())
    set_default_openai_client(custom_client)

    high_quality_state = CognitiveWorkspace()

    while True:
        query = input("Query (or ctrl+c to quit): ")
        result = Runner.run_sync(input=query, starting_agent=evaluation_agent)
        print(result)
