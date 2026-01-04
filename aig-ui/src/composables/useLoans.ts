import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { loansApi } from '@/api'
import type { LoanRequestCreate } from '@/types'

export function useLoans() {
  const queryClient = useQueryClient()

  const { data: loans, isLoading, error, refetch } = useQuery({
    queryKey: ['loans'],
    queryFn: () => loansApi.getLoans(),
  })

  const requestLoanMutation = useMutation({
    mutationFn: (data: LoanRequestCreate) => loansApi.requestLoan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] })
    },
  })

  return {
    loans,
    isLoading,
    error,
    refetch,
    requestLoan: requestLoanMutation.mutateAsync,
    isRequestingLoan: requestLoanMutation.isPending,
  }
}

