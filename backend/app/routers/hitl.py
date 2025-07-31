"""
Human-in-the-Loop (HITL) API routes for approval workflows.
Handles approval requests, Teams integration, and workflow resumption.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..services.hitl_service import hitl_service, ApprovalRequest, ApprovalStatus
from ..agents.agent_tools import tool_manager

router = APIRouter(prefix="/hitl", tags=["hitl", "approvals"])


class ApprovalResponse(BaseModel):
    """Request model for approval responses"""
    approval_id: str
    action: str  # "approve" or "reject"
    user_id: str
    reason: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class ApprovalRequestResponse(BaseModel):
    """Response model for approval requests"""
    approval_id: str
    action_type: str
    message: str
    created_at: datetime
    expires_at: datetime
    status: str
    action_data: Dict[str, Any]


@router.get("/approvals/{user_id}", response_model=List[ApprovalRequestResponse])
async def get_pending_approvals(user_id: str, conversation_id: Optional[str] = None):
    """
    Get all pending approval requests for a user.
    """
    try:
        pending = hitl_service.get_pending_approvals(user_id, conversation_id)
        
        return [
            ApprovalRequestResponse(
                approval_id=req.approval_id,
                action_type=req.action_type,
                message=req.message,
                created_at=req.created_at,
                expires_at=req.expires_at,
                status=req.status.value,
                action_data=req.action_data
            )
            for req in pending
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approvals: {str(e)}")


@router.get("/approvals/{user_id}/{approval_id}")
async def get_approval_request(user_id: str, approval_id: str):
    """
    Get a specific approval request.
    """
    try:
        request = hitl_service.get_approval_request(approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")
        
        if request.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ApprovalRequestResponse(
            approval_id=request.approval_id,
            action_type=request.action_type,
            message=request.message,
            created_at=request.created_at,
            expires_at=request.expires_at,
            status=request.status.value,
            action_data=request.action_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval: {str(e)}")


@router.post("/respond")
async def respond_to_approval(response: ApprovalResponse, background_tasks: BackgroundTasks):
    """
    Respond to an approval request (approve or reject).
    """
    try:
        request = hitl_service.get_approval_request(response.approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")
        
        if request.user_id != response.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if response.action.lower() == "approve":
            success = hitl_service.approve_request(
                response.approval_id, 
                response.user_id, 
                response.response_data
            )
            
            if success:
                # Execute the approved action in background
                background_tasks.add_task(
                    execute_approved_action, 
                    request, 
                    response.response_data or {}
                )
                
                return {
                    "success": True,
                    "message": "Request approved and action will be executed",
                    "approval_id": response.approval_id
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to approve request")
        
        elif response.action.lower() == "reject":
            success = hitl_service.reject_request(
                response.approval_id, 
                response.user_id, 
                response.reason
            )
            
            if success:
                return {
                    "success": True,
                    "message": "Request rejected",
                    "approval_id": response.approval_id
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to reject request")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")


@router.get("/teams/approval-card/{approval_id}")
async def get_teams_approval_card(approval_id: str, user_id: str):
    """
    Get a Teams Adaptive Card for an approval request.
    """
    try:
        request = hitl_service.get_approval_request(approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")
        
        if request.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        card = hitl_service.create_teams_approval_card(request)
        
        return {
            "card": card,
            "approval_id": approval_id,
            "expires_at": request.expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create approval card: {str(e)}")


@router.post("/teams/approval-response")
async def handle_teams_approval_response(card_response: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle approval responses from Teams Adaptive Cards.
    """
    try:
        # Extract data from Teams card response
        action_data = card_response.get("data", {})
        approval_id = action_data.get("approval_id")
        action = action_data.get("action")
        
        if not approval_id or not action:
            raise HTTPException(status_code=400, detail="Invalid card response data")
        
        # Get the approval request
        request = hitl_service.get_approval_request(approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")
        
        # For Teams, we'll use the user_id from the request (since Teams provides user context differently)
        user_id = request.user_id
        
        if action.lower() == "approve":
            success = hitl_service.approve_request(approval_id, user_id)
            
            if success:
                # Execute the approved action in background
                background_tasks.add_task(execute_approved_action, request, {})
                
                return {
                    "type": "message",
                    "text": "✅ **Approved!** Your request has been approved and the action will be executed.",
                    "approval_id": approval_id
                }
            else:
                return {
                    "type": "message", 
                    "text": "❌ Failed to approve the request. It may have expired or already been processed."
                }
        
        elif action.lower() == "reject":
            success = hitl_service.reject_request(approval_id, user_id, "Rejected via Teams")
            
            if success:
                return {
                    "type": "message",
                    "text": "❌ **Rejected.** The request has been rejected and no action will be taken.",
                    "approval_id": approval_id
                }
            else:
                return {
                    "type": "message",
                    "text": "❌ Failed to reject the request. It may have expired or already been processed."
                }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to handle Teams response: {str(e)}")


@router.delete("/cleanup")
async def cleanup_expired_approvals():
    """
    Clean up expired approval requests.
    """
    try:
        cleaned_count = hitl_service.cleanup_expired_requests()
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} expired requests"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")


async def execute_approved_action(request: ApprovalRequest, response_data: Dict[str, Any]):
    """
    Execute an approved action in the background.
    """
    try:
        if request.action_type == "send_communication":
            # Execute the communication sending
            draft = request.action_data.get("draft", "")
            recipient = request.action_data.get("recipient", "")
            
            result = await tool_manager.send_communication_tool(
                draft=draft, 
                recipient=recipient, 
                approved=True
            )
            
            print(f"Executed approved communication: {result.message}")
        
        # Add other action types as needed
        else:
            print(f"Unknown action type for execution: {request.action_type}")
            
    except Exception as e:
        print(f"Error executing approved action: {str(e)}")


@router.get("/health")
async def hitl_health_check():
    """Health check for HITL service"""
    try:
        # Get some basic stats
        all_pending = []
        for request in hitl_service.pending_approvals.values():
            if request.status == ApprovalStatus.PENDING:
                all_pending.append(request)
        
        return {
            "status": "healthy",
            "pending_approvals": len(all_pending),
            "total_requests": len(hitl_service.pending_approvals)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"HITL service unhealthy: {str(e)}")
