import React, { useState, useRef, useEffect } from 'react'
import {
  Send, Sparkles, CheckCircle2, AlertTriangle, XCircle, HelpCircle,
  BookOpen, Layers, ShieldCheck, Zap, Check, Info, ChevronRight,
  Star, Heart, Activity, Home, Eye, Pill, Lightbulb, RotateCcw,
  ArrowRight, Shield, FileText, ChevronDown, ChevronUp, Copy
} from 'lucide-react'

// ─── Plain English Explainer / Jargon Buster Accordion ────────────────────────
function ClauseExplainer({ clauseTitle, clauseText, verdict, insurer }) {
  const [open, setOpen] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleToggle = async () => {
    if (!open && !explanation && !loading) {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch('/api/chat/explain', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            clause_title: clauseTitle || 'Governing Policy Clause',
            clause_text: clauseText || 'Terms of coverage and limits',
            verdict: verdict,
            insurer: insurer
          })
        })
        if (!res.ok) throw new Error('Failed to load plain explanation')
        const data = await res.json()
        setExplanation(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    setOpen(!open)
  }

  return (
    <div style={{ marginTop: '14px', borderRadius: '12px', border: '1px solid rgba(56, 189, 248, 0.25)', overflow: 'hidden' }}>
      <button
        onClick={handleToggle}
        style={{
          width: '100%',
          padding: '10px 14px',
          background: 'rgba(2, 132, 199, 0.12)',
          border: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          color: '#38bdf8',
          fontSize: '12.5px',
          fontWeight: 700,
          transition: 'all 0.15s ease'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lightbulb size={16} color="#38bdf8" />
          <span>💡 Explain in Plain English (Jargon Buster)</span>
        </div>
        {open ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
      </button>

      {open && (
        <div style={{ padding: '16px', background: 'rgba(11, 17, 32, 0.95)', borderTop: '1px solid rgba(56, 189, 248, 0.2)' }}>
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '12.5px', padding: '8px 0' }}>
              <Sparkles size={14} color="#38bdf8" /> Translating legal jargon to everyday language...
            </div>
          )}

          {error && (
            <div style={{ color: '#f43f5e', fontSize: '12px' }}>{error}</div>
          )}

          {explanation && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* Plain Meaning */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '3px' }}>
                  🗣️ What This Means in Everyday Words
                </div>
                <p style={{ margin: 0, fontSize: '13px', color: '#e2e8f0', lineHeight: '1.5' }}>
                  {explanation.simple_explanation}
                </p>
              </div>

              {/* Wallet Impact */}
              <div style={{
                background: 'rgba(244, 63, 94, 0.08)',
                border: '1px solid rgba(244, 63, 94, 0.22)',
                borderRadius: '8px',
                padding: '10px 12px'
              }}>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#fb7185', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2px' }}>
                  💳 Financial Impact on Your Wallet
                </div>
                <div style={{ fontSize: '12.5px', color: '#fecdd3', lineHeight: '1.45' }}>
                  {explanation.wallet_impact}
                </div>
              </div>

              {/* Action Checklist */}
              {explanation.action_checklist && explanation.action_checklist.length > 0 && (
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                    📋 3 Concrete Steps You Should Take
                  </div>
                  <ul style={{ paddingLeft: 0, margin: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {explanation.action_checklist.map((act, i) => (
                      <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '7px', fontSize: '12.5px', color: '#cbd5e1' }}>
                        <span style={{ color: '#10b981', fontWeight: 800 }}>✓</span>
                        <span>{act}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Structured Answer Card ──────────────────────────────────────────────────
function AnswerCard({ message, onOpenPdf }) {
  const verdictConfig = {
    COVERED: {
      color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)', border: 'rgba(16, 185, 129, 0.35)',
      icon: <CheckCircle2 size={20} color="#10b981" />, label: 'COVERED',
      headline: 'This treatment is covered under your policy.',
      badgeClass: 'badge-covered'
    },
    EXCLUDED: {
      color: '#f43f5e', bg: 'rgba(244, 63, 94, 0.1)', border: 'rgba(244, 63, 94, 0.35)',
      icon: <XCircle size={20} color="#f43f5e" />, label: 'NOT COVERED',
      headline: 'This is excluded from your policy coverage.',
      badgeClass: 'badge-excluded'
    },
    CONDITIONAL: {
      color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', border: 'rgba(245, 158, 11, 0.35)',
      icon: <AlertTriangle size={20} color="#f59e0b" />, label: 'CONDITIONS APPLY',
      headline: 'Coverage applies but with specific restrictions or waiting periods.',
      badgeClass: 'badge-conditional'
    },
    INSUFFICIENT: {
      color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.08)', border: 'rgba(148, 163, 184, 0.25)',
      icon: <HelpCircle size={20} color="#94a3b8" />, label: 'NOT MENTIONED',
      headline: 'Your policy does not explicitly mention this condition.',
      badgeClass: 'badge-neutral'
    },
    INFO: {
      color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.08)', border: 'rgba(56, 189, 248, 0.2)',
      icon: <ShieldCheck size={20} color="#38bdf8" />, label: 'INFO',
      headline: null,
      badgeClass: 'badge-blue'
    },
    NEUTRAL: {
      color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.08)', border: 'rgba(56, 189, 248, 0.2)',
      icon: <Info size={20} color="#38bdf8" />, label: 'ANALYSIS',
      headline: null,
      badgeClass: 'badge-blue'
    }
  }

  const cfg = verdictConfig[message.verdict] || verdictConfig.NEUTRAL

  const parseAnswerSections = (text) => {
    if (!text) return []
    const lines = text.split('\n')
    const sections = []
    let currentSection = null

    const flushTable = (sec) => {
      if (sec && sec.pendingTableLines && sec.pendingTableLines.length >= 2) {
        const cleanLines = sec.pendingTableLines.filter(l => l.startsWith('|') && l.endsWith('|'))
        if (cleanLines.length >= 2) {
          const splitRow = (r) => r.slice(1, -1).split('|').map(c => c.trim())
          const headers = splitRow(cleanLines[0])
          const hasSep = cleanLines[1].replace(/[\s\-\|:]/g, '').length === 0
          const dataRows = (hasSep ? cleanLines.slice(2) : cleanLines.slice(1)).map(splitRow)
          if (!sec.tables) sec.tables = []
          sec.tables.push({ headers, rows: dataRows })
        }
        sec.pendingTableLines = []
      }
    }

    lines.forEach(rawLine => {
      const line = rawLine.trim()
      if (!line) return

      // System context annotations like *Follow-up context considered...* or *Please refer to source citations...*
      if (line.startsWith('*') && line.endsWith('*') && (line.includes('Follow-up context') || line.includes('source document citations') || line.includes('contractual wording') || line.includes('previous question'))) {
        flushTable(currentSection)
        if (!currentSection) currentSection = { heading: null, bullets: [], text: [], quotes: [], notes: [], tables: [], pendingTableLines: [] }
        currentSection.notes.push(line.replace(/^\*+|\*+$/g, '').trim())
      } else if (line.startsWith('>')) {
        flushTable(currentSection)
        // Blockquote extract from contract
        if (!currentSection) currentSection = { heading: null, bullets: [], text: [], quotes: [], notes: [], tables: [], pendingTableLines: [] }
        const cleanQuote = line.replace(/^>\s*/, '').replace(/^"+|"+$/g, '').trim()
        if (cleanQuote) {
          const tagMatch = cleanQuote.match(/^\*{0,2}\[((?:Section|Clause|Page|Policy).*?)\]\*{0,2}$/i)
          if (tagMatch) {
            currentSection.pendingQuoteHeader = tagMatch[1].trim()
          } else {
            const header = currentSection.pendingQuoteHeader || null
            currentSection.quotes.push({
              header: header,
              text: cleanQuote
            })
            currentSection.pendingQuoteHeader = null
          }
        }
      } else if (line.startsWith('|') && line.endsWith('|')) {
        // Table row
        if (!currentSection) currentSection = { heading: null, bullets: [], text: [], quotes: [], notes: [], tables: [], pendingTableLines: [] }
        if (!currentSection.pendingTableLines) currentSection.pendingTableLines = []
        if (!currentSection.tables) currentSection.tables = []
        currentSection.pendingTableLines.push(line)
      } else if (line.startsWith('## ') || line.startsWith('### ')) {
        flushTable(currentSection)
        if (currentSection) {
          if (currentSection.pendingQuoteHeader) {
            currentSection.quotes.push({ header: null, text: currentSection.pendingQuoteHeader })
            currentSection.pendingQuoteHeader = null
          }
          sections.push(currentSection)
        }
        currentSection = { heading: line.replace(/^#{2,3}\s/, ''), bullets: [], text: [], quotes: [], notes: [], tables: [], pendingTableLines: [] }
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        flushTable(currentSection)
        if (!currentSection) currentSection = { heading: null, bullets: [], text: [], quotes: [], notes: [], tables: [], pendingTableLines: [] }
        currentSection.bullets.push(line.slice(2).trim())
      } else {
        flushTable(currentSection)
        if (!currentSection) currentSection = { heading: null, bullets: [], text: [], quotes: [], notes: [], tables: [], pendingTableLines: [] }
        currentSection.text.push(line)
      }
    })
    flushTable(currentSection)
    if (currentSection) {
      if (currentSection.pendingQuoteHeader) {
        currentSection.quotes.push({ header: null, text: currentSection.pendingQuoteHeader })
        currentSection.pendingQuoteHeader = null
      }
      sections.push(currentSection)
    }
    return sections
  }

  const renderBold = (str) => {
    const parts = str.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ color: '#ffffff', fontWeight: 700 }}>{part.slice(2, -2)}</strong>
      }
      return part
    })
  }

  const sections = parseAnswerSections(message.text)
  const citationCount = message.citations ? message.citations.length : 0
  const topCitation = citationCount > 0 ? message.citations[0] : null

  return (
    <div style={{
      alignSelf: 'flex-start',
      maxWidth: '92%',
      background: 'rgba(11, 17, 32, 0.92)',
      border: `1px solid ${cfg.border}`,
      borderRadius: '18px',
      overflow: 'hidden',
      boxShadow: `0 4px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05)`
    }}>
      {/* Verdict Header Bar */}
      <div style={{
        background: cfg.bg,
        borderBottom: `1px solid ${cfg.border}`,
        padding: '14px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {cfg.icon}
          <div>
            <div style={{ fontSize: '12px', fontWeight: '800', color: cfg.color, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              {cfg.label}
            </div>
            {cfg.headline && (
              <div style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: 600, marginTop: '2px' }}>
                {cfg.headline}
              </div>
            )}
          </div>
        </div>

        {message.insufficient && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(148, 163, 184, 0.12)',
              border: '1px solid rgba(148, 163, 184, 0.25)',
              borderRadius: '20px',
              padding: '4px 10px'
            }}
            title="The engine inspected your policy and safely abstained because no matching clause exists."
          >
            <HelpCircle size={14} color="#94a3b8" />
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8' }}>
              No Matching Clause
            </span>
          </div>
        )}
      </div>

      {/* Body */}
      <div style={{ padding: '20px 22px' }}>
        {sections.length > 0 ? (
          sections.map((sec, i) => (
            <div key={i} style={{ marginBottom: i < sections.length - 1 ? '16px' : 0 }}>
              {sec.heading && (
                <div style={{
                  fontSize: '12px', fontWeight: '800', color: '#38bdf8',
                  textTransform: 'uppercase', letterSpacing: '0.05em',
                  marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px'
                }}>
                  <ChevronRight size={13} /> {sec.heading}
                </div>
              )}

              {/* Text paragraphs */}
              {sec.text.map((t, j) => (
                <p key={j} style={{ fontSize: '13.5px', color: '#cbd5e1', lineHeight: '1.65', margin: '0 0 8px 0' }}>
                  {renderBold(t)}
                </p>
              ))}

              {/* Styled Contract Quote Cards */}
              {sec.quotes && sec.quotes.length > 0 && (
                <div style={{ margin: '12px 0 16px 0', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {sec.quotes.map((qItem, qIdx) => {
                    const rawQText = typeof qItem === 'string' ? qItem : qItem.text
                    const qHeader = typeof qItem === 'object' ? qItem.header : null
                    
                    // Clean breadcrumbs and formatting
                    let displayText = (rawQText || '').replace(/^\[(?:Policy:?\s*)?[^\]]+\]\s*>\s*\[[^\]]+\](?:\s*>\s*\[[^\]]+\])?:?\s*/, '').trim()
                    
                    // Clean up qHeader if the Clause portion is just an excerpt of the quote body
                    let displayHeader = qHeader
                    if (displayHeader) {
                      displayHeader = displayHeader.replace(/\[(?:Policy:?\s*)?[^\]]+\]\s*>\s*/g, '').replace(/[\[\]]/g, '').trim()
                      const clauseMatch = displayHeader.match(/Clause:\s*(.+?)(?:\s*•|$)/i)
                      if (clauseMatch) {
                        const rawClause = clauseMatch[1].trim()
                        const cleanRaw = rawClause.replace(/^([a-z0-9]+[\.\)]\s*|\([a-z0-9]+\)\s*)/i, '').trim().toLowerCase()
                        const cleanBody = displayText.replace(/^([a-z0-9]+[\.\)]\s*|\([a-z0-9]+\)\s*)/i, '').trim().toLowerCase()
                        if (cleanRaw.length >= 20 && cleanBody.startsWith(cleanRaw.slice(0, 20))) {
                          const enumMatch = rawClause.match(/^([a-z0-9]+[\.\)]|\([a-z0-9]+\))/i)
                          const shortClause = enumMatch ? `Clause ${enumMatch[1]}` : 'Governing Provision'
                          displayHeader = displayHeader.replace(rawClause, shortClause)
                        }
                      }
                    }

                    return (
                      <div
                        key={qIdx}
                        style={{
                          padding: '14px 18px',
                          background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.08) 0%, rgba(15, 23, 42, 0.8) 100%)',
                          borderLeft: '4px solid #38bdf8',
                          borderRadius: '4px 12px 12px 4px',
                          borderTop: '1px solid rgba(56, 189, 248, 0.22)',
                          borderRight: '1px solid rgba(56, 189, 248, 0.22)',
                          borderBottom: '1px solid rgba(56, 189, 248, 0.22)',
                          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.25)'
                        }}
                      >
                        <div style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          flexWrap: 'wrap', gap: '8px', marginBottom: '10px'
                        }}>
                          <div style={{
                            display: 'flex', alignItems: 'center', gap: '6px',
                            fontSize: '11px', fontWeight: 800, color: '#38bdf8',
                            textTransform: 'uppercase', letterSpacing: '0.05em'
                          }}>
                            <BookOpen size={13} color="#38bdf8" />
                            <span>Exact Contractual Policy Extract</span>
                          </div>
                          {displayHeader && (
                            <span style={{
                              fontSize: '11px', fontWeight: 700, color: '#e0f2fe',
                              background: 'rgba(56, 189, 248, 0.16)', border: '1px solid rgba(56, 189, 248, 0.35)',
                              padding: '2px 8px', borderRadius: '12px'
                            }}>
                              {displayHeader}
                            </span>
                          )}
                        </div>
                        {(() => {
                          const formattedDisplay = displayText
                            .replace(/([^\s\n])\s+([1a]\.\s+|[1a]\)\s+|\([1a]\)\s+)/gi, '$1\n\n$2')
                            .replace(/([;\.\:])\s+(\b[0-9]{1,2}\.|\b[a-z0-9]\)|\b[ivxlcdm]+\.)\s+/g, '$1\n\n$2 ')
                            .replace(/([;\.\:\)])\s+(Code[\-\s]*Excl[0-9]+|\bExcl[0-9]+\b)/gi, '$1\n\n$2')
                            .replace(/([^\s\n])\s+(Def\s+[0-9]+[\.\:]|\bDefinition\s+[0-9]+[\.\:])/gi, '$1\n\n$2')
                          const paragraphs = formattedDisplay.split('\n\n').filter(Boolean)
                          return (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              {paragraphs.map((p, pIdx) => {
                                const isSubpoint = /^(?:[0-9]{1,2}\.|\([a-z0-9]+\)|[a-z0-9]\)|def\s+[0-9]+[\.\:]|definition\s+[0-9]+[\.\:])/i.test(p.trim())
                                return (
                                  <p
                                    key={pIdx}
                                    style={{
                                      margin: 0,
                                      fontSize: '13.5px',
                                      color: isSubpoint ? '#e2e8f0' : '#f8fafc',
                                      lineHeight: '1.65',
                                      fontFamily: 'inherit',
                                      paddingLeft: isSubpoint ? '10px' : '0px',
                                      borderLeft: isSubpoint ? '2px solid rgba(56, 189, 248, 0.4)' : 'none'
                                    }}
                                  >
                                    {pIdx === 0 && !p.startsWith('“') ? '“' : ''}
                                    {p}
                                    {pIdx === paragraphs.length - 1 && !p.endsWith('”') ? '”' : ''}
                                  </p>
                                )
                              })}
                            </div>
                          )
                        })()}
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Styled Glassmorphic Table Extracts */}
              {sec.tables && sec.tables.length > 0 && (
                <div style={{ margin: '14px 0 18px 0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {sec.tables.map((tbl, tblIdx) => (
                    <div
                      key={tblIdx}
                      style={{
                        borderRadius: '10px',
                        overflow: 'hidden',
                        border: '1px solid rgba(56, 189, 248, 0.28)',
                        background: 'rgba(11, 17, 32, 0.85)',
                        boxShadow: '0 6px 20px rgba(0, 0, 0, 0.35)'
                      }}
                    >
                      <div style={{
                        padding: '10px 14px',
                        background: 'linear-gradient(90deg, rgba(2, 132, 199, 0.22) 0%, rgba(15, 23, 42, 0.6) 100%)',
                        borderBottom: '1px solid rgba(56, 189, 248, 0.25)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        flexWrap: 'wrap',
                        gap: '8px'
                      }}>
                        <div style={{
                          display: 'flex', alignItems: 'center', gap: '6px',
                          fontSize: '11px', fontWeight: 800, color: '#38bdf8',
                          textTransform: 'uppercase', letterSpacing: '0.05em'
                        }}>
                          <FileText size={13} color="#38bdf8" />
                          <span>Exact Policy Schedule & Limit Grid</span>
                        </div>
                        <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>
                          {tbl.rows.length} {tbl.rows.length === 1 ? 'governing rule' : 'rules verified'}
                        </span>
                      </div>

                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12.5px' }}>
                          {tbl.headers && tbl.headers.length > 0 && (
                            <thead>
                              <tr style={{ background: 'rgba(30, 41, 59, 0.6)', borderBottom: '1px solid rgba(56, 189, 248, 0.2)' }}>
                                {tbl.headers.map((h, hIdx) => (
                                  <th
                                    key={hIdx}
                                    style={{
                                      padding: '9px 14px',
                                      color: '#94a3b8',
                                      fontWeight: 700,
                                      fontSize: '11px',
                                      textTransform: 'uppercase',
                                      letterSpacing: '0.05em',
                                      borderRight: hIdx < tbl.headers.length - 1 ? '1px solid rgba(56, 189, 248, 0.1)' : 'none'
                                    }}
                                  >
                                    {h.replace(/^Col_[0-9]+$/i, 'Clause Category')}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                          )}
                          <tbody>
                            {tbl.rows.map((row, rIdx) => {
                              const rowText = row.join(' ').toLowerCase()
                              const isHighlight = rowText.includes('room') || rowText.includes('rent') || rowText.includes('icu') || rowText.includes('⭐') || rowText.includes('1%') || rowText.includes('sublimit')
                              return (
                                <tr
                                  key={rIdx}
                                  style={{
                                    background: isHighlight ? 'rgba(56, 189, 248, 0.10)' : (rIdx % 2 === 0 ? 'transparent' : 'rgba(15, 23, 42, 0.35)'),
                                    borderBottom: rIdx < tbl.rows.length - 1 ? '1px solid rgba(56, 189, 248, 0.12)' : 'none',
                                    borderLeft: isHighlight ? '3px solid #38bdf8' : 'none'
                                  }}
                                >
                                  {row.map((cell, cIdx) => (
                                    <td
                                      key={cIdx}
                                      style={{
                                        padding: '10px 14px',
                                        color: isHighlight ? '#f8fafc' : '#cbd5e1',
                                        fontWeight: cIdx === 0 ? 600 : 400,
                                        lineHeight: '1.55',
                                        borderRight: cIdx < row.length - 1 ? '1px solid rgba(56, 189, 248, 0.08)' : 'none'
                                      }}
                                    >
                                      {renderBold(cell)}
                                    </td>
                                  ))}
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Bullet points */}
              {sec.bullets.length > 0 && (
                <ul style={{ paddingLeft: 0, margin: '6px 0 0 0', listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {sec.bullets.map((b, j) => (
                    <li key={j} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '13px', color: '#94a3b8' }}>
                      <span style={{ color: cfg.color, flexShrink: 0, marginTop: '2px' }}>›</span>
                      {renderBold(b)}
                    </li>
                  ))}
                </ul>
              )}

              {/* Context notes rendered as clean badges */}
              {sec.notes && sec.notes.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
                  {sec.notes.map((note, nIdx) => (
                    <div
                      key={nIdx}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '4px 10px',
                        borderRadius: '16px',
                        background: 'rgba(56, 189, 248, 0.1)',
                        border: '1px solid rgba(56, 189, 248, 0.25)',
                        fontSize: '11px',
                        color: '#93c5fd',
                        fontWeight: 500
                      }}
                    >
                      <Sparkles size={11} color="#38bdf8" />
                      <span>{note}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          <p style={{ fontSize: '13.5px', color: '#cbd5e1', lineHeight: '1.65', margin: 0 }}>
            {message.text}
          </p>
        )}

        {/* Feature B: Plain English Explainer / Jargon Buster */}
        {message.verdict !== 'INFO' && (
          <ClauseExplainer
            clauseTitle={topCitation ? topCitation.clause_title : 'Policy Coverage Clause'}
            clauseText={message.text}
            verdict={message.verdict}
            insurer={topCitation ? topCitation.insurer : null}
          />
        )}

        {/* Insufficient Evidence Banner */}
        {message.insufficient && (
          <div style={{
            marginTop: '14px', padding: '10px 14px', borderRadius: '10px',
            background: 'rgba(148, 163, 184, 0.08)', border: '1px solid rgba(148, 163, 184, 0.2)',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}>
            <HelpCircle size={14} color="#94a3b8" />
            <span style={{ fontSize: '12.5px', color: '#94a3b8' }}>
              Policy text doesn't contain enough information to give a definitive answer. Consider contacting your insurer directly.
            </span>
          </div>
        )}

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
            <div style={{
              fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)',
              textTransform: 'uppercase', marginBottom: '8px',
              display: 'flex', alignItems: 'center', gap: '5px'
            }}>
              <BookOpen size={13} color="#38bdf8" /> Source Clauses ({message.citations.length} verified) — click to open PDF
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {message.citations.map((c, idx) => (
                <button
                  key={idx}
                  className="citation-pill"
                  onClick={() => onOpenPdf(c.policy_id, c.page_number, c.clause_title, c.excerpt)}
                  title={`Open PDF at Page ${c.page_number}: ${c.clause_title}`}
                >
                  📄 {c.insurer} · Pg {c.page_number} · {c.clause_title?.slice(0, 26)}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function ChatAssistant({
  policies,
  activePolicyId,
  messages: propMessages,
  setMessages: propSetMessages,
  onOpenPdf,
  onOpenSummary
}) {
  const [query, setQuery] = useState('')
  const [selectedPolicyId, setSelectedPolicyId] = useState(
    activePolicyId || (policies && policies.length > 0 ? policies[0].policy_id : '')
  )
  const [loading, setLoading] = useState(false)
  const [localMessages, setLocalMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Welcome! I am your personal insurance intelligence guide.\n\nAsk me anything about your policy in plain language — whether your upcoming surgery is covered, what documents you need, or what the waiting period is for your condition.\n\n## How I protect you\n- Every answer comes directly from your official contract clauses\n- I cite the exact clause and page number\n- Clear plain-English summaries so you never get surprise deductions`,
      verdict: 'INFO',
      confidence: null,
      citations: []
    }
  ])

  const [messages, setMessages] = propMessages && propSetMessages
    ? [propMessages, propSetMessages]
    : [localMessages, setLocalMessages]
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Sync selected policy if active policy changes and user has not chosen another
  useEffect(() => {
    if (!selectedPolicyId && activePolicyId) {
      setSelectedPolicyId(activePolicyId)
    }
  }, [activePolicyId])

  // Plain-language suggested queries — what real users actually ask
  const suggestedQueries = [
    { label: '🦷 Dental treatment', query: 'Does my policy cover dental treatment or tooth extraction?', icon: Pill },
    { label: '👁️ Cataract surgery', query: 'Is cataract surgery covered? Is there a waiting period?', icon: Eye },
    { label: '🏥 Room rent limit', query: 'What is my room rent limit per day and what happens if I go over it?', icon: Home },
    { label: '💊 Pre-existing disease', query: 'I have diabetes. Is it covered and when does the waiting period end?', icon: Heart },
    { label: '🔬 Robotic surgery', query: 'My doctor recommends robotic surgery. Is it covered or is it extra?', icon: Activity },
  ]

  const handleClearHistory = () => {
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        text: `Consultation reset. Ask your question regarding any treatment, waiting period, or room rent limit.`,
        verdict: 'INFO',
        confidence: null,
        citations: []
      }
    ])
  }

  const handleSend = async (queryText) => {
    const q = queryText || query
    if (!q.trim()) return

    const userMsg = { id: Date.now(), sender: 'user', text: q }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setQuery('')
    setLoading(true)

    try {
      // Scope strictly to single selected policy (or active policy default)
      const effectivePolicyId = selectedPolicyId || activePolicyId || (policies[0] ? policies[0].policy_id : null)
      const scopePolicies = effectivePolicyId ? [effectivePolicyId] : []

      // Prepare conversation history (last 5 turns)
      const historyPayload = messages
        .filter(m => m.id !== 'welcome')
        .slice(-6)
        .map(m => ({
          role: m.sender === 'user' ? 'user' : 'assistant',
          content: m.text
        }))

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          policy_ids: scopePolicies,
          enable_graph: true,
          history: historyPayload
        })
      })

      if (!res.ok) throw new Error('Failed to query assistant')

      const data = await res.json()

      let verdict = 'NEUTRAL'
      const ans = data.answer || ''
      if (ans.includes('COVERED') && !ans.includes('CONDITIONALLY') && !ans.includes('NOT COVERED')) verdict = 'COVERED'
      else if (ans.includes('EXCLUDED') || ans.includes('NOT COVERED')) verdict = 'EXCLUDED'
      else if (ans.includes('CONDITIONALLY') || ans.includes('Subject to') || ans.includes('Conditions Apply')) verdict = 'CONDITIONAL'
      else if (data.insufficient_evidence) verdict = 'INSUFFICIENT'

      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: data.answer,
        verdict,
        confidence: data.confidence_score,
        citations: data.citations || [],
        insufficient: data.insufficient_evidence
      }])
    } catch (err) {
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: `## System Error\n${err.message}. Please check backend connection.`,
        verdict: 'EXCLUDED',
        citations: []
      }])
    } finally {
      setLoading(false)
    }
  }

  const currentTargetId = selectedPolicyId || activePolicyId || (policies[0] ? policies[0].policy_id : '')
  const activePolicyObj = policies.find(p => p.policy_id === activePolicyId)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 320px', gap: '20px', height: '100%', minHeight: 0 }}>
      {/* Main Chat Panel */}
      <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', height: '100%', minHeight: 0 }}>
        {/* Chat Header */}
        <div style={{
          padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(9, 14, 26, 0.7)', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexWrap: 'wrap', gap: '10px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={18} color="#38bdf8" />
            <span style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>Policy Assistant</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Target Policy:</span>
              <select
                value={currentTargetId}
                onChange={(e) => setSelectedPolicyId(e.target.value)}
                style={{
                  background: 'rgba(15, 23, 42, 0.85)',
                  border: '1px solid rgba(56, 189, 248, 0.35)',
                  color: '#38bdf8',
                  borderRadius: '8px',
                  padding: '4px 10px',
                  fontSize: '11.5px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                {policies.map(p => (
                  <option key={p.policy_id} value={p.policy_id}>
                    {p.policy_id === activePolicyId ? '⭐ ' : '📄 '}{p.plan_name} ({p.insurer}){p.policy_id === activePolicyId ? ' (Active)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {messages.length > 2 && (
              <button
                onClick={handleClearHistory}
                className="btn-secondary"
                style={{ padding: '4px 9px', fontSize: '11px' }}
                title="Start a new consultation thread"
              >
                <RotateCcw size={12} />
                <span>New Query</span>
              </button>
            )}
          </div>
        </div>

        {/* Messages Thread */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {messages.map((m) => (
            <div key={m.id}>
              {m.sender === 'user' ? (
                <div style={{
                  alignSelf: 'flex-end', display: 'flex', justifyContent: 'flex-end'
                }}>
                  <div style={{
                    maxWidth: '78%',
                    background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                    border: '1px solid rgba(255,255,255,0.15)',
                    borderRadius: '18px 18px 4px 18px',
                    padding: '13px 18px',
                    boxShadow: '0 4px 16px rgba(2, 132, 199, 0.3)'
                  }}>
                    <p style={{ margin: 0, color: '#ffffff', fontWeight: 500, fontSize: '14px', lineHeight: '1.5' }}>{m.text}</p>
                  </div>
                </div>
              ) : (
                <AnswerCard message={m} onOpenPdf={onOpenPdf} />
              )}
            </div>
          ))}

          {loading && (
            <div style={{
              alignSelf: 'flex-start',
              background: 'rgba(15, 23, 42, 0.85)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderRadius: '16px',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              color: 'var(--text-secondary)',
              fontSize: '13px'
            }}>
              <Sparkles size={17} color="#38bdf8" />
              <div>
                <div style={{ color: '#fff', fontWeight: 600, marginBottom: '3px' }}>Checking your policy...</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Searching clauses · Ranking evidence · Generating grounded answer</div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input Area */}
        <div style={{
          padding: '14px 20px',
          borderTop: '1px solid var(--border-subtle)',
          background: 'rgba(9, 14, 26, 0.95)',
          backdropFilter: 'blur(12px)'
        }}>
          {/* Quick suggestion chips */}
          <div style={{ display: 'flex', gap: '7px', overflowX: 'auto', marginBottom: '12px', paddingBottom: '2px' }}>
            {suggestedQueries.map((sq, i) => (
              <button
                key={i}
                className="query-chip"
                onClick={() => handleSend(sq.query)}
                disabled={loading}
                style={{ flexShrink: 0 }}
              >
                <span>{sq.label}</span>
              </button>
            ))}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); handleSend() }} style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. My father needs knee replacement surgery next month. Is it covered?"
              disabled={loading}
              className="form-input"
              style={{ fontSize: '14px', padding: '12px 18px' }}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="btn-primary"
              style={{ padding: '0 22px', flexShrink: 0 }}
            >
              <Send size={16} />
              <span>Ask</span>
            </button>
          </form>
        </div>
      </div>

      {/* Sidebar Controls */}
      {/* Sidebar Controls */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', height: '100%', minHeight: 0 }}>
        {/* Active Policy Summary Card Action */}
        {activePolicyId && (
          <div className="glass-panel" style={{
            padding: '16px',
            background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.15) 0%, rgba(15, 23, 42, 0.8) 100%)',
            border: '1px solid rgba(56, 189, 248, 0.35)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                <Shield size={16} color="#38bdf8" />
                <span style={{ fontSize: '12px', fontWeight: 800, color: '#fff' }}>My Active Policy</span>
              </div>
              <span className="badge badge-covered" style={{ fontSize: '10px' }}>DEFAULT</span>
            </div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#f8fafc', marginBottom: '2px' }}>
              {activePolicyObj?.plan_name || activePolicyId}
            </div>
            <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginBottom: '12px' }}>
              {activePolicyObj?.insurer} · {activePolicyObj?.total_pages || 1} pages
            </div>

            <button
              onClick={() => onOpenSummary(activePolicyId)}
              className="btn-primary"
              style={{ width: '100%', fontSize: '12px', padding: '8px 12px', justifyContent: 'center' }}
            >
              <Sparkles size={13} />
              <span>View Policy 1-Page Summary Card</span>
            </button>
          </div>
        )}

        {/* Policy Scope Selection */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <h3 style={{ fontSize: '13.5px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Layers size={15} color="#38bdf8" /> Query Scope
          </h3>
          <p style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginBottom: '12px', lineHeight: '1.4' }}>
            Consulting strictly one policy at a time. Click to switch.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
            {policies.map((p) => {
              const isSelected = p.policy_id === currentTargetId
              const isActive = p.policy_id === activePolicyId
              return (
                <div
                  key={p.policy_id}
                  onClick={() => setSelectedPolicyId(p.policy_id)}
                  style={{
                    padding: '9px 12px', borderRadius: '10px',
                    border: isSelected ? '1px solid #0284c7' : isActive ? '1px solid rgba(56,189,248,0.3)' : '1px solid var(--border-subtle)',
                    background: isSelected ? 'rgba(2, 132, 199, 0.18)' : isActive ? 'rgba(56,189,248,0.06)' : 'rgba(15, 23, 42, 0.5)',
                    cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {p.plan_name}
                      {isActive && <span style={{ fontSize: '10px', color: '#38bdf8', fontWeight: 700 }}>ACTIVE</span>}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '1px' }}>
                      {p.insurer} · {p.total_pages} pages
                    </div>
                  </div>
                  <div style={{
                    width: '18px', height: '18px', borderRadius: '50%',
                    border: isSelected ? '2px solid #38bdf8' : '1px solid rgba(255,255,255,0.22)',
                    background: isSelected ? '#0284c7' : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.14s ease', flexShrink: 0
                  }}>
                    {isSelected && <Check size={11} color="#fff" strokeWidth={3} />}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
