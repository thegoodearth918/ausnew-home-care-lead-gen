import json
import os
import time
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import functions
import requests
from flask_cors import CORS
from datetime import datetime

from packaging import version
import sqlite3

import re

def remove_special_symbols(input_string):
    pattern = re.compile('[^A-Za-z0-9 ]+')
    result_string = re.sub(pattern, '', input_string)
    
    return result_string

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

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=OPENAI_API_KEY)

assistant_id = functions.create_assistant(client)

####################################################################
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

def send_to_airtable_care_package(result):
  url = "https://api.airtable.com/v0/appjO6O8rmmjxcKa2/tblXQKKb0i1Z2CcjR"
  headers = {
      "Authorization": "Bearer " + AIRTABLE_API_KEY,
      "Content-Type": "application/json"
  }
  print("forming data part of request")
  data = {
      "records": [{
          "fields": {
              "User Name": result["name"],
              "User Email": result["email"],
              "Post Code": result["postcode"],
              "Who will use": result["who_is_this_care_for"],
              "Type of service": result["type_of_service"],
              "NDIS registered": result["ndis_registered"],
              "Hrs per day": result["hrs_per_day"],
              "Days per week": result["days_per_week"],
              "Months": result["how_long"],
              "When to start": result["when_to_start"]
          }
      }]
  }
  
  print(headers)
  print(data)
  
  response = requests.post(url, headers=headers, json=data)
  if response.status_code == 200:
    print("Lead created successfully.")
    return response.json()
  else:
    print(f"Failed to create lead: {response.text}")

def send_to_airtable_accommodation(result):
  url = "https://api.airtable.com/v0/appjO6O8rmmjxcKa2/tblSzVSYpJkhDxJhq"
  headers = {
      "Authorization": "Bearer " + AIRTABLE_API_KEY,
      "Content-Type": "application/json"
  }
  data = {
      "records": [{
          "fields": {
              "Name": result["name"],
              "Email": result["email"],
              "Postcode": result["postcode"],
              "Who will use": result["who_is_this_care_for"],
              "NDIS registered": result["ndis_registered"],
              "Type of Accommodation": result["type_of_accommodation"],
              "How Long": result["how_long"],
              "Supported Living Services": result["supported_living_services"],
              "How to pay for rent": result["how_pay_for_rent"],
              "When to start": result["when_to_start"]
          }
      }]
  }
  response = requests.post(url, headers=headers, json=data)
  if response.status_code == 200:
    print("Lead created successfully.")
    return response.json()
  else:
    print(f"Failed to create lead: {response.text}")


def get_care_evaluation_details(who_is_this_care_for=None, type_of_service=None, ndis_registered=None, hrs_per_day=None,
                 days_per_week=None, how_long=None, when_to_start=None):
  return json.dumps({"who_is_this_care_for": who_is_this_care_for, "type_of_service": type_of_service, "ndis_registered": ndis_registered,
                     "hrs_per_day": hrs_per_day, "days_per_week": days_per_week, "how_long": how_long, "when_to_start": when_to_start})

def get_accommodation_evaluation_details(who_is_this_care_for=None, ndis_registered=None, type_of_accommodation=None,
                                        how_long=None, supported_living_services=None, how_pay_for_rent=None, when_to_start=None):
  return json.dumps({"who_is_this_care_for": who_is_this_care_for, "ndis_registered": ndis_registered, "type_of_accommodation": type_of_accommodation,
                     "how_long": how_long, "supported_living_services": supported_living_services,
                     "how_pay_for_rent": how_pay_for_rent, "when_to_start": when_to_start})

def get_lead_info(email=None, name=None, postcode=None):
  return json.dumps({"email": email, "name": name, "postcode": postcode})
  
def create_new_records():
  now = datetime.now()
  date_string = now.strftime("%Y%m%d%H%M%S")
  date_int = int(date_string)
  
  con = sqlite3.connect("extracted_data.db")
  con.execute("pragma busy_timeout=10000")
  cur = con.cursor()
  
  cur.execute(f"INSERT INTO care_package VALUES ('{thread.id}', 'None', 'None', 'None', 'None', 'None', 'None', 'None', '{date_int}')")
  cur.execute(f"INSERT INTO accommodation VALUES ('{thread.id}', 'None', 'None', 'None', 'None', 'None', 'None', 'None', '{date_int}')")
  
  con.commit()
  con.close()
  return json.dumps({'success': True})


