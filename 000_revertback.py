import openai
from openai import OpenAI
import os
import shutil
import json

from packaging import version


required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

file_details = []

if current_version < required_version:
  raise ValueError(
      f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
  )
else:
  print("OpenAI version is compatible.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

assistant_file_path = 'assistant.json'

# If there is an assistant.json file already, then load that assistant
if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
        assistant_data = json.load(file)
        assistant_id = assistant_data['assistant_id']
        print("Got assistant id...", assistant_id)


files = client.beta.assistants.files.list(assistant_id=assistant_id)

for file in files:
    file_details.append(client.files.retrieve(file_id=file.id))
    client.files.delete(file_id=file.id)
    print("Removed remote file:", file_details[-1].filename)

assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
client.beta.assistants.delete(assistant_id=assistant_id)
print("Removed an assistant:", assistant.name)

def clear_local_files():
    user_input = input("Want to clear local files? [all/config file/no] ")

    if user_input.lower() == "a":
        try:
            print("Clearing all local files...")
            for file in file_details:
                os.remove(file.filename)
                print("Removed local file:", file.filename)
            print("Clearing config file...")
            os.remove(assistant_file_path)
            shutil.rmtree("__pycache__")
            print("Removed assistant.json")
        except:
            pass
    elif user_input.lower() == "c":
        try:
            print("Clearing config file...")
            os.remove(assistant_file_path)
            print("Removed assistant.json")
            shutil.rmtree("__pycache__")
        except:
            pass
    elif user_input.lower() == "n":
        print("Doing nothing...")
    else:
        print("Invalid input. Please enter a, c, or n.")
        clear_local_files()

    return

clear_local_files()