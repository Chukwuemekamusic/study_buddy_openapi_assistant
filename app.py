import streamlit as st
from assistantClass import AssistantManager
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if "manager" not in st.session_state:
    st.session_state.manager = AssistantManager()

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "messages" not in st.session_state:
    st.session_state.messages = []



# st.title("Study Buddy")
st.set_page_config(page_title="Study Buddy", page_icon=":books:")


# ==== Sidebar - where users can upload files ====
file_uploaded = st.sidebar.file_uploader("Upload a file", type=["pdf", "docx", "txt"], key="file_upload")

# upload file button - store file id

if st.sidebar.button("Upload File"):
    if file_uploaded is not None:
        with open(f"{file_uploaded.name}", "wb") as file:
            file.write(file_uploaded.getbuffer())
        file_id = st.session_state.manager.upload_file(f"{file_uploaded.name}")
        # st.session_state.manager.files_list.append(file_id)
        st.sidebar.success(f"File uploaded: {file_id}")
        
        # st.sidebar.write(f"File ID: {file_id}")
    else:
        st.sidebar.error("Please upload a file")
 
# retrieve file ids
st.session_state.manager.get_file_names_and_ids()

# Display uploaded files
if st.session_state.manager.files_list:
    st.sidebar.write("Uploaded Files IDs:")
    for file_name, file_id in st.session_state.manager.files_list:
        st.sidebar.write(f"{file_name}:<br>&emsp;{file_id}", unsafe_allow_html=True)
        # associate file id with assistant
        st.session_state.manager.associate_file_with_assistant(file_id)


# ==== Main content - where users can chat with the assistant ====
# Button to initiate the chat session
if st.sidebar.button("Start Chatting..."):
    if st.session_state.manager.files_list:
        st.session_state.start_chat = True

        # Create a new thread for this chat session
        chat_thread_id = st.session_state.manager.create_thread()
        st.write("Thread ID:", chat_thread_id)
    else:
        st.sidebar.warning(
            "No files found. Please upload at least one file to get started."
        )
    
# main interface
st.title("Study Buddy")
st.write("Learn fast by chatting with your files")

if not st.session_state.start_chat:
    st.write("Please upload a file and click 'Start Chatting...' to get started.")
    
else:
    # show existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
        
    # user input
    if prompt := st.chat_input("Ask a question"):
        # add user message to the messages list and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # add message to existing thread and get response
        with st.spinner("Thinking..."):
            try:
                message = st.session_state.manager.process_chat(prompt)
                if message:
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    with st.chat_message("assistant"):
                        st.markdown(message)
                else:
                    st.error("Failed to generate response. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        
        
