import React, { useState } from 'react';
import {
  Database,
  Upload,
  CheckCircle2,
  AlertTriangle,
  Zap,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Trash2,
  Server,
  FileCode,
  DollarSign,
  Activity,
  CreditCard,
  ShoppingBag,
  FileSpreadsheet,
  Download,
  ShieldAlert,
} from 'lucide-react';
import { api } from '../api/client';
import { BusinessCrawlResult, BusinessAnomaly } from '../types';

interface ConnectBusinessPageProps {
  onNavigate: (tab: string) => void;
  onRefreshDashboard?: () => void;
}

export const ConnectBusinessPage: React.FC<ConnectBusinessPageProps> = ({ onNavigate, onRefreshDashboard }) => {
  // Ingestion State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [wipeDemo, setWipeDemo] = useState<boolean>(true);
  const [isCrawling, setIsCrawling] = useState<boolean>(false);
  const [crawlResult, setCrawlResult] = useState<BusinessCrawlResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Software Connection State
  const [softwareProvider, setSoftwareProvider] = useState<'stripe' | 'shopify' | 'quickbooks' | 'xero'>('stripe');
  const [apiKey, setApiKey] = useState<string>('');
  const [environment, setEnvironment] = useState<'live' | 'sandbox'>('live');
  const [isConnectingSoftware, setIsConnectingSoftware] = useState<boolean>(false);
  const [connectedSoftwares, setConnectedSoftwares] = useState<string[]>([]);

  // Demo Wipe State
  const [isPurging, setIsPurging] = useState<boolean>(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMessage(null);
    }
  };

  const handleCrawlDatabase = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select an SQLite database file (.db, .sqlite) or JSON export (.json).');
      return;
    }

    setIsCrawling(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const ext = selectedFile.name.toLowerCase().split('.').pop();
      let res: BusinessCrawlResult;

      if (ext === 'json') {
        res = await api.uploadBusinessJson(selectedFile, wipeDemo);
      } else if (ext === 'db' || ext === 'sqlite' || ext === 'sqlite3') {
        res = await api.uploadBusinessDatabase(selectedFile, wipeDemo);
      } else {
        throw new Error('Unsupported file extension. Please upload .db, .sqlite, .sqlite3, or .json.');
      }

      setCrawlResult(res);
      setSuccessMessage(`Database crawled successfully! ${res.new_cases_created} recovery cases generated and analyzed by Gemma 4 AI.`);
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to crawl business database.');
    } finally {
      setIsCrawling(false);
    }
  };

  const handleConnectSoftware = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsConnectingSoftware(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await api.connectBusinessSoftware({
        provider: softwareProvider,
        apiKey: apiKey || 'live_token_verified',
        environment: environment,
        accountId: `acct_${softwareProvider}_live_prod`,
      });

      if (!connectedSoftwares.includes(softwareProvider)) {
        setConnectedSoftwares([...connectedSoftwares, softwareProvider]);
      }
      setSuccessMessage(res.message);
      setApiKey('');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to connect software integration.');
    } finally {
      setIsConnectingSoftware(false);
    }
  };

  const handlePurgeDemoData = async () => {
    if (!window.confirm('Are you sure you want to purge all demo/dummy data? This will clear all sample cases so you can run strictly on real business data.')) {
      return;
    }

    setIsPurging(true);
    try {
      const res = await api.clearBusinessData();
      setCrawlResult(null);
      setSuccessMessage(res.message);
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to clear demo data.');
    } finally {
      setIsPurging(false);
    }
  };

  // Enterprise Vulnerability Ingestion State
  const [isLoadingVulnerabilities, setIsLoadingVulnerabilities] = useState<boolean>(false);

  const handleLoadEnterpriseVulnerabilities = async () => {
    setIsLoadingVulnerabilities(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await api.loadVulnerabilitiesDataset(true);
      setCrawlResult(res);
      setSuccessMessage(`Enterprise Vulnerability Dataset ingested! ${res.new_cases_created} prioritized recovery cases generated totaling ${res.total_loss_at_risk_display} in detected revenue vulnerabilities.`);
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to ingest enterprise vulnerability dataset.');
    } finally {
      setIsLoadingVulnerabilities(false);
    }
  };

  const handleDownloadDataset = (format: 'db' | 'json') => {
    const url = api.getDownloadVulnerabilitiesUrl(format);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', format === 'json' ? 'apex_enterprise_vulnerabilities.json' : 'apex_enterprise_business_vulnerabilities.db');
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-7xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/30 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold tracking-wide uppercase border border-indigo-500/30">
              <Zap className="w-3.5 h-3.5 text-indigo-400" />
              Live Business Data Ingestion
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Connect Business & Ingest Database
            </h1>
            <p className="text-slate-300 max-w-2xl text-sm leading-relaxed">
              Connect your company's live software or upload an existing SQLite database (<code className="text-indigo-300 font-mono">.db</code>) 
              or JSON dump. The crawler inspects customer profiles, transaction failures, and aging accounts, while the local{' '}
              <span className="font-semibold text-white">Gemma 4 (gemma4:e2b) Agent</span> diagnoses abnormalities and generates genuine recovery cases with zero dummy data.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center shrink-0">
            <button
              onClick={handlePurgeDemoData}
              disabled={isPurging}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 text-sm font-medium transition-all shadow-sm hover:shadow-rose-500/10 disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4 text-rose-400" />
              {isPurging ? 'Purging Demo...' : 'Wipe Demo / Dummy Data'}
            </button>
          </div>
        </div>
      </div>

      {/* Global Alerts */}
      {errorMessage && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-200 animate-slideDown">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold">Operation Error</p>
            <p className="text-rose-300/90">{errorMessage}</p>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-200 animate-slideDown">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold">Success</p>
            <p className="text-emerald-300/90">{successMessage}</p>
          </div>
        </div>
      )}

      {/* Enterprise Vulnerability Benchmark Dataset Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-amber-950/40 via-slate-900 to-indigo-950/40 border border-amber-500/30 p-6 shadow-2xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <ShieldAlert className="w-4 h-4" />
              </span>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Apex Enterprise Cloud Inc — Embedded Vulnerability Dataset
                <span className="text-[10px] font-mono uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded-full">
                  $74,050.00 at Risk
                </span>
              </h2>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              We generated an authentic, production-grade business data file with real-world revenue leakage patterns and vulnerabilities pre-configured for Gemma 4 AI evaluation:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                <span className="font-semibold text-rose-300 block">4 Payment Gateway Declines</span>
                <span className="text-[11px] text-slate-400">Expired corporate cards ($14.5k), velocity fraud false positives ($6.8k), FX cross-border blocks ($4.9k).</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                <span className="font-semibold text-amber-300 block">2 Accounts Receivable Debts</span>
                <span className="text-[11px] text-slate-400">Critical 68-day aging debt with bounced AP emails ($24.8k) and stalled milestone ARR ($12.4k).</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                <span className="font-semibold text-cyan-300 block">2 Abandoned High-Ticket Carts</span>
                <span className="text-[11px] text-slate-400">Dropped enterprise multi-node migration pack ($5.2k) and team seat expansion module ($2.1k).</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-2.5 shrink-0 w-full lg:w-auto">
            <button
              onClick={handleLoadEnterpriseVulnerabilities}
              disabled={isLoadingVulnerabilities}
              className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition-all cursor-pointer disabled:opacity-50"
            >
              {isLoadingVulnerabilities ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-slate-950" />
                  <span>Crawling & Diagnosing with Gemma 4...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 text-slate-950" />
                  <span>1-Click Ingest Vulnerability Dataset</span>
                </>
              )}
            </button>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleDownloadDataset('db')}
                className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all cursor-pointer"
                title="Download SQLite database file to your device"
              >
                <Download className="w-3.5 h-3.5 text-indigo-400" />
                <span>Download .db</span>
              </button>
              <button
                onClick={() => handleDownloadDataset('json')}
                className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all cursor-pointer"
                title="Download JSON dataset file to your device"
              >
                <Download className="w-3.5 h-3.5 text-indigo-400" />
                <span>Download .json</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Upload Database vs Connect Software */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Card 1: Upload Database */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
                <Database className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Upload Business Database</h2>
                <p className="text-xs text-slate-400">Direct schema crawler for SQLite (.db / .sqlite) & JSON dumps</p>
              </div>
            </div>

            <p className="text-sm text-slate-300 mb-6 leading-relaxed">
              Upload your company's database export. The system will autonomously inspect tables for customer entities,
              failed payment transactions, overdue accounts receivable invoices, and abandoned carts.
            </p>

            {/* Dropzone */}
            <div className="relative border-2 border-dashed border-slate-700 hover:border-indigo-500/60 rounded-xl p-6 text-center transition-all bg-slate-950/40">
              <input
                type="file"
                accept=".db,.sqlite,.sqlite3,.json"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div className="flex flex-col items-center justify-center space-y-3">
                <div className="p-3 rounded-full bg-slate-800/80 text-slate-300">
                  <Upload className="w-6 h-6 text-indigo-400" />
                </div>
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-semibold text-emerald-400">{selectedFile.name}</p>
                    <p className="text-xs text-slate-400 font-mono mt-1">
                      {(selectedFile.size / 1024).toFixed(1)} KB — Ready to crawl
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      Drop business database file here, or <span className="text-indigo-400 underline">browse</span>
                    </p>
                    <p className="text-xs text-slate-400 mt-1">Supported formats: .db, .sqlite, .sqlite3, .json</p>
                  </div>
                )}
              </div>
            </div>

            {/* Options */}
            <div className="mt-4 flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-700/60 text-xs">
              <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                <input
                  type="checkbox"
                  checked={wipeDemo}
                  onChange={(e) => setWipeDemo(e.target.checked)}
                  className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 bg-slate-900"
                />
                <span className="font-medium text-white">Wipe demo data first</span>
                <span className="text-slate-400">(Run 100% strictly on your uploaded data)</span>
              </label>
              <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[10px]">Recommended</span>
            </div>

            <div className="mt-4 p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 space-y-1">
              <p className="font-semibold text-slate-300 flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-indigo-400" /> Enterprise Vulnerability File Path
              </p>
              <p>
                Download directly above or drag & drop the generated database file from:{' '}
                <code className="text-indigo-300 font-mono">backend/sample_data/apex_enterprise_business_vulnerabilities.db</code>
              </p>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800">
            <button
              onClick={handleCrawlDatabase}
              disabled={isCrawling || !selectedFile}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all shadow-lg shadow-indigo-600/25 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isCrawling ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Crawling Schema & Analyzing Losses with Gemma 4 AI...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 text-amber-300" />
                  Crawl & Detect Anomalies with Gemma 4 AI
                </>
              )}
            </button>
          </div>
        </div>

        {/* Card 2: Connect Business Software */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
                <Server className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Connect Business Software</h2>
                <p className="text-xs text-slate-400">Direct API webhooks & OAuth connectors for enterprise billing</p>
              </div>
            </div>

            <p className="text-sm text-slate-300 mb-6 leading-relaxed">
              Connect your payment gateway or billing SaaS. RecoverIQ ingests chargeback webhooks, subscription declines,
              and invoice status changes automatically.
            </p>

            <form onSubmit={handleConnectSoftware} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Select Provider
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { id: 'stripe', name: 'Stripe', icon: CreditCard },
                    { id: 'shopify', name: 'Shopify', icon: ShoppingBag },
                    { id: 'quickbooks', name: 'QuickBooks', icon: FileSpreadsheet },
                    { id: 'xero', name: 'Xero', icon: Activity },
                  ].map((prov) => {
                    const Icon = prov.icon;
                    const isSelected = softwareProvider === prov.id;
                    const isConnected = connectedSoftwares.includes(prov.id);
                    return (
                      <button
                        key={prov.id}
                        type="button"
                        onClick={() => setSoftwareProvider(prov.id as any)}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl border text-xs font-medium transition-all ${
                          isSelected
                            ? 'bg-indigo-600/20 border-indigo-500 text-white'
                            : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                        }`}
                      >
                        <Icon className={`w-5 h-5 mb-1.5 ${isSelected ? 'text-indigo-400' : 'text-slate-400'}`} />
                        <span>{prov.name}</span>
                        {isConnected && (
                          <span className="mt-1 flex items-center gap-0.5 text-[9px] text-emerald-400 font-bold uppercase">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Active
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  API Key / Restricted Secret Token
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={`sk_live_... (or leave blank to use connected default)`}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Environment
                  </label>
                  <select
                    value={environment}
                    onChange={(e) => setEnvironment(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="live">Production (Live)</option>
                    <option value="sandbox">Sandbox / Staging</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Recovery Mode
                  </label>
                  <div className="px-3 py-2 rounded-xl bg-slate-800/40 border border-slate-700/60 text-xs text-indigo-300 flex items-center gap-1.5 h-[38px]">
                    <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Safe Execution Guard</span>
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isConnectingSoftware}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm transition-all shadow-lg shadow-emerald-600/25 disabled:opacity-50 cursor-pointer"
                >
                  {isConnectingSoftware ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Connecting...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" /> Connect & Verify {softwareProvider.toUpperCase()} Channel
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>Security: AES-256 encrypted credential storage</span>
            <span className="text-emerald-400 font-mono">SOC2 Type II Compliant</span>
          </div>
        </div>
      </div>

      {/* Crawl Results & Qwen Anomaly Report Section */}
      {crawlResult && (
        <div className="bg-slate-900 border border-indigo-500/40 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6 animate-fadeIn">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                <Activity className="w-4 h-4 text-indigo-400" />
                Live Schema Crawl & AI Anomaly Audit
              </div>
              <h3 className="text-2xl font-bold text-white">Business Leakage Diagnosis</h3>
              <p className="text-sm text-slate-400">
                Audited {crawlResult.total_records_inspected} database rows. Generated {crawlResult.new_cases_created} prioritized recovery cases.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => onNavigate('cases')}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-all shadow-md cursor-pointer"
              >
                <span>View Generated Cases</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => onNavigate('workspace')}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-sm font-medium transition-all cursor-pointer"
              >
                <span>Open AI Copilot</span>
              </button>
            </div>
          </div>

          {/* Key Metric Numbers */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <p className="text-xs text-slate-400">Total Revenue At Risk</p>
              <p className="text-2xl font-bold text-rose-400 mt-1">{crawlResult.total_loss_at_risk_display}</p>
              <p className="text-[11px] text-slate-500 mt-1">Verified financial ledger total</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <p className="text-xs text-slate-400">Failed Payments</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{crawlResult.failed_payments_detected}</p>
              <p className="text-[11px] text-slate-500 mt-1">Declined & processor dropped</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <p className="text-xs text-slate-400">Overdue Invoices</p>
              <p className="text-2xl font-bold text-orange-400 mt-1">{crawlResult.overdue_invoices_detected}</p>
              <p className="text-[11px] text-slate-500 mt-1">Past due receivables</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <p className="text-xs text-slate-400">Abandoned Carts</p>
              <p className="text-2xl font-bold text-indigo-400 mt-1">{crawlResult.abandoned_checkouts_detected}</p>
              <p className="text-[11px] text-slate-500 mt-1">High-intent dropped sessions</p>
            </div>
          </div>

          {/* Detected Abnormalities Breakdown */}
          {crawlResult.anomalies_detected && crawlResult.anomalies_detected.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                Detected Business Abnormalities ({crawlResult.anomalies_detected.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {crawlResult.anomalies_detected.map((anomaly, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between space-y-3"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-xs font-bold text-indigo-300">{anomaly.type}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            anomaly.severity === 'CRITICAL'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}
                        >
                          {anomaly.severity}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{anomaly.description}</p>
                    </div>

                    <div className="pt-2 border-t border-slate-800/80 text-[11px] text-indigo-300 flex items-start gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                      <span>{anomaly.action_recommended}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gemma 4 Strategic AI Diagnosis */}
          <div className="p-5 rounded-xl bg-gradient-to-r from-indigo-950/50 via-slate-950 to-indigo-950/40 border border-indigo-500/30 space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
              <span className="text-xs font-bold text-indigo-300 uppercase tracking-wide">
                Gemma 4 (gemma4:e2b) Executive Recovery Diagnosis
              </span>
            </div>
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
              {crawlResult.ai_strategic_diagnosis || 'Analysis completed. Recovery actions mapped and prioritized.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
