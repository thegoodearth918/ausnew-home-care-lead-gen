import openai
from openai import OpenAI
import os
import shutil
import json

from packaging import version


required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# ft:gpt-3.5-turbo-1106:personal::8OYe4qu5


if current_version < required_version:
  raise ValueError(
      f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
  )
else:
  print("OpenAI version is compatible.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


client.models.delete(
    model="ft:gpt-3.5-turbo-1106:personal::8OYe4qu5"
)