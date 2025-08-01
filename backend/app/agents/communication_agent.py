"""
Communication Agent for drafting and sending professional messages.
Supports email drafting, Teams messages, and other communications.
"""

from typing import Dict, Any, List, Optional
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

from .base_agent import BaseAgent, AgentState, AgentResponse
from ..config import settings
from ..services.graph_api_service import graph_service

logger = logging.getLogger(__name__)


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
        """Send the drafted communication using Microsoft Graph API on-behalf-of user"""
        data = state.data
        draft = data.get("draft", "")
        recipient = data.get("recipient", "")
        approved = data.get("approved", False)
        
        # Critical: Only proceed if explicitly approved
        if not approved:
            return self.create_response(
                state.task_id, False, {},
                "Communication sending requires explicit human approval"
            )
        
        if not draft or not recipient:
            return self.create_response(
                state.task_id, False, {},
                "Missing draft content or recipient information"
            )
        
        # Extract user context (required for on-behalf-of sending)
        user_access_token = data.get("user_access_token")
        user_email = data.get("user_email")
        user_name = data.get("user_name")
        
        if not all([user_access_token, user_email, user_name]):
            logger.warning("Missing user context for on-behalf-of email sending")
            # Fallback to simulation for development/testing
            return await self._simulate_email_sending(draft, recipient, state.task_id)
        
        try:
            # Parse email content (assuming format: Subject: ... \n\n Body...)
            lines = draft.split('\n')
            subject = "Procurement Inquiry"
            body = draft
            
            # Extract subject if present
            if lines and lines[0].startswith("Subject:"):
                subject = lines[0].replace("Subject:", "").strip()
                body = '\n'.join(lines[2:])  # Skip subject and empty line
            
            # Send email using Microsoft Graph API
            result = await graph_service.send_email_on_behalf(
                user_access_token=user_access_token,
                user_email=user_email,
                user_name=user_name,
                recipient_email=recipient,
                subject=subject,
                body=body,
                body_type="HTML"
            )
            
            if result.get("success"):
                logger.info(f"✅ Email sent successfully from {user_email} to {recipient}")
                
                # Extract detailed confirmation from Graph API response
                confirmation = result.get("confirmation", {})
                user_feedback = result.get("user_feedback", f"Email sent successfully to {recipient}")
                
                response_data = {
                    "sent": True,
                    "status": "sent",
                    "recipient": recipient,
                    "subject": subject,
                    "from": user_email,
                    "method": "microsoft_graph_api",
                    "confirmation": confirmation,
                    "user_feedback": user_feedback,
                    "detailed_confirmation": {
                        "delivery_method": "Microsoft Outlook via Graph API",
                        "sent_timestamp": confirmation.get("sent_at_readable", "Just now"),
                        "delivery_status": confirmation.get("delivery_status", "Queued for delivery"),
                        "api_status_code": confirmation.get("status_code", 202)
                    }
                }
                
                # Create user-friendly success message
                success_message = f"✅ **Email Confirmation**\n\n{user_feedback}\n\n**Details:**\n- From: {user_email}\n- To: {recipient}\n- Subject: {subject}\n- Sent: {confirmation.get('sent_at_readable', 'Just now')}\n- Status: {confirmation.get('delivery_status', 'Queued for delivery')}"
                
                return self.create_response(
                    state.task_id, True, response_data,
                    success_message
                )
            else:
                logger.error(f"❌ Failed to send email: {result.get('error')}")
                
                # Extract detailed error information
                error_details = result.get("error_details", {})
                user_feedback = result.get("user_feedback", f"Failed to send email to {recipient}")
                
                # Create user-friendly error message
                error_message = f"❌ **Email Send Failed**\n\n{user_feedback}\n\n**Technical Details:**\n- Status Code: {error_details.get('status_code', 'Unknown')}\n- Error: {error_details.get('error_message', 'Unknown error')}\n- Attempted From: {error_details.get('attempted_from', user_email)}\n- Attempted To: {error_details.get('attempted_to', recipient)}"
                
                return self.create_response(
                    state.task_id, False, {
                        "sent": False,
                        "status": "failed",
                        "error_details": error_details,
                        "user_feedback": user_feedback
                    },
                    error_message
                )
                
        except Exception as e:
            logger.error(f"Exception in email sending: {str(e)}")
            return self.create_response(
                state.task_id, False, {"error": str(e)},
                f"Exception occurred while sending email: {str(e)}"
            )
    
    async def _simulate_email_sending(self, draft: str, recipient: str, task_id: str) -> AgentResponse:
        """Fallback simulation for development/testing when user context is missing"""
        logger.info("Simulating email sending (missing user context for Graph API)")
        print(f"\n---COMMUNICATION AGENT: SIMULATING EMAIL SEND---")
        print(f"To: {recipient}")
        print(f"Message:\n{draft}")
        print("---EMAIL SIMULATED (Missing user context for Graph API)---\n")
        
        response_data = {
            "sent": True,
            "recipient": recipient,
            "draft": draft,
            "method": "simulation",
            "note": "Simulated - missing user context for Graph API"
        }
        
        return self.create_response(
            task_id, True, response_data,
            f"Email simulated to {recipient} (missing user context for Graph API)"
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
