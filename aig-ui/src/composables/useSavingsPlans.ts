import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { savingsPlansApi } from '@/api'
import type { SavingsPlanDepositCreate } from '@/types'

export function useSavingsPlans() {
  const { data: plans, isLoading, error } = useQuery({
    queryKey: ['savingsPlans'],
    queryFn: () => savingsPlansApi.listPlans(),
  })

  return {
    plans,
    isLoading,
    error,
  }
}

export function useOpenSavingsPlan() {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (data: SavingsPlanDepositCreate) => savingsPlansApi.openPlan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account'] })
    },
  })

  return {
    openPlan: mutation.mutate,
    openPlanAsync: mutation.mutateAsync,
    isLoading: mutation.isPending,
    error: mutation.error,
    isSuccess: mutation.isSuccess,
    data: mutation.data,
  }
}

