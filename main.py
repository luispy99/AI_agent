import os
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.call_function import call_function


load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

model_name = "gemini-2.0-flash-001"

if len(sys.argv) < 2:
    print("No hay ningún texto al que responder")
    sys.exit(1)

args = sys.argv[1:]
verbose = False

if "--verbose" in args:
    args.remove("--verbose")
    verbose = True

schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Reads the contents of a file, with a limit of 10000 characters.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path of the file",
            ),
        },
    ),
)

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a designated python file.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path of the python file",
            ),
        },
    ),
)

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Overwrites the contents of a file or creates it if it doesn't exist.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path of the file",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The string that must be written into the file"
            ),
        },
    ),
)


available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file, 
        schema_write_file,
    ]
)

user_prompt = " ".join(args)

MAX_ITERATIONS = 20

messages = [
    types.Content(role="user", parts=[types.Part(text=user_prompt)])
]

system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""
for iteration in range(MAX_ITERATIONS):
    response = client.models.generate_content(
        model=model_name,
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[available_functions],
            system_instruction=system_prompt
        ),
    )

    for candidate in response.candidates:
        if candidate.content:
            messages.append(candidate.content)

    if response.function_calls:
        for function_call_part in response.function_calls:
            function_call_result = call_function(function_call_part, verbose)

            messages.append(function_call_result)

            if verbose:
                try:
                    print(f"-> {function_call_result.parts[0].function_response.response}")
                except AttributeError:
                    raise RuntimeError("Invalid function response format from LLM")
        continue

    print(f"Gemini: {response.text}")

    if verbose and hasattr(response, "usage_metadata"):
        usage = response.usage_metadata
        print()
        print(f"User prompt: {user_prompt}")
        print(f"Prompt tokens: {usage.prompt_token_count}")
        print(f"Response tokens: {usage.candidates_token_count}")
    break
else:
    print("❗ Agent hit max iterations (possible infinite loop)")
