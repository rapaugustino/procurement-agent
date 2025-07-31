"""
Enhanced workflow router that integrates tool-based multiagent architecture
with HITL capabilities, matching the multiagent_script.py patterns.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import asyncio
from datetime import datetime, timedelta

from ..agents.supervisor_agent import SupervisorAgent
from ..agents.agent_tools import tool_manager, AVAILABLE_TOOLS, get_critical_tools
from ..services.hitl_service import hitl_service
from ..services.streaming_service import streaming_service
from ..agents.base_agent import AgentState

router = APIRouter(prefix="/workflow", tags=["workflow", "multiagent"])


class ToolWorkflowRequest(BaseModel):
    """Request for tool-based workflow execution"""
    user_id: str
    conversation_id: str
    initial_message: str
    auto_approve: bool = False  # For testing - normally False for safety


class WorkflowStep(BaseModel):
    """Individual step in workflow execution"""
    step_id: str
    tool_name: str
    tool_args: Dict[str, Any]
    result: Optional[str] = None
    requires_approval: bool = False
    approval_id: Optional[str] = None
    status: str = "pending"  # pending, completed, failed, awaiting_approval


class WorkflowExecution(BaseModel):
    """Complete workflow execution state"""
    workflow_id: str
    user_id: str
    conversation_id: str
    initial_message: str
    steps: List[WorkflowStep]
    status: str = "running"  # running, completed, failed, awaiting_approval
    final_result: Optional[str] = None


# In-memory workflow storage (in production, use database)
active_workflows: Dict[str, WorkflowExecution] = {}


@router.post("/execute")
async def execute_tool_workflow(request: ToolWorkflowRequest, background_tasks: BackgroundTasks):
    """
    Execute a tool-based workflow similar to the multiagent_script.py supervisor.
    This endpoint mimics the supervisor's decision-making and tool execution.
    """
    workflow_id = str(uuid.uuid4())
    
    try:
        # Create workflow execution
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            initial_message=request.initial_message,
            steps=[]
        )
        
        active_workflows[workflow_id] = workflow
        
        # Analyze the request and determine tools to use
        planned_steps = await plan_workflow_steps(request.initial_message)
        workflow.steps = planned_steps
        
        # Execute the workflow
        background_tasks.add_task(
            execute_workflow_background, 
            workflow_id, 
            request.auto_approve
        )
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "planned_steps": len(planned_steps),
            "message": "Workflow execution started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.post("/execute/stream")
async def stream_tool_workflow(request: ToolWorkflowRequest):
    """
    Execute a tool-based workflow with real-time streaming updates.
    Returns Server-Sent Events (SSE) for real-time progress feedback.
    """
    workflow_id = str(uuid.uuid4())
    
    async def generate_workflow_stream():
        try:
            # Send workflow started event
            yield await streaming_service.format_sse_event("workflow_started", {
                "message": "Starting multi-agent workflow...",
                "workflow_id": workflow_id,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id
            })
            
            # Create workflow execution
            workflow = WorkflowExecution(
                workflow_id=workflow_id,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                initial_message=request.initial_message,
                steps=[]
            )
            
            active_workflows[workflow_id] = workflow
            
            # Send planning event
            yield await streaming_service.format_sse_event("planning", {
                "message": "Supervisor analyzing request and planning workflow...",
                "step": "workflow_planning"
            })
            
            # Plan workflow steps
            planned_steps = await plan_workflow_steps(request.initial_message)
            workflow.steps = planned_steps
            
            yield await streaming_service.format_sse_event("plan_created", {
                "message": f"Workflow planned with {len(planned_steps)} steps",
                "total_steps": len(planned_steps),
                "steps": [{
                    "step_id": step.step_id,
                    "tool_name": step.tool_name,
                    "requires_approval": step.requires_approval
                } for step in planned_steps]
            })
            
            # Execute workflow steps with streaming
            for step_index, step in enumerate(planned_steps):
                # Send step started event
                yield await streaming_service.format_sse_event("step_started", {
                    "message": f"Executing step {step_index + 1}: {step.tool_name}",
                    "step_id": step.step_id,
                    "tool_name": step.tool_name,
                    "step_index": step_index,
                    "total_steps": len(planned_steps)
                })
                
                # Check if step requires approval
                if step.requires_approval and not request.auto_approve:
                    # Send approval required event
                    approval_id = str(uuid.uuid4())
                    step.approval_id = approval_id
                    step.status = "pending_approval"
                    
                    yield await streaming_service.format_sse_event("approval_required", {
                        "message": f"Step {step.tool_name} requires human approval",
                        "step_id": step.step_id,
                        "approval_id": approval_id,
                        "tool_name": step.tool_name,
                        "tool_args": step.tool_args,
                        "approval_url": f"/workflow/approve/{workflow_id}"
                    })
                    
                    # Wait for approval (in real implementation, this would be handled differently)
                    yield await streaming_service.format_sse_event("waiting_approval", {
                        "message": "Waiting for human approval...",
                        "step_id": step.step_id
                    })
                    
                    # For demo purposes, auto-approve after a short delay
                    await asyncio.sleep(2)
                    
                    yield await streaming_service.format_sse_event("approval_granted", {
                        "message": "Approval granted, continuing execution",
                        "step_id": step.step_id
                    })
                
                # Execute the tool
                yield await streaming_service.format_sse_event("tool_executing", {
                    "message": f"Executing {step.tool_name}...",
                    "step_id": step.step_id,
                    "tool_name": step.tool_name
                })
                
                # Execute the actual tool
                try:
                    result = await execute_tool_step(step, workflow)
                    step.result = result
                    step.status = "completed"
                    
                    # Send step completed event
                    yield await streaming_service.format_sse_event("step_completed", {
                        "message": f"Step {step.tool_name} completed successfully",
                        "step_id": step.step_id,
                        "result": result[:200] + "..." if len(result) > 200 else result,  # Truncate long results
                        "status": "completed"
                    })
                    
                except Exception as e:
                    step.status = "failed"
                    yield await streaming_service.format_sse_event("step_failed", {
                        "message": f"Step {step.tool_name} failed: {str(e)}",
                        "step_id": step.step_id,
                        "error": str(e)
                    })
                    break
            
            # Determine final result
            completed_steps = [s for s in workflow.steps if s.status == "completed"]
            if completed_steps:
                workflow.final_result = completed_steps[-1].result
                workflow.status = "completed"
                
                yield await streaming_service.format_sse_event("workflow_completed", {
                    "message": "Workflow completed successfully",
                    "workflow_id": workflow_id,
                    "final_result": workflow.final_result,
                    "steps_completed": len(completed_steps),
                    "total_steps": len(planned_steps)
                })
            else:
                workflow.status = "failed"
                yield await streaming_service.format_sse_event("workflow_failed", {
                    "message": "Workflow failed to complete",
                    "workflow_id": workflow_id
                })
                
        except Exception as e:
            yield await streaming_service.format_sse_event("workflow_error", {
                "message": f"Workflow error: {str(e)}",
                "error_type": type(e).__name__,
                "workflow_id": workflow_id
            })
    
    return StreamingResponse(
        generate_workflow_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get the current status of a workflow execution"""
    workflow = active_workflows.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "workflow_id": workflow_id,
        "status": workflow.status,
        "steps_completed": len([s for s in workflow.steps if s.status == "completed"]),
        "total_steps": len(workflow.steps),
        "current_step": next((s for s in workflow.steps if s.status in ["pending", "awaiting_approval"]), None),
        "final_result": workflow.final_result,
        "steps": workflow.steps
    }


