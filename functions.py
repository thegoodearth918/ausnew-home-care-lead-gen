import json
# import requests
import os
from openai import OpenAI
from prompts import assistant_instructions

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create or load assistant
def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications

    # To change the knowledge document, modifiy the file name below to match your document
    # If you want to add multiple files, paste this function into ChatGPT and ask for it to add support for multiple files
    file = client.files.create(file=open("ausnew_home_care_knowledge.txt", "rb"), purpose='assistants')
    file = client.files.create(file=open("gpt3.5_test.txt", "rb"), purpose='assistants')

    assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
        instructions=assistant_instructions,
        model="gpt-3.5-turbo-1106",
        tools=[
            {
                "type": "retrieval"  # This adds the knowledge base as a tool
            },
            {
                "type": "function",  # This adds the solar calculator as a tool
                "function": {
                    "name": "capture_lead",
                    "description": "Capture the lead details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "who_will_use_service": {
                                "type":
                                "string",
                                "description":
                                "The man who will use the service, for example, customer or customer's mother."
                            },
                            "type_of_service": {
                                "type":
                                "string",
                                "description":
                                "Type of services looking for. They can be separated by comma."
                            },
                            "ndis_registered": {
                                "type":
                                "string",
                                "description":
                                "If the customer NDIS registered, put 'Yes, NDIS registered', else put 'No, Not registered'. If the customer is My Aged Care registered, put 'Yes, My Aged Care registered'."
                            },
                            "hrs_per_day": {
                                "type":
                                "string",
                                "description":
                                "Number of hours per day the customer need to use the service. if the customer is not sure about it, put 'Not sure'."
                            },
                            "days_per_week": {
                                "type":
                                "string",
                                "description":
                                "Number of days per week the customer need to use the service. if the customer is not sure about it, put 'Not sure'."
                            },
                            "months": {
                                "type":
                                "string",
                                "description":
                                "How long the customer needs to use the service. if the customer is not sure about it, put 'Not sure'."
                            },
                            "when_to_start": {
                                "type":
                                "string",
                                "description":
                                "When the customer starts using the service. if the customer is not sure about it, put 'Not sure'"
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the lead."
                            },
                            "email": {
                                "type": "string",
                                "description": "Email of the lead."
                            },
                            "postcode": {
                                "type": "string",
                                "description": "Postcode of the lead."
                            }
                        },
                        "required": ["thread_id"]
                    }
                }
            },
            {
                "type": "function",  # This adds the lead capture as a tool
                "function": {
                    "name": "send_to_airtable",
                    "description": "Send captured lead details to Airtable.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                        "required": []
                    }
                }
            }
        ],
        file_ids=[file.id])

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id
