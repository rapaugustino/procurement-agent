"""
Memory service for managing conversation history.
Provides persistent storage for agent conversations.
"""

import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime


class ConversationMemoryService:
    """Service for managing conversation memory across agent interactions"""
    
    def __init__(self, memory_file: str = "conversation_memory.json"):
        self.memory_file = memory_file
        self.memory_dir = os.path.dirname(os.path.abspath(memory_file))
        self.logger = logging.getLogger(__name__)
        
        # Ensure memory directory exists
        if self.memory_dir and not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
    
    def load_conversation_memory(self, conversation_id: str = "default") -> Dict[str, Any]:
        """
        Load conversation memory for a specific conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Dictionary containing conversation history
        """
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    all_memories = json.load(f)
                    return all_memories.get(conversation_id, {"history": []})
            else:
                return {"history": []}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading conversation memory: {e}")
            return {"history": []}
    
    def save_conversation_memory(self, memory: Dict[str, Any], conversation_id: str = "default"):
        """
        Save conversation memory for a specific conversation.
        
        Args:
            memory: Memory dictionary to save (single entry to append to history)
            conversation_id: Unique identifier for the conversation
        """
        try:
            # Load existing memories
            all_memories = {}
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    all_memories = json.load(f)
            
            # Get or create conversation history structure
            if conversation_id not in all_memories:
                all_memories[conversation_id] = {"history": []}
            elif "history" not in all_memories[conversation_id]:
                # Handle legacy format - convert flat entry to history array
                legacy_entry = all_memories[conversation_id]
                if "question" in legacy_entry and "answer" in legacy_entry:
                    all_memories[conversation_id] = {
                        "history": [{
                            "question": legacy_entry["question"],
                            "answer": legacy_entry["answer"]
                        }]
                    }
                else:
                    all_memories[conversation_id] = {"history": []}
            
            # Append new memory entry to history
            history_entry = {
                "question": memory.get("question", ""),
                "answer": memory.get("answer", "")
            }
            all_memories[conversation_id]["history"].append(history_entry)
            
            # Keep only last 10 entries to prevent memory bloat
            all_memories[conversation_id]["history"] = all_memories[conversation_id]["history"][-10:]
            
            # Save back to file
            with open(self.memory_file, 'w') as f:
                json.dump(all_memories, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving conversation memory: {e}")
    
    def add_interaction(self, question: str, answer: str, conversation_id: str = "default", 
                       metadata: Dict[str, Any] = None):
        """
        Add a new interaction to conversation memory.
        
        Args:
            question: User's question
            answer: Agent's answer
            conversation_id: Unique identifier for the conversation
            metadata: Additional metadata for the interaction
        """
        memory = self.load_conversation_memory(conversation_id)
        
        interaction = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        memory.setdefault("history", []).append(interaction)
        
        # Keep only last N interactions to prevent memory from growing too large
        max_history = 10
        memory["history"] = memory["history"][-max_history:]
        
        self.save_conversation_memory(memory, conversation_id)
    
    def get_recent_context(self, conversation_id: str = "default", num_turns: int = 3) -> str:
        """
        Get recent conversation context as formatted string.
        
        Args:
            conversation_id: Unique identifier for the conversation
            num_turns: Number of recent turns to include
            
        Returns:
            Formatted string with recent conversation history
        """
        memory = self.load_conversation_memory(conversation_id)
        recent_history = memory.get("history", [])[-num_turns:]
        
        context_parts = []
        for turn in recent_history:
            context_parts.append(f"User: {turn['question']}")
            context_parts.append(f"Assistant: {turn['answer'][:200]}...")  # Truncate long answers
        
        return "\n".join(context_parts)
    
    def clear_conversation(self, conversation_id: str = "default"):
        """
        Clear conversation memory for a specific conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
        """
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    all_memories = json.load(f)
                
                if conversation_id in all_memories:
                    del all_memories[conversation_id]
                
                with open(self.memory_file, 'w') as f:
                    json.dump(all_memories, f, indent=2)
                    
        except Exception as e:
            self.logger.error(f"Error clearing conversation memory: {e}")
    
    def get_all_conversations(self) -> List[str]:
        """
        Get list of all conversation IDs.
        
        Returns:
            List of conversation IDs
        """
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    all_memories = json.load(f)
                    return list(all_memories.keys())
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error getting conversation list: {e}")
            return []
