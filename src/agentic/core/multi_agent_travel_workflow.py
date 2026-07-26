# Description: this all in one file is based on Infante's code from ch.11 of AI
# Agents and Applications. I am mixed as to whether to define this all in some
# class, rather than functionally, but it needs encapsulation better than this.

import os
import uuid
from typing import List, Dict
from enum import Enum
from pydantic import BaseModel, Field


from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from langchain.agents.middleware import AgentState

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langgraph.errors import GraphRecursionError

from agentic.services.weather import WeatherForecastService
from agentic.services.bnb import BnBBookingService
from agentic.stores.travel_info import get_travel_info_retriever
from agentic.util.util import load_cred


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
        query: str,
    ) -> str:
        """Search embedded WikiVoyage content for information about destinations
        in England."""
        docs = ti_retriever.invoke(query)
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
    model="gpt-5",
    use_responses_api=True,
    use_previous_response_id=True,
    api_key=load_cred("openai"),
)


# Inheriting from AgentState is best practice because it implements messages and
# remaining_steps by default. A previous version of this was implemented as a
# TypedDict with a RemainingSteps field that caused errors: "ValueError: Invalid
# managed channels detected in InputSchema: remaining_steps. Managed channels
# are not permitted in Input/Output schema." Instead, simply inherit and rely on
# the langgraph builtin schema without customization or weirdness.
class TravelAgentState(AgentState):
    foo: str


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


def router_agent_node(state: TravelAgentState) -> Command[AgentType]:
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


# Note: langgraph docs use `builder = StateGraph(State)`, where State implements a remaining_steps RemainingSteps field.
# The create_agent method
travel_info_agent = create_agent(
    model=llm_model,
    tools=TOOLS,
    state_schema=TravelAgentState,
    system_prompt="You are a helpful assistant that can search travel information and get the weather forecast. Only use the tools to find the information you need (including town names).",
)


hotel_db = SQLDatabase.from_uri(os.environ["SQLITE_URI"])
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
    state_schema=TravelAgentState,
    system_prompt="You are a helpful assistant that can check hotel and BnB room availability and price for a destination in Cornwall. You can use the tools to get the information you need. If the user does not specify the accommodation type, you should check both hotels and BnBs.",
)


# -----------------------------------------------------------------------------
# Guardrail refusal node (no-op, used to shortcut to END)
# -----------------------------------------------------------------------------
def guardrail_refusal_node(state: TravelAgentState):
    return {}


