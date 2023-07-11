import subprocess

# Get the uploaded file name from the command-line argument
import sys

if len(sys.argv) > 1:
    filename = sys.argv[1]

    # Execute the pymusiclooper.py script with the specified command
    command = f"python pymusiclooper.py {filename} --export"
    subprocess.run(command, shell=True)
