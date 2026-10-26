import re
import json
import httpx
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.agent.prompts import SYSTEM_PROMPT
from backend.app.agent.tools import AVAILABLE_TOOLS, execute_tool_safely
from backend.app.schemas import AgentChatResponse, AgentToolCallInfo
from backend.app.models import RecoveryCase, ApprovalRecord

def get_ollama_tools_schema() -> List[Dict[str, Any]]:
    """Formats available tools for Ollama /api/chat tool-calling API."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"]
            }
        }
        for t in AVAILABLE_TOOLS
    ]

class OllamaClient:
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = settings.OLLAMA_REQUEST_TIMEOUT

    def check_health(self) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Verifies that the Ollama service is reachable and the exact configured model is available.
        Never reports connected simply because the variable is set.
        """
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                if resp.status_code != 200:
                    return False, f"Ollama HTTP error {resp.status_code}", None
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                matched = any(self.model in m or m.startswith(self.model) for m in models)
                if not matched:
                    return False, f"Model '{self.model}' not found in installed Ollama models: {models}", data
                return True, None, data
        except Exception as e:
            return False, f"Ollama unreachable at {self.base_url}: {str(e)}", None

    def _call_ollama(self, messages: List[Dict[str, Any]], use_tools: bool = True) -> Dict[str, Any]:
        """Sends request to local Ollama /api/chat."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": settings.OLLAMA_MAX_CONTEXT_TOKENS
            }
        }
        if use_tools:
            payload["tools"] = get_ollama_tools_schema()

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/chat", json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            return data.get("message", {})

    def _extract_tool_call_from_text(self, content: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Fallback tool extractor if the model outputs JSON in text."""
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, content, re.DOTALL)
        candidate = match.group(1) if match else content.strip()

        try:
            if candidate.startswith("{") and candidate.endswith("}"):
                parsed = json.loads(candidate)
                tool_name = parsed.get("tool") or parsed.get("name")
                args = parsed.get("arguments") or parsed.get("parameters") or {}
                if tool_name and any(t["name"] == tool_name for t in AVAILABLE_TOOLS):
                    return tool_name, args
        except Exception:
            pass

        try:
            brace_matches = re.findall(r"\{[^{}]*\"tool\"\s*:\s*\"[^\"]+\"[^{}]*\}", content)
            for m in brace_matches:
                parsed = json.loads(m)
                tool_name = parsed.get("tool")
                args = parsed.get("arguments", {})
                if tool_name:
                    return tool_name, args
        except Exception:
            pass

        return None

    def run_agent_turn(self, user_message: str, case_id: Optional[str], db: Session) -> AgentChatResponse:
        """
        Executes an agent turn using the local Qwen2.5 3B model.
        Supports native tool calling with Pydantic validation,
        deterministic financial fact verification, and fallback.
        """
        is_healthy, health_err, _ = self.check_health()
        if not is_healthy:
            return self._deterministic_fallback(user_message, case_id, db, reason=health_err)

        # Build message history with strong financial integrity instructions
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        if case_id:
            case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
            if case:
                messages.append({
                    "role": "system",
                    "content": (
                        f"Active Focused Case: {case.id} | Source: {case.source_type} | "
                        f"Amount: ${case.amount_cents/100:.2f} {case.currency} | Priority: {case.priority} "
                        f"(Score: {case.priority_score}) | Status: {case.status} | Failure Reason: {case.failure_reason}."
                    )
                })

        messages.append({"role": "user", "content": user_message})

        tools_called: List[AgentToolCallInfo] = []
        max_steps = 2
        requires_approval = False
        proposed_action_id = None

        try:
            for step in range(max_steps):
                msg_resp = self._call_ollama(messages, use_tools=True)
                tool_calls = msg_resp.get("tool_calls", [])
                text_content = msg_resp.get("content", "").strip()

                # 1. Native Tool Calling handling
                if tool_calls:
                    for tc in tool_calls:
                        func_obj = tc.get("function", {})
                        t_name = func_obj.get("name")
                        t_args = func_obj.get("arguments", {})
                        if isinstance(t_args, str):
                            try:
                                t_args = json.loads(t_args)
                            except Exception:
                                t_args = {}

                        # Supply focused case_id if omitted
                        if case_id and "case_id" not in t_args and t_name in (
                            "investigate_case", "get_case_details", "recommend_recovery_action",
                            "draft_customer_message", "request_action_approval"
                        ):
                            t_args["case_id"] = case_id

                        # Execute verified tool
                        t_result = execute_tool_safely(t_name, t_args, db)
                        tools_called.append(AgentToolCallInfo(
                            tool_name=t_name,
                            parameters=t_args,
                            result=t_result
                        ))

                        if t_name == "request_action_approval" and "action_id" in t_result:
                            requires_approval = True
                            proposed_action_id = t_result["action_id"]

                    # Add assistant tool call and tool result back to conversation
                    messages.append(msg_resp)
                    # Feed tool results as tool response
                    for tc, info in zip(tool_calls, tools_called[-len(tool_calls):]):
                        tool_msg: Dict[str, Any] = {
                            "role": "tool",
                            "content": json.dumps(info.result),
                            "name": info.tool_name
                        }
                        if tc.get("id"):
                            tool_msg["tool_call_id"] = tc["id"]
                        messages.append(tool_msg)

                    # Second call: let Qwen reason over the verified tool output
                    final_resp = self._call_ollama(messages, use_tools=False)
                    final_text = final_resp.get("content", "").strip()
                    if not final_text and final_resp.get("thinking"):
                        final_text = final_resp.get("thinking", "").strip()

                    # Compose final response with Verified Database Ledger facts at top
                    formatted_reply = self._format_verified_response(tools_called, final_text)
                    return AgentChatResponse(
                        reply=formatted_reply,
                        case_id=case_id,
                        tools_called=tools_called,
                        requires_approval=requires_approval,
                        proposed_action_id=proposed_action_id,
                        source=f"{self.model} (native-tool-calling)"
                    )

                # 2. Text-based tool extraction fallback
                text_tool = self._extract_tool_call_from_text(text_content)
                if text_tool:
                    t_name, t_args = text_tool
                    if case_id and "case_id" not in t_args:
                        t_args["case_id"] = case_id

                    t_result = execute_tool_safely(t_name, t_args, db)
                    tools_called.append(AgentToolCallInfo(
                        tool_name=t_name,
                        parameters=t_args,
                        result=t_result
                    ))

                    messages.append({"role": "assistant", "content": text_content})
                    messages.append({
                        "role": "user",
                        "content": f"Verified Tool '{t_name}' Result:\n{json.dumps(t_result, indent=2)}\nExplain the findings clearly to the user."
                    })

                    final_resp = self._call_ollama(messages, use_tools=False)
                    final_text = final_resp.get("content", "").strip()
                    if not final_text and final_resp.get("thinking"):
                        final_text = final_resp.get("thinking", "").strip()
                    formatted_reply = self._format_verified_response(tools_called, final_text)

                    return AgentChatResponse(
                        reply=formatted_reply,
                        case_id=case_id,
                        tools_called=tools_called,
                        source=f"{self.model} (structured-protocol)"
                    )

                # 3. Direct conversational answer (no tools requested by model)
                if not text_content and msg_resp.get("thinking"):
                    text_content = msg_resp.get("thinking", "").strip()

                if text_content:
                    return AgentChatResponse(
                        reply=text_content,
                        case_id=case_id,
                        tools_called=[],
                        source=f"{self.model} (direct)"
                    )

            # Fallback if loop ended without answer
            return self._deterministic_fallback(user_message, case_id, db, reason="Max turns reached")

        except Exception as e:
            # Resilient fallback on timeout or error
            return self._deterministic_fallback(
                user_message, case_id, db, reason=f"Ollama inference error: {str(e)}"
            )

    def _format_verified_response(self, tools_called: List[AgentToolCallInfo], ai_reasoning: str) -> str:
        """
        Combines verified database facts with Qwen's analytical reasoning.
        This ensures that financial calculations are NEVER corrupted by small model tokenization,
        while fully utilizing Qwen's linguistic reasoning, dunning draftsmanship, and strategy.
        """
        sections = []

        # Build Verified Database Facts section
        for t in tools_called:
            res = t.result
            if t.tool_name == "get_dashboard_summary":
                sections.append(
                    f"### 📊 Verified Financial Ledger (Direct DB Query)\n"
                    f"- **Total Revenue at Risk**: `{res.get('revenue_at_risk_display')}`\n"
                    f"- **Eligible for Active Recovery**: `{res.get('eligible_recovery_display')}`\n"
                    f"- **Confirmed Recovered (Live)**: `{res.get('confirmed_live_recovered_display')}`\n"
                    f"- **Simulated Recovered (Sandbox)**: `{res.get('simulated_recovered_display')}`\n"
                    f"- **Open Cases**: {res.get('open_cases_count')} | **Pending Approvals**: {res.get('pending_approvals_count')}"
                )
            elif t.tool_name == "list_recovery_cases":
                cases = res.get("cases", [])
                lines = [f"### 📋 Verified Priority Ranking (Multi-Factor Scoring Engine)"]
                for idx, c in enumerate(cases[:5], 1):
                    lines.append(
                        f"{idx}. **{c['id']}** ({c['source_type']}) — **{c['amount_display']}** | "
                        f"Priority: `{c['priority']}` (Score: {c['priority_score']}) | Customer: *{c['customer_name']}* | Next: `{c['recommended_action']}`"
                    )
                sections.append("\n".join(lines))
            elif t.tool_name in ("get_case_details", "investigate_case"):
                if "error" not in res:
                    sections.append(
                        f"### 🔍 Case Investigation Facts: {res.get('case_id')}\n"
                        f"- **Customer**: {res.get('customer', {}).get('name')} ({res.get('customer', {}).get('email')})\n"
                        f"- **Amount**: **{res.get('amount_display')}** | **Type**: `{res.get('source_type')}`\n"
                        f"- **Status**: `{res.get('status')}` | **Priority**: `{res.get('priority')}` (Score: {res.get('priority_score')}/100)\n"
                        f"- **Failure Diagnostic**: {res.get('failure_reason')}\n"
                        f"- **Retry Count**: {res.get('retry_count')} of {res.get('max_retries')} | **Eligible**: {'Yes' if res.get('is_eligible_for_recovery') else 'No (' + res.get('eligibility_notes', '') + ')'}"
                    )
            elif t.tool_name == "recommend_recovery_action":
                sections.append(
                    f"### 🛡️ Verified Recovery Engine Recommendation\n"
                    f"- **Recommended Action**: `{res.get('recommended_action')}`\n"
                    f"- **Requires Human Approval**: **{'YES (Protected Action)' if res.get('requires_human_approval') else 'NO (Pre-approved)'}**\n"
                    f"- **Engine Rationale**: {res.get('rationale')}"
                )
            elif t.tool_name == "draft_customer_message":
                sections.append(
                    f"### ✉️ Drafted Recovery Communication\n"
                    f"**Subject**: {res.get('subject')}\n\n"
                    f"```text\n{res.get('body')}\n```"
                )

        # Append Qwen's strategic reasoning
        if ai_reasoning:
            sections.append(f"### 🤖 AI Agent Analysis & Strategy (Qwen2.5 3B)\n{ai_reasoning}")

        return "\n\n".join(sections)

    def _deterministic_fallback(
        self,
        user_message: str,
        case_id: Optional[str],
        db: Session,
        reason: Optional[str] = None
    ) -> AgentChatResponse:
        """Deterministic offline fallback ensuring 100% demo continuity."""
        msg_lower = user_message.lower()
        tools_called = []

        if "at risk" in msg_lower or "summary" in msg_lower or "total" in msg_lower:
            result = execute_tool_safely("get_dashboard_summary", {}, db)
            tools_called.append(AgentToolCallInfo(tool_name="get_dashboard_summary", parameters={}, result=result))
            reply = (
                f"### Revenue Recovery Summary (Deterministic Engine)\n\n"
                f"- **Total Revenue at Risk**: {result['revenue_at_risk_display']}\n"
                f"- **Eligible for Active Recovery**: {result['eligible_recovery_display']}\n"
                f"- **Confirmed Live Recovered**: {result['confirmed_live_recovered_display']}\n"
                f"- **Simulated Recovered**: {result['simulated_recovered_display']} *(Sandbox)*\n"
                f"- **Open Cases**: {result['open_cases_count']}\n"
                f"- **Pending Human Approvals**: {result['pending_approvals_count']}\n\n"
                f"*Note: Live recovered revenue is strictly segregated from simulated sandbox outcomes.*"
            )
            return AgentChatResponse(reply=reply, case_id=case_id, tools_called=tools_called, source="deterministic_fallback")

        if "five cases" in msg_lower or "first" in msg_lower or "priority" in msg_lower or "list" in msg_lower:
            result = execute_tool_safely("list_recovery_cases", {"limit": 5}, db)
            tools_called.append(AgentToolCallInfo(tool_name="list_recovery_cases", parameters={"limit": 5}, result=result))
            cases = result.get("cases", [])
            lines = [f"### Top Priority Recovery Cases\n"]
            for idx, c in enumerate(cases, 1):
                lines.append(f"{idx}. **{c['id']}** ({c['source_type']}) — **{c['amount_display']}** | Priority: `{c['priority']}` (Score: {c['priority_score']}) | Customer: {c['customer_name']} | Next: `{c['recommended_action']}`")
            lines.append("\n*These cases were ranked using transparent multi-factor scoring (Amount + Age + Recoverability).*")
            return AgentChatResponse(reply="\n".join(lines), case_id=case_id, tools_called=tools_called, source="deterministic_fallback")

        target_case_id = case_id
        m = re.search(r"(CASE-[A-Z]+-\d+)", user_message.upper())
        if m:
            target_case_id = m.group(1)

        if target_case_id:
            inv_res = execute_tool_safely("investigate_case", {"case_id": target_case_id}, db)
            tools_called.append(AgentToolCallInfo(tool_name="investigate_case", parameters={"case_id": target_case_id}, result=inv_res))

            if "error" in inv_res:
                return AgentChatResponse(
                    reply=f"Could not investigate case: {inv_res['error']}",
                    case_id=target_case_id,
                    tools_called=tools_called,
                    source="deterministic_fallback"
                )

            if "draft" in msg_lower or "message" in msg_lower or "email" in msg_lower:
                draft_res = execute_tool_safely("draft_customer_message", {"case_id": target_case_id, "tone": "polite"}, db)
                tools_called.append(AgentToolCallInfo(tool_name="draft_customer_message", parameters={"case_id": target_case_id}, result=draft_res))
                reply = (
                    f"### Drafted Customer Recovery Message for {target_case_id}\n\n"
                    f"**Recipient**: {draft_res.get('recipient')}\n"
                    f"**Subject**: {draft_res.get('subject')}\n\n"
                    f"```text\n{draft_res.get('body')}\n```\n\n"
                    f"You can review and dispatch this simulated notice from the case view."
                )
                return AgentChatResponse(reply=reply, case_id=target_case_id, tools_called=tools_called, source="deterministic_fallback")

            rec_res = execute_tool_safely("recommend_recovery_action", {"case_id": target_case_id}, db)
            tools_called.append(AgentToolCallInfo(tool_name="recommend_recovery_action", parameters={"case_id": target_case_id}, result=rec_res))

            reply = (
                f"### Case Investigation: {target_case_id}\n\n"
                f"- **Customer**: {inv_res['customer']['name']} ({inv_res['customer']['email']})\n"
                f"- **Type**: `{inv_res['source_type']}` | **Amount**: **{inv_res['amount_display']}**\n"
                f"- **Status**: `{inv_res['status']}` | **Priority**: `{inv_res['priority']}` (Score: {inv_res['priority_score']})\n"
                f"- **Failure Diagnostic**: {inv_res['failure_reason']}\n"
                f"- **Retry History**: {inv_res['retry_count']} of {inv_res['max_retries']} retries utilized\n"
                f"- **Eligibility**: {'Eligible for recovery action' if inv_res['is_eligible_for_recovery'] else 'Not actionable (' + inv_res['eligibility_notes'] + ')'}\n\n"
                f"**Engine Recommendation**:\n"
                f"Recommended Action: `{rec_res.get('recommended_action')}`\n"
                f"- Requires Human Approval: **{'Yes' if rec_res.get('requires_human_approval') else 'No'}**\n"
                f"- Rationale: {rec_res.get('rationale')}"
            )
            return AgentChatResponse(reply=reply, case_id=target_case_id, tools_called=tools_called, source="deterministic_fallback")

        if "approval" in msg_lower or "pending" in msg_lower:
            approvals = db.query(ApprovalRecord).filter(ApprovalRecord.status == "PENDING").all()
            lines = [f"### 🛡️ Cases Awaiting Human Approval ({len(approvals)})\n"]
            for a in approvals:
                lines.append(f"- **Case {a.case_id}**: Action `{a.action.action_type if a.action else 'ACTION'}` | Reason: {a.reason} | Consequence: *{a.potential_consequence}*")
            if not approvals:
                lines.append("No cases are currently awaiting approval.")
            return AgentChatResponse(reply="\n".join(lines), case_id=case_id, tools_called=[], source="deterministic_fallback")

        return AgentChatResponse(
            reply=(
                f"Hello! I am RecoverIQ, your AI Revenue Recovery Agent.\n\n"
                f"I can assist you with:\n"
                f"- Investigating failed payments, overdue invoices, and abandoned carts.\n"
                f"- Calculating priority scores and explaining recovery eligibility.\n"
                f"- Recommending and validating next recovery actions under financial guardrails.\n"
                f"- Drafting customer dunning communications and scheduling payment retries.\n\n"
                f"Try asking:\n"
                f"- *'Which five cases should I handle first, and why?'*\n"
                f"- *'What is the total amount at risk?'*\n"
                f"- *'Investigate case CASE-PAY-1001'* or *'Draft a polite reminder for CASE-INV-2002'*"
            ),
            case_id=case_id,
            tools_called=[],
            source="deterministic_fallback"
        )
