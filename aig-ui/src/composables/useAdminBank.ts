import { useQuery } from '@tanstack/vue-query'
import { getBankCapital } from '@/api'
import type { BankCapitalBalance } from '@/types'

export const useAdminBank = () => {
  const {
    data: bankCapital,
    isLoading,
    error,
    refetch,
  } = useQuery<BankCapitalBalance>({
    queryKey: ['admin-bank-capital'],
    queryFn: getBankCapital,
  })

  return {
    bankCapital,
    isLoading,
    error,
    refetch,
  }
}

