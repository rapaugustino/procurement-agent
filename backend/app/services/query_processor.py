"""
Query Processing Service
Advanced query rewriting with conversation context
Integrated from python-script-testing.py
"""

import logging
from typing import Dict, Any, List
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI


class QueryProcessor:
    """
    Advanced query processing with context-aware rewriting and conversation history integration
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
    
    async def rewrite_query(self, question: str, conversation_memory: Dict[str, Any]) -> str:
        """
        Rewrite the user's question for better retrieval, incorporating chat history.
        Includes strict rules to prevent topic deviation.
        """
        self.logger.info("---NODE: REWRITING QUERY---")
        
        # Format conversation history
        history = conversation_memory.get("history", [])
        if not history:
            self.logger.info("No conversation history - using original query")
            return question
        
        # Get recent conversation context (last 2 exchanges)
        recent_history = history[-2:] if len(history) >= 2 else history
        history_context = ""
        
        for turn in recent_history:
            user_q = turn.get("question", "")
            assistant_a = turn.get("answer", "")
            if user_q:
                history_context += f"Previous Question: {user_q}\n"
            if assistant_a:
                # Truncate long answers for context
                truncated_answer = assistant_a[:200] + "..." if len(assistant_a) > 200 else assistant_a
                history_context += f"Previous Answer: {truncated_answer}\n"
        
        rewrite_prompt = PromptTemplate(
            template="""You are a query rewriter for a University of Washington procurement assistant.

            STRICT RULES:
            1. ONLY rewrite queries related to procurement, purchasing, vendors, policies, or university business processes.
            2. If the current question is NOT procurement-related, return it UNCHANGED.
            3. If there's no relevant conversation history, return the question UNCHANGED.
            4. When rewriting, incorporate relevant context from the conversation history to make the query more specific and searchable.
            5. Keep the rewritten query focused and concise.

            CONVERSATION HISTORY:
            {history}

            CURRENT QUESTION: {question}

            INSTRUCTIONS:
            - If this question is about procurement/purchasing/vendors/policies, rewrite it to be more specific using conversation context
            - If this question is NOT about procurement (e.g., weather, personal topics, general knowledge), return it exactly as-is
            - Focus on making procurement-related queries more searchable and specific

            REWRITTEN QUERY:""",
            input_variables=["question", "history"],
        )
        
        try:
            rewrite_chain = rewrite_prompt | self.llm | StrOutputParser()
            rewritten_query = await rewrite_chain.ainvoke({
                "question": question,
                "history": history_context
            })
            
            # Clean up the response
            rewritten_query = rewritten_query.strip()
            
            # Safety check: if rewrite is too different or empty, use original
            if not rewritten_query or len(rewritten_query) < 5:
                self.logger.warning("Rewritten query too short - using original")
                return question
            
            self.logger.info(f"Original: {question}")
            self.logger.info(f"Rewritten: {rewritten_query}")
            
            return rewritten_query
            
        except Exception as e:
            self.logger.error(f"Error rewriting query: {e}")
            return question  # Fallback to original query
    
    def is_procurement_related(self, question: str) -> bool:
        """
        Check if a question is procurement-related using keyword indicators.
        """
        question_lower = question.lower()
        
        procurement_keywords = [
            "procurement", "purchase", "buy", "buying", "vendor", "supplier", 
            "contract", "contracting", "requisition", "order", "ordering",
            "approval", "policy", "policies", "process", "procedure",
            "requirement", "requirements", "budget", "budgeting", "cost",
            "expense", "invoice", "invoicing", "payment", "bid", "bidding",
            "rfp", "rfq", "proposal", "quote", "quotation", "sourcing",
            "acquisition", "acquire", "university", "uw", "department"
        ]
        
        return any(keyword in question_lower for keyword in procurement_keywords)
    
    def format_conversation_history(self, history: List[Dict[str, Any]], max_turns: int = 3) -> str:
        """
        Format conversation history for use in prompts.
        """
        if not history:
            return "No previous conversation."
        
        # Get recent history
        recent_history = history[-max_turns:] if len(history) > max_turns else history
        
        formatted_history = []
        for turn in recent_history:
            user_q = turn.get("question", "")
            assistant_a = turn.get("answer", "")
            
            if user_q:
                formatted_history.append(f"User: {user_q}")
            if assistant_a:
                # Truncate long answers
                truncated = assistant_a[:150] + "..." if len(assistant_a) > 150 else assistant_a
                formatted_history.append(f"Assistant: {truncated}")
        
        return "\n".join(formatted_history)
    
    def should_use_context(self, question: str, history: List[Dict[str, Any]]) -> bool:
        """
        Determine if conversation context should be used for query rewriting.
        """
        if not history:
            return False
        
        # Only use context for procurement-related questions
        if not self.is_procurement_related(question):
            return False
        
        # Check if recent history is procurement-related
        recent_turn = history[-1] if history else {}
        recent_question = recent_turn.get("question", "")
        
        if recent_question and self.is_procurement_related(recent_question):
            return True
        
        return False
