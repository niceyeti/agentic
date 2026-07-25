# Description: this all in one file is based on Infante's code from ch.11 of AI
# Agents and Applications. I am mixed as to whether to define this all in some
# class, rather than functionally, but it needs encapsulation better than this.

import uuid
import operator
from typing import Annotated, Sequence, TypedDict, List, Dict
from dotenv import load_dotenv
from enum import Enum
from pydantic import BaseModel, Field


from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.managed.is_last_step import RemainingSteps
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent


from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


from agentic.services.weather import WeatherForecastService
from agentic.services.bnb import BnBBookingService
from agentic.stores.travel_info import get_travel_info_retriever

# TODO: refactor this to not pass api keys via env vars.
load_dotenv()


# Note: I like this pattern, as opposed to a class definition. A class
# definition by which to initialize the vector store and then expose a method
# decorate via "@tool" is the intuition, but is wrong because decorator can't be
# applied to a class method. Instead, implement a stateful func like this, which
# also eliminates a needless class definition. But NOTE: this pattern needs to
# be reviewed for thread safety and similar scenarios.
def get_search_travel_info_tool():
    ti_retriever = get_travel_info_retriever()

    @tool(description="Search travel information about destinations in England.")
    def search_travel_info(
        query: str, retriever: VectorStoreRetriever = ti_retriever
    ) -> str:
        """Search embedded WikiVoyage content for information about destinations
        in England."""
        docs = retriever.invoke(query)
        top = docs[:4] if isinstance(docs, list) else docs
        return "\n---\n".join(d.page_content for d in top)

    return search_travel_info


@tool(description="Get the weather forecast, given a town name.")
def weather_forecast(town: str) -> dict:
    """Get a mock weather forecast for a given town. Returns a WeatherForecast
    object with weather and temperature."""
    forecast = WeatherForecastService.get_forecast(town)
    if forecast is None:
        forecast = {"error": f"No weather data available for '{town}'."}

    return forecast


TOOLS = [get_search_travel_info_tool(), weather_forecast]

# FUTURE: use_previous_response_id is for stateful continuation, simply for a
# demo.
llm_model = ChatOpenAI(
    model="gpt-5", use_responses_api=True, use_previous_response_id=True
)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    remaining_steps: RemainingSteps


class AgentType(str, Enum):
    travel_info_agent = "travel_info_agent"
    accommodation_booking_agent = "accommodation_booking_agent"


class AgentTypeOutput(BaseModel):
    agent: AgentType = Field(..., description="Which agent should handle the query?")


llm_router = llm_model.with_structured_output(AgentTypeOutput)


# -----------------------------------------------------------------------------
# Guardrail: pre_model_hook to allow only travel-related questions
# -----------------------------------------------------------------------------
class GuardrailDecision(BaseModel):
    is_travel: bool = Field(
        ...,
        description=("""True if the user question is about travel information: 
            destinations, attractions, lodging (hotels/BnBs), prices,
            availability, or weather in Cornwall/England."""),
    )
    reason: str = Field(..., description="Brief justification for the decision.")


GUARDRAIL_SYSTEM_PROMPT = """You are a strict classifier. Given the user's 
    last message, respond with whether it is travel-related. Travel-related
    queries include destinations, attractions, lodging (hotels/BnBs), room
    availability, prices, or weather in Cornwall/England."""

REFUSAL_INSTRUCTION = """You can only help with travel-related questions 
    (destinations, attractions, lodging, prices, availability, or weather in
    Cornwall/England). The user's request is not travel-related. Politely refuse
    and briefly explain what topics you can help with."""

llm_guardrail = llm_model.with_structured_output(GuardrailDecision)

# The router base prompt ensures it directs to a particular agent in a
# structured way.
ROUTER_SYSTEM_PROMPT = """You are a router. Given the following user message, 
    decide if it is a travel information question (about destinations,
    attractions, or general travel info) or an accommodation booking question
    (about hotels, BnBs, room availability, or prices).\n If it is a travel
    information question, respond with 'travel_info_agent'.\n If it is an
    accommodation booking question, respond with
    'accommodation_booking_agent'."""


