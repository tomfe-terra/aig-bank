import { apiClient } from './client'
import type { LoanRead, LoanRequestCreate } from '@/types'

export const loansApi = {
  async getLoans(): Promise<LoanRead[]> {
    const response = await apiClient.get<LoanRead[]>('/users/loans')
    return response.data
  },

  async requestLoan(data: LoanRequestCreate): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/users/loans/request', data)
    return response.data
  },
}

