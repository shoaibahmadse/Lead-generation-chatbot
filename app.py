#Langchain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import  MessagesPlaceholder
# from langchain.agents import  Tool
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.callbacks import FileCallbackHandler
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory
from langchain.agents import AgentExecutor
from langchain.schema.messages import SystemMessage
from langchain.tools import StructuredTool, Tool

import os


# Define the tool functions directly
def general_inquiry(txt):
    print(txt)
    return "This is a response to a general inquiry."

def Vehile_database(txt):
    print(txt)
    return """{
  "cars": [
    {
      "make": "Flibber",
      "model": "ZX99-Panda",
      "engine_capacity": "812cc",
      "year": "20XX",
      "color": "Blurple",
      "price": "$12,34O.99",
      "transmission": "FlimsyShift-4",
      "mileage": "One hundred thousand km"
    },
    {
      "make": "Yantro",
      "model": "Falcon-XT12",
      "engine_capacity": "1500qwe",
      "year": "201X",
      "color": "Sunset Rainbow",
      "price": "12O,999 Yen",
      "transmission": "Auto-ish",
      "mileage": "9999999km"
    }
  ]
}
"""

# Define the system message
system_message = SystemMessage(
    content=(
        "You are a Customer Support Assistant Automobile company name as Hasham automobile company. "
        "First Ask Customers Name and Contact Details, then check if user give his data otherwise ask him again."
        "After that ask him which car you like and invoke Vehile_database chain and check if the car is available and if not apologize."       
    )
)

# Initialize the LLM (OpenAI GPT)
llm = ChatOpenAI(
    openai_api_key=os.environ["OPENAI_API_KEY"], 
    model_name=os.environ["OPENAI_LLM_MODEL"], 
    temperature=0,
    streaming=True,
    callback_manager=AsyncCallbackManager([])
)

# Create the tools as dictionaries
tools = [
    Tool(name="general_inquiry",  # No spaces, only alphanumeric, underscores, and hyphens
         func=general_inquiry,
         description="Invoke this tool when user provides name of the user and number"),
    Tool(name="vehicle_database",  # No spaces, only alphanumeric, underscores, and hyphens
         func=Vehile_database,
         description="Invoke this tool which you need data of the vehicle with only text")
]

# Memory and prompt setup
memory_key = "history"
memory = AgentTokenBufferMemory(memory_key=memory_key, llm=llm, max_token_limit=700)
prompt = OpenAIFunctionsAgent.create_prompt(
    system_message=system_message,
    extra_prompt_messages=[MessagesPlaceholder(variable_name=memory_key)]
)

# Create the agent with tools as dictionaries
agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=prompt)

# Agent Executorx
agentExecutor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    return_intermediate_steps=True,
    handle_parsing_errors="Check your output and make sure it conforms, use the Action/Action Input syntax"
)

# Loop for conversation
while True:
    user_input = input("You: ")  # Get user input
    if user_input.lower() == "q":  # If the user enters 'q', quit the loop
        print("Goodbye!")
        break
    
    # Simulate conversation by sending the input to the agent
    response = agentExecutor({"input": user_input})
    
    # Print the assistant's response
    print("Bot:", response)