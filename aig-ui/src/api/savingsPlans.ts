import { apiClient } from './client'
import type { SavingsPlanListResponse, SavingsPlanDepositCreate, SavingsPlanDepositRead } from '@/types'

export const savingsPlansApi = {
  async listPlans(): Promise<SavingsPlanListResponse> {
    const response = await apiClient.get<SavingsPlanListResponse>('/savings-plans')
    return response.data
  },

  async openPlan(data: SavingsPlanDepositCreate): Promise<SavingsPlanDepositRead> {
    const response = await apiClient.post<SavingsPlanDepositRead>('/users/savings-plans/open', data)
    return response.data
  },
}

