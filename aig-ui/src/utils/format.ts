export function formatMoney(cents: number): string {
  const dollars = cents / 100
  return `$${dollars.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function parseUTCDate(dateString: string): Date {
  if (!dateString.endsWith('Z') && !dateString.match(/[+-]\d{2}:\d{2}$/)) {
    return new Date(dateString + 'Z')
  }
  return new Date(dateString)
}

export function formatDate(dateString: string): string {
  const date = parseUTCDate(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  if (diffMs < 0) {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }
  
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSeconds < 60) {
    return 'Just now'
  }
  if (diffMinutes < 60) {
    return diffMinutes === 1 ? '1 minute ago' : `${diffMinutes} minutes ago`
  }
  if (diffHours < 24) {
    return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`
  }
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatFutureDate(dateString: string): string {
  const date = parseUTCDate(dateString)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  
  if (diffMs < 0) {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }
  
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSeconds < 60) {
    return 'in less than a minute'
  }
  if (diffMinutes < 60) {
    return diffMinutes === 1 ? 'in 1 minute' : `in ${diffMinutes} minutes`
  }
  if (diffHours < 24) {
    return diffHours === 1 ? 'in 1 hour' : `in ${diffHours} hours`
  }
  if (diffDays === 1) return 'Tomorrow'
  if (diffDays < 7) return `in ${diffDays} days`
  if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7)
    return weeks === 1 ? 'in 1 week' : `in ${weeks} weeks`
  }

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatDateTime(dateString: string): string {
  const date = parseUTCDate(dateString)
  return date.toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

export function getTransactionIcon(type: string): string {
  const icons: Record<string, string> = {
    TRANSFER_IN: 'mdi-arrow-down-circle',
    TRANSFER_OUT: 'mdi-arrow-up-circle',
    CARD_PAYMENT: 'mdi-credit-card',
    LOAN_DISBURSEMENT: 'mdi-cash-plus',
    LOAN_REPAYMENT: 'mdi-cash-minus',
    FEE: 'mdi-receipt',
    REFUND: 'mdi-cash-refund',
  }
  return icons[type] || 'mdi-swap-horizontal'
}

export function getTransactionColor(_type: string, amount: number): string {
  if (amount > 0) return 'success'
  if (amount < 0) return 'error'
  return 'default'
}

export function getCardBrandIcon(brand: string): string {
  const icons: Record<string, string> = {
    VISA: 'mdi-credit-card',
    MASTERCARD: 'mdi-credit-card',
    AMERICAN_EXPRESS: 'mdi-credit-card',
    DISCOVER: 'mdi-credit-card',
  }
  return icons[brand] || 'mdi-credit-card'
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    ACTIVE: 'success',
    PENDING: 'warning',
    APPROVED: 'success',
    REJECTED: 'error',
    CANCELLED: 'error',
    EXPIRED: 'error',
    CLOSED: 'default',
  }
  return colors[status] || 'default'
}

export function getErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (!error) return fallback
  
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>
    
    if (err.response && typeof err.response === 'object') {
      const response = err.response as Record<string, unknown>
      const data = response.data as Record<string, unknown> | undefined
      
      if (data) {
        if (typeof data.details === 'string') return data.details
        
        if (Array.isArray(data.detail)) {
          const messages = data.detail.map((d: { msg?: string; message?: string }) => d.msg || d.message).filter(Boolean)
          if (messages.length > 0) return messages.join('. ')
        }
        
        if (typeof data.detail === 'string') return data.detail
        if (typeof data.message === 'string') return data.message
        
        if (typeof data.error === 'string') return data.error
      }
    }
    
    if (typeof err.details === 'string') return err.details
    if (typeof err.detail === 'string') return err.detail
    if (typeof err.message === 'string') return err.message
    if (typeof err.error === 'string') return err.error
  }
  
  if (typeof error === 'string') return error
  
  return fallback
}

