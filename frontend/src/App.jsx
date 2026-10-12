import React, { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import ChatAssistant from './components/ChatAssistant'
import ComparisonMatrix from './components/ComparisonMatrix'
import ClaimsCalculator from './components/ClaimsCalculator'
import PolicyManager from './components/PolicyManager'
import PdfViewerModal from './components/PdfViewerModal'
import PolicySummaryModal from './components/PolicySummaryModal'

export default function App() {
  const [activeTab, setActiveTab] = useState('assistant')
  const [policies, setPolicies] = useState([])
  const [loadingPolicies, setLoadingPolicies] = useState(true)
  const [pdfModal, setPdfModal] = useState({
    open: false,
    policyId: '',
    pageNumber: 1,
    clauseTitle: '',
    clauseExcerpt: ''
  })
  const [summaryModalPolicyId, setSummaryModalPolicyId] = useState(null)
  // "My Policy" — the one policy the user designates as their primary policy
  const [activePolicyId, setActivePolicyId] = useState(null)

  // Persistent chat conversation history across tab navigation
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Welcome! I am your personal insurance intelligence guide.\n\nAsk me anything about your policy in plain language — whether your upcoming surgery is covered, room rent limits, required documents, or waiting periods.\n\n## How I protect you\n- Every answer comes directly from your official contract clauses\n- I cite the exact clause and page number\n- Clear plain-English summaries so you never get surprise deductions`,
      verdict: 'INFO',
      confidence: null,
      citations: []
    }
  ])

  const fetchPolicies = async () => {
    try {
      const res = await fetch('/api/policies')
      if (res.ok) {
        const data = await res.json()
        setPolicies(data)
        // Auto-set first policy as active if not yet set
        if (!activePolicyId && data.length > 0) {
          setActivePolicyId(data[0].policy_id)
        }
      }
    } catch (err) {
      console.error('Failed to fetch policies:', err)
    } finally {
      setLoadingPolicies(false)
    }
  }

  useEffect(() => {
    fetchPolicies()
  }, [])

  const handleOpenPdf = (policyId, pageNumber = 1, clauseTitle = '', clauseExcerpt = '') => {
    setPdfModal({
      open: true,
      policyId,
      pageNumber,
      clauseTitle,
      clauseExcerpt
    })
  }

  const handleOpenSummary = (policyId) => {
    setSummaryModalPolicyId(policyId)
  }

  const activePolicyName = policies.find(p => p.policy_id === activePolicyId)?.plan_name || null

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: activeTab === 'assistant' ? 'hidden' : 'auto' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        policyCount={policies.length}
        activePolicyName={activePolicyName}
      />

      <main style={{
        flex: 1,
        maxWidth: '1440px',
        width: '100%',
        margin: '0 auto',
        padding: activeTab === 'assistant' ? '16px 24px' : '24px',
        minHeight: 0,
        overflow: activeTab === 'assistant' ? 'hidden' : 'visible',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {activeTab === 'assistant' && (
          <ChatAssistant
            policies={policies}
            activePolicyId={activePolicyId}
            messages={chatMessages}
            setMessages={setChatMessages}
            onOpenPdf={handleOpenPdf}
            onOpenSummary={handleOpenSummary}
          />
        )}
        {activeTab === 'compare' && (
          <ComparisonMatrix
            policies={policies}
            onOpenPdf={handleOpenPdf}
            onOpenSummary={handleOpenSummary}
          />
        )}
        {activeTab === 'claims' && (
          <ClaimsCalculator
            policies={policies}
            activePolicyId={activePolicyId}
            onOpenPdf={handleOpenPdf}
            onOpenSummary={handleOpenSummary}
          />
        )}
        {activeTab === 'policies' && (
          <PolicyManager
            policies={policies}
            activePolicyId={activePolicyId}
            onSetActivePolicy={setActivePolicyId}
            onRefresh={fetchPolicies}
            onOpenPdf={handleOpenPdf}
            onOpenSummary={handleOpenSummary}
          />
        )}
      </main>

      {/* 1-Page Policy Health & Coverage Summary Card Modal */}
      {summaryModalPolicyId && (
        <PolicySummaryModal
          policyId={summaryModalPolicyId}
          onClose={() => setSummaryModalPolicyId(null)}
          onOpenPdf={handleOpenPdf}
        />
      )}

      {/* Enhanced PDF Document Viewer (rendered after summary modal to guarantee top-layer visibility) */}
      {pdfModal.open && (
        <PdfViewerModal
          policyId={pdfModal.policyId}
          pageNumber={pdfModal.pageNumber}
          clauseTitle={pdfModal.clauseTitle}
          clauseExcerpt={pdfModal.clauseExcerpt}
          onClose={() => setPdfModal({ open: false, policyId: '', pageNumber: 1, clauseTitle: '', clauseExcerpt: '' })}
        />
      )}
    </div>
  )
}
