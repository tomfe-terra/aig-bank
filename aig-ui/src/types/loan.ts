export enum LoanStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  ACTIVE = 'ACTIVE',
  CLOSED = 'CLOSED',
}

export interface LoanRead {
  id: string | null
  account_id: string | null
  principal_cents: number
  principal_dollars: number
  repayment_cycles: number
  installment_amount_cents: number
  paid_amount_cents: number
  remaining_balance_cents: number
  status: LoanStatus
  approved_by: string | null
  next_repayment_at: string | null
  last_repayment_at: string | null
  version: number
  created_at: string
  updated_at: string
}

export interface LoanRequestCreate {
  principal_cents: number
  repayment_cycles: number
}

