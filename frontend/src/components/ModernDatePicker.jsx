import React, { useState, useRef, useEffect } from 'react'
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react'

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

const DAYS_OF_WEEK = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

const padZero = (n) => String(n).padStart(2, '0')

// Convert Date object to DD-MM-YYYY string
export const toDDMMYYYY = (d) => {
  const date = new Date(d)
  const day = padZero(date.getDate())
  const month = padZero(date.getMonth() + 1)
  const year = date.getFullYear()
  return `${day}-${month}-${year}`
}

// Parse string (DD-MM-YYYY or YYYY-MM-DD) into Date object
export const parseDateStr = (str) => {
  if (!str) return new Date()
  const parts = str.split('-')
  if (parts.length === 3) {
    if (parts[0].length === 2 && parts[2].length === 4) {
      // DD-MM-YYYY
      const d = new Date(Number(parts[2]), Number(parts[1]) - 1, Number(parts[0]))
      if (!isNaN(d.getTime())) return d
    } else if (parts[0].length === 4) {
      // YYYY-MM-DD
      const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
      if (!isNaN(d.getTime())) return d
    }
  }
  return new Date()
}

// Format input digits to DD-MM-YYYY with strict validation and auto-hyphenation
const formatToDDMMYYYY = (inputVal) => {
  // Extract only digits, max 8 digits
  const digits = inputVal.replace(/\D/g, '').slice(0, 8)
  
  if (!digits) return ''
  
  let day = digits.slice(0, 2)
  if (day.length === 2) {
    const dNum = parseInt(day, 10)
    if (dNum > 31) day = '31'
    if (dNum === 0) day = '01'
  }
  
  let month = ''
  if (digits.length > 2) {
    month = digits.slice(2, 4)
    if (month.length === 2) {
      const mNum = parseInt(month, 10)
      if (mNum > 12) month = '12'
      if (mNum === 0) month = '01'
    }
  }
  
  let year = ''
  if (digits.length > 4) {
    year = digits.slice(4, 8)
  }
  
  let res = day
  if (month) res += '-' + month
  if (year) res += '-' + year
  return res
}

