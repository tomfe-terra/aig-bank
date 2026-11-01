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

  async fetchDocument(url: string): Promise<{ url: string; status_code: number; body: string }> {
    const response = await apiClient.get<{ url: string; status_code: number; body: string }>('/users/documents/fetch', {
      params: { url },
    })
    return response.data
  },
}

