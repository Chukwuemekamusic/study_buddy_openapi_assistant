import os
from openai import OpenAI
from utils import wait_for_run_to_complete


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

model = "gpt-4o-mini"

# ==== Step 1: Upload file to OpenAI embeddings =====

file_path = "./Cryptocurrency.pdf"
# file_path = os.path.join(os.path.dirname(__file__), "Cryptocurrency.pdf")


file_obj = client.files.create(
    file=open(file_path, "rb"), 
    purpose="assistants"
    )

print("File ID: ", file_obj.id)

assistant = client.beta.assistants.create(
    name="Study Buddy",
    instructions="""You are a helpful study assistant who knows a lot about understanding research papers.
    Your role is to summarize papers, clarify terminology within context, and extract key figures and data.
    Cross-reference information for additional insights and answer related questions comprehensively.
    Analyze the papers, noting strengths and limitations.
    Respond to queries effectively, incorporating feedback to enhance your accuracy.
    Handle data securely and update your knowledge base with the latest research.
    Adhere to ethical standards, respect intellectual property, and provide users with guidance on any limitations.
    Maintain a feedback loop for continuous improvement and user support.
    Your ultimate goal is to facilitate a deeper understanding of complex scientific material, making it more accessible and comprehensible.""",
    tools=[{"type": "code_interpreter"}],
    model=model,
    tool_resources={
        "code_interpreter": {
            "file_ids": [file_obj.id]
        }
    }
)

# ==== Get the assistant ID ====

assistant_id = assistant.id

print("Assistant ID: ", assistant_id)

# ==== Step 2: Create a thread ====
message = "What is mining?"

thread = client.beta.threads.create()
thread_id = thread.id
print("Thread ID: ", thread_id)

message = client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content=message
)

# ==== Step 3 Run the assistant ====

run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions="Please address the user as Bon."
)

run_id = run.id

print(run_id)

# ==== Step 4: Wait for the run to complete ====

wait_for_run_to_complete(run_id, client, thread_id)

run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run_id)
print("Run Steps: ", run_steps.data[0].step_details)


# Hardcoded ids
# File ID:  file-Swcq9eBJtF9nSAekBMukf9
# Assistant ID:  asst_fimwKQZMT8ZaFhlGogPIJ68Y
# Thread ID:  thread_D6zoPtLj4NZPEHFPX9s1iPPv