"""
Microsoft Graph API Service for sending emails on behalf of users.
Handles authentication, user context, and secure email sending.
"""

import json
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class GraphAPIService:
    """
    Service for Microsoft Graph API operations including on-behalf-of email sending.
    """
    
    def __init__(self):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        self.tenant_id = settings.azure_tenant_id
        
    async def send_email_on_behalf(
        self,
        user_access_token: str,
        user_email: str,
        user_name: str,
        recipient_email: str,
        subject: str,
        body: str,
        body_type: str = "HTML"
    ) -> Dict[str, Any]:
        """
        Send email on behalf of the authenticated user using Microsoft Graph API.
        
        Args:
            user_access_token: User's access token (obtained during Teams auth)
            user_email: User's email address
            user_name: User's display name
            recipient_email: Recipient's email address
            subject: Email subject
            body: Email body content
            body_type: "HTML" or "Text"
            
        Returns:
            Dict containing send result and metadata
        """
        try:
            # Construct the email message
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": body_type,
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": recipient_email,
                                "name": recipient_email.split("@")[0].title()
                            }
                        }
                    ],
                    "from": {
                        "emailAddress": {
                            "address": user_email,
                            "name": user_name
                        }
                    }
                }
            }
            
            # Send the email using Graph API
            headers = {
                "Authorization": f"Bearer {user_access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/me/sendMail",
                    headers=headers,
                    json=message,
                    timeout=30.0
                )
                
                if response.status_code == 202:  # Accepted - Email queued for delivery
                    sent_timestamp = datetime.utcnow()
                    logger.info(f"✅ Email sent successfully from {user_email} to {recipient_email}")
                    
                    # Enhanced confirmation with detailed feedback
                    return {
                        "success": True,
                        "status": "sent",
                        "message": f"✅ Email sent successfully from {user_email} to {recipient_email}",
                        "confirmation": {
                            "sent_at": sent_timestamp.isoformat(),
                            "sent_at_readable": sent_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "from_email": user_email,
                            "from_name": user_name,
                            "to_email": recipient_email,
                            "subject": subject,
                            "method": "Microsoft Graph API",
                            "status_code": response.status_code,
                            "delivery_status": "Queued for delivery by Microsoft Exchange"
                        },
                        "user_feedback": f"Your email '{subject}' has been successfully sent to {recipient_email} via Microsoft Outlook. The message has been queued for delivery by Microsoft Exchange and should arrive shortly."
                    }
                elif response.status_code == 200:  # OK - Alternative success response
                    sent_timestamp = datetime.utcnow()
                    logger.info(f"✅ Email sent successfully from {user_email} to {recipient_email}")
                    
                    return {
                        "success": True,
                        "status": "sent",
                        "message": f"✅ Email sent successfully from {user_email} to {recipient_email}",
                        "confirmation": {
                            "sent_at": sent_timestamp.isoformat(),
                            "sent_at_readable": sent_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "from_email": user_email,
                            "from_name": user_name,
                            "to_email": recipient_email,
                            "subject": subject,
                            "method": "Microsoft Graph API",
                            "status_code": response.status_code,
                            "delivery_status": "Successfully processed by Microsoft Exchange"
                        },
                        "user_feedback": f"Your email '{subject}' has been successfully sent to {recipient_email} via Microsoft Outlook. The message has been processed by Microsoft Exchange and should arrive shortly."
                    }
                else:
                    # Enhanced error handling with detailed feedback
                    error_detail = response.text
                    logger.error(f"❌ Failed to send email: {response.status_code} - {error_detail}")
                    
                    # Parse error details if available
                    error_message = "Unknown error occurred"
                    try:
                        if error_detail:
                            error_json = json.loads(error_detail)
                            error_message = error_json.get("error", {}).get("message", error_detail)
                    except:
                        error_message = error_detail or "No error details provided"
                    
                    return {
                        "success": False,
                        "status": "failed",
                        "error": f"Microsoft Graph API error: {response.status_code}",
                        "error_details": {
                            "status_code": response.status_code,
                            "error_message": error_message,
                            "attempted_from": user_email,
                            "attempted_to": recipient_email,
                            "subject": subject,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        "user_feedback": f"❌ Failed to send email to {recipient_email}. Error: {error_message}. Please check your permissions and try again, or contact support if the issue persists."
                    }
                    
        except Exception as e:
            logger.error(f"Exception sending email: {str(e)}")
            return {
                "success": False,
                "error": "Exception occurred while sending email",
                "detail": str(e)
            }
    
    async def get_user_profile(self, user_access_token: str) -> Dict[str, Any]:
        """
        Get user profile information from Microsoft Graph.
        
        Args:
            user_access_token: User's access token
            
        Returns:
            Dict containing user profile information
        """
        try:
            headers = {
                "Authorization": f"Bearer {user_access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "success": True,
                        "user": {
                            "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                            "name": user_data.get("displayName"),
                            "id": user_data.get("id"),
                            "job_title": user_data.get("jobTitle"),
                            "department": user_data.get("department")
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to get user profile: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Exception getting user profile: {str(e)}")
            return {
                "success": False,
                "error": "Exception occurred while getting user profile",
                "detail": str(e)
            }
    
    async def validate_access_token(self, user_access_token: str) -> bool:
        """
        Validate if the access token is still valid.
        
        Args:
            user_access_token: User's access token
            
        Returns:
            Boolean indicating if token is valid
        """
        try:
            headers = {
                "Authorization": f"Bearer {user_access_token}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    headers=headers,
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except Exception:
            return False


# Global instance
graph_service = GraphAPIService()
