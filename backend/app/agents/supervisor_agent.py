"""
Supervisor Agent for orchestrating multi-agent workflows.
Routes tasks to appropriate agents and manages overall workflow.
"""

import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentState, AgentResponse
from .rag_agent import RAGAgent
from .communication_agent import CommunicationAgent


class TaskType(str, Enum):
    """Types of tasks that can be handled by the system"""
    DOCUMENT_QUERY = "document_query"
    POLICY_LOOKUP = "policy_lookup"
    CONTACT_SEARCH = "contact_search"
    GENERAL_INQUIRY = "general_inquiry"
    MULTI_STEP_WORKFLOW = "multi_step_workflow"


class WorkflowStep(BaseModel):
    """Individual step in a multi-agent workflow"""
    step_id: str
    agent_id: str
    task_type: TaskType
    input_data: Dict[str, Any]
    depends_on: List[str] = []  # List of step_ids this step depends on
    status: str = "pending"
    result: Optional[AgentResponse] = None


class Workflow(BaseModel):
    """Multi-step workflow definition"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    status: str = "pending"


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that orchestrates multi-agent workflows.
    Routes tasks to appropriate agents and manages dependencies.
    """
    
    def __init__(self):
        super().__init__("supervisor", "Multi-Agent Supervisor")
        self.agents: Dict[str, BaseAgent] = {}
        self.active_workflows: Dict[str, Workflow] = {}
        self._register_agents()
    
    def _register_agents(self):
        """Register all available agents"""
        # Register RAG agent
        rag_agent = RAGAgent()
        self.agents[rag_agent.agent_id] = rag_agent
        
        # Register Communication agent
        comm_agent = CommunicationAgent()
        self.agents[comm_agent.agent_id] = comm_agent
        
        # Future agents can be registered here
        # self.agents["policy_agent"] = PolicyAgent()
        # self.agents["contact_agent"] = ContactAgent()
    
    async def process(self, state: AgentState) -> AgentResponse:
        """
        Process a task by routing to appropriate agent or managing workflow.
        
        Args:
            state: AgentState containing task information
            
        Returns:
            AgentResponse with results
        """
        try:
            task_type = state.data.get("task_type", TaskType.GENERAL_INQUIRY)
            
            # Handle single-agent tasks
            if task_type in [TaskType.DOCUMENT_QUERY, TaskType.POLICY_LOOKUP, 
                           TaskType.CONTACT_SEARCH, TaskType.GENERAL_INQUIRY]:
                return await self._route_single_task(state, task_type)
            
            # Handle multi-step workflows
            elif task_type == TaskType.MULTI_STEP_WORKFLOW:
                return await self._execute_workflow(state)
            
            else:
                return self.create_response(
                    state.task_id, False, 
                    error=f"Unknown task type: {task_type}"
                )
                
        except Exception as e:
            return self.create_response(
                state.task_id, False, 
                error=f"Supervisor error: {str(e)}"
            )
    
    async def _route_single_task(self, state: AgentState, task_type: TaskType) -> AgentResponse:
        """Route a single task to the appropriate agent"""
        
        # Determine which agent to use based on task type and capabilities
        target_agent = self._select_agent_for_task(task_type, state.data)
        
        if not target_agent:
            return self.create_response(
                state.task_id, False,
                error=f"No suitable agent found for task type: {task_type}"
            )
        
        # Route to the selected agent
        agent_state = AgentState(
            agent_id=target_agent.agent_id,
            task_id=state.task_id,
            data=state.data
        )
        
        response = await target_agent.process(agent_state)
        
        # Add supervisor metadata to response
        response.data["routed_by"] = self.agent_id
        response.data["target_agent"] = target_agent.agent_id
        
        return response
    
    def _select_agent_for_task(self, task_type: TaskType, data: Dict[str, Any]) -> Optional[BaseAgent]:
        """Select the best agent for a given task type"""
        
        # Simple routing logic - can be made more sophisticated
        if task_type in [TaskType.DOCUMENT_QUERY, TaskType.POLICY_LOOKUP, 
                        TaskType.CONTACT_SEARCH, TaskType.GENERAL_INQUIRY]:
            # For now, route all these to RAG agent
            return self.agents.get("rag_agent")
        
        # Future: Add more sophisticated routing based on:
        # - Agent capabilities
        # - Current load
        # - Task complexity
        # - User preferences
        
        return None
    
    async def _execute_workflow(self, state: AgentState) -> AgentResponse:
        """Execute a multi-step workflow"""
        workflow_def = state.data.get("workflow")
        if not workflow_def:
            return self.create_response(
                state.task_id, False,
                error="No workflow definition provided"
            )
        
        workflow = Workflow(**workflow_def)
        self.active_workflows[workflow.workflow_id] = workflow
        
        try:
            # Execute workflow steps
            completed_steps = {}
            
            while not self._is_workflow_complete(workflow):
                # Find next executable steps (dependencies satisfied)
                ready_steps = self._get_ready_steps(workflow, completed_steps)
                
                if not ready_steps:
                    break  # No more steps can be executed
                
                # Execute ready steps in parallel
                tasks = []
                for step in ready_steps:
                    task = self._execute_workflow_step(step, completed_steps)
                    tasks.append(task)
                
                # Wait for all parallel steps to complete
                step_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(step_results):
                    step = ready_steps[i]
                    if isinstance(result, Exception):
                        step.status = "failed"
                        step.result = self.create_response(
                            step.step_id, False, error=str(result)
                        )
                    else:
                        step.status = "completed"
                        step.result = result
                    
                    completed_steps[step.step_id] = step
            
            # Compile final workflow result
            workflow.status = "completed"
            final_result = self._compile_workflow_result(workflow, completed_steps)
            
            return self.create_response(
                state.task_id, True, final_result,
                f"Workflow {workflow.name} completed successfully"
            )
            
        except Exception as e:
            workflow.status = "failed"
            return self.create_response(
                state.task_id, False,
                error=f"Workflow execution failed: {str(e)}"
            )
        finally:
            # Clean up
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]
    
    def _is_workflow_complete(self, workflow: Workflow) -> bool:
        """Check if all workflow steps are completed"""
        return all(step.status in ["completed", "failed"] for step in workflow.steps)
    
    def _get_ready_steps(self, workflow: Workflow, completed_steps: Dict[str, WorkflowStep]) -> List[WorkflowStep]:
        """Get workflow steps that are ready to execute (dependencies satisfied)"""
        ready_steps = []
        
        for step in workflow.steps:
            if step.status != "pending":
                continue
            
            # Check if all dependencies are satisfied
            dependencies_satisfied = all(
                dep_id in completed_steps and completed_steps[dep_id].status == "completed"
                for dep_id in step.depends_on
            )
            
            if dependencies_satisfied:
                ready_steps.append(step)
        
        return ready_steps
    
    async def _execute_workflow_step(self, step: WorkflowStep, completed_steps: Dict[str, WorkflowStep]) -> AgentResponse:
        """Execute a single workflow step"""
        
        # Get input data, potentially from previous steps
        input_data = step.input_data.copy()
        
        # Merge data from dependency steps
        for dep_id in step.depends_on:
            if dep_id in completed_steps:
                dep_result = completed_steps[dep_id].result
                if dep_result and dep_result.success:
                    input_data.update(dep_result.data)
        
        # Create agent state for this step
        agent_state = AgentState(
            agent_id=step.agent_id,
            task_id=step.step_id,
            data=input_data
        )
        
        # Execute the step
        target_agent = self.agents.get(step.agent_id)
        if not target_agent:
            raise Exception(f"Agent {step.agent_id} not found")
        
        return await target_agent.process(agent_state)
    
    def _compile_workflow_result(self, workflow: Workflow, completed_steps: Dict[str, WorkflowStep]) -> Dict[str, Any]:
        """Compile final result from all workflow steps"""
        return {
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.name,
            "status": workflow.status,
            "steps": {
                step_id: {
                    "status": step.status,
                    "result": step.result.dict() if step.result else None
                }
                for step_id, step in completed_steps.items()
            },
            "summary": self._generate_workflow_summary(completed_steps)
        }
    
    def _generate_workflow_summary(self, completed_steps: Dict[str, WorkflowStep]) -> str:
        """Generate a summary of the workflow execution"""
        total_steps = len(completed_steps)
        successful_steps = sum(1 for step in completed_steps.values() 
                             if step.status == "completed")
        
        return f"Executed {total_steps} steps, {successful_steps} successful"
    
    def get_capabilities(self) -> List[str]:
        """Return capabilities of the supervisor agent"""
        capabilities = ["task_routing", "workflow_orchestration", "agent_coordination"]
        
        # Add capabilities from all registered agents
        for agent in self.agents.values():
            capabilities.extend(agent.get_capabilities())
        
        return list(set(capabilities))  # Remove duplicates
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        return {
            "supervisor_status": self.status,
            "registered_agents": {
                agent_id: {
                    "name": agent.name,
                    "status": agent.status,
                    "capabilities": agent.get_capabilities()
                }
                for agent_id, agent in self.agents.items()
            },
            "active_workflows": len(self.active_workflows)
        }
    
    async def create_workflow(self, workflow_definition: Dict[str, Any]) -> str:
        """Create a new workflow from definition"""
        workflow = Workflow(**workflow_definition)
        self.active_workflows[workflow.workflow_id] = workflow
        return workflow.workflow_id
