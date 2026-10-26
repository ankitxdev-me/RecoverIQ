import React, { useState, useEffect } from 'react';
import {
  X,
  HardDrive,
  Download,
  Trash2,
  CheckCircle2,
  MessageSquare,
  Upload,
  Shield,
  Activity,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api/client';

interface SessionHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SessionHistoryModal: React.FC<SessionHistoryModalProps> = ({ isOpen, onClose }) => {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<string>('ALL');

  const fetchSessionEvents = async () => {
    setLoading(true);
    try {
      const res = await api.getSessionEvents(200);
      setEvents(res.events || []);
    } catch (e) {
      console.error('Failed to load session events', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSessionEvents();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const filteredEvents = events.filter((evt) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'APPROVALS') return evt.event_type.includes('APPROV') || evt.event_type.includes('REJECT');
    if (filterType === 'CHATS') return evt.event_type.includes('CHAT') || evt.event_type.includes('BOT');
    if (filterType === 'UPLOADS') return evt.event_type.includes('UPLOAD') || evt.event_type.includes('DATA');
    return true;
  });

  const handleClearSession = async () => {
    if (!window.confirm('Clear all local session records from this device?')) return;
    try {
      await api.clearSessionEvents();
      localStorage.removeItem('recoveriq_chat_history');
      setEvents([]);
    } catch (e) {
      console.error('Failed to clear session', e);
    }
  };

  const handleExportJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(events, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `recoveriq_local_session_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                Local Device Session & Action Ledger
                <span className="text-[10px] font-mono uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                  Saved on Device
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Persistent storage of every user chat, database crawl, and approved recovery action.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExportJson}
              disabled={events.length === 0}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-all cursor-pointer disabled:opacity-40"
              title="Download local session JSON"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={handleClearSession}
              disabled={events.length === 0}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 text-xs font-medium transition-all cursor-pointer disabled:opacity-40"
              title="Clear session history"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-900/40 text-xs">
          <div className="flex items-center gap-2">
            {[
              { id: 'ALL', label: `All Events (${events.length})` },
              { id: 'APPROVALS', label: 'Approvals & Actions' },
              { id: 'CHATS', label: 'Bot Chats' },
              { id: 'UPLOADS', label: 'Data Ingestions' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilterType(f.id)}
                className={`px-3 py-1 rounded-full font-medium transition-all ${
                  filterType === f.id
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <button
            onClick={fetchSessionEvents}
            className="text-slate-400 hover:text-indigo-400 flex items-center gap-1 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Events List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {loading ? (
            <div className="text-center py-12 text-slate-400 text-sm">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              Reading local device session logs...
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              <HardDrive className="w-8 h-8 mx-auto mb-2 opacity-40 text-slate-400" />
              No local events recorded in this category yet.
            </div>
          ) : (
            filteredEvents.map((evt) => {
              const isApproval = evt.event_type.includes('APPROV') || evt.event_type.includes('REJECT');
              const isChat = evt.event_type.includes('CHAT') || evt.event_type.includes('BOT');
              const isUpload = evt.event_type.includes('UPLOAD') || evt.event_type.includes('DATABASE');

              let Icon = Activity;
              let badgeColor = 'bg-slate-800 text-slate-300';
              if (isApproval) {
                Icon = Shield;
                badgeColor = evt.event_type.includes('APPROV')
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-300 border-rose-500/30';
              } else if (isChat) {
                Icon = MessageSquare;
                badgeColor = 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
              } else if (isUpload) {
                Icon = Upload;
                badgeColor = 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
              }

              return (
                <div
                  key={evt.id}
                  className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all space-y-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-indigo-400">
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] border ${badgeColor}`}>
                        {evt.event_type}
                      </span>
                      <span className="text-slate-400">by <span className="text-slate-200 font-medium">{evt.actor}</span></span>
                    </div>

                    <span className="text-slate-500 font-mono text-[11px]">
                      {new Date(evt.timestamp).toLocaleString()}
                    </span>
                  </div>

                  {/* Event Details Content */}
                  <div className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60 font-mono">
                    {isChat && evt.data ? (
                      <div className="space-y-1 font-sans">
                        <p><span className="text-slate-400 font-bold">User:</span> {evt.data.user_message}</p>
                        {evt.data.bot_reply && (
                          <p className="text-slate-300 line-clamp-2">
                            <span className="text-indigo-400 font-bold">Bot:</span> {evt.data.bot_reply}
                          </p>
                        )}
                        {evt.data.tools_called?.length > 0 && (
                          <p className="text-[11px] text-emerald-400 font-mono">
                            Tools executed: {evt.data.tools_called.join(', ')}
                          </p>
                        )}
                      </div>
                    ) : isApproval && evt.data ? (
                      <div className="space-y-0.5 font-sans">
                        <p>
                          <span className="text-slate-400 font-bold">Action ID:</span> {evt.data.action_id} |{' '}
                          <span className="text-slate-400 font-bold">Decision:</span>{' '}
                          <span className={evt.data.decision === 'APPROVE' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                            {evt.data.decision}
                          </span>
                        </p>
                        <p><span className="text-slate-400 font-bold">Rationale:</span> {evt.data.reason}</p>
                      </div>
                    ) : isUpload && evt.data ? (
                      <div className="space-y-0.5 font-sans">
                        <p><span className="text-slate-400 font-bold">File:</span> {evt.data.filename} ({evt.data.file_size_bytes} bytes)</p>
                        <p className="text-indigo-300">
                          {evt.data.records_inspected} rows crawled | {evt.data.cases_created} cases generated | Loss: {evt.data.loss_at_risk}
                        </p>
                      </div>
                    ) : (
                      <pre className="text-[11px] whitespace-pre-wrap">{JSON.stringify(evt.data, null, 2)}</pre>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
          <span>Local Device Storage: <code className="text-indigo-300 font-mono">backend/sessions/audit_session.jsonl</code></span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
