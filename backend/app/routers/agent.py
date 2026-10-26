from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.agent.ollama_client import OllamaClient
from backend.app.schemas import AgentChatRequest, AgentChatResponse

from backend.app.services.session_logger import log_session_event

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])

@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(req: AgentChatRequest, db: Session = Depends(get_db)):
    client = OllamaClient()
    response = client.run_agent_turn(
        user_message=req.message,
        case_id=req.case_id,
        db=db
    )
    
    # Store complete chat interaction and tools called to local device session
    log_session_event(
        event_type="BOT_CHAT_INTERACTION",
        actor="USER",
        data={
            "user_message": req.message,
            "case_id": req.case_id,
            "bot_reply": response.reply,
            "tools_called": [t.tool_name for t in response.tools_called],
            "requires_approval": response.requires_approval,
            "source": response.source
        }
    )
    return response
