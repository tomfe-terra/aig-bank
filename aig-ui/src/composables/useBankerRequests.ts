import { ref } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { getBankerRequests, approveRequest, rejectRequest } from '@/api'
import type { RequestList } from '@/types'

export const useBankerRequests = (kind?: string) => {
  const queryClient = useQueryClient()
  const limit = ref(50)
  const offset = ref(0)

  const {
    data: requestList,
    isLoading,
    error,
    refetch,
  } = useQuery<RequestList>({
    queryKey: ['banker-requests', kind, limit, offset],
    queryFn: () => getBankerRequests({ kind, limit: limit.value, offset: offset.value }),
  })

  const { mutateAsync: approve, isPending: isApproving } = useMutation({
    mutationFn: approveRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['banker-requests'] })
    },
  })

  const { mutateAsync: reject, isPending: isRejecting } = useMutation({
    mutationFn: ({ requestId, reason }: { requestId: string; reason?: string }) =>
      rejectRequest(requestId, reason ? { reason } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['banker-requests'] })
    },
  })

  return {
    requests: requestList,
    isLoading,
    error,
    refetch,
    approve,
    reject,
    isApproving,
    isRejecting,
    limit,
    offset,
  }
}

