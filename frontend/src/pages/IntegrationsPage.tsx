import React, { useState, useEffect } from 'react';
import {
  Radio,
  Cpu,
  Database,
  ShieldCheck,
  Upload,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  FileSpreadsheet,
  Download,
} from 'lucide-react';
import { IntegrationConnection, SystemHealth, ImportResult } from '../types';
import { api } from '../api/client';

interface IntegrationsPageProps {
  health: SystemHealth | null;
  onRefreshHealth: () => void;
  onRefreshSummary: () => void;
}

export const IntegrationsPage: React.FC<IntegrationsPageProps> = ({
  health,
  onRefreshHealth,
  onRefreshSummary,
}) => {
  const [connectors, setConnectors] = useState<IntegrationConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [ollamaDiag, setOllamaDiag] = useState<any>(null);

  // CSV Import State
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [recordType, setRecordType] = useState('payments');
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [conns, diag] = await Promise.all([
        api.getIntegrations(),
        api.getOllamaDiagnostics(),
      ]);
      setConnectors(conns);
      setOllamaDiag(diag);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCsvUpload = async () => {
    if (!csvFile) return;
    setImportLoading(true);
    setImportResult(null);
    setImportError(null);

    try {
      const res = await api.importCsv(csvFile, recordType);
      setImportResult(res);
      onRefreshSummary();
    } catch (err: any) {
      setImportError(err.message || 'Import failed');
    } finally {
      setImportLoading(false);
    }
  };

  const loadSampleData = (type: string) => {
    let sampleContent = '';
    let fileName = '';

    if (type === 'payments') {
      fileName = 'sample_payments.csv';
      sampleContent = `external_id,customer_ref,customer_name,customer_email,amount,currency,status,failure_code,failure_reason
tx_demo_801,CUST-DEMO-1,Solaris Energy,billing@solarisenergy.com,2400.00,USD,FAILED,insufficient_funds,Declined due to daily limit
tx_demo_802,CUST-DEMO-2,AeroSpace Dynamics,ap@aerospacedyn.com,1850.50,USD,FAILED,expired_card,Card expired on 10/26`;
    } else if (type === 'invoices') {
      fileName = 'sample_invoices.csv';
      sampleContent = `invoice_number,customer_ref,customer_name,customer_email,amount,currency,status,due_date,days_overdue
INV-DEMO-701,CUST-DEMO-3,Metro Health Systems,finance@metrohealth.org,5600.00,USD,OVERDUE,2026-09-15,41
INV-DEMO-702,CUST-DEMO-4,Pacific Marine Logistics,ap@pacificmarine.com,1250.00,USD,OVERDUE,2026-10-05,21`;
    } else {
      fileName = 'sample_checkouts.csv';
      sampleContent = `checkout_token,customer_ref,customer_name,customer_email,amount,currency,cart_items_count,status,abandoned_at
chk_demo_601,CUST-DEMO-5,Jessica Taylor,jessica.t@example.com,495.00,USD,3,ABANDONED,2026-10-25 18:30:00
chk_demo_602,CUST-DEMO-6,Michael Chen,michael.c@example.com,199.00,USD,1,ABANDONED,2026-10-25 14:15:00`;
    }

    const blob = new Blob([sampleContent], { type: 'text/csv' });
    const file = new File([blob], fileName, { type: 'text/csv' });
    setCsvFile(file);
    setRecordType(type);
  };

  return (
    <div className="space-y-6">
      {/* Diagnostics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Ollama Service Diagnostic */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-indigo-400" />
              Ollama Reasoning Engine
            </span>
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                health?.ollama_ok ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
              }`}
            />
          </div>
          <div>
            <div className="text-base font-bold text-white font-mono">
              {health?.ollama_model || 'gemma4:e2b'}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Endpoint: <span className="font-mono text-slate-300">http://localhost:11434</span>
            </p>
            <div className="mt-2 text-xs">
              Status:{' '}
              <span
                className={`font-semibold ${health?.ollama_ok ? 'text-emerald-400' : 'text-amber-400'}`}
              >
                {health?.ollama_ok
                  ? 'Online (Tools & Chat Active)'
                  : 'Offline (Deterministic Fallback Active)'}
              </span>
            </div>
          </div>
        </div>

        {/* Database Diagnostic */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Database className="w-4 h-4 text-cyan-400" />
              SQLite Ledger
            </span>
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                health?.database_ok ? 'bg-emerald-400' : 'bg-rose-400'
              }`}
            />
          </div>
          <div>
            <div className="text-base font-bold text-white font-mono">recoveriq.db</div>
            <p className="text-xs text-slate-400 mt-1">
              Engine: <span className="font-mono text-slate-300">SQLAlchemy 2.0 (PRAGMA foreign_keys=ON)</span>
            </p>
            <div className="mt-2 text-xs">
              Status:{' '}
              <span className="font-semibold text-emerald-400">
                Healthy & Transactional
              </span>
            </div>
          </div>
        </div>

        {/* Financial Sandbox Diagnostic */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              Sandbox Guardrail
            </span>
            <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
          </div>
          <div>
            <div className="text-base font-bold text-white font-mono">SIMULATION_MODE = True</div>
            <p className="text-xs text-slate-400 mt-1">
              Safety Isolation: <span className="text-purple-300 font-medium">Real funds protected</span>
            </p>
            <div className="mt-2 text-xs text-slate-400">
              Simulated outcomes strictly isolated from live revenue.
            </div>
          </div>
        </div>
      </div>

      {/* CSV Import Tool */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-bold text-white">Import Business Records (CSV)</h3>
              <p className="text-xs text-slate-400">
                Upload raw transactions, overdue invoices, or abandoned carts. The recovery engine
                validates fields, deduplicates rows, and detects actionable recovery cases automatically.
              </p>
            </div>
          </div>
        </div>

        {/* Sample Templates Quick-Load Buttons */}
        <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Load built-in sample file:</span>
          <button
            onClick={() => loadSampleData('payments')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 flex items-center gap-1 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Sample Failed Payments</span>
          </button>
          <button
            onClick={() => loadSampleData('invoices')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 flex items-center gap-1 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Sample Overdue Invoices</span>
          </button>
          <button
            onClick={() => loadSampleData('checkouts')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 flex items-center gap-1 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Sample Abandoned Carts</span>
          </button>
        </div>

        {/* Upload Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div>
            <label className="text-xs font-medium text-slate-400 block mb-1">
              Select Record Category
            </label>
            <select
              value={recordType}
              onChange={(e) => setRecordType(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="payments">Failed Payments (Transactions)</option>
              <option value="invoices">Overdue Invoices</option>
              <option value="checkouts">Abandoned Checkouts</option>
            </select>
          </div>

          <div className="sm:col-span-2 flex items-end gap-3">
            <div className="flex-1">
              <label className="text-xs font-medium text-slate-400 block mb-1">
                CSV Data File
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 file:mr-3 file:py-1 file:px-2.5 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
              />
            </div>
            <button
              onClick={handleCsvUpload}
              disabled={!csvFile || importLoading}
              className="px-5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all whitespace-nowrap"
            >
              {importLoading ? (
                <RotateCw className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              <span>Import & Run Detection</span>
            </button>
          </div>
        </div>

        {/* Import Results Banner */}
        {importResult && (
          <div className="p-4 rounded-xl bg-slate-900 border border-emerald-600/50 space-y-2 text-xs">
            <div className="flex items-center gap-2 text-emerald-400 font-bold">
              <CheckCircle2 className="w-4 h-4" />
              <span>
                CSV Import Complete: {importResult.imported_rows} rows imported,{' '}
                {importResult.skipped_duplicates} duplicates skipped.
              </span>
            </div>
            <p className="text-slate-300">
              RecoverIQ recovery engine automatically created{' '}
              <strong className="text-white font-mono">{importResult.new_cases_detected}</strong>{' '}
              new prioritized recovery cases!
            </p>
            {importResult.errors.length > 0 && (
              <div className="mt-2 p-2 bg-rose-950/60 border border-rose-900/60 rounded text-rose-300">
                <span className="font-bold block">Validation Warnings / Rejected Rows:</span>
                <ul className="list-disc list-inside mt-1 font-mono">
                  {importResult.errors.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {importError && (
          <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 text-xs rounded-lg">
            {importError}
          </div>
        )}
      </div>

      {/* Available Business Connectors */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Radio className="w-4 h-4 text-indigo-400" />
          <span>Payment & Business System Connectors</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {connectors.map((conn) => (
            <div
              key={conn.id}
              className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between">
                  <h4 className="font-bold text-white text-sm">{conn.provider_name}</h4>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold border ${
                      conn.status === 'CONNECTED'
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                        : conn.status === 'SIMULATED'
                        ? 'bg-purple-950 text-purple-300 border-purple-800'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {conn.status}
                  </span>
                </div>
                <span className="text-[10px] uppercase font-mono text-slate-500 block mt-0.5">
                  Type: {conn.provider_type.replace('_', ' ')}
                </span>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">{conn.description}</p>
              </div>

              <div className="pt-3 border-t border-slate-800/60 text-[11px] flex justify-between text-slate-500">
                <span>Last Sync:</span>
                <span className="font-mono text-slate-400">
                  {conn.last_sync_at ? new Date(conn.last_sync_at).toLocaleTimeString() : 'Never'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