export default function ModernDatePicker({
  value,
  onChange,
  placeholder = 'DD-MM-YYYY',
  presets = []
}) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)

  // Ensure initial or updated value is formatted as DD-MM-YYYY if passed as YYYY-MM-DD
  const normalizedValue = (() => {
    if (value && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
      const [y, m, d] = value.split('-')
      return `${d}-${m}-${y}`
    }
    return value || ''
  })()

  const parsedDate = parseDateStr(normalizedValue)
  const [viewYear, setViewYear] = useState(parsedDate.getFullYear())
  const [viewMonth, setViewMonth] = useState(parsedDate.getMonth())

  useEffect(() => {
    if (normalizedValue) {
      const d = parseDateStr(normalizedValue)
      setViewYear(d.getFullYear())
      setViewMonth(d.getMonth())
    }
  }, [normalizedValue])

  // Close calendar popup when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick)
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [isOpen])

  // Handle direct keyboard input with strict numeric-only filtering and auto-formatting
  const handleInputChange = (e) => {
    const raw = e.target.value
    // If user hit backspace on a hyphen, allow normal deletion
    if (raw.length < normalizedValue.length) {
      onChange(raw)
      return
    }
    const formatted = formatToDDMMYYYY(raw)
    onChange(formatted)
  }

  const handleKeyDown = (e) => {
    // Allowed control keys
    const allowedKeys = [
      'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter', 'Home', 'End'
    ]
    if (allowedKeys.includes(e.key)) return

    // Allow Ctrl/Cmd combinations (copy, paste, select all)
    if (e.ctrlKey || e.metaKey) return

    // Allow hyphen if length permits
    if (e.key === '-' && e.currentTarget.value.length < 10) return

    // STRICT: Only allow numbers 0-9
    if (!/^[0-9]$/.test(e.key)) {
      e.preventDefault()
      return
    }

    // Limit length to 10 characters (DD-MM-YYYY)
    if (e.currentTarget.value.length >= 10 && e.currentTarget.selectionStart === e.currentTarget.selectionEnd) {
      e.preventDefault()
    }
  }

  const handlePrevMonth = (e) => {
    e.stopPropagation()
    if (viewMonth === 0) {
      setViewMonth(11)
      setViewYear((y) => y - 1)
    } else {
      setViewMonth((m) => m - 1)
    }
  }

  const handleNextMonth = (e) => {
    e.stopPropagation()
    if (viewMonth === 11) {
      setViewMonth(0)
      setViewYear((y) => y + 1)
    } else {
      setViewMonth((m) => m + 1)
    }
  }

  const handleSelectDay = (day, isCurrentMonth = true, offset = 0) => {
    let targetMonth = viewMonth + offset
    let targetYear = viewYear
    if (targetMonth < 0) {
      targetMonth = 11
      targetYear -= 1
    } else if (targetMonth > 11) {
      targetMonth = 0
      targetYear += 1
    }
    const selected = `${padZero(day)}-${padZero(targetMonth + 1)}-${targetYear}`
    onChange(selected)
    setIsOpen(false)
  }

  // Days calculations
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()
  const firstDayIndex = new Date(viewYear, viewMonth, 1).getDay()
  const prevMonthDays = new Date(viewYear, viewMonth, 0).getDate()

  const calendarDays = []

  // Trailing days from previous month
  for (let i = firstDayIndex - 1; i >= 0; i--) {
    calendarDays.push({
      day: prevMonthDays - i,
      isCurrentMonth: false,
      offset: -1
    })
  }

  // Days of current month
  for (let i = 1; i <= daysInMonth; i++) {
    calendarDays.push({
      day: i,
      isCurrentMonth: true,
      offset: 0
    })
  }

  // Leading days of next month to fill 42 cells
  const remainingCells = 42 - calendarDays.length
  for (let i = 1; i <= remainingCells; i++) {
    calendarDays.push({
      day: i,
      isCurrentMonth: false,
      offset: 1
    })
  }

  // Preview badge: ONLY display if fully valid 10-char date (DD-MM-YYYY)
  const formattedPreview = (() => {
    if (!normalizedValue || normalizedValue.length !== 10) return null
    const parts = normalizedValue.split('-')
    if (parts.length === 3 && parts[0].length === 2 && parts[1].length === 2 && parts[2].length === 4) {
      const d = new Date(Number(parts[2]), Number(parts[1]) - 1, Number(parts[0]))
      if (!isNaN(d.getTime())) {
        return d.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
      }
    }
    return null
  })()

  // Generate Year options (2012 to 2032)
  const currentYear = new Date().getFullYear()
  const yearOptions = []
  for (let y = currentYear - 15; y <= currentYear + 8; y++) {
    yearOptions.push(y)
  }

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      {/* Input Field with Calendar Trigger */}
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <input
          type="text"
          value={normalizedValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          maxLength={10}
          className="form-input"
          style={{
            paddingLeft: '38px',
            paddingRight: formattedPreview ? '110px' : '38px',
            fontFamily: 'var(--font-mono)',
            fontSize: '13.5px',
            letterSpacing: '0.04em',
            cursor: 'text'
          }}
        />
        
        {/* Left Calendar Icon */}
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          style={{
            position: 'absolute',
            left: '10px',
            background: 'transparent',
            border: 'none',
            color: isOpen ? '#38bdf8' : 'var(--text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            padding: '2px',
            transition: 'color 0.15s ease'
          }}
          title="Open interactive calendar"
        >
          <Calendar size={16} />
        </button>

        {/* Right formatted preview pill (Only when complete valid date) */}
        {formattedPreview && (
          <div
            onClick={() => setIsOpen((prev) => !prev)}
            style={{
              position: 'absolute',
              right: '8px',
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderRadius: '7px',
              padding: '3px 8px',
              fontSize: '11px',
              fontWeight: 600,
              color: '#38bdf8',
              cursor: 'pointer',
              userSelect: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            {formattedPreview}
          </div>
        )}
      </div>

      {/* Floating Modern Calendar Popover */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            left: 0,
            zIndex: 9999,
            width: '320px',
            background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.98) 0%, rgba(10, 16, 30, 0.98) 100%)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '16px',
            boxShadow: '0 18px 40px -8px rgba(0, 0, 0, 0.8), 0 0 24px rgba(2, 132, 199, 0.25)',
            backdropFilter: 'blur(20px)',
            padding: '16px',
            animation: 'fadeIn 0.15s ease'
          }}
        >
          {/* Quick Presets row */}
          {presets.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
              {presets.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    const val = preset.getValue()
                    onChange(val)
                    const d = parseDateStr(val)
                    setViewYear(d.getFullYear())
                    setViewMonth(d.getMonth())
                  }}
                  style={{
                    background: 'rgba(2, 132, 199, 0.15)',
                    border: '1px solid rgba(56, 189, 248, 0.25)',
                    borderRadius: '7px',
                    padding: '4px 9px',
                    color: '#38bdf8',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.12s ease'
                  }}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          )}

          {/* Month & Year Navigation Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <button
              type="button"
              onClick={handlePrevMonth}
              style={{
                width: '30px',
                height: '30px',
                borderRadius: '8px',
                background: 'rgba(30, 41, 59, 0.7)',
                border: '1px solid var(--border-subtle)',
                color: '#f8fafc',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <ChevronLeft size={16} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {/* Month Dropdown */}
              <select
                value={viewMonth}
                onChange={(e) => setViewMonth(Number(e.target.value))}
                style={{
                  background: 'rgba(30, 41, 59, 0.8)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  color: '#ffffff',
                  fontSize: '12.5px',
                  fontWeight: 600,
                  padding: '4px 8px',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                {MONTH_NAMES.map((m, i) => (
                  <option key={m} value={i} style={{ background: '#0f172a', color: '#fff' }}>
                    {m}
                  </option>
                ))}
              </select>

              {/* Year Dropdown */}
              <select
                value={viewYear}
                onChange={(e) => setViewYear(Number(e.target.value))}
                style={{
                  background: 'rgba(30, 41, 59, 0.8)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  color: '#38bdf8',
                  fontSize: '12.5px',
                  fontWeight: 700,
                  padding: '4px 8px',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                {yearOptions.map((y) => (
                  <option key={y} value={y} style={{ background: '#0f172a', color: '#fff' }}>
                    {y}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={handleNextMonth}
              style={{
                width: '30px',
                height: '30px',
                borderRadius: '8px',
                background: 'rgba(30, 41, 59, 0.7)',
                border: '1px solid var(--border-subtle)',
                color: '#f8fafc',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <ChevronRight size={16} />
            </button>
          </div>

          {/* Days of Week Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px', textAlign: 'center', marginBottom: '6px' }}>
            {DAYS_OF_WEEK.map((d, i) => (
              <div
                key={d}
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  color: i === 0 || i === 6 ? '#fb7185' : 'var(--text-dim)',
                  padding: '4px 0'
                }}
              >
                {d}
              </div>
            ))}
          </div>

          {/* Calendar Days 7x6 Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px' }}>
            {calendarDays.map((cell, idx) => {
              let m = viewMonth + cell.offset
              let y = viewYear
              if (m < 0) { m = 11; y -= 1 }
              else if (m > 11) { m = 0; y += 1 }
              const cellDateStr = `${padZero(cell.day)}-${padZero(m + 1)}-${y}`

              const isSelected = normalizedValue === cellDateStr
              const isToday = toDDMMYYYY(new Date()) === cellDateStr

              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectDay(cell.day, cell.isCurrentMonth, cell.offset)}
                  style={{
                    height: '32px',
                    borderRadius: '8px',
                    border: isSelected
                      ? '1px solid #38bdf8'
                      : isToday
                      ? '1px solid rgba(56, 189, 248, 0.4)'
                      : '1px solid transparent',
                    background: isSelected
                      ? 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)'
                      : isToday
                      ? 'rgba(56, 189, 248, 0.1)'
                      : 'transparent',
                    color: isSelected
                      ? '#ffffff'
                      : cell.isCurrentMonth
                      ? '#f1f5f9'
                      : 'rgba(148, 163, 184, 0.35)',
                    fontSize: '12px',
                    fontWeight: isSelected ? 800 : cell.isCurrentMonth ? 500 : 400,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.12s ease',
                    boxShadow: isSelected ? '0 2px 10px rgba(2, 132, 199, 0.4)' : 'none'
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = isToday ? 'rgba(56, 189, 248, 0.1)' : 'transparent'
                    }
                  }}
                >
                  {cell.day}
                </button>
              )
            })}
          </div>

          {/* Footer Controls: Today & Close */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
            <button
              type="button"
              onClick={() => {
                const todayStr = toDDMMYYYY(new Date())
                onChange(todayStr)
                setViewYear(new Date().getFullYear())
                setViewMonth(new Date().getMonth())
                setIsOpen(false)
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#38bdf8',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer',
                padding: '4px 6px'
              }}
            >
              Select Today
            </button>

            <button
              type="button"
              onClick={() => setIsOpen(false)}
              style={{
                background: 'rgba(30, 41, 59, 0.7)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                color: 'var(--text-muted)',
                fontSize: '11px',
                padding: '3px 9px',
                cursor: 'pointer'
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
