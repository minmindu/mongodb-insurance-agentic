from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent_llm import get_llm
from agent_tools import tools


llm = get_llm(model_id="anthropic.claude-3-haiku-20240307-v1:0")

def create_agent(llm, tools, system_message: str):
    """Create an agent

    Args:
        llm (ChatBedrock): The ChatBedrock instance to use.
        tools (List[Callable]): The list of tools to bind to the agent.
        system_message (str): The system message to display to the agent.

    Returns:
        ChatAgent: The created ChatAgent instance.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an experienced claim handler assistant for an insurance company. Your goal is to provide specific, actionable guidance to help claim handlers process claims efficiently and accurately."
                "\n\nBased on the accident description, you must:"
                "\n1. Use the fetch_guidelines tool to find the most relevant insurance policy"
                "\n2. Extract specific handler actions, approval thresholds, and decision tree guidance from the policy"
                "\n3. Generate time-bound, actionable recommendations using insurance industry terminology"
                "\n\nWhen creating recommendations, focus on:"
                "\n- IMMEDIATE ACTIONS (next 4 hours): Specific tasks with claims system operations, reserve setting, and vendor coordination"
                "\n- SHORT-TERM ACTIONS (24-72 hours): Investigation steps, documentation requirements, and stakeholder coordination"
                "\n- APPROVAL GUIDANCE: Reference specific dollar thresholds and required approval levels from the policy"
                "\n- RESERVE RECOMMENDATIONS: Provide specific dollar amounts based on policy guidelines and incident severity"
                "\n- DECISION TREE LOGIC: Apply the policy's decision tree to determine priority, timeline, and investigation level"
                "\n\nUse industry terminology like: claims system, recorded statements, reserves, DRP shops, vendor portals, coverage analysis, liability assessment, etc."
                "\n\nYou have access to these tools: {tool_names}"
                "At the end, persist data with these fields:"
                "\n- date: current ISO format timestamp" 
                "\n- description: concise accident summary"
                "\n- recommendation: STRUCTURED OBJECT with the following format:"
                "\n  {{"
                '\n    "immediate_actions": ["Action 1", "Action 2", "Action 3"],'
                '\n    "short_term_actions": ["Action 1", "Action 2"],'
                '\n    "approval_guidance": {{"initial_reserve_threshold": 25000, "supplement_estimate_threshold": 10000}},'
                '\n    "reserve_recommendations": {{"initial_reserve": 15000, "maximum_reserve": 50000}}'
                "\n  }}"
                "\n- approval_level: required approval tier based on policy thresholds"
                "\n- estimated_reserves: dollar amounts based on policy guidelines"
                "\n- priority: urgency level from policy decision tree"
                "\n- timeline: expected resolution timeframe"
                "\n- claim_handler: generate realistic handler name"
                "\n\nCRITICAL: The recommendation field must be a JSON object with these exact keys:"
                '\n- immediate_actions: Array of 3-5 specific tasks for next 4 hours'
                '\n- short_term_actions: Array of 2-4 tasks for 24-72 hours'
                '\n- approval_guidance: Object with threshold amounts (use policy data)'
                '\n- reserve_recommendations: Object with initial and maximum reserve amounts'
                "\n\nThen clean chat history and respond with FINAL ANSWER."
                "\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(time=lambda: str(datetime.now()))
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

    return prompt | llm.bind_tools(tools)


# Chatbot agent and node
chatbot_agent = create_agent(
    llm,
    tools,
    system_message="Edit this message.",
)