import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { transfersApi } from '@/api'
import type { TransferCreate } from '@/types'

export function useTransfer() {
  const queryClient = useQueryClient()

  const transferMutation = useMutation({
    mutationFn: (data: TransferCreate) => transfersApi.createTransfer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
  })

  return {
    transfer: transferMutation.mutateAsync,
    isTransferring: transferMutation.isPending,
    transferError: transferMutation.error,
    transferData: transferMutation.data,
  }
}

