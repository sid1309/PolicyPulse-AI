import React, { useState, useEffect } from 'react'
import { apiUrl } from '../apiConfig'
import {
  Scale, Check, AlertCircle, Sparkles, Award, Layers,
  FileDiff, ArrowRight, PlusCircle, MinusCircle, Info, History
} from 'lucide-react'

// ─── Sub-view: Side-by-Side Comparison ───────────────────────────────────────
function ComparisonView({ policies, onOpenPdf }) {
  const [selectedPolicies, setSelectedPolicies] = useState([])
  const [loading, setLoading] = useState(false)
  const [comparisonData, setComparisonData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setSelectedPolicies((prev) => {
      const valid = prev.filter((pid) => policies.some((p) => p.policy_id === pid))
      if (valid.length === 0 && policies.length >= 2) {
        return [policies[0].policy_id, policies[1].policy_id]
      }
      return valid
    })

    if (comparisonData) {
      const activeIds = new Set(policies.map((p) => p.policy_id))
      const hasDeleted = Object.keys(comparisonData.matrix || {}).some((pid) => !activeIds.has(pid))
      if (hasDeleted) {
        setComparisonData(null)
      }
    }
  }, [policies])

  const togglePolicy = (policyId) => {
    setSelectedPolicies((prev) =>
      prev.includes(policyId) ? prev.filter((p) => p !== policyId) : [...prev, policyId]
    )
  }

  const runComparison = async () => {
    if (selectedPolicies.length < 2) {
      setError('Please select at least 2 policies.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const res = await fetch(apiUrl('/api/compare'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy_ids: selectedPolicies }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Comparison failed')
      }
      setComparisonData(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Policy Selector */}
      <div style={{ padding: '20px', background: 'rgba(15,23,42,0.5)', borderRadius: '14px', border: '1px solid var(--border-subtle)' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '14px' }}>
          Select 2 or more policies to compare across 8 coverage benchmarks simultaneously.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '16px' }}>
          {policies.map((p) => {
            const isChecked = selectedPolicies.includes(p.policy_id)
            return (
              <label key={p.policy_id} style={{
                display: 'inline-flex', alignItems: 'center', gap: '10px',
                padding: '9px 15px', borderRadius: '11px', cursor: 'pointer',
                border: isChecked ? '1px solid #0284c7' : '1px solid var(--border-subtle)',
                background: isChecked ? 'rgba(2, 132, 199, 0.18)' : 'rgba(15, 23, 42, 0.6)',
                fontSize: '13px', color: isChecked ? '#ffffff' : 'var(--text-muted)',
                transition: 'all 0.16s ease', userSelect: 'none'
              }}>
                <input type="checkbox" checked={isChecked} onChange={() => togglePolicy(p.policy_id)}
                  style={{ cursor: 'pointer', accentColor: '#0284c7', width: '15px', height: '15px' }} />
                <span><strong style={{ color: '#38bdf8' }}>{p.insurer}</strong> — {p.plan_name} <span style={{ opacity: 0.65 }}>(v{p.version})</span></span>
              </label>
            )
          })}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <button onClick={runComparison} disabled={loading || selectedPolicies.length < 2}
            className="btn-primary" style={{ padding: '10px 22px' }}>
            <Sparkles size={15} />
            {loading ? 'Comparing clauses...' : `Compare ${selectedPolicies.length} Policies`}
          </button>
          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', color: '#fb7185', fontSize: '13px' }}>
              <AlertCircle size={15} /> {error}
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {comparisonData ? (
        <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
          {/* Executive Verdict */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.18) 0%, rgba(13, 21, 38, 0.85) 100%)',
            border: '1px solid rgba(56, 189, 248, 0.35)', borderRadius: '14px',
            padding: '18px 22px', marginBottom: '22px',
            display: 'flex', alignItems: 'flex-start', gap: '14px'
          }}>
            <div style={{
              width: '38px', height: '38px', borderRadius: '10px',
              background: 'rgba(2, 132, 199, 0.25)', display: 'flex',
              alignItems: 'center', justifyContent: 'center', flexShrink: 0
            }}>
              <Award size={20} color="#38bdf8" />
            </div>
            <div>
              <div style={{ fontSize: '11px', fontWeight: '800', color: '#38bdf8', letterSpacing: '0.04em', textTransform: 'uppercase', marginBottom: '4px' }}>
                AI Recommendation
              </div>
              <div style={{ fontSize: '14px', color: '#f8fafc', lineHeight: '1.55', fontWeight: 500 }}>
                {comparisonData.executive_verdict}
              </div>
            </div>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '800px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid rgba(255,255,255,0.12)' }}>
                <th style={{ padding: '14px 12px', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', width: '200px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Coverage Area
                </th>
                {selectedPolicies.map((pid) => {
                  const policy = policies.find((p) => p.policy_id === pid)
                  return (
                    <th key={pid} style={{ padding: '14px 12px' }}>
                      <div style={{ fontSize: '11px', color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{policy?.insurer}</div>
                      <div style={{ fontSize: '14px', fontWeight: '700', color: '#fff', marginTop: '2px' }}>{policy?.plan_name}</div>
                    </th>
                  )
                })}
                <th style={{ padding: '14px 12px', fontSize: '12px', fontWeight: '700', color: '#fbbf24', width: '240px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Takeaway
                </th>
              </tr>
            </thead>
            <tbody>
              {comparisonData.matrix.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid var(--border-subtle)',
                  background: idx % 2 === 0 ? 'rgba(15,23,42,0.3)' : 'transparent'
                }}>
                  <td style={{ padding: '16px 12px', fontSize: '13px', fontWeight: '700', color: '#e2e8f0', verticalAlign: 'top' }}>
                    {row.feature_category}
                  </td>
                  {selectedPolicies.map((pid) => {
                    const evalItem = row.policies[pid] || {}
                    return (
                      <td key={pid} style={{ padding: '16px 12px', fontSize: '13px', verticalAlign: 'top' }}>
                        <div style={{ fontWeight: '600', color: '#f8fafc', marginBottom: '5px', lineHeight: '1.4' }}>
                          {evalItem.summary}
                        </div>
                        {evalItem.excerpt && (
                          <p style={{
                            fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px',
                            lineHeight: '1.45', fontStyle: 'italic',
                            background: 'rgba(255,255,255,0.02)', padding: '5px 7px',
                            borderRadius: '5px', borderLeft: '2px solid rgba(56,189,248,0.35)'
                          }}>
                            "{evalItem.excerpt}"
                          </p>
                        )}
                        {evalItem.page_number && (
                          <button className="citation-pill" onClick={() => onOpenPdf(pid, evalItem.page_number)}>
                            📄 Pg {evalItem.page_number} · {evalItem.clause_title?.slice(0, 22)}
                          </button>
                        )}
                      </td>
                    )
                  })}
                  <td style={{ padding: '16px 12px', fontSize: '12px', color: '#cbd5e1', verticalAlign: 'top', background: 'rgba(30,41,59,0.2)' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '7px' }}>
                      <div style={{
                        width: '16px', height: '16px', borderRadius: '50%',
                        background: 'rgba(16,185,129,0.2)', display: 'flex',
                        alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '1px'
                      }}>
                        <Check size={10} color="#34d399" />
                      </div>
                      <span style={{ lineHeight: '1.45' }}>{row.recommendation}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '48px 32px', textAlign: 'center' }}>
          <div style={{
            width: '56px', height: '56px', borderRadius: '16px',
            background: 'rgba(2,132,199,0.15)', border: '1px solid rgba(56,189,248,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px'
          }}>
            <Layers size={28} color="#38bdf8" />
          </div>
          <h3 style={{ fontSize: '17px', fontWeight: '700', color: '#ffffff', marginBottom: '8px' }}>
            Ready for Side-by-Side Comparison
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto', lineHeight: '1.5' }}>
            Select policies above and click Compare to see room-rent limits, waiting periods, robotic surgery caps, and more in a unified grid.
          </p>
        </div>
      )}
    </div>
  )
}