def router_agent_node(state: AgentState) -> Command[AgentType]:
    """Router node: decides which agent should handle the user query."""
    messages = state["messages"]
    last_msg = messages[-1] if messages else None
    if isinstance(last_msg, HumanMessage):
        user_input = last_msg.content

        # Guardrail classification at routing time
        classifier_messages = [
            SystemMessage(content=GUARDRAIL_SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]
        decision = llm_guardrail.invoke(classifier_messages)
        if not decision.is_travel:
            # Return refusal directly as an AI message and shortcut to END via a
            # dedicated node
            refusal_text = """Sorry, I can only help with travel-related 
                questions (destinations, attractions, lodging, prices,
                availability, or weather in Cornwall/England). Please rephrase
                your request to be travel-related."""
            return Command(
                update={"messages": [AIMessage(content=refusal_text)]},
                goto="guardrail_refusal",
            )

        router_messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]
        router_response = llm_router.invoke(router_messages)
        agent_name = router_response.agent.value
        return Command(update=state, goto=agent_name)

    return Command(update=state, goto=AgentType.travel_info_agent)


travel_info_agent = create_agent(
    model=llm_model,
    tools=TOOLS,
    state_schema=AgentState,
    prompt="You are a helpful assistant that can search travel information and get the weather forecast. Only use the tools to find the information you need (including town names).",
)

hotel_db = SQLDatabase.from_uri("sqlite:///hotel_db/cornwall_hotels.db")
hotel_db_toolkit = SQLDatabaseToolkit(db=hotel_db, llm=llm_model)
hotel_db_toolkit_tools = hotel_db_toolkit.get_tools()


@tool(
    description="Check BnB room availability and price for a destination in Cornwall."
)
def check_bnb_availability(destination: str, num_rooms: int) -> List[Dict]:
    """Check BnB room availability and price for the requested destination and
    number of rooms."""
    offers = BnBBookingService.get_offers_near_town(destination, num_rooms)
    if not offers:
        return [
            {
                "error": f"No available BnBs found in {destination} for {num_rooms} rooms."
            }
        ]
    return offers


BOOKING_TOOLS = hotel_db_toolkit_tools + [check_bnb_availability]

accommodation_booking_agent = create_agent(
    model=llm_model,
    tools=BOOKING_TOOLS,
    state_schema=AgentState,
    prompt="You are a helpful assistant that can check hotel and BnB room availability and price for a destination in Cornwall. You can use the tools to get the information you need. If the user does not specify the accommodation type, you should check both hotels and BnBs.",
)


# -----------------------------------------------------------------------------
# Guardrail refusal node (no-op, used to shortcut to END)
# -----------------------------------------------------------------------------
def guardrail_refusal_node(state: AgentState):
    return {}


graph = StateGraph(AgentState)
graph.add_node("router_agent", router_agent_node)
graph.add_node("travel_info_agent", travel_info_agent)
graph.add_node("accommodation_booking_agent", accommodation_booking_agent)
graph.add_node("guardrail_refusal", guardrail_refusal_node)

graph.add_edge("travel_info_agent", END)
graph.add_edge("accommodation_booking_agent", END)
graph.add_edge("guardrail_refusal", END)

graph.set_entry_point("router_agent")

checkpointer = InMemorySaver()
travel_assistant = graph.compile(checkpointer=checkpointer)


def chat_loop():
    """chat_loop is the main function of this workflow."""
    thread_id = uuid.uuid1()
    print(f"Thread ID: {thread_id}")
    config = {"configurable": {"thread_id": thread_id}}

    print("UK Travel Assistant (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        state = {"messages": [HumanMessage(content=user_input)]}
        result = travel_assistant.invoke(state, config=config)
        response_msg = result["messages"][-1]
        print(f"Assistant: {response_msg.content}\n")
