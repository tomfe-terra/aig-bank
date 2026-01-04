import { useQuery } from '@tanstack/vue-query'
import { getSettings } from '@/api/admin'

export function useAdminSettings() {
  const {
    data: settings,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['admin', 'settings'],
    queryFn: getSettings,
  })

  return {
    settings,
    isLoading,
    error,
    refetch,
  }
}

