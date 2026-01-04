import { useQuery } from '@tanstack/vue-query'
import { getMyRequests } from '@/api'
import type { Request } from '@/types'

export const useRequests = () => {
  const {
    data: requests,
    isLoading,
    error,
    refetch,
  } = useQuery<Request[]>({
    queryKey: ['requests'],
    queryFn: getMyRequests,
  })

  return {
    requests,
    isLoading,
    error,
    refetch,
  }
}