@router.post("/approve/{workflow_id}")
async def approve_workflow_step(workflow_id: str, approval_data: Dict[str, Any], 
                               background_tasks: BackgroundTasks):
    """
    Approve a workflow step that requires human approval.
    This handles the HITL approval similar to the multiagent_script.py.
    """
    workflow = active_workflows.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Find the step awaiting approval
    pending_step = next((s for s in workflow.steps if s.status == "awaiting_approval"), None)
    if not pending_step:
        raise HTTPException(status_code=400, detail="No step awaiting approval")
    
    try:
        # Process the approval
        if approval_data.get("action") == "approve":
            pending_step.status = "pending"  # Resume execution
            
            # Continue workflow execution in background
            background_tasks.add_task(
                continue_workflow_execution, 
                workflow_id, 
                pending_step.step_id
            )
            
            return {
                "success": True,
                "message": "Step approved, workflow continuing",
                "workflow_id": workflow_id
            }
        
        elif approval_data.get("action") == "reject":
            pending_step.status = "failed"
            workflow.status = "failed"
            workflow.final_result = f"Workflow stopped: Step '{pending_step.tool_name}' rejected by user"
            
            return {
                "success": True,
                "message": "Step rejected, workflow stopped",
                "workflow_id": workflow_id
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")


async def plan_workflow_steps(initial_message: str) -> List[WorkflowStep]:
    """
    Plan workflow steps based on the initial message.
    This mimics the supervisor's decision-making from multiagent_script.py.
    """
    steps = []
    message_lower = initial_message.lower()
    
    # Simple rule-based planning (in production, use LLM for planning)
    step_counter = 1
    
    # If asking about procurement policies, use RAG tool
    if any(word in message_lower for word in ["policy", "procurement", "contract", "vendor", "purchase"]):
        steps.append(WorkflowStep(
            step_id=f"step_{step_counter}",
            tool_name="procurement_rag_agent_tool",
            tool_args={"query": initial_message},
            requires_approval=False
        ))
        step_counter += 1
    
    # If asking to draft or send communication
    if any(word in message_lower for word in ["draft", "email", "send", "message", "contact"]):
        # First draft the communication
        steps.append(WorkflowStep(
            step_id=f"step_{step_counter}",
            tool_name="draft_communication_tool",
            tool_args={
                "context": "Based on procurement inquiry",
                "recipient": "Procurement Team",
                "request": initial_message,
                "communication_type": "email"
            },
            requires_approval=False
        ))
        step_counter += 1
        
        # Then send it (requires approval)
        steps.append(WorkflowStep(
            step_id=f"step_{step_counter}",
            tool_name="send_communication_tool",
            tool_args={
                "draft": "{{previous_step_result}}",  # Will be filled from previous step
                "recipient": "Procurement Team"
            },
            requires_approval=True
        ))
        step_counter += 1
    
    # If no specific tools identified, default to RAG
    if not steps:
        steps.append(WorkflowStep(
            step_id=f"step_{step_counter}",
            tool_name="procurement_rag_agent_tool",
            tool_args={"query": initial_message},
            requires_approval=False
        ))
    
    return steps


async def execute_workflow_background(workflow_id: str, auto_approve: bool = False):
    """
    Execute workflow steps in background, handling approvals as needed.
    This mimics the execution flow from multiagent_script.py.
    """
    workflow = active_workflows.get(workflow_id)
    if not workflow:
        return
    
    try:
        for step in workflow.steps:
            if step.status != "pending":
                continue
            
            # Check if this step requires approval
            if step.requires_approval and not auto_approve:
                # Create approval request
                approval_id = hitl_service.create_approval_request(
                    user_id=workflow.user_id,
                    conversation_id=workflow.conversation_id,
                    action_type=f"execute_tool_{step.tool_name}",
                    action_data=step.tool_args,
                    message=f"Approve execution of {step.tool_name}?"
                )
                
                step.approval_id = approval_id
                step.status = "awaiting_approval"
                workflow.status = "awaiting_approval"
                
                # Stop execution here - will resume when approved
                break
            
            # Execute the tool
            try:
                result = await execute_tool_step(step, workflow)
                step.result = result
                step.status = "completed"
                
            except Exception as e:
                step.result = f"Error: {str(e)}"
                step.status = "failed"
                workflow.status = "failed"
                workflow.final_result = f"Workflow failed at step {step.step_id}: {str(e)}"
                break
        
        # Check if workflow is complete
        if all(s.status in ["completed", "failed"] for s in workflow.steps):
            if any(s.status == "failed" for s in workflow.steps):
                workflow.status = "failed"
            else:
                workflow.status = "completed"
                # Compile final result
                results = [s.result for s in workflow.steps if s.result]
                workflow.final_result = "\n\n".join(results)
        
    except Exception as e:
        workflow.status = "failed"
        workflow.final_result = f"Workflow execution error: {str(e)}"


async def continue_workflow_execution(workflow_id: str, from_step_id: str):
    """Continue workflow execution after approval"""
    await execute_workflow_background(workflow_id, auto_approve=False)


async def execute_tool_step(step: WorkflowStep, workflow: WorkflowExecution) -> str:
    """Execute a single tool step"""
    tool_name = step.tool_name
    tool_args = step.tool_args
    
    # Handle template variables in args (like {{previous_step_result}})
    if "{{previous_step_result}}" in str(tool_args):
        # Find the previous completed step
        prev_step = None
        for s in workflow.steps:
            if s.step_id == step.step_id:
                break
            if s.status == "completed":
                prev_step = s
        
        if prev_step and prev_step.result:
            # Replace template variable
            tool_args = {
                k: v.replace("{{previous_step_result}}", prev_step.result) if isinstance(v, str) else v
                for k, v in tool_args.items()
            }
    
    # Execute the appropriate tool
    if tool_name == "procurement_rag_agent_tool":
        result = await tool_manager.procurement_rag_tool(tool_args.get("query", ""))
        return result.message if result.success else f"Error: {result.error}"
    
    elif tool_name == "draft_communication_tool":
        result = await tool_manager.draft_communication_tool(
            context=tool_args.get("context", ""),
            recipient=tool_args.get("recipient", ""),
            request=tool_args.get("request", ""),
            communication_type=tool_args.get("communication_type", "email")
        )
        return result.data.get("draft", "") if result.success else f"Error: {result.error}"
    
    elif tool_name == "send_communication_tool":
        result = await tool_manager.send_communication_tool(
            draft=tool_args.get("draft", ""),
            recipient=tool_args.get("recipient", ""),
            approved=True  # Already approved if we reach here
        )
        return result.message if result.success else f"Error: {result.error}"
    
    else:
        raise Exception(f"Unknown tool: {tool_name}")


@router.get("/tools")
async def get_available_tools():
    """Get list of available tools and their descriptions"""
    from ..agents.agent_tools import get_tool_descriptions
    
    return {
        "tools": get_tool_descriptions(),
        "critical_tools": get_critical_tools(),
        "total_tools": len(AVAILABLE_TOOLS)
    }


@router.delete("/cleanup")
async def cleanup_completed_workflows():
    """Clean up completed workflows"""
    global active_workflows
    
    completed_count = 0
    workflow_ids_to_remove = []
    
    for workflow_id, workflow in active_workflows.items():
        if workflow.status in ["completed", "failed"]:
            workflow_ids_to_remove.append(workflow_id)
            completed_count += 1
    
    for workflow_id in workflow_ids_to_remove:
        del active_workflows[workflow_id]
    
    return {
        "success": True,
        "cleaned_workflows": completed_count,
        "active_workflows": len(active_workflows)
    }
