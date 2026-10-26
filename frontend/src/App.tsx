import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { CasesPage } from './pages/CasesPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { AuditPage } from './pages/AuditPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { ConnectBusinessPage } from './pages/ConnectBusinessPage';
import { CaseDrawer } from './components/CaseDrawer';
import { ResetModal } from './components/ResetModal';
import { SessionHistoryModal } from './components/SessionHistoryModal';
import { DashboardSummary, RecoveryCase, SystemHealth } from './types';
import { api } from './api/client';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('connect-business');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  
  // Case Drawer State
  const [selectedCase, setSelectedCase] = useState<RecoveryCase | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Reset Demo Modal State
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);

  // Local Device Session Modal State
  const [isSessionModalOpen, setIsSessionModalOpen] = useState(false);

  const fetchGlobalData = async () => {
    try {
      const [sumData, healthData] = await Promise.all([
        api.getDashboardSummary(),
        api.getHealth(),
      ]);
      setSummary(sumData);
      setHealth(healthData);
    } catch (err) {
      console.error('Failed to fetch initial data', err);
    }
  };

  useEffect(() => {
    fetchGlobalData();
    // Refresh every 15s in background
    const interval = setInterval(fetchGlobalData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenCaseDrawer = async (caseIdOrObj: string | RecoveryCase) => {
    if (typeof caseIdOrObj === 'string') {
      try {
        const fullCase = await api.getCaseById(caseIdOrObj);
        setSelectedCase(fullCase);
        setIsDrawerOpen(true);
      } catch (err) {
        console.error('Could not fetch case', err);
      }
    } else {
      setSelectedCase(caseIdOrObj);
      setIsDrawerOpen(true);
    }
  };

  const handleCaseUpdated = async () => {
    if (selectedCase) {
      try {
        const updated = await api.getCaseById(selectedCase.id);
        setSelectedCase(updated);
      } catch (e) {
        console.error(e);
      }
    }
    fetchGlobalData();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Header Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        pendingApprovalsCount={summary?.pending_approvals_count || 0}
        health={health}
        onOpenResetModal={() => setIsResetModalOpen(true)}
        onOpenSessionModal={() => setIsSessionModalOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <DashboardPage
            summary={summary}
            onNavigateTab={setActiveTab}
            onSelectCaseId={handleOpenCaseDrawer}
          />
        )}

        {activeTab === 'cases' && (
          <CasesPage
            onSelectCase={handleOpenCaseDrawer}
            selectedCaseId={selectedCase?.id}
            onNavigateTab={setActiveTab}
          />
        )}

        {activeTab === 'workspace' && (
          <WorkspacePage
            initialCaseId={selectedCase?.id}
            onNavigateTab={setActiveTab}
            onOpenCaseModal={handleOpenCaseDrawer}
          />
        )}

        {activeTab === 'approvals' && (
          <ApprovalsPage
            onSelectCaseId={handleOpenCaseDrawer}
            onRefreshSummary={fetchGlobalData}
          />
        )}

        {activeTab === 'connect-business' && (
          <ConnectBusinessPage
            onNavigate={setActiveTab}
            onRefreshDashboard={fetchGlobalData}
          />
        )}

        {activeTab === 'audit' && (
          <AuditPage onSelectCaseId={handleOpenCaseDrawer} />
        )}

        {activeTab === 'integrations' && (
          <IntegrationsPage
            health={health}
            onRefreshHealth={fetchGlobalData}
            onRefreshSummary={fetchGlobalData}
          />
        )}
      </main>

      {/* Global Case Inspection Drawer */}
      <CaseDrawer
        caseData={selectedCase}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onCaseUpdated={handleCaseUpdated}
      />

      {/* Demo Reset Confirmation Modal */}
      <ResetModal
        isOpen={isResetModalOpen}
        onClose={() => setIsResetModalOpen(false)}
        onSuccess={fetchGlobalData}
      />

      {/* Local Device Session History Modal */}
      <SessionHistoryModal
        isOpen={isSessionModalOpen}
        onClose={() => setIsSessionModalOpen(false)}
      />
    </div>
  );
};

export default App;
