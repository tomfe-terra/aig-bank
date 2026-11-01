import type { TransactionRead } from './transaction'
import type { AccountRead } from './account'

export interface TransferCreate {
  from_account_number?: string | null
  to_account_number: string
  amount_cents: number
  meta?: Record<string, any> | null
}

export interface TransferRead {
  transaction: TransactionRead
  from_account: AccountRead
  to_account: AccountRead
}