// ─── Sub-view: Version Diff ───────────────────────────────────────────────────
function DiffView({ policies, onOpenPdf }) {
  const [oldPolicyId, setOldPolicyId] = useState(
    policies.length > 2 ? policies[2].policy_id : (policies[0]?.policy_id || '')
  )
  const [newPolicyId, setNewPolicyId] = useState(policies[0]?.policy_id || '')
  const [loading, setLoading] = useState(false)
  const [diffData, setDiffData] = useState(null)
  const [error, setError] = useState('')

  const runDiff = async () => {
    if (!oldPolicyId || !newPolicyId) { setError('Select both policies.'); return }
    if (oldPolicyId === newPolicyId) { setError('Select two distinct policy versions.'); return }
    setError('')
    setLoading(true)
    try {
      const res = await fetch(apiUrl('/api/compare/diff'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_policy_id: oldPolicyId, new_policy_id: newPolicyId })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Diff failed')
      }
      setDiffData(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const renderBadge = (changeType) => {
    if (changeType === 'EXPANSION')
      return <span className="badge badge-covered"><PlusCircle size={12} /> Benefit Added</span>
    if (changeType === 'RESTRICTION')
      return <span className="badge badge-excluded"><MinusCircle size={12} /> Restriction Added</span>
    return <span className="badge badge-blue"><Info size={12} /> Procedural Update</span>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Selector */}
      <div style={{ padding: '20px', background: 'rgba(15,23,42,0.5)', borderRadius: '14px', border: '1px solid var(--border-subtle)' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Compare an older policy edition against a renewal to spot hidden restriction changes, new co-payments, or expanded benefits.
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '240px' }}>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
              Older / Base Version
            </label>
            <select value={oldPolicyId} onChange={(e) => setOldPolicyId(e.target.value)} className="form-select">
              {policies.map((p) => (
                <option key={p.policy_id} value={p.policy_id}>{p.insurer} — {p.plan_name} (v{p.version})</option>
              ))}
            </select>
          </div>
          <div style={{ paddingTop: '22px' }}>
            <div style={{
              width: '34px', height: '34px', borderRadius: '50%',
              background: 'rgba(2,132,199,0.15)', border: '1px solid rgba(56,189,248,0.25)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <ArrowRight size={17} color="#38bdf8" />
            </div>
          </div>
          <div style={{ flex: 1, minWidth: '240px' }}>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
              Newer / Renewal Version
            </label>
            <select value={newPolicyId} onChange={(e) => setNewPolicyId(e.target.value)} className="form-select">
              {policies.map((p) => (
                <option key={p.policy_id} value={p.policy_id}>{p.insurer} — {p.plan_name} (v{p.version})</option>
              ))}
            </select>
          </div>
          <div style={{ paddingTop: '22px' }}>
            <button onClick={runDiff} disabled={loading} className="btn-primary" style={{ padding: '10px 20px' }}>
              <Sparkles size={15} />
              <span>{loading ? 'Analyzing...' : 'Detect Changes'}</span>
            </button>
          </div>
        </div>
        {error && (
          <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '7px', color: '#fb7185', fontSize: '13px' }}>
            <AlertCircle size={15} /> {error}
          </div>
        )}
      </div>

      {/* Results */}
      {diffData ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="glass-panel" style={{
            padding: '20px 24px', borderLeft: '4px solid #0284c7',
            background: 'linear-gradient(135deg, rgba(2,132,199,0.12) 0%, rgba(13,21,38,0.8) 100%)'
          }}>
            <div style={{ fontSize: '11px', fontWeight: '800', color: '#38bdf8', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Renewal Summary
            </div>
            <p style={{ fontSize: '14px', color: '#f8fafc', lineHeight: '1.6', marginTop: '5px' }}>
              {diffData.summary_of_changes}
            </p>
          </div>

          {diffData.changes.map((item, idx) => (
            <div key={idx} className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '15px', fontWeight: '700', color: '#ffffff' }}>{item.category}</span>
                  {renderBadge(item.change_type)}
                </div>
                <span style={{ fontSize: '12px', color: '#38bdf8', fontWeight: '600', background: 'rgba(2,132,199,0.12)', padding: '3px 9px', borderRadius: '6px' }}>
                  {item.impact_analysis}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '14px' }}>
                <div style={{ background: 'rgba(11,17,32,0.7)', border: '1px solid rgba(244,63,94,0.25)', borderRadius: '10px', padding: '14px' }}>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: '#fb7185', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span>Previous Version</span>
                    {item.old_page && <button className="citation-pill" onClick={() => onOpenPdf(diffData.old_policy_id, item.old_page)}>📄 Pg {item.old_page}</button>}
                  </div>
                  <p style={{ fontSize: '13px', color: '#94a3b8', fontStyle: 'italic', lineHeight: '1.55', margin: 0 }}>"{item.old_clause_text}"</p>
                </div>
                <div style={{ background: 'rgba(11,17,32,0.7)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: '10px', padding: '14px' }}>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: '#34d399', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span>Renewal Version</span>
                    {item.new_page && <button className="citation-pill" onClick={() => onOpenPdf(diffData.new_policy_id, item.new_page)}>📄 Pg {item.new_page}</button>}
                  </div>
                  <p style={{ fontSize: '13px', color: '#f1f5f9', lineHeight: '1.55', margin: 0 }}>"{item.new_clause_text}"</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '48px 32px', textAlign: 'center' }}>
          <div style={{
            width: '56px', height: '56px', borderRadius: '16px',
            background: 'rgba(2,132,199,0.15)', border: '1px solid rgba(56,189,248,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px'
          }}>
            <History size={28} color="#38bdf8" />
          </div>
          <h3 style={{ fontSize: '17px', fontWeight: '700', color: '#ffffff', marginBottom: '8px' }}>
            Renewal Change Detector
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto', lineHeight: '1.5' }}>
            Select an older base policy and its renewal edition above to automatically detect expansions, new restrictions, or changed waiting periods.
          </p>
        </div>
      )}
    </div>
  )
}

// ─── Parent Tab with Segmented Control ───────────────────────────────────────
export default function ComparisonMatrix({ policies, onOpenPdf }) {
  const [mode, setMode] = useState('compare') // 'compare' | 'diff'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Tab Header */}
      <div className="glass-panel" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: '800', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              {mode === 'compare' ? <Scale size={21} color="#38bdf8" /> : <FileDiff size={21} color="#38bdf8" />}
              {mode === 'compare' ? 'Compare Policies Side-by-Side' : 'Renewal Version Diff'}
            </h2>
            <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginTop: '3px' }}>
              {mode === 'compare'
                ? 'Benchmark multiple policies across 8 critical coverage dimensions at once.'
                : 'Detect hidden changes between policy editions — new restrictions, expanded benefits, shifted waiting periods.'}
            </p>
          </div>

          {/* Segmented Control */}
          <div style={{
            display: 'flex', background: 'rgba(15,23,42,0.7)',
            borderRadius: '10px', padding: '3px', border: '1px solid var(--border-subtle)'
          }}>
            {[
              { id: 'compare', label: 'Side-by-Side', icon: Scale },
              { id: 'diff', label: 'Version Diff', icon: FileDiff },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setMode(id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  padding: '7px 16px', borderRadius: '8px',
                  border: mode === id ? '1px solid rgba(56,189,248,0.4)' : '1px solid transparent',
                  background: mode === id ? 'linear-gradient(135deg, rgba(2,132,199,0.28) 0%, rgba(3,105,161,0.18) 100%)' : 'transparent',
                  color: mode === id ? '#38bdf8' : 'var(--text-muted)',
                  fontSize: '13px', fontWeight: mode === id ? 700 : 500,
                  cursor: 'pointer', transition: 'all 0.16s ease', whiteSpace: 'nowrap'
                }}
              >
                <Icon size={14} />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Render active sub-view */}
      {mode === 'compare'
        ? <ComparisonView policies={policies} onOpenPdf={onOpenPdf} />
        : <DiffView policies={policies} onOpenPdf={onOpenPdf} />
      }
    </div>
  )
}
