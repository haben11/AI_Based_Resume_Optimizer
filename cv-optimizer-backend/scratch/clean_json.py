import json

# PASTE YOUR DIRTY TEXT HERE
text = """
PASTE THE JOB DESCRIPTION HERE
"""

# This cleans and escapes the text for JSON
clean_text = json.dumps(text.strip())
print("--- CLEANED JSON STRING ---")
print(clean_text)
print("---------------------------")
