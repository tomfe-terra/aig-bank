import { apiClient } from './client'
import type { APIKeyRead, APIKeyCreate, APIKeyUpdate, APIKeySecretRead, APIKeyList } from '@/types'

export const apiKeysApi = {
  async getAPIKeys(includeRevoked = false): Promise<APIKeyRead[]> {
    const response = await apiClient.get<APIKeyList>('/users/api-keys', {
      params: { include_revoked: includeRevoked }
    })
    return response.data.api_keys
  },

  async createAPIKey(data: APIKeyCreate): Promise<APIKeySecretRead> {
    const response = await apiClient.post<APIKeySecretRead>('/users/api-keys', data)
    return response.data
  },

  async updateAPIKey(apiKeyId: string, data: APIKeyUpdate): Promise<APIKeyRead> {
    const response = await apiClient.patch<APIKeyRead>(`/users/api-keys/${apiKeyId}`, data)
    return response.data
  },

  async deleteAPIKey(apiKeyId: string): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`/users/api-keys/${apiKeyId}`)
    return response.data
  },
}

