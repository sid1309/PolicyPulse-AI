import React, { useState } from 'react'
import { apiUrl } from '../apiConfig'
import {
  Calculator, CheckCircle2, AlertTriangle, XCircle, FileText,
  IndianRupee, Sparkles, ChevronRight, ChevronLeft, Check,
  Building2, Calendar, Stethoscope, Info, Wallet, RotateCcw
} from 'lucide-react'
import ModernDatePicker, { toDDMMYYYY } from './ModernDatePicker'

const STEPS = [
  { id: 1, label: 'Treatment & Dates', icon: Stethoscope },
  { id: 2, label: 'Hospital & Room', icon: Building2 },
  { id: 3, label: 'Your Result', icon: Calculator },
]

export default function ClaimsCalculator({ policies, activePolicyId, onOpenPdf }) {
  const defaultPolicy = activePolicyId || policies[0]?.policy_id || ''
  const [step, setStep] = useState(1)
  const [policyId, setPolicyId] = useState(defaultPolicy)
  const [treatment, setTreatment] = useState('')
  const [inceptionDate, setInceptionDate] = useState('')
  const [incidentDate, setIncidentDate] = useState('')
  const [isPed, setIsPed] = useState(false)
  const [hospitalType, setHospitalType] = useState('network_cashless')
  const [roomCategory, setRoomCategory] = useState('')
  const [actualRoomRent, setActualRoomRent] = useState('')
  const [roomBill, setRoomBill] = useState('')
  const [associatedBill, setAssociatedBill] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [checkedDocs, setCheckedDocs] = useState({})

  const quickPresets = [
    { label: '🔬 Hernia (Room Capping)', treatment: 'Hernia Repair (Laparoscopic)', rent: 10000, roomBill: 30000, medBill: 120000, ped: false },
    { label: '👁️ Cataract', treatment: 'Cataract Surgery with Monofocal IOL', rent: 4000, roomBill: 8000, medBill: 45000, ped: false },
    { label: '❤️ Cardiac Bypass (PED)', treatment: 'Coronary Artery Bypass Graft (CABG)', rent: 12000, roomBill: 60000, medBill: 350000, ped: true },
  ]

  const applyPreset = (p) => {
    setTreatment(p.treatment)
    setActualRoomRent(p.rent)
    setRoomBill(p.roomBill)
    setAssociatedBill(p.medBill)
    setIsPed(p.ped)
    setStep(1)
    setResult(null)
    setError('')
  }

  const toggleDoc = (idx) => setCheckedDocs((prev) => ({ ...prev, [idx]: !prev[idx] }))

  const normalizeToBackend = (dStr) => {
    if (!dStr) return '2024-01-01'
    const parts = dStr.split('-')
    if (parts.length === 3 && parts[0].length === 2 && parts[2].length === 4) {
      return `${parts[2]}-${parts[1]}-${parts[0]}`
    }
    return dStr
  }

  const parseDateObj = (dStr) => {
    if (!dStr) return null
    const parts = dStr.split('-')
    if (parts.length === 3) {
      if (parts[0].length === 2 && parts[2].length === 4) {
        return new Date(parseInt(parts[2], 10), parseInt(parts[1], 10) - 1, parseInt(parts[0], 10))
      }
      if (parts[0].length === 4 && parts[2].length === 2) {
        return new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10))
      }
    }
    return null
  }

  const handleNextToStep2 = () => {
    if (!treatment.trim()) {
      setError('Please enter a treatment or procedure name.')
      return
    }
    const dInception = parseDateObj(inceptionDate)
    const dIncident = parseDateObj(incidentDate)
    if (dInception && dIncident && dIncident < dInception) {
      setError('Planned Admission Date cannot be earlier than Policy Start Date.')
      return
    }
    setError('')
    setStep(2)
  }

  const handleCalculate = async () => {
    if (!policyId) { setError('Please select a policy.'); return }
    const dInception = parseDateObj(inceptionDate)
    const dIncident = parseDateObj(incidentDate)
    if (dInception && dIncident && dIncident < dInception) {
      setError('Planned Admission Date cannot be earlier than Policy Start Date.')
      return
    }
    setError('')
    setLoading(true)
    setCheckedDocs({})
    try {
      const res = await fetch(apiUrl('/api/claims/assess'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          policy_id: policyId,
          treatment_name: treatment.trim() || 'General Hospitalization',
          hospital_type: hospitalType,
          room_category_chosen: roomCategory.trim(),
          actual_room_rent_per_day: parseFloat(actualRoomRent) || 0,
          total_room_rent_bill: parseFloat(roomBill) || 0,
          associated_medical_bills: parseFloat(associatedBill) || 0,
          policy_inception_date: normalizeToBackend(inceptionDate),
          incident_date: normalizeToBackend(incidentDate),
          is_pre_existing: isPed
        })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Calculation failed')
      }
      setResult(await res.json())
      setStep(3)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setTreatment('')
    setInceptionDate('')
    setIncidentDate('')
    setIsPed(false)
    setHospitalType('network_cashless')
    setRoomCategory('')
    setActualRoomRent('')
    setRoomBill('')
    setAssociatedBill('')
    setCheckedDocs({})
    setResult(null)
    setStep(1)
    setError('')
  }

  // Presets for Date Pickers (DD-MM-YYYY)
  const inceptionPresets = [
    { label: 'Today', getValue: () => toDDMMYYYY(new Date()) },
    { label: '1 Yr Ago', getValue: () => toDDMMYYYY(new Date(new Date().setFullYear(new Date().getFullYear() - 1))) },
    { label: '2 Yrs Ago', getValue: () => toDDMMYYYY(new Date(new Date().setFullYear(new Date().getFullYear() - 2))) },
    { label: '3 Yrs Ago', getValue: () => toDDMMYYYY(new Date(new Date().setFullYear(new Date().getFullYear() - 3))) },
  ]

  const incidentPresets = [
    { label: 'Today', getValue: () => toDDMMYYYY(new Date()) },
    { label: '+7 Days', getValue: () => toDDMMYYYY(new Date(Date.now() + 7 * 86400000)) },
    { label: '+1 Month', getValue: () => toDDMMYYYY(new Date(Date.now() + 30 * 86400000)) },
    { label: '+3 Months', getValue: () => toDDMMYYYY(new Date(Date.now() + 90 * 86400000)) },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '24px', alignItems: 'start' }}>
      {/* Wizard Column */}
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '10px', color: '#ffffff' }}>
            <Calculator size={20} color="#38bdf8" /> Pre-Claim Eligibility Check
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {(treatment || actualRoomRent || roomBill || associatedBill || result) && (
              <button
                type="button"
                onClick={reset}
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  borderRadius: '6px',
                  padding: '4px 10px',
                  fontSize: '11.5px',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px'
                }}
                title="Clear all fields"
              >
                <RotateCcw size={12} /> Clear Form
              </button>
            )}
            <span className="badge badge-blue">Claims Math</span>
          </div>
        </div>
        <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginBottom: '28px', lineHeight: '1.45' }}>
          Check if your planned hospitalization is covered, estimate your out-of-pocket cost, and get a document checklist — before you go to the hospital.
        </p>

        {/* Step Progress Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0', marginBottom: '28px' }}>
          {STEPS.map((s, i) => {
            const done = step > s.id
            const active = step === s.id
            const Icon = s.icon
            return (
              <React.Fragment key={s.id}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                  <div style={{
                    width: '38px', height: '38px', borderRadius: '50%',
                    border: done ? '2px solid #10b981' : active ? '2px solid #38bdf8' : '2px solid rgba(255,255,255,0.15)',
                    background: done ? 'rgba(16,185,129,0.2)' : active ? 'rgba(56,189,248,0.15)' : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.25s ease'
                  }}>
                    {done
                      ? <Check size={17} color="#10b981" />
                      : <Icon size={17} color={active ? '#38bdf8' : 'var(--text-dim)'} />
                    }
                  </div>
                  <span style={{
                    fontSize: '11px', fontWeight: active ? 700 : 500,
                    color: done ? '#10b981' : active ? '#38bdf8' : 'var(--text-dim)',
                    whiteSpace: 'nowrap'
                  }}>
                    {s.label}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div style={{
                    flex: 1, height: '2px', margin: '0 8px', marginBottom: '22px',
                    background: done ? 'rgba(16,185,129,0.5)' : 'rgba(255,255,255,0.1)',
                    borderRadius: '1px', transition: 'all 0.25s ease'
                  }} />
                )}
              </React.Fragment>
            )
          })}
        </div>

        {/* ─── STEP 1: Treatment & Dates ─── */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '4px' }}>
                What treatment or procedure is planned?
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                Enter the treatment name and your policy & hospitalization dates to check waiting period eligibility.
              </p>
            </div>

            {/* Quick Presets */}
            <div>
              <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Quick Scenarios:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px' }}>
                {quickPresets.map((p, idx) => (
                  <button key={idx} type="button" onClick={() => applyPreset(p)} style={{
                    background: 'rgba(2,132,199,0.1)', border: '1px solid rgba(56,189,248,0.25)',
                    borderRadius: '8px', padding: '6px 12px', color: '#38bdf8', fontSize: '12px',
                    cursor: 'pointer', fontWeight: 500, transition: 'all 0.15s ease'
                  }}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Policy Selector */}
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                Which policy to check against?
              </label>
              <select value={policyId} onChange={(e) => setPolicyId(e.target.value)} className="form-select">
                {policies.map((p) => (
                  <option key={p.policy_id} value={p.policy_id}>
                    {p.insurer} — {p.plan_name} (v{p.version}){p.policy_id === activePolicyId ? ' ★ Active' : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Treatment Input (Stable Focus) */}
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                Treatment / Procedure Name
              </label>
              <input
                type="text"
                value={treatment}
                onChange={(e) => setTreatment(e.target.value)}
                placeholder="e.g. Knee Replacement, Cataract Surgery, Hernia Repair"
                className="form-input"
                autoComplete="off"
              />
            </div>

            {/* Modern Date Pickers with Sleek Dark Calendar */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                  Policy Start Date
                </label>
                <ModernDatePicker
                  value={inceptionDate}
                  onChange={setInceptionDate}
                  placeholder="DD-MM-YYYY"
                  presets={inceptionPresets}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                  Planned Admission Date
                </label>
                <ModernDatePicker
                  value={incidentDate}
                  onChange={setIncidentDate}
                  placeholder="DD-MM-YYYY"
                  presets={incidentPresets}
                />
              </div>
            </div>

            {/* PED Toggle */}
            <label style={{
              display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 14px',
              borderRadius: '11px', background: isPed ? 'rgba(245,158,11,0.1)' : 'rgba(15,23,42,0.6)',
              border: isPed ? '1px solid rgba(245,158,11,0.4)' : '1px solid var(--border-subtle)',
              fontSize: '13px', color: isPed ? '#fbbf24' : 'var(--text-secondary)', cursor: 'pointer',
              transition: 'all 0.18s ease'
            }}>
              <input type="checkbox" checked={isPed} onChange={(e) => setIsPed(e.target.checked)}
                style={{ accentColor: '#f59e0b', width: '16px', height: '16px' }} />
              <div>
                <div style={{ fontWeight: 600 }}>This is a Pre-Existing Disease (PED) case</div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  e.g. diabetes, hypertension, cardiac conditions diagnosed before policy start
                </div>
              </div>
            </label>

            {error && (
              <div style={{
                padding: '10px 13px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px',
                background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.35)', color: '#fb7185', fontSize: '13px'
              }}>
                <XCircle size={15} /> {error}
              </div>
            )}

            <button onClick={handleNextToStep2} className="btn-primary" style={{ padding: '12px', marginTop: '4px' }}>
              Next: Hospital Details <ChevronRight size={16} />
            </button>
          </div>
        )}

        {/* ─── STEP 2: Hospital & Room ─── */}
        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '4px' }}>
                Which hospital and room type?
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                Room rent is one of the most important factors. Choosing a room above your policy limit can reduce your surgery and doctor fee reimbursement proportionally.
              </p>
            </div>

            {/* Room Rent Warning Info Box */}
            <div style={{
              padding: '12px 14px', borderRadius: '10px',
              background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)',
              display: 'flex', alignItems: 'flex-start', gap: '8px'
            }}>
              <Info size={16} color="#f59e0b" style={{ flexShrink: 0, marginTop: '1px' }} />
              <p style={{ fontSize: '12px', color: '#fbbf24', lineHeight: '1.5', margin: 0 }}>
                <strong>Room Rent Rule:</strong> If you choose a room more expensive than your policy allows, the insurer will also cut your doctor fees, surgeon fees, and OT charges by the same proportion — not just the room rent.
              </p>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                Hospital Type
              </label>
              <select value={hospitalType} onChange={(e) => setHospitalType(e.target.value)} className="form-select">
                <option value="network_cashless">Network Hospital (Cashless Pre-Authorization)</option>
                <option value="non_network_reimbursement">Non-Network Hospital (Reimbursement Claim)</option>
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                  Room Rent Per Day (Rs.)
                </label>
                <input
                  type="number"
                  value={actualRoomRent}
                  onChange={(e) => setActualRoomRent(e.target.value)}
                  placeholder="e.g. 5000"
                  autoComplete="off"
                  className="form-input"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                  Room Category
                </label>
                <input
                  type="text"
                  value={roomCategory}
                  onChange={(e) => setRoomCategory(e.target.value)}
                  placeholder="e.g. Deluxe Room"
                  autoComplete="off"
                  className="form-input"
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                  Total Room Rent Bill (Rs.)
                </label>
                <input
                  type="number"
                  value={roomBill}
                  onChange={(e) => setRoomBill(e.target.value)}
                  placeholder="e.g. 25000"
                  autoComplete="off"
                  className="form-input"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase' }}>
                  Surgeon & OT Charges (Rs.)
                </label>
                <input
                  type="number"
                  value={associatedBill}
                  onChange={(e) => setAssociatedBill(e.target.value)}
                  placeholder="e.g. 80000"
                  autoComplete="off"
                  className="form-input"
                />
              </div>
            </div>

            {error && (
              <div style={{
                padding: '10px 13px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px',
                background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.35)', color: '#fb7185', fontSize: '13px'
              }}>
                <XCircle size={15} /> {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', marginTop: '4px' }}>
              <button onClick={() => setStep(1)} className="btn-secondary" style={{ padding: '12px 20px' }}>
                <ChevronLeft size={16} /> Back
              </button>
              <button onClick={handleCalculate} disabled={loading} className="btn-primary" style={{ flex: 1, padding: '12px' }}>
                <Sparkles size={16} />
                <span>{loading ? 'Checking policy clauses...' : 'Check My Claim Eligibility'}</span>
              </button>
            </div>
          </div>
        )}

        {/* ─── STEP 3: Results ─── */}
        {step === 3 && result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {/* Verdict Card */}
            {(() => {
              const isIneligible = result.admissibility_status?.includes('Ineligible')
              const penalty = result.financial_breakdown?.proportional_deduction_penalty || 0
              const factor = result.room_rent_math?.proportional_factor
              const allowed = result.room_rent_math?.allowed_rate_per_day
              const actual = result.room_rent_math?.actual_rate_per_day
              const hasPenalty = penalty > 0 && factor && factor !== 1.0

              return (
                <>
                  <div style={{
                    padding: '20px 22px',
                    borderRadius: '14px',
                    borderLeft: `5px solid ${isIneligible ? '#f43f5e' : '#10b981'}`,
                    background: isIneligible
                      ? 'linear-gradient(135deg, rgba(244,63,94,0.1) 0%, rgba(15,23,42,0.9) 100%)'
                      : 'linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(15,23,42,0.9) 100%)',
                    border: `1px solid ${isIneligible ? 'rgba(244,63,94,0.35)' : 'rgba(16,185,129,0.35)'}`,
                    boxShadow: `0 4px 20px ${isIneligible ? 'rgba(244,63,94,0.12)' : 'rgba(16,185,129,0.12)'}`
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                      <span className={`badge ${isIneligible ? 'badge-excluded' : 'badge-covered'}`} style={{ fontSize: '12px', padding: '5px 12px' }}>
                        {isIneligible ? <XCircle size={14} /> : <CheckCircle2 size={14} />}
                        {result.admissibility_status}
                      </span>
                    </div>
                    <h3 style={{ fontSize: '17px', fontWeight: '800', color: '#ffffff', marginBottom: '6px' }}>
                      {result.treatment_name}
                    </h3>
                    <p style={{ fontSize: '13.5px', color: '#cbd5e1', lineHeight: '1.55', margin: 0 }}>
                      {result.status_reason}
                    </p>
                  </div>

                  {/* Financial Grid */}
                  <div className="glass-panel" style={{ padding: '20px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '7px', color: '#fff' }}>
                      <IndianRupee size={16} color="#34d399" /> Settlement Breakdown
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(145px, 1fr))', gap: '12px', marginBottom: hasPenalty ? '16px' : '0' }}>
                      {[
                        { label: 'Total Bill', value: `Rs. ${result.financial_breakdown.total_hospital_bill?.toLocaleString()}`, color: '#fff', bg: 'rgba(11,17,32,0.7)', border: 'var(--border-subtle)' },
                        penalty > 0 && { label: 'Room Penalty', value: `-Rs. ${penalty.toLocaleString()}`, color: '#fb7185', bg: 'rgba(244,63,94,0.07)', border: 'rgba(244,63,94,0.22)' },
                        { label: 'Estimated Payout', value: `Rs. ${result.financial_breakdown.estimated_settlement?.toLocaleString()}`, color: '#34d399', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)' },
                        { label: 'Your Out-of-Pocket', value: `Rs. ${result.financial_breakdown.estimated_out_of_pocket?.toLocaleString()}`, color: '#fbbf24', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.28)' },
                      ].filter(Boolean).map((item, i) => (
                        <div key={i} style={{ background: item.bg, padding: '14px', borderRadius: '11px', border: `1px solid ${item.border}` }}>
                          <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700 }}>{item.label}</div>
                          <div style={{ fontSize: '19px', fontWeight: '800', color: item.color, marginTop: '3px', fontFamily: 'var(--font-mono)' }}>{item.value}</div>
                        </div>
                      ))}
                    </div>

                    {/* Plain-English Penalty Explanation */}
                    {hasPenalty && (
                      <div style={{
                        padding: '13px 15px', borderRadius: '10px',
                        background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.28)',
                        display: 'flex', alignItems: 'flex-start', gap: '8px'
                      }}>
                        <AlertTriangle size={16} color="#f59e0b" style={{ flexShrink: 0, marginTop: '2px' }} />
                        <div>
                          <div style={{ fontSize: '12.5px', fontWeight: '700', color: '#fbbf24', marginBottom: '3px' }}>
                            Why was Rs. {penalty.toLocaleString()} deducted?
                          </div>
                          <p style={{ fontSize: '12.5px', color: '#cbd5e1', lineHeight: '1.55', margin: 0 }}>
                            Your policy allows up to <strong>Rs. {allowed}/day</strong> for room rent, but you chose a room at <strong>Rs. {actual}/day</strong>.
                            Because the room was {Math.round((1 - allowed / actual) * 100)}% over the limit, your insurer also reduced your surgeon fees and OT charges
                            by the same proportion — this is the <em>Proportionate Deduction Clause</em>. This cut resulted in a Rs. {penalty.toLocaleString()} deduction from your claim.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Document Checklist */}
                  {result.document_checklist?.length > 0 && (
                    <div className="glass-panel" style={{ padding: '20px' }}>
                      <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '7px', color: '#fff' }}>
                        <FileText size={16} color="#38bdf8" /> Documents to Submit ({result.document_checklist.length})
                      </h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                        Check off items as you collect them.
                      </p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
                        {result.document_checklist.map((doc, i) => {
                          const isChecked = !!checkedDocs[i]
                          return (
                            <div key={i} onClick={() => toggleDoc(i)} style={{
                              display: 'flex', alignItems: 'center', gap: '11px', padding: '9px 13px',
                              borderRadius: '9px',
                              background: isChecked ? 'rgba(16,185,129,0.1)' : 'rgba(15,23,42,0.5)',
                              border: isChecked ? '1px solid rgba(16,185,129,0.35)' : '1px solid var(--border-subtle)',
                              cursor: 'pointer', transition: 'all 0.15s ease'
                            }}>
                              <div style={{
                                width: '19px', height: '19px', borderRadius: '5px', flexShrink: 0,
                                border: isChecked ? '1px solid #10b981' : '1px solid rgba(255,255,255,0.18)',
                                background: isChecked ? '#10b981' : 'transparent',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                transition: 'all 0.14s ease'
                              }}>
                                {isChecked && <Check size={12} color="#fff" />}
                              </div>
                              <span style={{
                                fontSize: '13px',
                                color: isChecked ? '#f8fafc' : 'var(--text-secondary)',
                                textDecoration: isChecked ? 'line-through' : 'none'
                              }}>
                                {doc}
                              </span>
                            </div>
                          )
                        })}
                      </div>

                      {/* Citations */}
                      {result.citations?.length > 0 && (
                        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', marginTop: '14px' }}>
                          <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '7px' }}>
                            Source Clauses:
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {result.citations.map((c, idx) => (
                              <button key={idx} className="citation-pill" onClick={() => onOpenPdf(c.policy_id, c.page_number)}>
                                📄 Page {c.page_number} · {c.clause_title?.slice(0, 28)}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  <button onClick={reset} className="btn-secondary" style={{ padding: '11px' }}>
                    <ChevronLeft size={15} /> Check Another Scenario
                  </button>
                </>
              )
            })()}
          </div>
        )}
      </div>

      {/* Info Sidebar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '18px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#fff', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '7px' }}>
            <Wallet size={15} color="#34d399" /> How this check works
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { label: 'Waiting period check', desc: 'Verifies your policy is old enough to cover this treatment.' },
              { label: 'Room rent deduction', desc: 'Calculates proportional penalty if you choose a room above your limit.' },
              { label: 'Out-of-pocket estimate', desc: 'Shows exactly how much you will need to pay yourself.' },
              { label: 'Document checklist', desc: 'Lists every document needed to file your reimbursement claim.' },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                <div style={{
                  width: '20px', height: '20px', borderRadius: '50%',
                  background: 'rgba(56,189,248,0.15)', border: '1px solid rgba(56,189,248,0.25)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '1px'
                }}>
                  <span style={{ fontSize: '10px', fontWeight: '800', color: '#38bdf8' }}>{i + 1}</span>
                </div>
                <div>
                  <div style={{ fontSize: '12.5px', fontWeight: '700', color: '#fff' }}>{item.label}</div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', lineHeight: '1.4', marginTop: '1px' }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel" style={{
          padding: '16px',
          background: 'linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(15,23,42,0.8) 100%)',
          border: '1px solid rgba(245,158,11,0.25)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <AlertTriangle size={14} color="#f59e0b" />
            <span style={{ fontSize: '11px', fontWeight: '800', color: '#f59e0b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Room Rent Tip
            </span>
          </div>
          <p style={{ fontSize: '12px', color: '#fde68a', lineHeight: '1.5', margin: 0 }}>
            Always choose a room at or below your policy's room rent limit. Going even Rs. 1 above can proportionally reduce your doctor and surgery fees — sometimes cutting thousands from your payout.
          </p>
        </div>
      </div>
    </div>
  )
}
