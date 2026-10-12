import React, { useState, useEffect } from 'react'
import {
  Shield, CheckCircle2, AlertTriangle, X, FileText, ExternalLink,
  Sparkles, Calendar, Building2, Wallet, Stethoscope, ChevronRight,
  Info, Award, ArrowUpRight, Copy, Check
} from 'lucide-react'

export default function PolicySummaryModal({ policyId, onClose, onOpenPdf }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!policyId) return
    setLoading(true)
    setError(null)
    fetch(`/api/policies/${policyId}/summary`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load policy summary')
        return res.json()
      })
      .then(data => setSummary(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [policyId])

  if (!policyId) return null

  const handleCopy = () => {
    if (!summary) return
    const text = `Policy: ${summary.insurer} ${summary.plan_name} (${summary.version})\nRoom Rent: ${summary.room_rent_cap}\nPED Waiting Period: ${summary.ped_waiting_period}\nSpecific Illness: ${summary.specific_illness_waiting}\nCo-payment: ${summary.copay}\nPre/Post Hospitalization: ${summary.pre_post_hospitalization}\nSummary: ${summary.plain_english_summary}`
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
      background: 'rgba(5, 8, 16, 0.82)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 110,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '860px',
        maxHeight: '92vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid rgba(56, 189, 248, 0.4)',
        boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 35px rgba(2, 132, 199, 0.2)'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(2, 132, 199, 0.15) 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '38px', height: '38px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)'
            }}>
              <Award size={20} color="#fff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '16px', fontWeight: '800', color: '#fff', margin: 0 }}>
                  Policy Health & Coverage Summary Card
                </h2>
                <span className="badge badge-blue" style={{ fontSize: '10.5px' }}>Instant 1-Page ID</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                Verified clause-grounded summary extracted directly from official contract PDF
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {summary && (
              <button
                onClick={handleCopy}
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: '12px' }}
                title="Copy Summary to Clipboard"
              >
                {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                <span>{copied ? 'Copied!' : 'Copy'}</span>
              </button>
            )}
            <button
              onClick={onClose}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '6px 10px',
                display: 'flex', alignItems: 'center'
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
              <Sparkles size={28} color="#38bdf8" style={{ animation: 'spin 2s linear infinite', marginBottom: '14px' }} />
              <div style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>Analyzing Policy Contract...</div>
              <div style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginTop: '4px' }}>
                Extracting room limits, waiting periods, deductibles, and exclusions
              </div>
            </div>
          )}

          {error && (
            <div style={{
              padding: '20px', borderRadius: '12px',
              background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)',
              color: '#f43f5e', textAlign: 'center'
            }}>
              <AlertTriangle size={24} style={{ marginBottom: '8px' }} />
              <div>{error}</div>
            </div>
          )}

          {summary && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Policy Header Badge */}
              <div style={{
                background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(2, 132, 199, 0.12) 100%)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: '14px',
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px'
              }}>
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {summary.insurer}
                  </div>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: '#fff', marginTop: '2px' }}>
                    {summary.plan_name} <span style={{ fontSize: '13px', color: 'var(--text-dim)', fontWeight: 500 }}>v{summary.version}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <div style={{
                    padding: '8px 14px', borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.04)', border: '1px solid var(--border-subtle)',
                    textAlign: 'right'
                  }}>
                    <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Sum Insured</div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#10b981' }}>{summary.sum_insured}</div>
                  </div>
                  <button
                    onClick={() => onOpenPdf(summary.policy_id, 1)}
                    className="btn-secondary"
                    style={{ fontSize: '12px', padding: '6px 14px' }}
                  >
                    <FileText size={14} color="#38bdf8" />
                    <span>View Contract PDF ({summary.total_pages}p)</span>
                  </button>
                </div>
              </div>

              {/* Plain English Verdict Box */}
              <div style={{
                background: 'rgba(2, 132, 199, 0.08)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderRadius: '12px',
                padding: '14px 18px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px'
              }}>
                <Sparkles size={18} color="#38bdf8" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Policyholder TL;DR Summary
                  </div>
                  <p style={{ margin: '4px 0 0 0', fontSize: '13.5px', color: '#e2e8f0', lineHeight: '1.55' }}>
                    {summary.plain_english_summary}
                  </p>
                </div>
              </div>

              {/* 6 Key Insurance Dimension Metrics Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
                {/* Room Rent */}
                <div className="glass-panel" style={{ padding: '14px 16px', border: '1px solid rgba(255,255,255,0.07)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Building2 size={16} color="#38bdf8" />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Room Rent Eligibility
                    </span>
                  </div>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    {summary.room_rent_cap}
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#10b981' }}>
                    ICU Limit: {summary.icu_limit}
                  </div>
                </div>

                {/* Pre-Existing Disease */}
                <div className="glass-panel" style={{ padding: '14px 16px', border: '1px solid rgba(255,255,255,0.07)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Calendar size={16} color="#f59e0b" />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      PED Waiting Period
                    </span>
                  </div>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    {summary.ped_waiting_period}
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-dim)' }}>
                    Continuous policy tenure required
                  </div>
                </div>

                {/* Specific Surgeries */}
                <div className="glass-panel" style={{ padding: '14px 16px', border: '1px solid rgba(255,255,255,0.07)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Stethoscope size={16} color="#a855f7" />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Specific Surgeries Wait
                    </span>
                  </div>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    {summary.specific_illness_waiting}
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-dim)' }}>
                    Hernia, cataract, joint replacements
                  </div>
                </div>

                {/* Pre / Post Hospitalization */}
                <div className="glass-panel" style={{ padding: '14px 16px', border: '1px solid rgba(255,255,255,0.07)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Calendar size={16} color="#10b981" />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Pre & Post Coverage
                    </span>
                  </div>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    {summary.pre_post_hospitalization}
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-dim)' }}>
                    Doctor visits, tests, medicine bills
                  </div>
                </div>

                {/* Co-Payment */}
                <div className="glass-panel" style={{ padding: '14px 16px', border: '1px solid rgba(255,255,255,0.07)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Wallet size={16} color="#ec4899" />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Co-payment
                    </span>
                  </div>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    {summary.copay}
                  </div>
                  <div style={{ fontSize: '11.5px', color: summary.copay.includes('0%') ? '#10b981' : '#f59e0b' }}>
                    {summary.copay.includes('0%') ? 'Full reimbursement admissible' : 'Out-of-pocket mandatory deduction'}
                  </div>
                </div>

                {/* Restoration & Daycare */}
                <div className="glass-panel" style={{ padding: '14px 16px', border: '1px solid rgba(255,255,255,0.07)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Shield size={16} color="#38bdf8" />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Restoration Benefit
                    </span>
                  </div>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    {summary.restoration_benefit}
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-dim)' }}>
                    {summary.day_care}
                  </div>
                </div>
              </div>

              {/* Key Exclusions List */}
              <div className="glass-panel" style={{ padding: '18px 20px' }}>
                <div style={{
                  fontSize: '13px', fontWeight: 700, color: '#f43f5e',
                  display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px'
                }}>
                  <AlertTriangle size={16} /> Key Non-Payable Exclusions to Watch Out For
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {summary.key_exclusions.map((excl, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '13px', color: '#cbd5e1' }}>
                      <span style={{ color: '#f43f5e', fontWeight: 800 }}>✕</span>
                      <span>{excl}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Citations bar */}
              {summary.citations && summary.citations.length > 0 && (
                <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                    Verified Supporting Clauses ({summary.citations.length} extracted)
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {summary.citations.map((c, idx) => (
                      <button
                        key={idx}
                        className="citation-pill"
                        onClick={() => onOpenPdf(c.policy_id, c.page_number)}
                        title={`Open Page ${c.page_number}: ${c.clause_title}`}
                      >
                        📄 Pg {c.page_number} · {c.clause_title?.slice(0, 32)}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