####################################################################


# Start conversation thread
@app.route('/startx', methods=['GET'])
def start_conversation():
  print("Starting a new conversation...")
  thread = client.beta.threads.create()
  print(f"New thread created with ID: {thread.id}")

  message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Say hi, introduce yourself including which company you are from and ask me how you can help me today. Put a line break at the end of each sentence.",
  )

  run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant_id,
  )
  wait_on_run(run, thread)

  messages = client.beta.threads.messages.list(
    thread_id=thread.id, order="asc", after=message.id
  )
  
  now = datetime.now()
  date_string = now.strftime("%Y%m%d%H%M%S")
  date_int = int(date_string)
  
  con = sqlite3.connect("extracted_data.db")
  con.execute("pragma busy_timeout=10000")
  cur = con.cursor()
  
  cur.execute(f"INSERT INTO sessions VALUES ('{thread.id}', 'in progress', '{date_int}')")
  cur.execute(f"INSERT INTO care_package VALUES ('{thread.id}', 'None', 'None', 'None', 'None', 'None', 'None', 'None', '{date_int}')")
  cur.execute(f"INSERT INTO accommodation VALUES ('{thread.id}', 'None', 'None', 'None', 'None', 'None', 'None', 'None', '{date_int}')")
  cur.execute(f"INSERT INTO lead_info VALUES ('{thread.id}', 'None', 'None', 'None')")
  
  con.commit()
  con.close()
  
  return jsonify({"thread_id": thread.id, "assistant_message": messages.data[0].content[0].text.value})


