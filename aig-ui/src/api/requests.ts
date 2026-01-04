import { apiClient } from './client'
import type { Request } from '@/types'

export const getMyRequests = async (): Promise<Request[]> => {
  const response = await apiClient.get<Request[]>('/users/requests')
  return response.data
}

export const getRequestById = async (requestId: string): Promise<Request> => {
  const response = await apiClient.get<Request>(`/users/requests/${requestId}`)
  return response.data
}

