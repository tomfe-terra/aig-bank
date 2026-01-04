import { apiClient } from './client'
import type { TransactionListResponse } from '@/types'

export const transactionsApi = {
  async getTransactions(params?: {
    limit?: number
    offset?: number
    transaction_type?: string
    start_date?: string
    end_date?: string
  }): Promise<TransactionListResponse> {
    const response = await apiClient.get<TransactionListResponse>('/users/transactions', { params })
    return response.data
  },
}

