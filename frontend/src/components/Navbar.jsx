import React, { useState, useEffect } from 'react'
import { apiUrl } from '../apiConfig'
import {
  Sparkles, Scale, Calculator, FolderOpen, Info,
  CheckCircle2, X, Zap, Cpu, Key, HelpCircle
} from 'lucide-react'

function PulseLogo({ size = 32 }) {
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      filter: 'drop-shadow(0 0 10px rgba(59, 130, 246, 0.6))',
      flexShrink: 0
    }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M3 16H8.5L12 5L17.5 27L22 10.5L25 16H29"
          stroke="url(#pulse-logo-gradient)"
          strokeWidth="2.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <defs>
          <linearGradient id="pulse-logo-gradient" x1="3" y1="16" x2="29" y2="16" gradientUnits="userSpaceOnUse">
            <stop stopColor="#3b82f6" />
            <stop offset="0.5" stopColor="#60a5fa" />
            <stop offset="1" stopColor="#38bdf8" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  )
}

export default function Navbar({ activeTab, setActiveTab, policyCount, activePolicyName }) {
  const [engineInfo, setEngineInfo] = useState(null)
  const [showEngineModal, setShowEngineModal] = useState(false)

  useEffect(() => {
    fetch(apiUrl('/api/health'))
      .then(res => res.json())
      .then(data => setEngineInfo(data))
      .catch(() => {})
  }, [])

  const tabs = [
    { id: 'assistant', label: 'Ask PolicyPulse', icon: Sparkles },
    { id: 'compare', label: 'Compare & Diff', icon: Scale },
    { id: 'claims', label: 'Pre-Claim Check', icon: Calculator },
    { id: 'policies', label: `My Policies (${policyCount})`, icon: FolderOpen },
  ]

  const isGenerative = engineInfo?.has_gemini || engineInfo?.has_openai

  return (
    <header style={{
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(7, 11, 20, 0.94)',
      backdropFilter: 'blur(16px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.45)'
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <PulseLogo size={36} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '19px', fontWeight: '800', letterSpacing: '-0.02em', color: '#ffffff' }}>
                PolicyPulse <span style={{ color: '#38bdf8' }}>AI</span>
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
              <span className="pulse-indicator" />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>
                {activePolicyName
                  ? <>Active: <strong style={{ color: '#38bdf8' }}>{activePolicyName}</strong></>
                  : 'Hybrid Search · Graph Grounded · Zero Hallucination'}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <nav style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            background: 'rgba(15, 23, 42, 0.65)',
            padding: '4px',
            borderRadius: '12px',
            border: '1px solid var(--border-subtle)',
            overflowX: 'auto',
            maxWidth: '100%'
          }}>
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '7px',
                    padding: '9px 16px',
                    borderRadius: '9px',
                    border: isActive ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid transparent',
                    background: isActive
                      ? 'linear-gradient(135deg, rgba(2, 132, 199, 0.3) 0%, rgba(3, 105, 161, 0.2) 100%)'
                      : 'transparent',
                    color: isActive ? '#38bdf8' : 'var(--text-muted)',
                    fontSize: '13px',
                    fontWeight: isActive ? 700 : 500,
                    cursor: 'pointer',
                    transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                    whiteSpace: 'nowrap',
                    boxShadow: isActive ? '0 2px 12px rgba(2, 132, 199, 0.3)' : 'none'
                  }}
                >
                  <Icon size={15} />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Enterprise Customer Protection Assurance Modal */}
      {showEngineModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(5, 8, 16, 0.85)',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 120,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            maxWidth: '560px',
            width: '100%',
            padding: '24px',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            boxShadow: '0 25px 60px rgba(0,0,0,0.85)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Shield size={20} color="#38bdf8" />
                <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#fff', margin: 0 }}>
                  How PolicyPulse Protects You
                </h3>
              </div>
              <button
                onClick={() => setShowEngineModal(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '13px', color: '#cbd5e1' }}>
              <div style={{
                background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.12) 0%, rgba(16, 185, 129, 0.1) 100%)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderRadius: '10px',
                padding: '14px'
              }}>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Enterprise Zero-Hallucination Guarantee
                </div>
                <div style={{ fontSize: '13.5px', color: '#f1f5f9', lineHeight: '1.5' }}>
                  PolicyPulse is purpose-built for insurance decision support. Unlike generic chatbots, every recommendation is bound to contractual policy wording.
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                  <div style={{ width: '24px', height: '24px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px' }}>
                    <CheckCircle2 size={14} color="#10b981" />
                  </div>
                  <div>
                    <strong style={{ color: '#fff', fontSize: '13px' }}>Direct Contract Citations</strong>
                    <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#94a3b8', lineHeight: '1.45' }}>
                      Every statement links to the exact PDF page number and section so you can audit the source clause yourself.
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                  <div style={{ width: '24px', height: '24px', borderRadius: '6px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px' }}>
                    <CheckCircle2 size={14} color="#38bdf8" />
                  </div>
                  <div>
                    <strong style={{ color: '#fff', fontSize: '13px' }}>Safe Abstention Principle</strong>
                    <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#94a3b8', lineHeight: '1.45' }}>
                      If your policy does not explicitly mention a treatment or exclusion, the engine clearly declares insufficient evidence rather than guessing.
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                  <div style={{ width: '24px', height: '24px', borderRadius: '6px', background: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px' }}>
                    <CheckCircle2 size={14} color="#c084fc" />
                  </div>
                  <div>
                    <strong style={{ color: '#fff', fontSize: '13px' }}>Plain-English Translation</strong>
                    <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#94a3b8', lineHeight: '1.45' }}>
                      Complex legal exclusions are automatically explained in terms of your out-of-pocket wallet impact and concrete next steps.
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowEngineModal(false)}
                className="btn-primary"
                style={{ width: '100%', justifyContent: 'center', marginTop: '6px' }}
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
