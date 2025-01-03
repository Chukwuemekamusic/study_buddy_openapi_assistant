# app.py
import streamlit as st
from pathlib import Path
from assistantClass import AssistantManager

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "manager" not in st.session_state:
        st.session_state.manager = AssistantManager()
    if "start_chat" not in st.session_state:
        st.session_state.start_chat = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

def handle_file_upload():
    """Handle file upload and processing"""
    uploaded_file = st.sidebar.file_uploader(
        "Upload a file",
        type=["pdf", "docx", "txt", "md"],
        key="file_upload"
    )
    
    if st.sidebar.button("Upload File") and uploaded_file:
        try:
            file_path = Path(uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            file_id = st.session_state.manager.upload_file_openai(str(file_path))
            st.sidebar.success(f"File uploaded successfully")
            
            # Clean up temporary file
            file_path.unlink()
            return file_id
            
        except Exception as e:
            st.sidebar.error(f"Upload failed: {str(e)}")

def display_file_list():
    """Display list of uploaded files"""
    files = st.session_state.manager.get_file_names_and_ids()
    if files:
        st.sidebar.subheader("Uploaded Files:")
        for filename, file_id in files:
            st.sidebar.write(f"{filename}:<br>&emsp;{file_id}", unsafe_allow_html=True)

def initialize_chat():
    """Initialize chat session"""
    if st.sidebar.button("Start Chatting"):
        if st.session_state.manager.files_list:
            st.session_state.start_chat = True
            if not st.session_state.manager.assistant:
                st.session_state.manager.create_assistant()
        else:
            st.sidebar.warning("Please upload at least one file first")

def main():
    """Main application logic"""
    st.set_page_config(page_title="Study Buddy", page_icon=":books:")
    initialize_session_state()
    
    st.title("Study Buddy")
    st.write("Learn fast by chatting with your files")
    
    # Sidebar components
    file_id = handle_file_upload()
    display_file_list()
    initialize_chat()
    
    if not st.session_state.start_chat:
        st.write("Please upload a file and click 'Start Chatting' to begin")
        return
        
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle new messages
    if prompt := st.chat_input("Ask a question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.manager.process_chat(prompt)
                if response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    with st.chat_message("assistant"):
                        st.markdown(response)
                else:
                    st.error("Failed to generate response")
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()