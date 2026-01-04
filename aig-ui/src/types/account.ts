export interface AccountRead {
  id: string
  number: string
  user_id: string
  balance_cents: number
  balance_dollars: number
  created_at: string
  updated_at: string | null
}