# Generate response
@app.route('/chatx', methods=['POST'])
def chat():
  line_counter = 0
  data = request.json
  thread_id = data.get('thread_id')
  user_input = data.get('message', '')
  print("User's input: ", user_input)
  if not thread_id:
    print("Error: Missing thread_id")
    return jsonify({"error": "Missing thread_id"}), 400

  con = sqlite3.connect("extracted_data.db")
  con.execute("pragma busy_timeout=10000")
  cur = con.cursor()
    
  client.beta.threads.messages.create(thread_id=thread_id,
                                      role="user",
                                      content=user_input)
  run = client.beta.threads.runs.create(thread_id=thread_id,
                                        assistant_id=assistant_id)
  while True:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    # queued, in_progress, completed, requires_action, expired, cancelling, cancelled, failed
    if run_status.status == 'completed':
      break
    elif run_status.status == 'requires_action':
      print(run_status.required_action.submit_tool_outputs.tool_calls)
      total_output = []
      for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "get_care_evaluation_details":
          try:
            arguments = json.loads(tool_call.function.arguments)

            who_is_this_care_for = arguments.get("who_is_this_care_for", None)
            type_of_service = arguments.get("type_of_service", None)
            ndis_registered = arguments.get("ndis_registered", None)
            hrs_per_day = arguments.get("hrs_per_day", None)
            days_per_week = arguments.get("days_per_week", None)
            how_long = arguments.get("how_long", None)
            when_to_start = arguments.get("when_to_start", None)
            
            output = get_care_evaluation_details(who_is_this_care_for, type_of_service,
                                  ndis_registered, hrs_per_day, days_per_week,
                                  how_long, when_to_start)
            
            # To prevent TypeError exception while concatenating the strings
            if who_is_this_care_for == None:
              who_is_this_care_for = 'None'
            if type_of_service == None:
              type_of_service = 'None'
            if ndis_registered == None:
              ndis_registered = 'None'
            if hrs_per_day == None:
              hrs_per_day = 'None'
            if days_per_week == None:
              days_per_week = 'None'
            if how_long == None:
              how_long = 'None'
            if when_to_start == None:
              when_to_start = 'None'
            
            # clear out special symbols
            who_is_this_care_for = remove_special_symbols(who_is_this_care_for)
            type_of_service = remove_special_symbols(type_of_service)
            ndis_registered = remove_special_symbols(ndis_registered)
            hrs_per_day = remove_special_symbols(hrs_per_day)
            days_per_week = remove_special_symbols(days_per_week)
            how_long = remove_special_symbols(how_long)
            when_to_start = remove_special_symbols(when_to_start)
            
            output_json = json.loads(output)
            res = cur.execute(f"SELECT rowid, * FROM care_package WHERE created_at = (SELECT MAX(created_at) FROM care_package WHERE session_id='{thread_id}') LIMIT 1;")
            db_fetch_result = res.fetchall()
            row_id = db_fetch_result[0][0]

            cur.execute(f"""UPDATE care_package SET
                        who_is_this_care_for={"'" + who_is_this_care_for + "'" if output_json["who_is_this_care_for"] != None else "'" + db_fetch_result[0][2] + "'"},
                        type_of_service={"'" + type_of_service + "'" if output_json["type_of_service"] != None else "'" + db_fetch_result[0][3] + "'"},
                        ndis_registered={"'" + ndis_registered + "'" if output_json["ndis_registered"] != None else "'" + db_fetch_result[0][4] + "'"},
                        hrs_per_day={"'" + hrs_per_day + "'" if output_json["hrs_per_day"] != None else "'" + db_fetch_result[0][5] + "'"},
                        days_per_week={"'" + days_per_week + "'" if output_json["days_per_week"] != None else "'" + db_fetch_result[0][6] + "'"},
                        how_long={"'" + how_long + "'" if output_json["how_long"] != None else "'" + db_fetch_result[0][7] + "'"},
                        when_to_start={"'" + when_to_start + "'" if output_json["when_to_start"] != None else "'" + db_fetch_result[0][8] + "'"} WHERE rowid={row_id}""")
            con.commit()
            
            total_output.append({
              "tool_call_id": tool_call.id,
              "output": output
            })
          except json.decoder.JSONDecodeError as e:
            print("!!!--> no arguments are passed")
            print(e)
          except TypeError as e:
            print("!!!--> TypeError occurred: may be None type is returned to var!")
            print(e)
          except Exception as e:
            print("!!! ---> unexpected exception <--- !!!")
            print(e)
       
        elif tool_call.function.name == "get_accommodation_evaluation_details":
          try:
            arguments = json.loads(tool_call.function.arguments)

            who_is_this_care_for = arguments.get("who_is_this_care_for", None)
            ndis_registered = arguments.get("ndis_registered", None)
            type_of_accommodation = arguments.get("type_of_accommodation", None)
            how_long = arguments.get("how_long", None)
            supported_living_services = arguments.get("supported_living_services", None)
            how_pay_for_rent = arguments.get("how_pay_for_rent", None)
            when_to_start = arguments.get("when_to_start", None)

            output = get_accommodation_evaluation_details(who_is_this_care_for, ndis_registered, type_of_accommodation, how_long,
                  supported_living_services, how_pay_for_rent, when_to_start)
            
            # To prevent TypeError exception while concatenating the strings
            if who_is_this_care_for == None:
              who_is_this_care_for = 'None'
            if ndis_registered == None:
              ndis_registered = 'None'
            if type_of_accommodation == None:
              type_of_accommodation = 'None'
            if how_long == None:
              how_long = 'None'
            if supported_living_services == None:
              supported_living_services = 'None'
            if how_pay_for_rent == None:
              how_pay_for_rent = 'None'
            if when_to_start == None:
              when_to_start = 'None'
            
            # clear out special symbols
            who_is_this_care_for = remove_special_symbols(who_is_this_care_for)
            ndis_registered = remove_special_symbols(ndis_registered)
            type_of_accommodation = remove_special_symbols(type_of_accommodation)
            how_long = remove_special_symbols(how_long)
            supported_living_services = remove_special_symbols(supported_living_services)
            how_pay_for_rent = remove_special_symbols(how_pay_for_rent)
            when_to_start = remove_special_symbols(when_to_start)
            
            output_json = json.loads(output)
            res = cur.execute(f"SELECT rowid, * FROM accommodation WHERE created_at = (SELECT MAX(created_at) FROM care_package WHERE session_id='{thread_id}') LIMIT 1;")
            db_fetch_result = res.fetchall()
            row_id = db_fetch_result[0][0]

            cur.execute(f"""UPDATE accommodation SET
                        who_is_this_care_for={"'" + who_is_this_care_for + "'" if output_json["who_is_this_care_for"] != None else "'" + db_fetch_result[0][2] + "'"},
                        ndis_registered={"'" + ndis_registered + "'" if output_json["ndis_registered"] != None else "'" + db_fetch_result[0][3] + "'"},
                        type_of_accommodation={"'" + type_of_accommodation + "'" if output_json["type_of_accommodation"] != None else "'" + db_fetch_result[0][4] + "'"},
                        how_long={"'" + how_long + "'" if output_json["how_long"] != None else "'" + db_fetch_result[0][5] + "'"},
                        supported_living_services={"'" + supported_living_services + "'" if output_json["supported_living_services"] != None else "'" + db_fetch_result[0][6] + "'"},
                        how_pay_for_rent={"'" + how_pay_for_rent + "'" if output_json["how_pay_for_rent"] != None else "'" + db_fetch_result[0][7] + "'"},
                        when_to_start={"'" + when_to_start + "'" if output_json["when_to_start"] != None else "'" + db_fetch_result[0][8] + "'"} WHERE rowid={row_id}""")
            con.commit()
            
            total_output.append({
              "tool_call_id": tool_call.id,
              "output": output
            })

          except json.decoder.JSONDecodeError as e:
            print("!!!--> no arguments are passed")
            print(e)
          except TypeError as e:
            print("!!!--> TypeError occurred: may be None type is returned to var!")
            print(e)
          except Exception as e:
            print("!!! ---> unexpected exception <--- !!!")
            print(e)
        
        elif tool_call.function.name == "send_to_airtable":
          try:
            cp_res = cur.execute(f"SELECT rowid, * FROM care_package WHERE session_id='{thread_id}'")
            cp_db_fetch_result = cp_res.fetchall()
            
            ac_res = cur.execute(f"SELECT rowid, * FROM accommodation WHERE session_id='{thread_id}'")
            ac_db_fetch_result = ac_res.fetchall()

            ld_res = cur.execute(f"SELECT rowid, * FROM lead_info WHERE session_id='{thread_id}'")
            ld_data_to_submit = ld_res.fetchall()[0]
            
            for i in cp_db_fetch_result:
              if i[2] == 'None' and i[3] == 'None' and i[4] == 'None' and i[5] == 'None' and i[6] == 'None' and i[7] == 'None' and i[8] == 'None':
                continue
              else:
                data_to_submit = {"who_is_this_care_for": i[2], "type_of_service": i[3], "ndis_registered": i[4],
                                  "hrs_per_day": i[5], "days_per_week": i[6], "how_long": i[7], "when_to_start": i[8],
                                  "email": ld_data_to_submit[3], "name": ld_data_to_submit[2], "postcode": ld_data_to_submit[4]}
                print("----------> trying to send lead_info table data to airtable")
                send_to_airtable_care_package(data_to_submit)
                
            for j in ac_db_fetch_result:
              if j[2] == 'None' and j[3] == 'None' and j[4] == 'None' and j[5] == 'None' and j[6] == 'None' and j[7] == 'None' and j[8] == 'None':
                continue
              else:
                data_to_submit = {"who_is_this_care_for": j[2], "ndis_registered": j[3], "type_of_accommodation": j[4],
                                  "how_long": j[5], "supported_living_services": j[6], "how_pay_for_rent": j[7], "when_to_start": j[8],
                                  "email": ld_data_to_submit[3], "name": ld_data_to_submit[2], "postcode": ld_data_to_submit[4]}
                print("----------> trying to send lead_info table data to airtable")
                send_to_airtable_accommodation(data_to_submit)
            
            output = json.dumps({"To": "The next step"})
            total_output.append({
              "tool_call_id": tool_call.id,
              "output": output
            })
          except json.decoder.JSONDecodeError as e:
            print("!!!--> no arguments are passed")
            print(e)
          except TypeError as e:
            print("!!!--> TypeError occurred: may be None type is returned to var!")
            print(e)
          except Exception as e:
            print("!!! ---> unexpected exception <--- !!!")
            print(e)

        elif tool_call.function.name == "get_lead_info":
          try:
            arguments = json.loads(tool_call.function.arguments)
            
            email = arguments.get("email", None)
            name = arguments.get("name", None)
            postcode = arguments.get("postcode", None)
            
            output = get_lead_info(email, name, postcode)
              
            output_json = json.loads(output)
            res = cur.execute(f"SELECT rowid, * FROM lead_info WHERE session_id='{thread_id}' LIMIT 1;")
            db_fetch_result = res.fetchall()
            row_id = db_fetch_result[0][0]

            cur.execute(f"""UPDATE lead_info SET
                        email={"'" + email + "'" if output_json["email"] != None else "'" + db_fetch_result[0][3] + "'"},
                        name={"'" + name + "'" if output_json["name"] != None else "'" + db_fetch_result[0][2] + "'"},
                        postcode={"'" + postcode + "'" if output_json["postcode"] != None else "'" + db_fetch_result[0][4] + "'"} WHERE rowid={row_id}""")
            con.commit()
            output_json = json.loads(output)
            total_output.append({
              "tool_call_id": tool_call.id,
              "output": output
            })
          except json.decoder.JSONDecodeError as e:
            print("!!!--> no arguments are passed")
            print(e)
          except TypeError as e:
            print("!!!--> TypeError occurred: may be None type is returned to var!")
            print(e)
          except Exception as e:
            print("!!! ---> unexpected exception <--- !!!")
            print(e)
          
        elif tool_call.function.name == "retrieve_data_for_summarization":
          cp_res = cur.execute(f"SELECT rowid, * FROM care_package WHERE session_id='{thread_id}'")
          ac_res = cur.execute(f"SELECT rowid, * FROM accommodation WHERE session_id='{thread_id}'")
          data_to_summarize = []

          cp_db_fetch_result = cp_res.fetchall()
          for i in cp_db_fetch_result:
            if i[2] == 'None' and i[3] == 'None' and i[4] == 'None' and i[5] == 'None' and i[6] == 'None' and i[7] == 'None' and i[8] == 'None':
              continue
            else:
              data_to_summarize.append({"who_is_this_care_for": i[2], "type_of_service": i[3], "ndis_registered": i[4], "hrs_per_day": i[5], "days_per_week": i[6], "how_long": i[7], "when_to_start": i[8]})
          
          ac_db_fetch_result = ac_res.fetchall()
          for j in ac_db_fetch_result:
            if j[2] == 'None' and j[3] == 'None' and j[4] == 'None' and j[5] == 'None' and j[6] == 'None' and j[7] == 'None' and j[8] == 'None':
              continue
            else:
              data_to_summarize.append({"who_is_this_care_for": j[2], "ndis_registered": j[3], "type_of_accommodation": j[4], "how_long": j[5], "supported_living_services": j[6], "how_pay_for_rent": j[7], "when_to_start": j[8]})
          
          output = json.dumps(data_to_summarize)
          total_output.append({
            "tool_call_id": tool_call.id,
            "output": output
          })

        elif tool_call.function.name == "create_new_records":
          now = datetime.now()
          date_string = now.strftime("%Y%m%d%H%M%S")
          date_int = int(date_string)
                   
          cur.execute(f"INSERT INTO care_package VALUES ('{thread_id}', 'None', 'None', 'None', 'None', 'None', 'None', 'None', '{date_int}')")
          cur.execute(f"INSERT INTO accommodation VALUES ('{thread_id}', 'None', 'None', 'None', 'None', 'None', 'None', 'None', '{date_int}')")
          con.commit()
          output = json.dumps({'To': 'The next step'})
          total_output.append({
            "tool_call_id": tool_call.id,
            "output": output
          })
      # put total output here
      print("total output ---->", total_output)
      if total_output == []:
        total_output = [{
            "tool_call_id": tool_call.id,
            "output": '{"To": "The next question"}'
          }]
      client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                    run_id=run.id,
                                                    tool_outputs=total_output)
      time.sleep(1)
    elif run_status.status == "failed":
      if total_output == []:
        total_output = [{
            "tool_call_id": tool_call.id,
            "output": '{"To": "The next question"}'
          }]
      client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                    run_id=run.id,
                                                    tool_outputs=total_output)
    else:
      line_counter += 1
      print(line_counter, "---------------------------->",run_status.status)
    
  
  messages = client.beta.threads.messages.list(thread_id=thread_id)
  response = messages.data[0].content[0].text.value
  
  con.close()
  print(f"Assistant response: {response}")
  return jsonify({"response": response})


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80, debug=True)
