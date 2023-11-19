import json
import os
import time
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import functions
import requests

# Check OpenAI version compatibility
from packaging import version

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']

if current_version < required_version:
  raise ValueError(
      f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
  )
else:
  print("OpenAI version is compatible.")

# Create Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create or load assistant
assistant_id = functions.create_assistant(
    client)  # this function comes from "functions.py"

lead_details = {}
current_thread_id = ''


####################################################################
def send_to_airtable():
  url = "https://api.airtable.com/v0/appjO6O8rmmjxcKa2/tblXQKKb0i1Z2CcjR"
  headers = {
      "Authorization": AIRTABLE_API_KEY,
      "Content-Type": "application/json"
  }
  data = {
      "records": [{
          "fields": {
              "User Name": lead_details[current_thread_id]["name"],
              "User Email": lead_details[current_thread_id]["email"],
              "Post Code": lead_details[current_thread_id]["postcode"],
              "Who will use": lead_details[current_thread_id]["who_will_use_service"],
              "Type of service": lead_details[current_thread_id]["type_of_service"],
              "NDIS registered": lead_details[current_thread_id]["ndis_registered"],
              "Hrs per day": lead_details[current_thread_id]["hrs_per_day"],
              "Days per week": lead_details[current_thread_id]["days_per_week"],
              "Months": lead_details[current_thread_id]["months"],
              "When to start": lead_details[current_thread_id]["when_to_start"]
          }
      }]
  }
  response = requests.post(url, headers=headers, json=data)
  if response.status_code == 200:
    print("Lead created successfully.")
    del lead_details[current_thread_id]
    return response.json()
  else:
    print(f"Failed to create lead: {response.text}")


def capture_lead(who_will_use_service=None,
                 type_of_service=None,
                 ndis_registered=None,
                 hrs_per_day=None,
                 days_per_week=None,
                 months=None,
                 when_to_start=None,
                 name=None,
                 email=None,
                 postcode=None):
  captured_what = "Captured "
  if who_will_use_service is not None:
    lead_details[current_thread_id]["who_will_use_service"] = who_will_use_service
    captured_what += "Who will use, "
  if type_of_service is not None:
    lead_details[current_thread_id]["type_of_service"] = type_of_service
    captured_what += "type of service, "
  if ndis_registered is not None:
    lead_details[current_thread_id]["ndis_registered"] = ndis_registered
    captured_what += "ndis registered, "
  if hrs_per_day is not None:
    lead_details[current_thread_id]["hrs_per_day"] = hrs_per_day
    captured_what += "hrs per day, "
  if days_per_week is not None:
    lead_details[current_thread_id]["days_per_week"] = days_per_week
    captured_what += "days per week, "
  if months is not None:
    lead_details[current_thread_id]["months"] = months
    captured_what += "months, "
  if when_to_start is not None:
    lead_details[current_thread_id]["when_to_start"] = when_to_start
    captured_what += "when to start, "
  if name is not None:
    lead_details[current_thread_id]["name"] = name
    captured_what += "name, "
  if email is not None:
    lead_details[current_thread_id]["email"] = email
    captured_what += "email, "
  if postcode is not None:
    lead_details[current_thread_id]["postcode"] = postcode
    captured_what += "postcode, "
  
  return captured_what


####################################################################


# Start conversation thread
@app.route('/start', methods=['GET'])
def start_conversation():
  print("Starting a new conversation...")
  thread = client.beta.threads.create()
  print(f"New thread created with ID: {thread.id}")

  lead_details[thread.id] = {
      "name": None,
      "email": None,
      "postcode": None,
      "who_will_use_service": None,
      "type_of_service": None,
      "ndis_registered": None,
      "hrs_per_day": None,
      "days_per_week": None,
      "months": None,
      "when_to_start": None
  }

  return jsonify({"thread_id": thread.id})


# Generate response
@app.route('/chat', methods=['POST'])
def chat():
  data = request.json
  thread_id = data.get('thread_id')
  user_input = data.get('message', '')

  if not thread_id:
    print("Error: Missing thread_id")
    return jsonify({"error": "Missing thread_id"}), 400
  global current_thread_id
  current_thread_id = thread_id
  print(f"Received message: {user_input} for thread ID: {thread_id}")

  # Add the user's message to the thread
  client.beta.threads.messages.create(thread_id=thread_id,
                                      role="user",
                                      content=user_input)

  # Run the Assistant
  run = client.beta.threads.runs.create(thread_id=thread_id,
                                        assistant_id=assistant_id)

  # Check if the Run requires action (function call)
  while True:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    # print(f"Run status: {run_status.status}")
    if run_status.status == 'completed':
      break
    elif run_status.status == 'requires_action':

      for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "capture_lead":

          arguments = json.loads(tool_call.function.arguments)

          who_will_use_service = arguments.get("who_will_use_service", None)
          type_of_service = arguments.get("type_of_service", None)
          ndis_registered = arguments.get("ndis_registered", None)
          hrs_per_day = arguments.get("hrs_per_day", None)
          days_per_week = arguments.get("days_per_week", None)
          months = arguments.get("months", None)
          when_to_start = arguments.get("when_to_start", None)
          name = arguments.get("name", None)
          email = arguments.get("email", None)
          postcode = arguments.get("postcode", None)

          # capture_lead(who_will_use_service, type_of_service,
          # ndis_registered, hrs_per_day, days_per_week,
          # months, when_to_start, name, email, postcode)
          output = capture_lead(who_will_use_service, type_of_service,
                                ndis_registered, hrs_per_day, days_per_week,
                                months, when_to_start, name, email, postcode)
          client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                       run_id=run.id,
                                                       tool_outputs=[{
                                                           "tool_call_id": tool_call.id,
                                                           "output": output
                                                       }])
        elif tool_call.function.name == "send_to_airtable":
          # Process lead creation
          arguments = json.loads(tool_call.function.arguments)
          output = send_to_airtable()
          client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                       run_id=run.id,
                                                       tool_outputs=[{
                                                           "tool_call_id": tool_call.id,
                                                           "output": json.dumps(output)
                                                       }])
      time.sleep(1)  # Wait for a second before checking again

  # Retrieve and return the latest message from the assistant
  messages = client.beta.threads.messages.list(thread_id=thread_id)
  response = messages.data[0].content[0].text.value

  print(f"Assistant response: {response}")
  return jsonify({"response": response})


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
