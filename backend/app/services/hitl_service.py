"""
Human-in-the-Loop (HITL) Service for managing approval workflows.
Handles interrupts, approval requests, and workflow resumption.
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum


class ApprovalStatus(str, Enum):
    """Status of approval requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    """Model for approval requests"""
    approval_id: str
    user_id: str
    conversation_id: str
    action_type: str
    action_data: Dict[str, Any]
    message: str
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    response_data: Optional[Dict[str, Any]] = None


class HITLService:
    """
    Service for managing Human-in-the-Loop approval workflows.
    Handles approval requests, timeouts, and workflow resumption.
    """
    
    def __init__(self, default_timeout_minutes: int = 30):
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.default_timeout_minutes = default_timeout_minutes
    
    def create_approval_request(self, user_id: str, conversation_id: str, 
                              action_type: str, action_data: Dict[str, Any],
                              message: str, timeout_minutes: Optional[int] = None) -> str:
        """
        Create a new approval request.
        
        Args:
            user_id: ID of the user who needs to approve
            conversation_id: ID of the conversation
            action_type: Type of action requiring approval
            action_data: Data for the action to be approved
            message: Human-readable message describing the action
            timeout_minutes: Minutes until request expires
            
        Returns:
            approval_id: Unique ID for the approval request
        """
        approval_id = str(uuid.uuid4())
        timeout = timeout_minutes or self.default_timeout_minutes
        
        request = ApprovalRequest(
            approval_id=approval_id,
            user_id=user_id,
            conversation_id=conversation_id,
            action_type=action_type,
            action_data=action_data,
            message=message,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=timeout)
        )
        
        self.pending_approvals[approval_id] = request
        return approval_id
    
    def get_approval_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID"""
        request = self.pending_approvals.get(approval_id)
        if request and self._is_expired(request):
            request.status = ApprovalStatus.EXPIRED
        return request
    
    def approve_request(self, approval_id: str, user_id: str, 
                       response_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Approve a pending request.
        
        Args:
            approval_id: ID of the approval request
            user_id: ID of the user approving (must match request)
            response_data: Optional additional data from user
            
        Returns:
            bool: True if approved successfully, False otherwise
        """
        request = self.pending_approvals.get(approval_id)
        if not request:
            return False
        
        if request.user_id != user_id:
            return False
        
        if self._is_expired(request):
            request.status = ApprovalStatus.EXPIRED
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.response_data = response_data or {}
        return True
    
    def reject_request(self, approval_id: str, user_id: str,
                      reason: Optional[str] = None) -> bool:
        """
        Reject a pending request.
        
        Args:
            approval_id: ID of the approval request
            user_id: ID of the user rejecting (must match request)
            reason: Optional reason for rejection
            
        Returns:
            bool: True if rejected successfully, False otherwise
        """
        request = self.pending_approvals.get(approval_id)
        if not request:
            return False
        
        if request.user_id != user_id:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.response_data = {"reason": reason} if reason else {}
        return True
    
    def get_pending_approvals(self, user_id: str, 
                            conversation_id: Optional[str] = None) -> List[ApprovalRequest]:
        """
        Get all pending approval requests for a user.
        
        Args:
            user_id: ID of the user
            conversation_id: Optional filter by conversation
            
        Returns:
            List of pending approval requests
        """
        pending = []
        for request in self.pending_approvals.values():
            if request.user_id != user_id:
                continue
            
            if conversation_id and request.conversation_id != conversation_id:
                continue
            
            if self._is_expired(request):
                request.status = ApprovalStatus.EXPIRED
                continue
            
            if request.status == ApprovalStatus.PENDING:
                pending.append(request)
        
        return pending
    
    def cleanup_expired_requests(self) -> int:
        """
        Clean up expired approval requests.
        
        Returns:
            Number of requests cleaned up
        """
        expired_ids = []
        for approval_id, request in self.pending_approvals.items():
            if self._is_expired(request):
                request.status = ApprovalStatus.EXPIRED
                expired_ids.append(approval_id)
        
        for approval_id in expired_ids:
            del self.pending_approvals[approval_id]
        
        return len(expired_ids)
    
    def _is_expired(self, request: ApprovalRequest) -> bool:
        """Check if a request has expired"""
        return datetime.now() > request.expires_at
    
    def create_communication_approval(self, user_id: str, conversation_id: str,
                                    draft: str, recipient: str) -> str:
        """
        Create an approval request specifically for sending communications.
        
        Args:
            user_id: ID of the user who needs to approve
            conversation_id: ID of the conversation
            draft: The draft message to be sent
            recipient: The recipient of the message
            
        Returns:
            approval_id: Unique ID for the approval request
        """
        action_data = {
            "draft": draft,
            "recipient": recipient,
            "action": "send_communication"
        }
        
        message = f"Please review and approve sending this message to {recipient}:\n\n{draft[:200]}..."
        
        return self.create_approval_request(
            user_id=user_id,
            conversation_id=conversation_id,
            action_type="send_communication",
            action_data=action_data,
            message=message
        )
    
    def create_teams_approval_card(self, approval_request: ApprovalRequest) -> Dict[str, Any]:
        """
        Create a Teams Adaptive Card for approval requests.
        
        Args:
            approval_request: The approval request to create a card for
            
        Returns:
            Dict containing the Adaptive Card JSON
        """
        if approval_request.action_type == "send_communication":
            return self._create_communication_approval_card(approval_request)
        else:
            return self._create_generic_approval_card(approval_request)
    
    def _create_communication_approval_card(self, request: ApprovalRequest) -> Dict[str, Any]:
        """Create approval card for communication sending"""
        draft = request.action_data.get("draft", "")
        recipient = request.action_data.get("recipient", "Unknown")
        
        card = {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🔔 Approval Required",
                    "weight": "Bolder",
                    "size": "Medium",
                    "color": "Attention"
                },
                {
                    "type": "TextBlock",
                    "text": f"Ready to send message to: **{recipient}**",
                    "wrap": True,
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": "Message Preview:",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": draft,
                            "wrap": True,
                            "size": "Small"
                        }
                    ]
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Approval ID:",
                            "value": request.approval_id[:8] + "..."
                        },
                        {
                            "title": "Expires:",
                            "value": request.expires_at.strftime("%H:%M")
                        }
                    ],
                    "spacing": "Medium"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "✅ Approve & Send",
                    "style": "positive",
                    "data": {
                        "action": "approve",
                        "approval_id": request.approval_id
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Reject",
                    "style": "destructive",
                    "data": {
                        "action": "reject",
                        "approval_id": request.approval_id
                    }
                }
            ]
        }
        
        return card
    
    def _create_generic_approval_card(self, request: ApprovalRequest) -> Dict[str, Any]:
        """Create generic approval card for other actions"""
        card = {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🔔 Approval Required",
                    "weight": "Bolder",
                    "size": "Medium",
                    "color": "Attention"
                },
                {
                    "type": "TextBlock",
                    "text": request.message,
                    "wrap": True,
                    "spacing": "Medium"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Action Type:",
                            "value": request.action_type
                        },
                        {
                            "title": "Approval ID:",
                            "value": request.approval_id[:8] + "..."
                        },
                        {
                            "title": "Expires:",
                            "value": request.expires_at.strftime("%H:%M")
                        }
                    ],
                    "spacing": "Medium"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "✅ Approve",
                    "style": "positive",
                    "data": {
                        "action": "approve",
                        "approval_id": request.approval_id
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Reject",
                    "style": "destructive",
                    "data": {
                        "action": "reject",
                        "approval_id": request.approval_id
                    }
                }
            ]
        }
        
        return card


# Global HITL service instance
hitl_service = HITLService()
