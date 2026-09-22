/**
 * Date and timezone utilities for SmartMaintain application.
 * Standardizes date formatting across all components.
 * 
 * Backend sends timestamps in Africa/Tunis timezone (UTC+1).
 * Frontend displays them directly without conversion.
 */

/**
 * Format a date/time string for display in French locale.
 * 
 * @param {string|Date} dateValue - ISO string or Date object
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string or '-' if invalid
 */
export function formatDateTime(dateValue, options = {}) {
  if (!dateValue) return '-'
  
  try {
    const date = typeof dateValue === 'string' ? new Date(dateValue) : dateValue
    
    if (isNaN(date.getTime())) return '-'
    
    const defaultOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      ...options
    }
    
    return date.toLocaleString('fr-FR', defaultOptions)
  } catch (error) {
    console.error('Error formatting date:', error)
    return '-'
  }
}

/**
 * Format date only (without time).
 * 
 * @param {string|Date} dateValue - ISO string or Date object
 * @returns {string} Formatted date string (DD/MM/YYYY)
 */
export function formatDate(dateValue) {
  return formatDateTime(dateValue, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: undefined,
    minute: undefined,
    second: undefined
  })
}

/**
 * Format time only (without date).
 * 
 * @param {string|Date} dateValue - ISO string or Date object
 * @returns {string} Formatted time string (HH:MM:SS)
 */
export function formatTime(dateValue) {
  return formatDateTime(dateValue, {
    year: undefined,
    month: undefined,
    day: undefined,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * Format date with short month name.
 * Example: "20 sept. 2026, 15:30"
 * 
 * @param {string|Date} dateValue - ISO string or Date object
 * @returns {string} Formatted date string
 */
export function formatDateShort(dateValue) {
  return formatDateTime(dateValue, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

/**
 * Format relative time (e.g., "il y a 5 minutes").
 * 
 * @param {string|Date} dateValue - ISO string or Date object
 * @returns {string} Relative time string or '-' if invalid
 */
export function timeAgo(dateValue) {
  if (!dateValue) return '-'
  
  try {
    const date = typeof dateValue === 'string' ? new Date(dateValue) : dateValue
    
    if (isNaN(date.getTime())) return '-'
    
    const diffMs = Date.now() - date.getTime()
    const diffMinutes = Math.floor(diffMs / 60000)
    
    if (diffMinutes < 0) return 'à venir'
    if (diffMinutes === 0) return "à l'instant"
    if (diffMinutes === 1) return 'il y a 1 minute'
    if (diffMinutes < 60) return `il y a ${diffMinutes} minutes`
    
    const diffHours = Math.floor(diffMinutes / 60)
    if (diffHours === 1) return 'il y a 1 heure'
    if (diffHours < 24) return `il y a ${diffHours} heures`
    
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays === 1) return 'il y a 1 jour'
    if (diffDays < 7) return `il y a ${diffDays} jours`
    
    const diffWeeks = Math.floor(diffDays / 7)
    if (diffWeeks === 1) return 'il y a 1 semaine'
    if (diffWeeks < 4) return `il y a ${diffWeeks} semaines`
    
    const diffMonths = Math.floor(diffDays / 30)
    if (diffMonths === 1) return 'il y a 1 mois'
    if (diffMonths < 12) return `il y a ${diffMonths} mois`
    
    const diffYears = Math.floor(diffDays / 365)
    if (diffYears === 1) return 'il y a 1 an'
    return `il y a ${diffYears} ans`
  } catch (error) {
    console.error('Error calculating time ago:', error)
    return '-'
  }
}

/**
 * Extract hour from ISO timestamp for chart labels.
 * 
 * @param {string} isoString - ISO timestamp string
 * @returns {number} Hour (0-23)
 */
export function extractHour(isoString) {
  if (!isoString) return 0
  try {
    return new Date(isoString).getHours()
  } catch {
    return 0
  }
}

/**
 * Format timestamp for chart axis (HH:MM:SS).
 * 
 * @param {string|Date} dateValue - ISO string or Date object
 * @returns {string} Time string for charts
 */
export function formatChartTime(dateValue) {
  if (!dateValue) return ''
  try {
    const date = typeof dateValue === 'string' ? new Date(dateValue) : dateValue
    return date.toLocaleTimeString('fr-FR', { hour12: false })
  } catch {
    return ''
  }
}

/**
 * Check if a date is today.
 * 
 * @param {string|Date} dateValue - ISO string or Date object
 * @returns {boolean} True if date is today
 */
export function isToday(dateValue) {
  if (!dateValue) return false
  try {
    const date = typeof dateValue === 'string' ? new Date(dateValue) : dateValue
    const today = new Date()
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    )
  } catch {
    return false
  }
}
