import uuid
from enum import Enum

from pydantic import BaseModel, Field


class SpeakerOverride(str, Enum):
    USER = "user"
    AI = "ai"

class StreamingState(str, Enum):
    CONNECTED = "connected"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    DISCONNECTED = "disconnected"

class VoiceSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: int
    user_id: int
    current_speaker: SpeakerOverride = SpeakerOverride.USER
    partial_transcript: str = ""
    streaming_state: StreamingState = StreamingState.CONNECTED
    interruption_state: bool = False
    
    def barge_in(self) -> None:
        """Called when user starts speaking while AI is talking."""
        self.interruption_state = True
        self.current_speaker = SpeakerOverride.USER
        self.streaming_state = StreamingState.LISTENING
        self.partial_transcript = ""

    def ai_starts_speaking(self) -> None:
        """Called when AI begins transmitting audio chunks."""
        self.interruption_state = False
        self.current_speaker = SpeakerOverride.AI
        self.streaming_state = StreamingState.SPEAKING
