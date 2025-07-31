"""
RAG Agent for procurement document retrieval and question answering.
Migrated from notebook code with modular architecture.
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from .base_agent import BaseAgent, AgentState, AgentResponse
from ..services.azure_search_service import AdaptiveHybridAzureSearchRetriever
from ..services.memory_service import ConversationMemoryService
from ..config import settings


class RAGGraphState(TypedDict):
    """State for the RAG agent's internal graph processing"""
    question: str
    original_question: str
    generation: str
    documents: List[Document]
    original_documents: List[Document]
    conversation_memory: dict


class RAGAgent(BaseAgent):
    """
    Retrieval-Augmented Generation Agent for procurement queries.
    Uses LangGraph for orchestrating the RAG pipeline.
    """
    
    def __init__(self):
        super().__init__("rag_agent", "Procurement RAG Agent")
        self.llm = None
        self.embeddings = None
        self.retriever = None
        self.memory_service = ConversationMemoryService()
        self.graph = None
        self._initialize_models()
        self._build_graph()
    
    def _initialize_models(self):
        """Initialize Azure OpenAI models"""
        try:
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_chat_endpoint,
                api_key=settings.azure_openai_chat_key,
                deployment_name=settings.azure_openai_chat_deployment,
                api_version=settings.azure_openai_api_version,
                temperature=0.1,
            )
            
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_openai_embedding_endpoint,
                api_key=settings.azure_openai_embedding_key,
                azure_deployment=settings.azure_openai_embedding_deployment,
                api_version=settings.azure_openai_api_version,
            )
            
            self.retriever = AdaptiveHybridAzureSearchRetriever(
                search_service=settings.azure_search_service,
                search_key=settings.azure_search_key,
                index_name=settings.azure_search_index,
                embeddings=self.embeddings
            )
            
        except Exception as e:
            print(f"Error initializing RAG agent models: {e}")
            raise
    
    def _build_graph(self):
        """Build the LangGraph workflow for RAG processing"""
        workflow = StateGraph(RAGGraphState)
        
        # Add nodes
        workflow.add_node("rewrite_query", self._rewrite_query)
        workflow.add_node("retrieve", self._retrieve_docs)
        workflow.add_node("grade_documents", self._grade_documents)
        workflow.add_node("rerank_documents", self._rerank_documents)
        workflow.add_node("generate", self._generate)
        workflow.add_node("handle_no_docs", self._handle_no_docs)
        workflow.add_node("update_memory", self._update_memory)
        
        # Define flow
        workflow.set_entry_point("rewrite_query")
        workflow.add_edge("rewrite_query", "retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_edge("grade_documents", "rerank_documents")
        
        workflow.add_conditional_edges(
            "rerank_documents",
            self._decide_to_generate,
            {
                "generate": "generate",
                "fallback": "handle_no_docs",
            },
        )
        
        workflow.add_edge("generate", "update_memory")
        workflow.add_edge("handle_no_docs", "update_memory")
        workflow.add_edge("update_memory", END)
        
        self.graph = workflow.compile()
    
    async def process(self, state: AgentState) -> AgentResponse:
        """
        Process a procurement query using the RAG pipeline.
        
        Args:
            state: AgentState containing the user's question
            
        Returns:
            AgentResponse with the generated answer
        """
        try:
            if not self.validate_input(state):
                return self.create_response(
                    state.task_id, False, error="Invalid input state"
                )
            
            question = state.data.get("question", "")
            if not question:
                return self.create_response(
                    state.task_id, False, error="No question provided"
                )
            
            # Run the RAG graph
            inputs = {"question": question}
            final_state = {}
            
            for output in self.graph.stream(inputs):
                for key, value in output.items():
                    final_state.update(value)
            
            generation = final_state.get("generation", "No response generated.")
            documents = final_state.get("documents", [])
            
            # Prepare response data
            response_data = {
                "answer": generation,
                "sources": [
                    {
                        "title": doc.metadata.get("title", "Unknown"),
                        "chunk_id": doc.metadata.get("chunk_id", ""),
                        "search_score": doc.metadata.get("search_score", 0)
                    }
                    for doc in documents
                ],
                "original_question": question
            }
            
            return self.create_response(
                state.task_id, True, response_data, 
                "Successfully processed procurement query"
            )
            
        except Exception as e:
            return self.create_response(
                state.task_id, False, error=f"Error processing query: {str(e)}"
            )
    
    def get_capabilities(self) -> List[str]:
        """Return capabilities of the RAG agent"""
        return [
            "document_retrieval",
            "question_answering", 
            "procurement_guidance",
            "policy_lookup",
            "contact_information"
        ]
    
    # Internal graph node methods
    def _rewrite_query(self, state: RAGGraphState) -> dict:
        """Rewrite query for better retrieval"""
        question = state["question"]
        memory = self.memory_service.load_conversation_memory()
        
        history_context = ""
        if memory.get("history"):
            recent_turns = memory["history"][-2:]
            history_context = "\n".join([
                f"Previous User Question: {turn['question']}" 
                for turn in recent_turns
            ])

        prompt = PromptTemplate(
            template="""You are a query optimization expert. Rewrite the user's question into a more effective search query based on their original intent and the conversation history.

            **CRITICAL RULE: Do not add new topics, subjects, or concepts that are not present in the user's original question or the conversation history. Your goal is to clarify and add relevant keywords, not to change the topic.**

            CONVERSATION HISTORY:
            {history}

            USER QUESTION: "{question}"

            Optimized Search Query:""",
            input_variables=["question", "history"],
        )
        
        rewriter_chain = prompt | self.llm | StrOutputParser()
        rewritten_question = rewriter_chain.invoke({
            "question": question, 
            "history": history_context
        })
        
        return {
            "question": rewritten_question,
            "original_question": question,
            "conversation_memory": memory
        }
    
    def _retrieve_docs(self, state: RAGGraphState) -> dict:
        """Retrieve documents from Azure Search"""
        documents = self.retriever.invoke(state["question"])
        return {"original_documents": documents, "documents": documents}
    
    def _grade_documents(self, state: RAGGraphState) -> dict:
        """Grade document relevance"""
        question = state["original_question"]
        documents = state["documents"]
        
        grader_prompt = PromptTemplate(
            template="""You are a helpful assistant grading document relevance for a procurement question.
            A document is RELEVANT if it contains any information that could help answer the user's question, including general guidelines or contact details.
            
            User Question: {question}
            Document Content: {document}
            
            Is this document relevant? Respond with a single word: RELEVANT or NOT_RELEVANT.""",
            input_variables=["question", "document"],
        )
        
        grader_chain = grader_prompt | self.llm | StrOutputParser()
        relevant_docs = []
        
        for doc in documents:
            try:
                grade = grader_chain.invoke({
                    "question": question, 
                    "document": doc.page_content
                })
                if "RELEVANT" in grade.upper():
                    relevant_docs.append(doc)
            except Exception as e:
                print(f"Error grading document: {e}")
                
        return {"documents": relevant_docs}
    
    def _rerank_documents(self, state: RAGGraphState) -> dict:
        """Rerank documents by relevance"""
        if not state["documents"]:
            return {"documents": []}

        scorer_prompt = PromptTemplate(
            template="""You are a document re-ranking expert. Score the following document's relevance to the user's question on a scale from 1 (least relevant) to 5 (most relevant).
            Your output MUST be a JSON object with two keys: "reason" and "score".

            User Question: {question}
            Document Content: {document}
            
            JSON Output:""",
            input_variables=["question", "document"],
        )
        
        scorer_chain = scorer_prompt | self.llm | JsonOutputParser()
        scored_docs = []
        
        for doc in state["documents"]:
            try:
                result = scorer_chain.invoke({
                    "question": state["original_question"], 
                    "document": doc.page_content
                })
                scored_docs.append((doc, result.get("score", 0)))
            except Exception as e:
                print(f"Error scoring document: {e}")
                scored_docs.append((doc, 0))

        scored_docs.sort(key=lambda x: x[1], reverse=True)
        final_docs = [doc for doc, score in scored_docs]
        
        return {"documents": final_docs}
    
    def _decide_to_generate(self, state: RAGGraphState) -> str:
        """Decide next step based on document availability"""
        if not state["documents"]:
            return "fallback"
        else:
            return "generate"
    
    def _generate(self, state: RAGGraphState) -> dict:
        """Generate final answer with citations"""
        question = state["original_question"]
        documents = state["documents"]
        memory = state["conversation_memory"]

        history_context = "\n".join([
            f"User: {turn['question']}\nAssistant: {turn['answer'][:100]}..." 
            for turn in memory.get("history", [])[-2:]
        ])
        
        doc_context = "\n\n".join([
            f"Source Name: {d.metadata.get('title', 'N/A')}\nContent: {d.page_content}" 
            for d in documents
        ])

        # Extract contact information
        contacts = []
        contact_pattern = re.compile(r"Name:\s*(.*?)\s*Email:\s*(\S+@\S+)")
        for doc in documents:
            matches = contact_pattern.findall(doc.page_content)
            for match in matches:
                contact_str = f"{match[0].strip()} ({match[1].strip()})"
                if contact_str not in contacts:
                    contacts.append(contact_str)

        contact_info_for_prompt = (
            "Specific contact(s) found: " + ", ".join(contacts) 
            if contacts else "No specific contact information was found in the documents."
        )

        prompt = PromptTemplate(
            template="""You are a professional, helpful, and highly-trained assistant for the University of Washington's procurement department.

            CRITICAL INSTRUCTIONS:
            1.  Your entire response **MUST** be based **ONLY** on the "SOURCE DOCUMENTS". Never use outside knowledge.
            2.  You **MUST** add inline citations after each claim, like `[Source Name: filename.pdf]`.
            3.  If the documents don't answer the question, state that clearly.
            4.  **Conclude Naturally:** After the main answer, provide a helpful closing. Use the "GUIDANCE FOR CLOSING" section to inform your closing remarks. Do not be repetitive; vary your language to sound human.

            ---
            CONVERSATION HISTORY:
            {history}
            ---
            SOURCE DOCUMENTS:
            {context}
            ---
            GUIDANCE FOR CLOSING:
            {contact_info}
            ---

            USER'S QUESTION: "{question}"

            YOUR PROFESSIONAL RESPONSE (with citations and a natural closing):
            """,
            input_variables=["question", "context", "history", "contact_info"],
        )

        rag_chain = prompt | self.llm | StrOutputParser()
        final_generation = rag_chain.invoke({
            "context": doc_context, 
            "question": question, 
            "history": history_context,
            "contact_info": contact_info_for_prompt
        })
        
        return {"generation": final_generation}
    
    def _handle_no_docs(self, state: RAGGraphState) -> dict:
        """Handle case when no relevant documents found"""
        question = state["original_question"]

        fallback_prompt = PromptTemplate(
            template="""You are a helpful procurement assistant. A search was performed for a user's question, but no directly relevant documents were found.
            
            Your task is to inform the user of this limitation in a professional and helpful way. DO NOT invent an answer.
            
            USER'S QUESTION: "{question}"
            
            Compose a brief response that:
            1.  Acknowledges their question.
            2.  States that you were unable to find specific information in the available documents.
            3.  Suggests a general next step, such as contacting the procurement department directly for the most accurate guidance.
            
            Response:""",
            input_variables=["question"],
        )
        
        fallback_chain = fallback_prompt | self.llm | StrOutputParser()
        generation = fallback_chain.invoke({"question": question})
        return {"generation": generation, "documents": []}
    
    def _update_memory(self, state: RAGGraphState) -> dict:
        """Update conversation memory"""
        memory = state["conversation_memory"]
        question = state["original_question"]
        generation = state["generation"]
        
        memory.setdefault("history", []).append({
            "question": question,
            "answer": generation,
        })
        
        memory["history"] = memory["history"][-5:]
        self.memory_service.save_conversation_memory(memory)
        
        return state
