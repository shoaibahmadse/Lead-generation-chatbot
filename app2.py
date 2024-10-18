#Langchain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import  MessagesPlaceholder
# from langchain.agents import  Tool
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.agents.openai_functions_agent.base import create_openai_functions_agent,OpenAIFunctionsAgent
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory
from langchain.agents import AgentExecutor
from langchain.schema.messages import SystemMessage
from tools_custom import StructuredTool
# Imports for Pydantic model (used in StructuredTool)
from pydantic import BaseModel, Field
import os
import asyncio
import uuid

import csv
import os

# Class to handle user data and saving to CSV
class UserDataManager:
    def __init__(self, file_name="user_data.csv"):
        self.file_name = file_name
        self.create_csv_file()

    # Check if file exists, if not create one with headers
    def create_csv_file(self):
        if not os.path.exists(self.file_name):
            with open(self.file_name, mode="w", newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["session_id", "user_name", "contact_number", "car_name"])  # Headers

    # Save user data (session_id, name, contact number, car name) to CSV
    def save_user_data(self, session_id, user_name, contact_number, car_name=None):
        # Check if session_id already exists, then append the car_name
        existing_data = self.load_existing_data()

        if session_id in existing_data:
            # Append new car name if the session already exists
            current_cars = existing_data[session_id]['car_name']
            if car_name and car_name not in current_cars:
                current_cars.append(car_name)
            existing_data[session_id]['car_name'] = current_cars
        else:
            # Otherwise, add new entry
            existing_data[session_id] = {
                'user_name': user_name,
                'contact_number': contact_number,
                'car_name': [car_name] if car_name else []
            }
        
        self.save_to_csv(existing_data)

    # Load existing data from the CSV into a dictionary
    def load_existing_data(self):
        existing_data = {}
        if os.path.exists(self.file_name):
            with open(self.file_name, mode="r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    car_names = row["car_name"].strip("[]").split(", ")
                    existing_data[row["session_id"]] = {
                        "user_name": row["user_name"],
                        "contact_number": row["contact_number"],
                        "car_name": car_names if car_names[0] else []  # Handle empty car name field
                    }
        return existing_data

    # Save the updated dictionary back to CSV
    def save_to_csv(self, data):
        with open(self.file_name, mode="w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["session_id", "user_name", "contact_number", "car_name"])  # Write header
            for session_id, info in data.items():
                writer.writerow([
                    session_id, 
                    info["user_name"], 
                    info["contact_number"], 
                    str(info["car_name"])  # Store car_name list as a string in CSV
                ])

# Instantiate the data manager
user_data_manager = UserDataManager()

# Function to generate a new session ID for each user
def generate_session_id():
    return str(uuid.uuid4())

# Example of session tracking
session_id = generate_session_id()
# Modify general_inquiry to save data in CSV
def general_inquiry(user_name: str, contact_number: str,car_intrested:str):
    # Save user name, contact number, and session ID to CSV
    user_data_manager.save_user_data(session_id, user_name, contact_number,car_intrested)
    return f"User {user_name} with contact number {contact_number} has been registered with session ID {session_id}."


# Define the tool function for Vehicle_database with StructuredTool schema

# Define schema for the vehicle inquiry
class VehicleRequest(BaseModel):
    car_name: str = Field(..., description="The name of the car the customer is asking about.")

llm = ChatOpenAI(
    openai_api_key=os.environ["OPENAI_API_KEY"], 
    model_name=os.environ["OPENAI_LLM_MODEL"], 
    temperature=0.2,
    streaming=True,
    callbacks=AsyncCallbackManager([])
)

# Define the system message
system_message = SystemMessage(
    content=(
        "You are a Customer Support Assistant Automobile company name as Hasham automobile company. "
        "First Ask Customers Name and Contact Details, then check if user give his data otherwise ask him again."
        "After that ask him which car you like and invoke Vehile_database chain and check if the car is available and if not apologize."
        "After you get information of name contact and ask car invoke the general inquiry and then answer him appropiate."
        "If user show interset in multiple cars then invoke general inquiry"       
    )
)

# Define the tool function for Vehicle_database with StructuredTool schema
def vehicle_database(car_name:str):
    car_data = '''[
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
    ]'''
    return car_data
    # Process the request object to extract the ca r name
    for car in car_data:
        if car_name.lower() in car["make"].lower() or request.car_name.lower() in car["model"].lower():
            return car
    return {"error": "Car not found, apologize to the customer."}

# General inquiry tool schema
class GeneralInquiryRequest(BaseModel):
    user_name: str = Field(..., description="The name of the customer.")
    contact_number: str = Field(..., description="The contact number of the customer.")
    car_intrested: str = Field(..., description="Car model in which user is intersted.")

# def general_inquiry(user_name:str,contact_number:str):
#     # Simulating processing the user's name and contact number
#     return f"User {user_name} with contact number {contact_number} has been registered."

# Structured tools with validation
tools = [
    StructuredTool.from_function(
        name="general_inquiry",
        func=general_inquiry,
        description="Invoke this tool when user provides their name and number",
        args_schema=GeneralInquiryRequest,  # The Pydantic model to validate input
    ),
    StructuredTool.from_function(
        name="vehicle_database",
        func=vehicle_database,
        description="Invoke this tool when you need data about a vehicle by name",
        args_schema=VehicleRequest,  # The Pydantic model to validate input
        return_direct=False
    )
]

# Memory and prompt setup
memory_key = "history"
memory = AgentTokenBufferMemory(memory_key=memory_key, llm=llm, max_token_limit=700)

# Create the prompt using the OpenAIFunctionsAgent
prompt = OpenAIFunctionsAgent.create_prompt(
    system_message=system_message,
    extra_prompt_messages=[MessagesPlaceholder(variable_name=memory_key)]
)

# Create the agent with tools
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

# Agent Executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    return_intermediate_steps=True,
    handle_parsing_errors="Check your output and make sure it conforms, use the Action/Action Input syntax"
)

async def conversation_loop():
    global session_id
    session_id = generate_session_id()  # Generate a new session ID when the conversation starts
    while True:
        user_input = input("You: ")  # Get user input
        if user_input.lower() == "q":  # If the user enters 'q', quit the loop
            print("Goodbye!")
            break
        
        # Await the agent's response asynchronously (streaming handled in the callback)
        await agent_executor.ainvoke({"input": user_input})

if __name__ == "__main__":
    asyncio.run(conversation_loop())

    # Simulate conversation by sending the input to the agent
    # response = agent_executor.ainvoke({"input": user_input})
    
    # Print the assistant's response
    # print("Bot:", response['output'])