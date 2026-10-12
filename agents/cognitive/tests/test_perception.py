import os

import pytest

from agents import Runner, set_default_openai_client
from openai import AsyncOpenAI

from cognitive.agents import perception_agent
from cognitive.util.util import load_from_cred_dict


# This is merely a manual test, requiring user input.
@pytest.mark.skipif(
    "PERCEPTION" not in os.environ,
    reason="Skipping perception test. Set PERCEPTION environment var to run.",
)
def test_perception_agent():

    print("""
This main driver is purely for testing the perception module in isolation,
for my own learning and practice.

Enter a user query for which the perception module should output a structured
percept-representation of the problem.

Examples:

  1) straightforward: what is the weather forecast tomorrow for Pullman, Washington?
  2) complex: I have inherited $100,000 and need to know how invest the money on a three year horizon.
""")

    api_cred = load_from_cred_dict(".cred", key="openai")
    custom_client = AsyncOpenAI(api_key=api_cred.get_secret_value())
    set_default_openai_client(custom_client)

    while True:
        query = input("Query (or ctrl+c to quit): ")
        result = Runner.run_sync(input=query, starting_agent=perception_agent)
        print(result)
