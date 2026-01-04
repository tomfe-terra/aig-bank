import { apiClient } from './client'
import type { TransferCreate, TransferRead } from '@/types'

export const transfersApi = {
  async createTransfer(data: TransferCreate): Promise<TransferRead> {
    const response = await apiClient.post<TransferRead>('/users/transfers', data)
    return response.data
  },
}

