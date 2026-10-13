import React, { useState } from 'react'
import { apiUrl } from '../apiConfig'
import {
  UploadCloud, FileText, Trash2, ExternalLink, Sparkles,
  Shield, Database, FileCheck, Star, StarOff, AlertTriangle,
  ChevronRight, Clock, CheckCircle2, XCircle
} from 'lucide-react'

export default function PolicyManager({ policies, activePolicyId, onSetActivePolicy, onRefresh, onOpenPdf, onOpenSummary }) {
  const [file, setFile] = useState(null)
  const [insurer, setInsurer] = useState('')
  const [planName, setPlanName] = useState('')
  const [version, setVersion] = useState('')
  const [uploading, setUploading] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')
  const [statusType, setStatusType] = useState('info') // 'info' | 'success' | 'error'
  const [uploadProgress, setUploadProgress] = useState(0)

  const uploadSteps = [
    'Parsing PDF layout...',
    'Extracting tables & sections...',
    'Structure-aware clause chunking...',
    'Generating dense embeddings...',
    'Building BM25 sparse index...',
    'Indexing into vector database...',
    'Done! Policy ready to query.'
  ]

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) return

    setUploading(true)
    setUploadProgress(0)
    setStatusType('info')

    // Simulate step-by-step progress display
    let step = 0
    const stepInterval = setInterval(() => {
      if (step < uploadSteps.length - 1) {
        setStatusMessage(uploadSteps[step])
        setUploadProgress(Math.round(((step + 1) / uploadSteps.length) * 90))
        step++
      }
    }, 600)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('insurer', insurer.trim() || 'General Insurer')
    formData.append('plan_name', planName.trim() || 'Health Plan')
    formData.append('version', version.trim() || '2024')

    try {
      const res = await fetch(apiUrl('/api/policies/upload'), { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Upload failed')
      }
      clearInterval(stepInterval)
      setUploadProgress(100)
      setStatusMessage('Policy successfully indexed! Ready to query.')
      setStatusType('success')
      // Reset form fields so placeholders reappear
      setInsurer('')
      setPlanName('')
      setVersion('')
      setFile(null)
      const fileInput = document.getElementById('policy-file-input')
      if (fileInput) fileInput.value = ''
      onRefresh()
    } catch (err) {
      clearInterval(stepInterval)
      setStatusMessage(`Error: ${err.message}`)
      setStatusType('error')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (policyId) => {
    if (!window.confirm(`Delete this policy? This cannot be undone.`)) return
    try {
      await fetch(apiUrl(`/api/policies/${policyId}`), { method: 'DELETE' })
      // If we deleted the active policy, clear it
      if (policyId === activePolicyId) onSetActivePolicy(null)
      onRefresh()
    } catch (err) {
      console.error(err)
    }
  }

  const statusColors = {
    info: { bg: 'rgba(2,132,199,0.1)', border: 'rgba(56,189,248,0.3)', text: '#93c5fd' },
    success: { bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.35)', text: '#6ee7b7' },
    error: { bg: 'rgba(244,63,94,0.1)', border: 'rgba(244,63,94,0.35)', text: '#fda4af' },
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 420px) 1fr', gap: '24px' }}>
      {/* Upload Column */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ marginBottom: '8px' }}>
          <h2 style={{ fontSize: '17px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '10px', color: '#ffffff', margin: 0 }}>
            <UploadCloud size={19} color="#38bdf8" /> Add New Policy
          </h2>
        </div>

        <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginBottom: '20px', lineHeight: '1.45' }}>
          Upload your insurance policy PDF. The engine will parse clauses, extract tables, and build a queryable index automatically.
        </p>

        <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '13px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11.5px', fontWeight: '700', marginBottom: '5px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Insurance Company
            </label>
            <input type="text" value={insurer} onChange={(e) => setInsurer(e.target.value)}
              placeholder="e.g. HDFC ERGO, Star Health" className="form-input" required />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11.5px', fontWeight: '700', marginBottom: '5px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Plan Name
            </label>
            <input type="text" value={planName} onChange={(e) => setPlanName(e.target.value)}
              placeholder="e.g. Optima Secure" className="form-input" required />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11.5px', fontWeight: '700', marginBottom: '5px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Version / Year
            </label>
            <input type="text" value={version} onChange={(e) => setVersion(e.target.value)}
              placeholder="e.g. 2024.1" className="form-input" required />
          </div>

          {/* Drag-drop upload */}
          <div>
            <label style={{ display: 'block', fontSize: '11.5px', fontWeight: '700', marginBottom: '5px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Policy PDF File
            </label>
            <div style={{
              border: `2px dashed ${file ? 'rgba(16,185,129,0.5)' : 'rgba(56,189,248,0.3)'}`,
              borderRadius: '12px', padding: '18px', textAlign: 'center',
              background: file ? 'rgba(16,185,129,0.05)' : 'rgba(11,17,32,0.6)', cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}>
              <input type="file" accept=".pdf" id="policy-file-input"
                onChange={(e) => setFile(e.target.files[0])} style={{ display: 'none' }} required />
              <label htmlFor="policy-file-input" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                {file
                  ? <CheckCircle2 size={28} color="#10b981" />
                  : <FileText size={28} color="#38bdf8" />
                }
                <span style={{ fontSize: '13px', color: '#ffffff', fontWeight: 600 }}>
                  {file ? file.name : 'Click to select PDF'}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                  {file ? `${(file.size / 1024).toFixed(1)} KB selected` : 'PDF only · Max 25 MB'}
                </span>
              </label>
            </div>
          </div>

          {/* Progress Bar */}
          {uploading && (
            <div style={{ marginTop: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Processing...</span>
                <span style={{ fontSize: '11px', color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>{uploadProgress}%</span>
              </div>
              <div style={{ height: '5px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%', width: `${uploadProgress}%`, borderRadius: '3px',
                  background: 'linear-gradient(90deg, #0284c7, #38bdf8)',
                  transition: 'width 0.5s ease'
                }} />
              </div>
            </div>
          )}

          <button type="submit" disabled={uploading || !file} className="btn-primary"
            style={{ marginTop: '6px', width: '100%', padding: '12px' }}>
            {uploading ? 'Indexing...' : 'Upload & Index Policy'}
          </button>
        </form>

        {/* Status Message */}
        {statusMessage && (
          <div style={{
            marginTop: '14px', padding: '11px 13px', borderRadius: '10px',
            background: statusColors[statusType].bg,
            border: `1px solid ${statusColors[statusType].border}`,
            fontSize: '12.5px', color: statusColors[statusType].text, lineHeight: '1.45',
            display: 'flex', alignItems: 'flex-start', gap: '8px'
          }}>
            {statusType === 'success' && <CheckCircle2 size={15} style={{ flexShrink: 0, marginTop: '1px' }} />}
            {statusType === 'error' && <XCircle size={15} style={{ flexShrink: 0, marginTop: '1px' }} />}
            {statusType === 'info' && <ChevronRight size={15} style={{ flexShrink: 0, marginTop: '1px' }} />}
            {statusMessage}
          </div>
        )}
      </div>

      {/* Policy Repository */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: '800', color: '#ffffff' }}>My Policy Library</h2>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Star a policy to set it as your default. All chat queries use your active policy by default.
            </p>
          </div>
          <span className="badge badge-covered" style={{ fontSize: '11px', padding: '4px 10px' }}>
            {policies.length} Indexed
          </span>
        </div>

        {policies.length === 0 ? (
          <div style={{
            padding: '56px 24px', textAlign: 'center',
            border: '1px dashed var(--border-subtle)', borderRadius: '14px'
          }}>
            <FileText size={44} color="var(--text-dim)" style={{ marginBottom: '14px' }} />
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '6px', color: '#ffffff' }}>
              No policies loaded yet
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '380px', margin: '0 auto', lineHeight: '1.5' }}>
              Upload your insurance policy PDF on the left to index its clauses and start asking questions.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: '16px' }}>
            {policies.map((p) => {
              const isActive = p.policy_id === activePolicyId
              return (
                <div key={p.policy_id} style={{
                  background: isActive ? 'rgba(2,132,199,0.1)' : 'rgba(11,17,32,0.75)',
                  border: isActive ? '1px solid rgba(56,189,248,0.45)' : '1px solid var(--border-subtle)',
                  borderRadius: '14px', padding: '18px',
                  display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                  transition: 'all 0.2s ease', position: 'relative',
                  boxShadow: isActive ? '0 0 20px rgba(2,132,199,0.15)' : 'var(--shadow-sm)'
                }}>
                  {/* Active badge */}
                  {isActive && (
                    <div style={{
                      position: 'absolute', top: '12px', right: '12px',
                      background: 'rgba(2,132,199,0.25)', border: '1px solid rgba(56,189,248,0.4)',
                      borderRadius: '6px', padding: '2px 8px',
                      fontSize: '10px', fontWeight: '800', color: '#38bdf8', letterSpacing: '0.04em'
                    }}>
                      ACTIVE
                    </div>
                  )}

                  <div>
                    {/* Header */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                      <span className="badge badge-blue" style={{ fontSize: '10.5px' }}>{p.insurer}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>v{p.version}</span>
                    </div>

                    <h4 style={{ fontSize: '16px', fontWeight: '800', color: '#ffffff', marginBottom: '12px' }}>
                      {p.plan_name}
                    </h4>

                    {/* Insight Stats — not chunk count */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '16px' }}>
                      {[
                        { icon: FileCheck, color: '#38bdf8', label: 'Pages', value: p.total_pages },
                        { icon: Database, color: '#10b981', label: 'Clauses', value: p.chunk_count },
                        { icon: Clock, color: '#f59e0b', label: 'Indexed', value: p.version ? `v${p.version}` : 'Latest' },
                        { icon: Shield, color: '#a78bfa', label: 'Type', value: 'Health' },
                      ].map(({ icon: Icon, color, label, value }, i) => (
                        <div key={i} style={{
                          background: 'rgba(15,23,42,0.6)', borderRadius: '9px', padding: '8px 10px',
                          border: '1px solid rgba(255,255,255,0.06)'
                        }}>
                          <div style={{ fontSize: '10px', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Icon size={11} color={color} /> {label}
                          </div>
                          <div style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>{value}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', flexWrap: 'wrap' }}>
                    {/* Set Active */}
                    <button
                      onClick={() => onSetActivePolicy(isActive ? null : p.policy_id)}
                      title={isActive ? 'Remove as active policy' : 'Set as My Active Policy'}
                      style={{
                        background: isActive ? 'rgba(2,132,199,0.2)' : 'rgba(15,23,42,0.6)',
                        border: isActive ? '1px solid rgba(56,189,248,0.4)' : '1px solid var(--border-subtle)',
                        color: isActive ? '#38bdf8' : 'var(--text-muted)',
                        borderRadius: '8px', cursor: 'pointer', padding: '7px 11px',
                        display: 'flex', alignItems: 'center', gap: '5px',
                        fontSize: '12px', fontWeight: 600, transition: 'all 0.15s ease'
                      }}
                    >
                      {isActive ? <Star size={13} /> : <StarOff size={13} />}
                      {isActive ? 'My Policy' : 'Set Active'}
                    </button>

                    <button
                      onClick={() => onOpenSummary(p.policy_id)}
                      className="btn-secondary"
                      style={{ padding: '7px 11px', fontSize: '12px', gap: '5px', borderColor: 'rgba(56, 189, 248, 0.35)', color: '#38bdf8' }}
                      title="View 1-Page Coverage Summary Card"
                    >
                      <Sparkles size={13} color="#38bdf8" />
                      <span>Summary</span>
                    </button>

                    <button onClick={() => onOpenPdf(p.policy_id, 1)} className="btn-secondary"
                      style={{ padding: '7px 11px', fontSize: '12px', gap: '5px', flex: 1 }}>
                      <ExternalLink size={13} />
                      <span>PDF</span>
                    </button>

                    <button onClick={() => handleDelete(p.policy_id)} title="Delete Policy" style={{
                      background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.22)',
                      color: '#fb7185', borderRadius: '8px', cursor: 'pointer',
                      padding: '7px 10px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      transition: 'all 0.15s ease'
                    }}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