graph = StateGraph(TravelAgentState)
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
    """chat_loop is the main function of this workflow.

    Example successful output:

    Thread ID: 5e55a480-8946-11f1-a60e-860d39ecea7c
    UK Travel Assistant (type 'exit' to quit)
    You: Find me a location in cornwall with nice weather.
    Assistant: [{'id': 'rs_09eab53f9a3a96a9006a6692ab7b40819bb398b6f88f212ea7', 'summary': [], 'type': 'reasoning', 'content': [], 'encrypted_content':'gAAAAABqZpK04jRbKOQ4AGb-hlJnbZ4jhEE9pbD2MWfwW4G3LqqMPdZJmM1Ch0ehZh6PUHhWPTTv2PwwsX-SWJRD1MVaqgctNWI5CSl8T2FS_UwJjL1ICYdtGIAVIsVF_lrjSxil2b4pf-i4JeIIw7aGs87iNSmgL-VYIOqXrBH4l_Jzt7OJr6fQ8-D4Vl9muJ4xUOL7K_J_8WASlspLqxly2fesU056uU55C07Hg9m-a2UpzVcexrJkczUuj-yXrrQOOM_uAYrJzJ-x2263Ypmu2PgIFQIUm5CC5nqzEYSAsbpmouExr-G_vgt0RRy7QwaFTRHlD--buhsfxy0XIh2yCo9hUy-_d6c-nSMAVjWYFY6dVAIts0SCptL0_4HlandxgbTMQA1g08FhxAS1_cBS4ohT2ioJZoA3ZwrtaGl_PTGj305xw6O9hom9XmGigtL7YuXPULqFprQDmMaw4DAMCMKmOqUuiWBxUlbbaO7uk8nxtsoYb6AdxYCZb--eDh63WncrtwkLkzkhNhsrmrpqq-4_zSq46rWoCnKGnwhxNNXwIikAKyZB08_wt0kreLEsmcPYErXTpdcztbHwyG2KfJNExjqS9yJHbwNjzsbUV1HmchSRQ-O9pBFRQxwnIUBBUDA8_FRf_SZqz1qAVxekNOe7zRmPu6Apy7RSrPoSihCpzxWGHPDMBOlKaYO9nyzcnPUaerNlGdWJzKCCkSBJWMkRuq9T8he57quoDr-vt-8Uuz6TnkaCE3Ya5TezLV3Y-NZsCY-p4pd9UOSFjDVDcPd0n07J6gQELwjJacGVRDPO0XYZjuQ0U0078W56cQIn7BdxxkRgCeQhwRMP1Qjnbk2jag_JbYB65GUfzlGzf89zeakuXVZbJpUI1G_DY-YcExp2DTEb1n88KyWqfQirG4zFLS8IhtYtzBZ176mEu5VFb1rKZVoVBJzLVhyig9R2QRcFgSLWRCuCzpmwoKwH5gCZnpqp7KiNSubexNC55BFMKGipuwuaegdRItpbcKMtHjv5y_o6PY72xcU5JqHvKQ7DrjrCeaq1Rj-5mrnUpldnjhUBHF4XJ2557xPXsHMX028Vgdve0tQH8oE4tI89KRSYlCUZJm0SisEBPlHiwQ6FZ5z_XpIt5PnRx-VEbqlQguTsroEI31yE1cmriOMOGuiO_6GrRpm8ws34A7QJftPHdwqbVjiLcl9ITVnGwX51EriZsZIEcqLGAJT4yTZ13IFvZFRGzWziSrlGD7DPbiE3M8pU7-RCFcGKCLxkXjqYwdbeg88baM919hO06gyqtQAl9oM636Ig-W-wVaKrdOY3qDAxYJ1hnfMTrIQi7X0Jhd0BzuN8Vn1VcHFNMvB-SyPtKSp1lKZ7y7cNM03elbbS9CND4kSQMrz3V6rFzU7cs2yNnU_-WLjPWYS9aBbaOhbcCXt7srdLPDQ43x8JniBgWVvjy6PNOa4NYFP4_EdOhFBKg4UOpHB_xrVfa4GWyY6guUhJyo_Ft6YF_2-OnsO9YC3ymEhChXiYCsXdwSmJPgvVx8evjNzwGxAC89lJAc9ay7ui3pjTcBdfN5wdJK7D5oASh1XRpIyqDgEatEe1fp07YiLeFPFuz2hxl6RzsuIPROU_GtmbnmZcdGN7DnzLvMnaRO4eWl-TscU77n3OfZpSmSUgw2AMzfu6k1IxqOAnaQ-IL4Y3MYwj79AFgRBxSxSJh8Er6ep1hQMtdo5M88srUdy_tDlKO_2kfgLZQTrxf1llUMJhBNOUEk5h8GLLIg9MRz32Kb9GGcRIK7FrZd2QvYn29LtQbX1Oxfomo3VG__AdZ9TsQsvyYK0VpVo2Hc9KrVCt-0_dCfhThX_r5jQjPT4qMFgUGP-PXXkx8OIr9BF6HjAL-Nc9zFPyqy5yw6Kbe8I-AwYCbuRhWBLWdtejTgVOxLJTLbRWiKutX0ZPEdwSqCD8VnndJqD7XU6tuJsqlt6t8xmWnlR9TnqayepX_A5yzUYU2XVyHo12c_2QkC6yQKg50W5URqz203Xth6EFWUkYRsFpvWVqjk8JTImi8Zdj3Kauez5yrWSOlqPRiGbYR0sH8OrJIMkX4SiU1jyOGO54zjjK7wv029zNO4IUOUfNBVD7g7zezvDO0fPoTuumXETUAuHGg_0zrc4T4Dy_Cm89VPE7Wej2rXxUsrDe3BGLJmveP3MacY7-FItEB8wKEtl2iJIKQcUxbdNI-oy0DgoSv-jGNlPG3nZ8nvymAwykD3SYrVr1TfPI-0mhhbSzoLcalIOaVHM-sWBOCsPKz3bL70zks-Wu1lcJAdw8jAFkrs8XT797BV2Rp4pJQY-54TNTduk9EsS4sHik105N2wmX6RkzdyQCBwzUzYPCcvUtih2w3yzfzw7EDU8HHhqgRC9w1EEZ5irRoESAw6Ip1XPNQmmOcFZxleTAZwwPagLUrKlA7T6SiI4JcFjmYNYBvBSE6zB3sbsvyYu-yLr_QTUEjSrhxb8NLsQDpsxBEmGoVzUM26PXKi05cRX8XGatonjyRyFhh7TtnCi3R9PlU016GyeKW9LrWunQn2pVuzNFxAibFnuyfXtkuShIzQIizxRvL_dlfkvQE0cdgWz7W9owOqXUDNSn8-6cSUb11dSt7yTwINHcJk2ohhyr4SH1p3qvL-KCDxAIbUIqlbSbN6G5gh5C0dA751dayjgOQwqZK33bMjekiRinUzLhBXjX2foqWP7gGlEyPQifV824xrHrNlIryLi4L3foYOWDOfMGexTqQ0Eqqnfe_VnxYZ4VzBbdOi1SeP0YDIWPYEfAjuThKHDQREvPxTORz_dEORu0Q8BwGMfQXMcq5HQhI_-I7B2h5s6QvdEvWYr8iraUXU20qJ9S_lBSVxBgtlf5jMUX1-1iShwFMKeDTU1GTAjvY2mUqWD3wEMvbQ7wUsQkFw1KzxWcrestt17BT5RGAKrJcXLJl7fQn7iPZCqE0alA5-WtX1QTP6DWB0-Ob5D9xY0wrTQdmbS2TuyVCX6PZMMadzRFGChGNhZgI5J1Q5aJTTGgg2ae_uhOJKMYyIw0q7x3X04Y4hc7S6JYwsynOt1NsV4gIhR9UbPQ56vZNxykkDl6rasFuYUAUtIwkIzdY13snBT-GMk70rQMG08kCiVLg43V664OLvpt9K1lrU1Z6lkXVJPflOALH-74aQ5Abdn9MXbQbSgeo9uLIqNlV_JoayLdkRx3_vxC0V_GDmg1WtaVAk1FXTjXp1reNqSK8_kH4KFUWXMoqcnhuTfR-AvT6zVDxI1YO_ZOauID4lxFhsP5oq3E9ZYnNNKYTe2IrpJRqhTRsEmZHi29CddylnahJSzmFe1nbvAfufhix6XKvqv8gJ9FvdzQm1ULjJB-Ky_lGzVINCOzYj2TZ5fAZIwVz9L3ep-E8pX8p77ZWCA8ZI0TkDej2zayrx7Y6I_UKSMW5qPOAxuOw_gpWg440qlOrLwLfvxFYmcFUFA4H805FLA4snhxfM4JxMTR531vBmRQ74Sk97cNzbWXFHqjMF3CY3wOmkedeIaMBd8ZG0BsIwphvbPjzn16K_eyj0fG4HwGWSnZ-WcEb7R8gnVFNJSLct1H-wR7FkzWmEz-T0LiA_9FnPA7IGNvTWln9BAEV_f7KUFJvwsSZZH3TyOEn4YFGPCKKimC7EVwxP_-z7hwWTWyBdof5UkNBputmS7XDa2a8EsCDV4mJRYFNzQ854ccsYjQcfFaofzK-2VKnCpJptlNKHyIKMgjG6WoClgfgorzPAc0gX2Tvwwe4e55PS2J-KdWU7WOfEyD8092xio0tzYI2gvCTy5RC6-qhRXPkIyclKz2rFhcfsKYf9RBUNHTIA8oyhIpEf1-3PDTVtK3gMQAj-RJFAb0bOH8bDpNIt5krV929H82TaPzfONnB6bKy-jqrhsHivqIeaMvJmGgPIFzbDA6xIMHgds4q-IRy5oEK83jzJjts9aVWQDRRErH_mZBCb6fDuLmPS2BHXcorEXrhlUDHHsgdKIISak3DlJDyj1EgtZS0BeMHJ6XOgorxE2p-5TZ1CNcWpxKMLK8ojoco3FCcOjrmBqOxRkr0S8xn3TSw_k5Wdm6FQJwmANepIU_W7G8-s4159KXnrzUJWUvhgAlv2lXIx5AaKVCculT8YEB1e1P8KgUcCPE5-8aVQm8dgkH7kgYq_GB1xUlS0YznoJqeRfzJWkAppC-deGsIypqHSQnPM4raRCNFIiGHMPg_B2PEwaiYtp1MlbwtOifz10vJ6ur_fQto6buSnaV3jAYZOdnvPXh_lwx35FUvD2SNECP2Qx8N6jk9yCyy19xALSfu_CMskqWsEEXfAD8jkjL2y_MZAC7yQQ3cwShbavWFUAxms_Co1GhIsE0BrsRp6JDqKOE7acSFsqY3tjLA6qdHan_-0CmPcmlvZrCMPCzEkoy_qFPBnCmjg_dRrKej7V8e_jATIcm6A88jFWVUZxvaXaBbNguW9VI6eGnz5SW923oOfhaNR3nw5taG6R0qZaflAsRtBl4pcbVVXrWERQlHPdQ3TIP604HSXtexdLF73vNX_CJ48tCq4pxYberXFlllQY6nYCZeXORCa4FSQ_xxI4Gy35tHbfLyBjTAg_KSz6TaY-oFw_8pdLXe6pCnDF7WTNvwI52IDnez61hYM5TWFkGfySDBcopCYxHNOQ9bIxiRu2wkxlo-2cpbMAM_niSeNOF3EUc5-uN0qrtYb3Oha-J9haJjNGviLndX2UzP6N3lSgeq7YllQN8BV0Amp7u39Kn8fMvezpauHEofntK5iHs4KtAtvZcOU8DYgzNgk8QVwB-Q0mDkELaqQaD3tkoadU6IA_UnA2qQaUVJopA9zVQESvIwe33pFIiYvDRJk_n2f_ve5oVn-RzOoAnQYdc8FpU2n7FekKDgtSG_HkaM5-1GvP6dO3w6huF_Q3NB0_OMw_UGlXlOeSAH3J1zmcjX0rZu8bf9r9bhoPeWogmc6l_d3uNsr_c5Q1Yu5wC7wyK7wX3xubAKP964RVCSUGlDk1zRRIe2b0oDLRKJAaAmrQ-1YqOOn9U3deG9wVdp0Ek0ZO4Lr1JAbxCdnHTzJ9p-E2gUKp7qHjJBPx8lJKJ4QXuQE01Q2A3NS-VnUdYUZr2Mx2vteBu2ryKxr4yneprBGZ84lRAynuTIhSS_o67jXCKFRs9ljVqNKhZbUR_NX3WxdWjDatADItDpahqqCVmN1x3XME13ms0GpVupi44RTWU3Kp3VTiTrDwXDt-gs-yQJje2JmbHnO8gGjP-iROPdo_3QjkK20irjkxKXqwpr0AqV9RQfRqFjzu-vVNGPcjhK9s3YFEkOZ0iG7UkPCe3h6DDF-eIftlzTjZ7DSTOpLexGbdPF9xVmPQwZ2N9195y_lwgc9tOIffWc-Mgj0TNtyawmJZr2S2gI6KvnnQ3Vt5QnMqTHqBxAZ3Itgnk8Oq5eqPCR2i5GsKVHkvf5w_51XTDnc7HImF7HxabEL1mZtIfXSRof_7uP_xf_HXqEI3mFdt4G_PtMNE3JKNkwm_xrQke51J-6eSAPeB9HLxB1cJHHFaeMzRdov9eSidokcbunz-qGexfkYcC31vh3OL8YBoUOCiZsY59hfj_gJW3FK9Y1V_nMrPerT8sLf4rrN1rnZmR0BJHkllut3nZ5ZFTi8dBowOuT4_UStdnF-Wddj-OLoW9v6scVcJI8coRA1F9AqtGHb1JdVx-MR1y7M6BOf4MusYrekgUqY0WKaxrUVa6p4CTnn5sjVp3nUb-uFWVnrez2p8uhuxKKQf0dOuMhQgq_R0STj1_l082O-sWEEZq89O4nwVyEAP-K3EAhrdCACa_EryCqtTFqE_WkKQXj1NBSsSpKOieshW3D8vyXn_wJ2eTa6zvo_jMgkmN6-DPUDrhqsNPT_nWk44P_tbx5H-M-eB3u4MHxkP5LFZfsySartZQxmVwDhloBANJa1XO-pP81EvnzgT44_h9XZzLiu2Ilihag_vcErfYIiMcVs9LUjj25cdElK293W7a75nf3QLPYexOQW_TdTQsZj2khCd06uMaFknX5JxSjZK9VM4gdulhWU2WO1eS4cKpQxGbBNooGJZUfzOTHiTseOyC97CMCKgSYhWRwfRzRRoqG7jGoXfAFMvh2itonJuIBHkQTWzvoU2AC6yKSV_xRhL8K2MxanQMu2GyFM9jkoO3Gr7AEzT6gKptlcd1Kjd5nWkBGAnzTW-F5cjgY_70OrBFMvJslxCLGhzI6wOS_AELoeZDIAv3S9CQtU8isRo3PaP4uJkI29nXKQFH3nyNhMHLfkesA2CrdVHkg1ZTaEWe2RStStsMyYQUOL1MGgZyjlaCyMTidfeABvCPu_21FcctdbvgJzJoyIu0xE2zDGfmGJJLhQlfDl884E8HgSdehrmYV_3haD31mtu6RRiltO2uUnACphjw7bdiwY6h5XwjGn8rwnbn29dIgd9YZVlbVGenmzGDLywh_ygF6Pk4Cu7YLYVJiKJ7whpyHSh4GKvg9Pf72sHkBVr-A9p479vSvpzb9GZ9nyaRQmwUWZU8SW7ky6W9KS_FyjjfmG5C1Gl96AulqeAwhrFtugICduzl6VLXBd8edBUlUw7wbBJBgBuE-YnsDv35jIXbKnm9zk3aGWP3fiXbBl18lWqGwdyub7wdPjBOya8BZLoyttYphzzgdC9pyPuN426zcVMyFyeWvqXlzkw6qa4-jRG6U3SojISHIAdc_Q4BB7VHXg=='}, {'type': 'text', 'text': 'Here are Cornwall spots with nice weather right now:\n\n- Looe — sunny, around 30°C\n- Newquay — sunny, around 30°C\n- Wadebridge — sunny, around 27°C\n- Truro — sunny,around 24°C\n- St Austell — sunny, around 20°C\n\nIf you want a coastal town with warm beach weather, Looe or Newquay are great picks today. Prefersomething milder? Try Truro or St Austell.\n\nWhen are you planning to go? I can recheck the forecast for your dates and suggest the best base.', 'annotations': [], 'id': 'msg_09eab53f9a3a96a9006a6692b37bf8819b940838fd22fafb6e'}]
    """
    thread_id = uuid.uuid1()
    print(f"Thread ID: {thread_id}")
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

    print("UK Travel Assistant (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        state = {"messages": [HumanMessage(content=user_input)]}
        try:
            result = travel_assistant.invoke(state, config=config)
            response_msg = result["messages"][-1]
            print(f"Assistant: {response_msg.content}\n")
        except GraphRecursionError as gre:
            print("Recursion limit reached: ", gre)
            print("Last messages: ", travel_assistant.get_state(config).values)
