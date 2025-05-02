import json
from openai import OpenAI
client = OpenAI()



def convert_py_to_json(filename):
    """
    Converts a Python file to a JSON file with keys: file_name and content.
    Saves the result in Input_files.
    Returns the JSON file path.
    """

    with open(filename, "r") as f: 
        code_content = f.read()

    code_json = {
        "file_name": filename,
        "content": code_content
    }

    json_str = json.dumps(code_json, indent=2)

    with open(filename + ".json", "w") as f:
        f.write(json_str)

    return filename

def create_file(client, file_path):
    """
    Creates a File to be uploaded to the vector store 
    Returns the File ID
    """
    # Handle local file path
    with open(file_path, "rb") as file_content:
        result = client.files.create(
            file=file_content,
            purpose="assistants"
        )
        
    print(f"Uploaded {file_path} -> file ID: {result.id}")
    return result.id

import time

def wait_until_files_uploaded(vector_store_id, client, poll_interval=2):
    """
    Accounts for asynchronous file upload 
    Waits until all files in the vector store are uploaded and ready for use.
    """
    print("Waiting for all files to finish uploading...")

    while True:
        files_response = client.vector_stores.files.list(vector_store_id=vector_store_id)
        all_done = True

        for file_ref in files_response.data:
            status = file_ref.status
            print(f"{file_ref.id}: {status}")
            if status != "completed":
                all_done = False

        if all_done:
            print("All files are ready and are being processed...")
            break

        time.sleep(poll_interval)



# Upload 3 Python test functions: buggy, needs improvement, and good

#calculate_average.py | HAS BUGS
#   BUG: typo in 'number'
#   BUG: Why add 1? Logically incorrect
avg_fpath = convert_py_to_json("./Input_files/calculate_average.py")
avg_file_id = create_file(client, avg_fpath)

#reverse_string.py | NEEDS IMPROVEMENT
#   NOTE: Slow for long strings (due to string concatenation inside loop)
#   NOTE: Can be simplified using slicing
revStr_fpath = convert_py_to_json("./Input_files/reverse_string.py")
revStr_file_id = create_file(client, revStr_fpath)

#is_prime.py | GOOD
prime_fpath = convert_py_to_json("./Input_files/is_prime.py")
prime_file_id = create_file(client, prime_fpath)


#Create Vector Store
vector_store = client.vector_stores.create(
    name="Python Functions"
)

client.vector_stores.file_batches.create(
    vector_store_id = vector_store.id,
    file_ids = [avg_file_id, revStr_file_id, prime_file_id]
)

# Wait until all files are ready
wait_until_files_uploaded(vector_store.id, client)

#Get OpenAI Response
response = client.responses.create(
    model="gpt-4o",
    input=
        "You are a code reviewer. Analyze ALL of the following Python functions in the attached files. For each function, return:\n\n 1. A brief quality summary.\n 2. Line-specific comments for any issues.\n 3. A quality rating: (Good: If function is efficiently implemented) / (Needs Improvement: If function is inefficient and can be Improved ) / (Buggy: If function contains any bugs).\n\n ",
    tools=[{
        "type": "file_search",
        "vector_store_ids": [vector_store.id]
    }]
)

#Output AI Response to output.txt
review_text = response.output[1].content[0].text
with open("output.txt", "w") as f:
    print("Output File Successfully Created")
    f.write(review_text)




