"""
Communication Agent for drafting and sending professional messages.
Supports email drafting, Teams messages, and other communications.
"""

from typing import Dict, Any, List, Optional
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .base_agent import BaseAgent, AgentState, AgentResponse
from ..config import settings


class CommunicationAgent(BaseAgent):
    """
    Specialized agent for handling communication tasks including:
    - Drafting professional emails
    - Creating Teams messages
    - Formatting communications based on context
    """
    
    def __init__(self):
        super().__init__("communication_agent", "Professional Communication Agent")
        self.llm = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize Azure OpenAI model for communication generation"""
        try:
            from langchain_openai import AzureChatOpenAI
            
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_chat_endpoint,
                api_key=settings.azure_openai_chat_key,
                deployment_name=settings.azure_openai_chat_deployment,
                api_version=settings.azure_openai_api_version,
                temperature=0.3,  # Slightly higher for more natural communication
            )
        except Exception as e:
            print(f"Error initializing Communication agent models: {e}")
            raise
    
    async def process(self, state: AgentState) -> AgentResponse:
        """
        Process communication requests including drafting and sending messages.
        
        Args:
            state: AgentState containing communication parameters
            
        Returns:
            AgentResponse with drafted message or send confirmation
        """
        try:
            if not self.validate_input(state):
                return self.create_response(
                    state.task_id, False, error="Invalid input state"
                )
            
            action = state.data.get("action", "draft")
            
            if action == "draft":
                return await self._draft_communication(state)
            elif action == "send":
                return await self._send_communication(state)
            else:
                return self.create_response(
                    state.task_id, False, 
                    error=f"Unknown communication action: {action}"
                )
                
        except Exception as e:
            return self.create_response(
                state.task_id, False, 
                error=f"Error processing communication: {str(e)}"
            )
    
    async def _draft_communication(self, state: AgentState) -> AgentResponse:
        """Draft a professional communication"""
        context = state.data.get("context", "")
        recipient = state.data.get("recipient", "")
        request = state.data.get("request", "")
        communication_type = state.data.get("type", "email")
        
        if not all([context, recipient, request]):
            return self.create_response(
                state.task_id, False,
                error="Missing required fields: context, recipient, and request"
            )
        
        # Select appropriate template based on communication type
        if communication_type.lower() == "teams":
            template = self._get_teams_template()
        else:
            template = self._get_email_template()
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "recipient", "request"]
        )
        
        draft_chain = prompt | self.llm | StrOutputParser()
        
        try:
            draft = draft_chain.invoke({
                "context": context,
                "recipient": recipient,
                "request": request
            })
            
            response_data = {
                "draft": draft,
                "recipient": recipient,
                "type": communication_type,
                "requires_approval": True,
                "metadata": {
                    "context": context,
                    "request": request
                }
            }
            
            return self.create_response(
                state.task_id, True, response_data,
                f"Successfully drafted {communication_type} for {recipient}"
            )
            
        except Exception as e:
            return self.create_response(
                state.task_id, False,
                error=f"Error generating draft: {str(e)}"
            )
    
    async def _send_communication(self, state: AgentState) -> AgentResponse:
        """Send a communication (simulated - requires HITL approval)"""
        draft = state.data.get("draft", "")
        recipient = state.data.get("recipient", "")
        approved = state.data.get("approved", False)
        
        if not draft:
            return self.create_response(
                state.task_id, False,
                error="No draft provided for sending"
            )
        
        if not approved:
            return self.create_response(
                state.task_id, False,
                error="Communication not approved for sending"
            )
        
        # Simulate sending (in production, this would integrate with MS Graph API)
        print(f"\n---COMMUNICATION AGENT: SENDING MESSAGE---")
        print(f"To: {recipient}")
        print(f"Message:\n{draft}")
        print("---MESSAGE SENT (SIMULATED)---\n")
        
        response_data = {
            "sent": True,
            "recipient": recipient,
            "draft": draft,
            "timestamp": "simulated_timestamp",
            "message": "Message sent successfully (simulated)"
        }
        
        return self.create_response(
            state.task_id, True, response_data,
            f"Message sent successfully to {recipient}"
        )
    
    def _get_email_template(self) -> str:
        """Get email drafting template"""
        return """Draft a professional email based on the provided context and request.

Context: {context}
Recipient: {recipient}
Request: {request}

Please draft a professional email that:
1. Has an appropriate subject line
2. Uses professional but friendly tone
3. Is clear and concise
4. Includes all necessary information from the context
5. Has a proper closing

Format as:
Subject: [Subject Line]

Dear [Recipient],

[Email Body]

Best regards,
[Your Name]
Procurement Department
University of Washington

Draft:"""
    
    def _get_teams_template(self) -> str:
        """Get Teams message drafting template"""
        return """Draft a professional Teams message based on the provided context and request.

Context: {context}
Recipient: {recipient}
Request: {request}

Please draft a Teams message that:
1. Is concise and direct
2. Uses appropriate Teams formatting (markdown if needed)
3. Is professional but conversational
4. Includes all necessary information from the context
5. Has a clear call-to-action if needed

Draft:"""
    
    def get_capabilities(self) -> List[str]:
        """Return capabilities of the Communication agent"""
        return [
            "email_drafting",
            "teams_messaging",
            "professional_communication",
            "message_formatting",
            "communication_sending"
        ]
    
    def create_draft_request(self, context: str, recipient: str, request: str, 
                           communication_type: str = "email") -> AgentState:
        """Helper method to create a draft request state"""
        return AgentState(
            agent_id=self.agent_id,
            task_id="draft_request",
            data={
                "action": "draft",
                "context": context,
                "recipient": recipient,
                "request": request,
                "type": communication_type
            }
        )
    
    def create_send_request(self, draft: str, recipient: str, approved: bool = False) -> AgentState:
        """Helper method to create a send request state"""
        return AgentState(
            agent_id=self.agent_id,
            task_id="send_request",
            data={
                "action": "send",
                "draft": draft,
                "recipient": recipient,
                "approved": approved
            }
        )
