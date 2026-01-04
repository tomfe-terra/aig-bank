export interface SavingsPlanInfo {
  id: number
  name: string
  display_name: string
  description: string
  tagline: string
}

export interface SavingsPlanListResponse {
  plans: SavingsPlanInfo[]
}

export interface SavingsPlanDepositCreate {
  plan_id: number
  amount_cents: number
}

export interface SavingsPlanDepositRead {
  plan_id: number
  plan_name: string
  amount_cents: number
  message: string
}

