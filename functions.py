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
    files = []
    files.append(client.files.create(file=open("company_knowledge.docx", "rb"), purpose='assistants'))
    files.append(client.files.create(file=open("60-Seconds Free Evaluation for Care Package.docx", "rb"), purpose='assistants'))
    files.append(client.files.create(file=open("No-cost evaluation for Accommodation.docx", "rb"), purpose='assistants'))

    assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
        name="AusNew Home Care Assistant",
        instructions=assistant_instructions,
        model="gpt-3.5-turbo-1106",
        # model="gpt-4-1106-preview",
        tools=[
            {
                "type": "retrieval"  
            },
            {
                "type": "function",  
                "function": {
                    "name": "get_care_evaluation_details",
                    "description": "Capture details from the customer's responses during 60 Seconds free evaluation for care package.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "who_is_this_care_for": {
                                "type":
                                "string",
                                "description":
                                "The man who will use the service (NOT NAME, expect 'me', 'my father', 'friend', 'client' etc)"
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
                                "NDIS registered status"
                            },
                            "hrs_per_day": {
                                "type":
                                "string",
                                "description":
                                "Number of hours per day the customer need to use the service."
                            },
                            "days_per_week": {
                                "type":
                                "string",
                                "description":
                                "Number of days per week the customer need to use the service."
                            },
                            "how_long": {
                                "type":
                                "string",
                                "description":
                                "Duration the customer needs to use the service."
                            },
                            "when_to_start": {
                                "type":
                                "string",
                                "description":
                                "When the customer starts using the service."
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",  
                "function": {
                    "name": "get_accommodation_evaluation_details",
                    "description": "Capture details from the customer's responses during no-cost evaluation for accommodation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "who_is_this_care_for": {
                                "type":
                                "string",
                                "description":
                                "The man who will use the service (NOT NAME, expect 'me', 'my father', 'friend', 'client' etc)"
                            },
                            "ndis_registered": {
                                "type":
                                "string",
                                "description":
                                "NDIS registered status"
                            },
                            "type_of_accommodation": {
                                "type":
                                "string",
                                "description":
                                "Type of accommodation"
                            },
                            "how_long": {
                                "type":
                                "string",
                                "description":
                                "Duration the customer needs to use the service."
                            },
                            "supported_living_services": {
                                "type":
                                "string",
                                "description":
                                "Care services along with accommodation"
                            },
                            "how_pay_for_rent": {
                                "type":
                                "string",
                                "description":
                                "Source of fund for accommodation"
                            },
                            "when_to_start": {
                                "type": "string",
                                "description": "When the customer starts using the service."
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "retrieve_data_for_summarization",
                    "description": "Retrieve data from table for summarization",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_lead_info",
                    "description": "Get lead info from the user's input",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "email address of a customer"
                            },
                            "name": {
                                "type": "string",
                                "description": "name of a customer"
                            },
                            "postcode": {
                                "type": "string",
                                "description": "postcode of a customer"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_to_airtable",
                    "description": "Send all info to Airtable",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_new_records",
                    "description": "Create new records both in care_package table, and accommodation table of DB",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                        "required": []
                    }
                }
            }
        ],
        file_ids = list(map(lambda file: file.id, files)))
    
    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id
