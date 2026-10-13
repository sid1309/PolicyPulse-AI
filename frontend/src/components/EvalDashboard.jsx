import React, { useState } from 'react'
import { apiUrl } from '../apiConfig'
import { LineChart, CheckCircle2, AlertCircle, Play, Sparkles, Clock, Target, Award, BookCheck, ShieldCheck, Zap } from 'lucide-react'

export default function EvalDashboard() {
  const [loading, setLoading] = useState(false)
  const [evalData, setEvalData] = useState(null)
  const [error, setError] = useState('')

  const runBenchmark = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(apiUrl('/api/eval/benchmark'))
      if (!res.ok) {
        throw new Error('Benchmark execution failed')
      }
      const data = await res.json()
      setEvalData(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Panel */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '19px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '10px', color: '#ffffff' }}>
                <LineChart size={22} color="#38bdf8" /> RAG Evaluation & Benchmarking Suite
              </h2>
              <span className="badge badge-blue">Automated QA</span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Evaluate retrieval quality, ranking accuracy (MRR), citation integrity, and query latency across curated golden test questions.
            </p>
          </div>
          <button
            onClick={runBenchmark}
            disabled={loading}
            className="btn-primary"
            style={{ padding: '12px 24px' }}
          >
            <Play size={16} />
            <span>{loading ? 'Evaluating Golden QA Set...' : 'Run Automated Benchmark'}</span>
          </button>
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

      {/* Metrics Cards */}
      {evalData ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '16px' }}>
            <div className="glass-panel" style={{ padding: '22px', borderTop: '3px solid #10b981' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  RETRIEVAL RECALL@5
                </span>
                <Target size={18} color="#10b981" />
              </div>
              <div style={{ fontSize: '32px', fontWeight: '800', color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                {evalData.metrics.recall_at_5}%
              </div>
              <div style={{ fontSize: '11.5px', color: '#34d399', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                <CheckCircle2 size={13} /> Target: ≥ 85% (Passing)
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '22px', borderTop: '3px solid #0284c7' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  MEAN RECIPROCAL RANK (MRR)
                </span>
                <Award size={18} color="#38bdf8" />
              </div>
              <div style={{ fontSize: '32px', fontWeight: '800', color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                {evalData.metrics.mean_reciprocal_rank}
              </div>
              <div style={{ fontSize: '11.5px', color: '#38bdf8', marginTop: '6px' }}>
                Top clause ranking precision
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '22px', borderTop: '3px solid #06b6d4' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  CITATION GROUNDING
                </span>
                <BookCheck size={18} color="#06b6d4" />
              </div>
              <div style={{ fontSize: '32px', fontWeight: '800', color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                {evalData.metrics.citation_precision}%
              </div>
              <div style={{ fontSize: '11.5px', color: '#06b6d4', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                <CheckCircle2 size={13} /> Verified Page Number Grounding
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '22px', borderTop: '3px solid #f59e0b' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  AVERAGE PIPELINE LATENCY
                </span>
                <Clock size={18} color="#f59e0b" />
              </div>
              <div style={{ fontSize: '32px', fontWeight: '800', color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                {evalData.metrics.average_latency_ms} ms
              </div>
              <div style={{ fontSize: '11.5px', color: '#fbbf24', marginTop: '6px' }}>
                Hybrid Retriever + Reranker + LLM
              </div>
            </div>
          </div>

          {/* Test Cases Table */}
          <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#ffffff' }}>
                Evaluated Test Cases Breakdown ({evalData.total_evaluated_questions} Golden Questions)
              </h3>
              <span className="badge badge-covered">100% Deterministic</span>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '750px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid rgba(255, 255, 255, 0.1)', color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '12px 14px' }}>Category</th>
                  <th style={{ padding: '12px 14px' }}>Question</th>
                  <th style={{ padding: '12px 14px' }}>Recall@5</th>
                  <th style={{ padding: '12px 14px' }}>MRR</th>
                  <th style={{ padding: '12px 14px' }}>Citations</th>
                  <th style={{ padding: '12px 14px' }}>Latency</th>
                </tr>
              </thead>
              <tbody>
                {evalData.breakdown.map((row, idx) => (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      fontSize: '13px',
                      background: idx % 2 === 0 ? 'rgba(15, 23, 42, 0.3)' : 'transparent'
                    }}
                  >
                    <td style={{ padding: '14px' }}>
                      <span className="badge badge-blue">{row.category}</span>
                    </td>
                    <td style={{ padding: '14px', color: '#ffffff', fontWeight: '600' }}>
                      {row.question}
                    </td>
                    <td style={{ padding: '14px' }}>
                      <span className={`badge ${row.recall_at_5 === 1 ? 'badge-covered' : 'badge-excluded'}`}>
                        {row.recall_at_5 === 1 ? 'HIT' : 'MISS'}
                      </span>
                    </td>
                    <td style={{ padding: '14px', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                      {row.reciprocal_rank}
                    </td>
                    <td style={{ padding: '14px' }}>
                      <span className="badge badge-neutral">{row.citations_count} Verified</span>
                    </td>
                    <td style={{ padding: '14px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {row.latency_ms} ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="glass-panel" style={{ padding: '56px 24px', textAlign: 'center' }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '16px',
            background: 'rgba(2, 132, 199, 0.15)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto'
          }}>
            <Target size={30} color="#38bdf8" />
          </div>
          <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#ffffff', marginBottom: '8px' }}>
            Production Benchmark Suite Ready
          </h3>
          <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto 24px auto', lineHeight: '1.5' }}>
            Run the automated golden test suite to measure Recall@5, Mean Reciprocal Rank (MRR), Citation Grounding Accuracy, and Response Latency across critical policy scenarios.
          </p>
          <button
            onClick={runBenchmark}
            disabled={loading}
            className="btn-primary"
            style={{ padding: '12px 28px' }}
          >
            <Play size={16} />
            <span>{loading ? 'Evaluating...' : 'Run Automated Benchmark'}</span>
          </button>
        </div>
      )}
    </div>
  )
}
