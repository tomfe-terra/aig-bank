export enum TransactionType {
  TRANSFER_OUT = 'TRANSFER_OUT',
  TRANSFER_IN = 'TRANSFER_IN',
  CARD_PAYMENT = 'CARD_PAYMENT',
  LOAN_DISBURSEMENT = 'LOAN_DISBURSEMENT',
  LOAN_REPAYMENT = 'LOAN_REPAYMENT',
  FEE = 'FEE',
  REFUND = 'REFUND',
}

export interface TransactionRead {
  id: string | null
  account_id: string | null
  type: TransactionType
  amount_cents: number
  amount_dollars: number
  related_account_id: string | null
  idempotency_key: string
  meta: Record<string, any> | null
  created_at: string
}

export interface TransactionListResponse {
  transactions: TransactionRead[]
  total: number
  limit: number
  offset: number
}

