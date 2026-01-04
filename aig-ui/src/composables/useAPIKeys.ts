import { ref } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { apiKeysApi } from '@/api'
import type { APIKeyCreate, APIKeyUpdate } from '@/types'

export function useAPIKeys() {
  const queryClient = useQueryClient()
  const includeRevoked = ref(false)

  const { data: apiKeys, isLoading, error, refetch } = useQuery({
    queryKey: ['apiKeys', includeRevoked],
    queryFn: () => apiKeysApi.getAPIKeys(includeRevoked.value),
  })

  const createAPIKeyMutation = useMutation({
    mutationFn: (data: APIKeyCreate) => apiKeysApi.createAPIKey(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] })
    },
  })

  const updateAPIKeyMutation = useMutation({
    mutationFn: ({ apiKeyId, data }: { apiKeyId: string; data: APIKeyUpdate }) => 
      apiKeysApi.updateAPIKey(apiKeyId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] })
    },
  })

  const deleteAPIKeyMutation = useMutation({
    mutationFn: (apiKeyId: string) => apiKeysApi.deleteAPIKey(apiKeyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] })
    },
  })

  return {
    apiKeys,
    isLoading,
    error,
    includeRevoked,
    refetchAPIKeys: refetch,
    createAPIKey: createAPIKeyMutation.mutateAsync,
    isCreating: createAPIKeyMutation.isPending,
    updateAPIKey: updateAPIKeyMutation.mutateAsync,
    isUpdating: updateAPIKeyMutation.isPending,
    deleteAPIKey: deleteAPIKeyMutation.mutateAsync,
    isDeleting: deleteAPIKeyMutation.isPending,
  }
}

