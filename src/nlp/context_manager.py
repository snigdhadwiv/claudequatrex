"""
Context Manager Module
Manages conversation state and history
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import deque
from loguru import logger


@dataclass
class ConversationTurn:
    """Single conversation turn"""
    timestamp: float
    speaker: str  # "user" or "assistant"
    text: str
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Complete conversation context"""
    session_id: str
    user_id: Optional[str] = None
    language: str = "en"
    scenario: Optional[str] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)


class ContextManager:
    """Manages conversation context and history"""
    
    def __init__(
        self,
        max_history: int = 10,
        context_timeout: int = 300,  # 5 minutes
        enable_persistence: bool = False
    ):
        """
        Initialize context manager
        
        Args:
            max_history: Maximum number of turns to keep
            context_timeout: Context timeout in seconds
            enable_persistence: Enable context persistence
        """
        self.max_history = max_history
        self.context_timeout = context_timeout
        self.enable_persistence = enable_persistence
        
        # Active contexts
        self.contexts: Dict[str, ConversationContext] = {}
        
        # Current context
        self.current_context: Optional[ConversationContext] = None
        
        logger.info(
            f"ContextManager initialized: max_history={max_history}, "
            f"timeout={context_timeout}s"
        )
    
    def create_context(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        language: str = "en"
    ) -> ConversationContext:
        """
        Create new conversation context
        
        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            language: Conversation language
            
        Returns:
            New ConversationContext
        """
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            language=language
        )
        
        self.contexts[session_id] = context
        self.current_context = context
        
        logger.info(f"Created context: session={session_id}, language={language}")
        
        return context
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get context by session ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationContext or None
        """
        context = self.contexts.get(session_id)
        
        if context:
            # Check if context is expired
            if time.time() - context.last_activity > self.context_timeout:
                logger.warning(f"Context expired: {session_id}")
                self.delete_context(session_id)
                return None
        
        return context
    
    def set_current_context(self, session_id: str) -> bool:
        """
        Set active context
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        context = self.get_context(session_id)
        if context:
            self.current_context = context
            return True
        return False
    
    def add_turn(
        self,
        speaker: str,
        text: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> None:
        """
        Add conversation turn
        
        Args:
            speaker: "user" or "assistant"
            text: Turn text
            intent: Optional intent classification
            entities: Optional extracted entities
            session_id: Optional session ID (uses current if not provided)
        """
        # Get context
        if session_id:
            context = self.get_context(session_id)
        else:
            context = self.current_context
        
        if not context:
            logger.warning("No active context for adding turn")
            return
        
        # Create turn
        turn = ConversationTurn(
            timestamp=time.time(),
            speaker=speaker,
            text=text,
            intent=intent,
            entities=entities or {}
        )
        
        # Add to context
        context.turns.append(turn)
        context.last_activity = time.time()
        
        # Trim history if needed
        if len(context.turns) > self.max_history:
            context.turns = context.turns[-self.max_history:]
        
        logger.debug(f"Added turn: {speaker}: {text[:50]}...")
    
    def get_last_turn(
        self,
        speaker: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[ConversationTurn]:
        """
        Get last conversation turn
        
        Args:
            speaker: Filter by speaker (None for any)
            session_id: Optional session ID
            
        Returns:
            Last ConversationTurn or None
        """
        context = self.get_context(session_id) if session_id else self.current_context
        
        if not context or not context.turns:
            return None
        
        # Find last turn by speaker
        if speaker:
            for turn in reversed(context.turns):
                if turn.speaker == speaker:
                    return turn
            return None
        
        return context.turns[-1]
    
    def get_history(
        self,
        limit: Optional[int] = None,
        speaker: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[ConversationTurn]:
        """
        Get conversation history
        
        Args:
            limit: Maximum number of turns
            speaker: Filter by speaker
            session_id: Optional session ID
            
        Returns:
            List of ConversationTurn objects
        """
        context = self.get_context(session_id) if session_id else self.current_context
        
        if not context:
            return []
        
        turns = context.turns
        
        # Filter by speaker
        if speaker:
            turns = [t for t in turns if t.speaker == speaker]
        
        # Limit results
        if limit:
            turns = turns[-limit:]
        
        return turns
    
    def get_context_summary(
        self,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get context summary
        
        Args:
            session_id: Optional session ID
            
        Returns:
            Context summary dictionary
        """
        context = self.get_context(session_id) if session_id else self.current_context
        
        if not context:
            return {}
        
        return {
            "session_id": context.session_id,
            "language": context.language,
            "scenario": context.scenario,
            "turn_count": len(context.turns),
            "duration": time.time() - context.start_time,
            "last_activity": context.last_activity,
            "user_profile": context.user_profile
        }
    
    def set_scenario(
        self,
        scenario: str,
        session_id: Optional[str] = None
    ) -> None:
        """
        Set conversation scenario
        
        Args:
            scenario: Scenario name
            session_id: Optional session ID
        """
        context = self.get_context(session_id) if session_id else self.current_context
        
        if context:
            context.scenario = scenario
            logger.info(f"Set scenario: {scenario}")
    
    def set_language(
        self,
        language: str,
        session_id: Optional[str] = None
    ) -> None:
        """
        Set conversation language
        
        Args:
            language: Language code
            session_id: Optional session ID
        """
        context = self.get_context(session_id) if session_id else self.current_context
        
        if context:
            context.language = language
            logger.info(f"Set language: {language}")
    
    def update_user_profile(
        self,
        profile_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> None:
        """
        Update user profile
        
        Args:
            profile_data: Profile data to update
            session_id: Optional session ID
        """
        context = self.get_context(session_id) if session_id else self.current_context
        
        if context:
            context.user_profile.update(profile_data)
            logger.debug(f"Updated user profile: {list(profile_data.keys())}")
    
    def set_metadata(
        self,
        key: str,
        value: Any,
        session_id: Optional[str] = None
    ) -> None:
        """
        Set context metadata
        
        Args:
            key: Metadata key
            value: Metadata value
            session_id: Optional session ID
        """
        context = self.get_context(session_id) if session_id else self.current_context
        
        if context:
            context.metadata[key] = value
    
    def get_metadata(
        self,
        key: str,
        default: Any = None,
        session_id: Optional[str] = None
    ) -> Any:
        """
        Get context metadata
        
        Args:
            key: Metadata key
            default: Default value if not found
            session_id: Optional session ID
            
        Returns:
            Metadata value
        """
        context = self.get_context(session_id) if session_id else self.current_context
        
        if context:
            return context.metadata.get(key, default)
        
        return default
    
    def delete_context(self, session_id: str) -> None:
        """
        Delete context
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.contexts:
            del self.contexts[session_id]
            
            if self.current_context and self.current_context.session_id == session_id:
                self.current_context = None
            
            logger.info(f"Deleted context: {session_id}")
    
    def clear_all_contexts(self) -> None:
        """Clear all contexts"""
        self.contexts.clear()
        self.current_context = None
        logger.info("Cleared all contexts")
    
    def cleanup_expired_contexts(self) -> int:
        """
        Clean up expired contexts
        
        Returns:
            Number of contexts deleted
        """
        current_time = time.time()
        expired = []
        
        for session_id, context in self.contexts.items():
            if current_time - context.last_activity > self.context_timeout:
                expired.append(session_id)
        
        for session_id in expired:
            self.delete_context(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired contexts")
        
        return len(expired)
