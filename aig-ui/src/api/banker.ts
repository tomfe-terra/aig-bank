import { apiClient } from './client'
import type { RequestList, RequestDecision, RequestRejection, BankerCardList } from '@/types'

export const getBankerRequests = async (params?: {
  kind?: string
  limit?: number
  offset?: number
}): Promise<RequestList> => {
  const response = await apiClient.get<RequestList>('/banker/requests', { params })
  return response.data
}

export const approveRequest = async (requestId: string): Promise<RequestDecision> => {
  const response = await apiClient.post<RequestDecision>(`/banker/requests/${requestId}/approve`)
  return response.data
}

export const rejectRequest = async (
  requestId: string,
  data?: RequestRejection
): Promise<RequestDecision> => {
  const response = await apiClient.post<RequestDecision>(
    `/banker/requests/${requestId}/reject`,
    data
  )
  return response.data
}

export const getBankerCards = async (params?: {
  limit?: number
  offset?: number
}): Promise<BankerCardList> => {
  const response = await apiClient.get<BankerCardList>('/banker/cards', { params })
  return response.data
}

export const cancelCard = async (cardId: string): Promise<void> => {
  await apiClient.post(`/banker/cards/${cardId}/cancel`)
}

