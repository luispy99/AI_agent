import os
import subprocess
import sys

def run_python_file(working_directory, file_path):
    try:
        abs_working_dir = os.path.abspath(working_directory)

        if not os.path.isabs(file_path):
            temp_file_path = os.path.join(working_directory, file_path)

        abs_file_path = os.path.abspath(temp_file_path)
        
        if not abs_file_path.startswith(abs_working_dir):
                return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
        
        if not file_path.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file.'
        
        if not os.path.exists(abs_file_path):
            return f'Error: File "{file_path}" not found.'
        
        result = subprocess.run([sys.executable, abs_file_path], cwd=abs_working_dir, capture_output=True, text=True, timeout=30)
        output = ""

        if result.stdout:
            output += f"STDOUT:\n{result.stdout}"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}"
        if result.returncode:
            output += f"\nProcess exited with code {result.returncode}"
        
        if not output.strip():
            return "No output produced."
        
        return output.strip()

    except Exception as e:
        return f"Error: executing Python file: {e}"
