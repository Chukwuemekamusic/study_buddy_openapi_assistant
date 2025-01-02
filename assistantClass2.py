import time
from openai import OpenAI
import os
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from pathlib import Path



@dataclass
class Citation:
    """Represents a citation with its metadata"""
    index: int
    text: str
    quote: Optional[str] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None

class AssistantManager:
    
    def __init__(self, model = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.file_id = None
        self.assistant = None
        self.thread = None
        self.run = None
        self.response = None
        
        self.ASSISTANT_CONFIG = {
            "name": "Study Buddy",
            "instructions": """You are a helpful study assistant who knows a lot about understanding research papers.
            Your role is to summarize papers, clarify terminology within context, and extract key figures and data.
            Cross-reference information for additional insights and answer related questions comprehensively.
            Analyze the papers, noting strengths and limitations.
            Respond to queries effectively, incorporating feedback to enhance your accuracy.
            Handle data securely and update your knowledge base with the latest research.
            Adhere to ethical standards, respect intellectual property, and provide users with guidance on any limitations.
            Maintain a feedback loop for continuous improvement and user support.
            Your ultimate goal is to facilitate a deeper understanding of complex scientific material, making it more accessible and comprehensible.""",
            "run_instructions": """Please answer the questions using the knowledge provided in the files.
            when adding additional information, make sure to distinguish it with bold or underlined text.""",
            "tools":[{
                    "type": "code_interpreter"
                }],
            "tool_resources": {
                "code_interpreter": {
                    "file_ids": [self.file_id]
                }
            }
        }
       
    
    def upload_file_openai(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, "rb") as file:
                file_obj = self.client.files.create(
                    file=file.read(),
                    purpose="assistants"
                )
            self.file_id = file_obj.id
            logging.info(f"File created: {file_obj.id}")
            return file_obj.id
        except Exception as e:
            logging.error(f"Error uploading file: {str(e)}")
            raise
    
    def upload_file_openai_2(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            file_obj = self.client.files.create(
                file=open(file_path, "rb"), 
                purpose="assistants"
            )
            self.file_id = file_obj.id
            logging.info(f"File created: {file_obj.id}")
            return file_obj.id
        except Exception as e:
            logging.error(f"Error uploading file: {str(e)}")
            raise
     
    def create_assistant(self, file_id: str = None, custom_config: Dict = None):
        """Creates an OpenAI assistant with given or default configuration."""
        file_id = file_id or self.file_id
        if self.assistant is None:
            try:
                config = custom_config or self.ASSISTANT_CONFIG
                self.assistant = self.client.beta.assistants.create(
                    name=config["name"],
                    instructions=config["instructions"],
                    tools=config["tools"],
                    model=self.model,
                    tool_resources= {
                "code_interpreter": {
                    "file_ids": [file_id]
                }
            }
                )
                logging.info(f"Assistant created: {self.assistant.id}")
                
            except Exception as e:
                logging.error(f"Error creating assistant: {e}")
                raise
        else:
            logging.info(f"Assistant already created: {self.assistant.id}")
    
    def create_thread(self):
        """Creates an OpenAI thread."""
        
        if self.thread is None:
            self.thread = self.client.beta.threads.create()
            logging.info(f"Thread created: {self.thread.id}")
        else:
            logging.info(f"Thread already created: {self.thread.id}")
        
        return self.thread.id
    
    def add_message_to_thread(self, role: str, content: str):
        if self.thread is None:
            self.create_thread()
        try:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )
            logging.info(f"Message added to thread: {content}")
        except Exception as e:
            logging.error(f"Error adding message to thread: {e}")
            raise
        
    def run_assistant(self, custom_instructions: str = None):
        if not self.assistant:
            raise ValueError("Assistant not initialized")
        if not self.thread:
            raise ValueError("Thread not initialized")
        
        try:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=custom_instructions or self.ASSISTANT_CONFIG["run_instructions"]
            )
            logging.info(f"Run created: {self.run.id}")
        except Exception as e:
            logging.error(f"Error running assistant: {e}")
            raise
        
    def process_messages(self):
        """Processes messages from the thread and extracts the response."""
        if not self.thread:
            raise ValueError("Thread not initialized")
        
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread.id
            )
            
            if messages.data:
                last_message = messages.data[0]
                if last_message.role == "assistant" and last_message.content:
                    # self.response = last_message.content[0].text.value
                    self.response = self.process_message_with_citations(last_message)
                    logging.info(f"Response processed from {last_message.role}")
                else:
                    logging.warning("No assistant message or content found")
            else:
                logging.warning("No messages found in thread")
                
        except Exception as e:
            logging.error(f"Error processing messages: {e}")
            raise
    
    def wait_for_completion(self, interval: int = 2, timeout: int = 300) -> None:
        """Wait for the assistant's run to complete with improved error handling."""
        if not (self.thread and self.run):
            raise ValueError("Thread or Run not initialized")
        
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("Assistant run timed out")
            
            time.sleep(interval)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=self.run.id
            )
            if run.status == "completed":
                self.process_messages()
                break
            # elif self.run.status == "requires_action":
            #     self.handle_required_actions(self.run.required_action.submit_tool_outputs.model_dump())
            elif run.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed with status: {run.status}")
    
        
    def associate_file_with_assistant(self, file_id: str):
        """Associates a file with the assistant."""
        if not self.assistant:
            self.create_assistant()
        
        try:
            # Add the file ID to the assistant's tool resources
            self.assistant = self.client.beta.assistants.update(
                self.assistant.id,
                tool_resources={"code_interpreter": {"file_ids": [file_id]}}
            )
            logging.info(f"File ID {file_id} associated with assistant {self.assistant.id}.")
        except Exception as e:
            logging.error(f"Error associating file with assistant: {e}")
            raise

        
    
    def process_message_with_citations(self, message):
        """
        Extract content and annotations from the message and format citations as footnotes.

        Args:
            message: The message object containing content and annotations.

        Returns:
            str: The formatted message content with footnotes.
        """
        try:
            message_content = message.content[0].text
            annotations = (
                message_content.annotations if hasattr(message_content, "annotations") else []
            )
        except AttributeError as e:
            raise ValueError("Invalid message structure. Ensure message has correct attributes.") from e

        citations = []

        for index, annotation in enumerate(annotations):
            footnote_index = index + 1

            # Replace annotation text in the content with a footnote
            if hasattr(message_content, "value"):
                message_content.value = message_content.value.replace(
                    annotation.text, f" [{footnote_index}]"
                )
            else:
                raise ValueError("Message content is missing the 'value' attribute.")

            # Handle file citations
            file_citation = getattr(annotation, "file_citation", None)
            file_path = getattr(annotation, "file_path", None)

            if file_citation:
                cited_file = {"filename": "cryptocurrency.pdf"}  # Replace with actual retrieval logic
                citations.append(
                    f"[{footnote_index}] {file_citation.quote} from {cited_file['filename']}"
                )
            elif file_path:
                cited_file = {"filename": "cryptocurrency.pdf"}  # Replace with actual retrieval logic
                citations.append(
                    f"[{footnote_index}] Click [here](#) to download {cited_file['filename']}"
                )
            else:
                citations.append(f"[{footnote_index}] Citation details not available.")

        formatted_response = message_content.value + "\n\n" + "\n".join(citations)
        return formatted_response
    
    
    def process_chat(self, message: str, custom_instructions: str = None) -> Optional[str]:
        """Process a news summarization request end-to-end."""
        try:
            self.create_thread()
            self.create_assistant()
            self.add_message_to_thread("user", message)
            self.run_assistant(custom_instructions)
            self.wait_for_completion()
            return self.response
        except Exception as e:
            logging.error(f"Error processing news request: {e}")
            return None
        
    
    # ===== 
    def process_message_with_citations(self, message: Any) -> str:
        """
        Process an assistant message to format its citations.
        
        Args:
            message: The message object containing content and annotations
            
        Returns:
            Formatted message content with footnotes
        """
        try:
            content, annotations = self._extract_message_components(message)
            citations = self._process_annotations(content, annotations)
            return self._format_response(content, citations)
        except Exception as e:
            self.logger.error(f"Error processing message with citations: {str(e)}")
            raise

    def _extract_message_components(self, message: Any) -> tuple[Any, List[Any]]:
        """Extract main content and annotations from the message."""
        try:
            message_content = message.content[0].text
            annotations = getattr(message_content, 'annotations', [])
            
            if not hasattr(message_content, 'value'):
                raise ValueError("Message content is missing 'value' attribute")
                
            return message_content, annotations
        except (AttributeError, IndexError) as e:
            raise ValueError(f"Invalid message structure: {str(e)}") from e

    def _process_annotations(self, content: Any, annotations: List[Any]) -> List[Citation]:
        """Process annotations and create citations."""
        citations: List[Citation] = []
        
        for index, annotation in enumerate(annotations, start=1):
            content.value = content.value.replace(
                annotation.text, f" [{index}]"
            )
            
            citation = self._create_citation(index, annotation)
            citations.append(citation)
            
        return citations

    def _create_citation(self, index: int, annotation: Any) -> Citation:
        """Create a Citation object from an annotation."""
        file_citation = getattr(annotation, 'file_citation', None)
        file_path = getattr(annotation, 'file_path', None)
        
        if file_citation:
            file_info = self._get_file_info(file_citation)
            return Citation(
                index=index,
                text=f"[{index}] {file_citation.quote} from {file_info['filename']}",
                quote=file_citation.quote,
                filename=file_info['filename']
            )
        elif file_path:
            file_info = self._get_file_info(file_path)
            return Citation(
                index=index,
                text=f"[{index}] Click [here](#) to download {file_info['filename']}",
                file_path=Path(file_path)
            )
        else:
            return Citation(
                index=index,
                text=f"[{index}] Citation details not available."
            )

    def _get_file_info(self, citation_source: Any) -> Dict[str, str]:
        """Get file information for a citation."""
        try:
            file_id = getattr(citation_source, 'file_id', None)
            if file_id:
                file = self.client.files.retrieve(file_id)
                return {"filename": file.filename}
            return {"filename": "unknown_file"}
        except Exception as e:
            self.logger.error(f"Error retrieving file info: {str(e)}")
            return {"filename": "unknown_file"}

    def _format_response(self, content: Any, citations: List[Citation]) -> str:
        """Format the final response with content and citations."""
        citation_texts = [citation.text for citation in citations]
        return f"{content.value}\n\n{chr(10).join(citation_texts)}"
    
    