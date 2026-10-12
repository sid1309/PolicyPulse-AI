import React, { useState } from 'react'
import { FileDiff, ArrowRight, PlusCircle, MinusCircle, Info, Sparkles, AlertCircle, History, ShieldAlert } from 'lucide-react'

export default function PolicyDiffView({ policies, onOpenPdf }) {
  const [oldPolicyId, setOldPolicyId] = useState(policies.length > 2 ? policies[2].policy_id : (policies[0]?.policy_id || ''))
  const [newPolicyId, setNewPolicyId] = useState(policies[0]?.policy_id || '')
  const [loading, setLoading] = useState(false)
  const [diffData, setDiffData] = useState(null)
  const [error, setError] = useState('')

  const runDiff = async () => {
    if (!oldPolicyId || !newPolicyId) {
      setError('Please select both an older base and a renewal policy version.')
      return
    }
    if (oldPolicyId === newPolicyId) {
      setError('Please select two distinct policy versions to compare differences.')
      return
    }
    setError('')
    setLoading(true)

    try {
      const res = await fetch('/api/compare/diff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          old_policy_id: oldPolicyId,
          new_policy_id: newPolicyId
        })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Diff failed')
      }
      const data = await res.json()
      setDiffData(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const renderBadge = (changeType) => {
    if (changeType === 'EXPANSION') {
      return <span className="badge badge-covered"><PlusCircle size={12} /> Benefit Expansion</span>
    } else if (changeType === 'RESTRICTION') {
      return <span className="badge badge-excluded"><MinusCircle size={12} /> New Restriction</span>
    } else {
      return <span className="badge badge-blue"><Info size={12} /> Procedural Update</span>
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Selector Header */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '19px', fontWeight: '800', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '10px', color: '#ffffff' }}>
          <FileDiff size={22} color="#38bdf8" /> Policy Version Delta & Renewal Diff Engine
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '22px' }}>
          Compare older policy wordings against renewal editions to uncover hidden clause restrictions, waiting period shifts, or added co-payments.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '260px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Base / Older Policy Edition
            </label>
            <select
              value={oldPolicyId}
              onChange={(e) => setOldPolicyId(e.target.value)}
              className="form-select"
            >
              {policies.map((p) => (
                <option key={p.policy_id} value={p.policy_id}>
                  {p.insurer} — {p.plan_name} (v{p.version})
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', paddingTop: '22px', color: '#38bdf8' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'rgba(2, 132, 199, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <ArrowRight size={18} />
            </div>
          </div>

          <div style={{ flex: 1, minWidth: '260px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Renewal / New Policy Edition
            </label>
            <select
              value={newPolicyId}
              onChange={(e) => setNewPolicyId(e.target.value)}
              className="form-select"
            >
              {policies.map((p) => (
                <option key={p.policy_id} value={p.policy_id}>
                  {p.insurer} — {p.plan_name} (v{p.version})
                </option>
              ))}
            </select>
          </div>

          <div style={{ paddingTop: '22px' }}>
            <button
              onClick={runDiff}
              disabled={loading}
              className="btn-primary"
              style={{ padding: '11px 24px' }}
            >
              <Sparkles size={16} />
              <span>{loading ? 'Analyzing Semantic Shifts...' : 'Run Version Diff'}</span>
            </button>
          </div>
        </div>

        {error && (
          <div style={{
            marginTop: '16px',
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.35)',
            color: '#fb7185',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}
      </div>

      {/* Diff Results or Empty State */}
      {diffData ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Summary Box */}
          <div className="glass-panel" style={{
            padding: '22px 26px',
            borderLeft: '4px solid #0284c7',
            background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.12) 0%, rgba(13, 21, 38, 0.8) 100%)'
          }}>
            <div style={{ fontSize: '11px', fontWeight: '800', color: '#38bdf8', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Renewal Delta Intelligence Summary
            </div>
            <p style={{ fontSize: '14.5px', color: '#f8fafc', lineHeight: '1.6', marginTop: '6px' }}>
              {diffData.summary_of_changes}
            </p>
          </div>

          {/* Cards for each changed category */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {diffData.changes.map((item, idx) => (
              <div key={idx} className="glass-panel" style={{ padding: '22px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '16px', fontWeight: '700', color: '#ffffff' }}>
                      {item.category}
                    </span>
                    {renderBadge(item.change_type)}
                  </div>
                  <span style={{ fontSize: '12.5px', color: '#38bdf8', fontWeight: '600', background: 'rgba(2, 132, 199, 0.12)', padding: '4px 10px', borderRadius: '6px' }}>
                    {item.impact_analysis}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                  {/* Old Version Clause */}
                  <div style={{
                    background: 'rgba(11, 17, 32, 0.7)',
                    border: '1px solid rgba(244, 63, 94, 0.25)',
                    borderRadius: '12px',
                    padding: '16px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                      <span style={{ fontSize: '11px', fontWeight: '700', color: '#fb7185', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                        Previous Policy Clause
                      </span>
                      {item.old_page && (
                        <button
                          className="citation-pill"
                          onClick={() => onOpenPdf(diffData.old_policy_id, item.old_page)}
                        >
                          📄 Page {item.old_page}
                        </button>
                      )}
                    </div>
                    <p style={{ fontSize: '13px', color: '#94a3b8', fontStyle: 'italic', lineHeight: '1.55' }}>
                      "{item.old_clause_text}"
                    </p>
                  </div>

                  {/* New Version Clause */}
                  <div style={{
                    background: 'rgba(11, 17, 32, 0.7)',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                    borderRadius: '12px',
                    padding: '16px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                      <span style={{ fontSize: '11px', fontWeight: '700', color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                        Renewal Policy Clause
                      </span>
                      {item.new_page && (
                        <button
                          className="citation-pill"
                          onClick={() => onOpenPdf(diffData.new_policy_id, item.new_page)}
                        >
                          📄 Page {item.new_page}
                        </button>
                      )}
                    </div>
                    <p style={{ fontSize: '13px', color: '#f1f5f9', lineHeight: '1.55' }}>
                      "{item.new_clause_text}"
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '48px 32px', textAlign: 'center' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'rgba(2, 132, 199, 0.15)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto'
          }}>
            <History size={28} color="#38bdf8" />
          </div>
          <h3 style={{ fontSize: '17px', fontWeight: '700', color: '#ffffff', marginBottom: '8px' }}>
            Clause Shift & Contract Evolution Tracking
          </h3>
          <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', maxWidth: '580px', margin: '0 auto 24px auto', lineHeight: '1.5' }}>
            Select an older policy release (e.g. <em>Optima Secure Legacy 2021</em>) and compare against its latest renewal (e.g. <em>Optima Secure 2024</em>) to audit changes in exclusions, co-pays, and waiting periods.
          </p>
          <button
            onClick={runDiff}
            disabled={loading}
            className="btn-primary"
            style={{ padding: '12px 28px' }}
          >
            <Sparkles size={16} />
            <span>Audit Renewal Changes</span>
          </button>
        </div>
      )}
    </div>
  )
}
