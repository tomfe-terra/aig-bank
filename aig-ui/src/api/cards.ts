import { apiClient } from './client'
import type { CardRead, CardRequestCreate, CardReveal } from '@/types'

export const cardsApi = {
  async getCards(): Promise<CardRead[]> {
    const response = await apiClient.get<CardRead[]>('/users/cards')
    return response.data
  },

  async requestCard(data: CardRequestCreate): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/users/cards/request', data)
    return response.data
  },

  async revealCard(cardId: string): Promise<CardReveal> {
    const response = await apiClient.get<CardReveal>(`/users/cards/${cardId}/reveal`)
    return response.data
  },
}

