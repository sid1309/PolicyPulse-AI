import React, { useState, useEffect } from 'react'
import {
  X, ExternalLink, FileText, CheckCircle2, ChevronLeft, ChevronRight,
  Maximize2, Minimize2, Copy, Check, ShieldCheck, Columns, Square
} from 'lucide-react'

export default function PdfViewerModal({
  policyId,
  pageNumber = 1,
  clauseTitle = '',
  clauseExcerpt = '',
  onClose
}) {
  const [currentPage, setCurrentPage] = useState(pageNumber)
  const [dockMode, setDockMode] = useState(false) // false: centered modal, true: right dock
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    setCurrentPage(pageNumber)
  }, [pageNumber, policyId])

  if (!policyId) return null

  const pdfUrl = `/api/policies/pdf/${policyId}#page=${currentPage}`

  const handleCopy = () => {
    const text = clauseExcerpt || `Policy: ${policyId}, Page: ${currentPage}`
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: dockMode ? 'transparent' : 'rgba(4, 7, 15, 0.82)',
      backdropFilter: dockMode ? 'none' : 'blur(8px)',
      display: 'flex',
      alignItems: dockMode ? 'stretch' : 'center',
      justifyContent: dockMode ? 'flex-end' : 'center',
      zIndex: 500,
      padding: dockMode ? '0' : '20px',
      pointerEvents: dockMode ? 'none' : 'auto',
      transition: 'all 0.25s ease'
    }}>
      <div
        className="glass-panel"
        style={{
          width: dockMode ? '540px' : '100%',
          maxWidth: dockMode ? '540px' : '1040px',
          height: dockMode ? '100vh' : '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          borderRadius: dockMode ? '0' : '18px',
          border: dockMode ? 'none' : '1px solid rgba(56, 189, 248, 0.35)',
          borderLeft: dockMode ? '1px solid rgba(56, 189, 248, 0.4)' : undefined,
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(2, 132, 199, 0.25)',
          pointerEvents: 'auto',
          transition: 'all 0.25s ease'
        }}
      >
        {/* Modal Header */}
        <div style={{
          padding: '12px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(2, 132, 199, 0.15) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '8px',
              background: 'rgba(2, 132, 199, 0.2)', border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <FileText size={16} color="#38bdf8" />
            </div>
            <div>
              <div style={{ fontSize: '13.5px', fontWeight: '800', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                Contract Source Document
                <span className="badge badge-blue" style={{ fontSize: '10px', padding: '1px 6px' }}>Verified</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {policyId}
              </div>
            </div>
          </div>

          {/* Action buttons & mode toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {/* Page navigation controls */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '4px',
              background: 'rgba(255, 255, 255, 0.05)', borderRadius: '8px',
              padding: '2px 4px', border: '1px solid var(--border-subtle)', marginRight: '6px'
            }}>
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage <= 1}
                style={{
                  background: 'transparent', border: 'none', color: currentPage <= 1 ? 'var(--text-dim)' : '#fff',
                  cursor: currentPage <= 1 ? 'default' : 'pointer', padding: '3px 5px', display: 'flex', alignItems: 'center'
                }}
                title="Previous Page"
              >
                <ChevronLeft size={14} />
              </button>
              <span style={{ fontSize: '11px', color: '#93c5fd', fontWeight: 700, padding: '0 4px', fontFamily: 'var(--font-mono)' }}>
                Pg {currentPage}
              </span>
              <button
                onClick={() => setCurrentPage(p => p + 1)}
                style={{
                  background: 'transparent', border: 'none', color: '#fff',
                  cursor: 'pointer', padding: '3px 5px', display: 'flex', alignItems: 'center'
                }}
                title="Next Page"
              >
                <ChevronRight size={14} />
              </button>
            </div>

            {/* Toggle Dock vs Center */}
            <button
              onClick={() => setDockMode(!dockMode)}
              className="btn-secondary"
              style={{ padding: '5px 9px', fontSize: '11px' }}
              title={dockMode ? "Switch to Centered View" : "Dock to Side (Split-Screen)"}
            >
              {dockMode ? <Square size={13} /> : <Columns size={13} />}
              <span>{dockMode ? 'Full' : 'Dock'}</span>
            </button>

            {/* Open in new browser tab */}
            <a
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary"
              style={{ padding: '5px 9px', fontSize: '11px' }}
              title="Open raw PDF in new browser tab"
            >
              <ExternalLink size={13} />
            </a>

            {/* Close */}
            <button
              onClick={onClose}
              style={{
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '7px',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '5px 7px',
                display: 'flex', alignItems: 'center'
              }}
              title="Close PDF Viewer"
            >
              <X size={15} />
            </button>
          </div>
        </div>

        {/* Verification Alert Banner + Cited Clause Excerpt */}
        <div style={{
          background: 'rgba(2, 132, 199, 0.1)',
          padding: '10px 18px',
          borderBottom: '1px solid rgba(56, 189, 248, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', fontSize: '11.5px', color: '#93c5fd' }}>
              <CheckCircle2 size={13} color="#10b981" />
              <span>Grounding verified: Navigated to Page {currentPage} in source policy.</span>
            </div>
            {clauseExcerpt && (
              <button
                onClick={handleCopy}
                style={{
                  background: 'transparent', border: 'none', color: '#38bdf8',
                  fontSize: '11px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px'
                }}
              >
                {copied ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                <span>{copied ? 'Copied clause' : 'Copy clause'}</span>
              </button>
            )}
          </div>

          {clauseTitle && (
            <div style={{
              fontSize: '12px', fontWeight: 600, color: '#f8fafc',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
            }}>
              Clause: <span style={{ color: '#38bdf8' }}>{clauseTitle}</span>
            </div>
          )}
        </div>

        {/* PDF Frame */}
        <div style={{ flex: 1, background: '#0f172a', position: 'relative' }}>
          <iframe
            src={pdfUrl}
            title="Policy PDF Viewer"
            style={{ width: '100%', height: '100%', border: 'none' }}
          />
        </div>
      </div>
    </div>
  )
}
