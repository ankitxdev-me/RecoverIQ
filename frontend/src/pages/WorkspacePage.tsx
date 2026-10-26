import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Cpu,
  Bot,
  User,
  Wrench,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Play,
  RotateCcw,
} from 'lucide-react';
import { AgentChatResponse, AgentToolCallInfo, RecoveryCase } from '../types';
import { api } from '../api/client';

interface WorkspacePageProps {
  initialCaseId?: string | null;
  onNavigateTab: (tab: string) => void;
  onOpenCaseModal: (caseId: string) => void;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  content: string;
  toolsCalled?: AgentToolCallInfo[];
  source?: string;
  requiresApproval?: boolean;
  proposedActionId?: string;
  timestamp: string;
}

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  initialCaseId,
  onNavigateTab,
  onOpenCaseModal,
}) => {
  const defaultInitialMessage: ChatMessage = {
    id: 'init-1',
    sender: 'agent',
    content:
      'Hello! I am RecoverIQ, your AI Revenue Recovery Agent.\n\nI monitor failed payments, overdue invoices, and abandoned checkouts. You can ask me to rank high-priority cases, perform deep diagnostic investigations, draft customer dunning notices, or execute permitted simulated actions.\n\nWhat would you like to investigate today?',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    source: 'gemma4:e2b',
  };

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem('recoveriq_chat_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn('Failed to parse saved chat history', e);
    }
    return [defaultInitialMessage];
  });

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(initialCaseId || '');
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sync chat messages to local storage whenever updated
  useEffect(() => {
    try {
      localStorage.setItem('recoveriq_chat_history', JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to persist chat history to local storage', e);
    }
  }, [messages]);

  useEffect(() => {
    if (initialCaseId) {
      setSelectedCaseId(initialCaseId);
    }
  }, [initialCaseId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleClearChatHistory = () => {
    if (window.confirm('Clear all conversation messages from this device?')) {
      localStorage.removeItem('recoveriq_chat_history');
      setMessages([defaultInitialMessage]);
    }
  };

  const promptSuggestions = [
    'Which five cases should I handle first?',
    'What is the total amount at risk?',
    'Investigate case CASE-PAY-1001',
    'Why is invoice CASE-INV-2002 high priority?',
    'Draft a polite reminder for CASE-PAY-1001',
    'Why can abandoned carts not be retried automatically?',
  ];

  const handleSend = async (messageText: string) => {
    if (!messageText.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.sendAgentMessage(messageText, selectedCaseId || undefined);
      const agentMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        sender: 'agent',
        content: res.reply,
        toolsCalled: res.tools_called,
        source: res.source,
        requiresApproval: res.requires_approval,
        proposedActionId: res.proposed_action_id,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'agent',
        content: `Error contacting agent service: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        source: 'error',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const toggleToolExpand = (toolId: string) => {
    setExpandedTools((prev) => ({ ...prev, [toolId]: !prev[toolId] }));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-12rem)]">
      {/* Left Sidebar: Context & Prompt Suggestions */}
      <div className="lg:col-span-1 space-y-4 flex flex-col h-full">
        {/* Active Context Box */}
        <div className="p-4 rounded-xl glass-card space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Investigation Scope
          </span>
          <input
            type="text"
            placeholder="Focus Case ID (e.g. CASE-PAY-1001)"
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs font-mono text-indigo-300 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          {selectedCaseId && (
            <button
              onClick={() => setSelectedCaseId('')}
              className="text-[11px] text-slate-400 hover:text-slate-200 underline"
            >
              Clear case filter (global query)
            </button>
          )}
        </div>

        {/* Prompt Suggestions */}
        <div className="p-4 rounded-xl glass-card space-y-2.5 flex-1 overflow-y-auto">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Suggested Queries
          </span>
          <div className="space-y-1.5">
            {promptSuggestions.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                disabled={loading}
                className="w-full text-left p-2 rounded-lg bg-slate-900/60 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-700/60 text-xs text-slate-300 hover:text-indigo-200 transition-all flex items-start gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                <span className="line-clamp-2">{prompt}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Agent Guardrail Notice */}
        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-xl text-[11px] text-slate-400 space-y-1">
          <div className="flex items-center gap-1.5 text-indigo-400 font-semibold">
            <Cpu className="w-3.5 h-3.5" />
            <span>Financial Safeguards Active</span>
          </div>
          <p>
            Agent queries run through allowlisted Python tools with Pydantic schemas. Financial totals
            are queried directly from the SQLite ledger.
          </p>
        </div>
      </div>

      {/* Main Chat Stream & Input Area */}
      <div className="lg:col-span-3 glass-panel rounded-2xl border border-slate-800 flex flex-col h-full overflow-hidden shadow-2xl">
        {/* Chat Stream Header */}
        <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-900/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-semibold text-slate-200">Gemma 4 AI Recovery Session</span>
            <span className="text-[10px] font-mono uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full">
              Stored Locally
            </span>
          </div>
          <button
            onClick={handleClearChatHistory}
            className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 hover:bg-slate-800 px-2.5 py-1 rounded-md transition-colors"
            title="Clear conversation history from this device"
          >
            <RotateCcw className="w-3 h-3 text-slate-400" />
            <span>Clear Local Chat</span>
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    isUser
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800 border border-slate-700 text-indigo-400'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Bubble */}
                <div className="space-y-2">
                  <div
                    className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                      isUser
                        ? 'bg-indigo-600 text-white rounded-tr-none'
                        : 'bg-slate-800/90 text-slate-200 border border-slate-700/80 rounded-tl-none'
                    }`}
                  >
                    <div className="whitespace-pre-wrap font-sans">{msg.content}</div>

                    {/* Metadata Footer */}
                    <div className="flex items-center justify-between gap-4 mt-2 pt-2 border-t border-slate-700/40 text-[10px] text-slate-400">
                      <span>{msg.timestamp}</span>
                      {!isUser && msg.source && (
                        <span className="font-mono bg-slate-900/60 px-1.5 py-0.5 rounded text-indigo-300">
                          {msg.source}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Tool Invocations Timeline */}
                  {!isUser && msg.toolsCalled && msg.toolsCalled.length > 0 && (
                    <div className="space-y-2 pt-1">
                      <div className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
                        <Wrench className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Validated Agent Tool Actions ({msg.toolsCalled.length})</span>
                      </div>
                      {msg.toolsCalled.map((tool, idx) => {
                        const toolKey = `${msg.id}-tool-${idx}`;
                        const isExpanded = expandedTools[toolKey];
                        return (
                          <div
                            key={toolKey}
                            className="rounded-xl bg-slate-950/80 border border-slate-800 overflow-hidden text-xs font-mono"
                          >
                            <button
                              onClick={() => toggleToolExpand(toolKey)}
                              className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-slate-900/80 transition-colors"
                            >
                              <div className="flex items-center gap-2">
                                <span className="text-emerald-400 font-bold">✓</span>
                                <span className="text-indigo-300 font-bold">{tool.tool_name}</span>
                              </div>
                              {isExpanded ? (
                                <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                              ) : (
                                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                              )}
                            </button>

                            {isExpanded && (
                              <div className="p-3 border-t border-slate-800/80 space-y-2 text-[11px] bg-slate-950">
                                <div>
                                  <span className="text-slate-500 block mb-0.5">Parameters:</span>
                                  <pre className="text-slate-300 bg-slate-900 p-2 rounded border border-slate-800 overflow-x-auto">
                                    {JSON.stringify(tool.parameters, null, 2)}
                                  </pre>
                                </div>
                                <div>
                                  <span className="text-slate-500 block mb-0.5">Verified Database Output:</span>
                                  <pre className="text-emerald-300 bg-slate-900 p-2 rounded border border-slate-800 overflow-x-auto">
                                    {JSON.stringify(tool.result, null, 2)}
                                  </pre>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-3 text-xs text-indigo-400 animate-pulse">
              <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                <Bot className="w-4 h-4 animate-spin text-indigo-400" />
              </div>
              <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/60">
                Ollama model is executing validated recovery tools...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input Box */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(input);
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              placeholder="Ask RecoverIQ to investigate cases, prioritize debt, draft messages..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              className="flex-1 px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white font-medium text-xs sm:text-sm flex items-center gap-1.5 transition-all shadow-lg shadow-indigo-600/30"
            >
              <span>Send</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
