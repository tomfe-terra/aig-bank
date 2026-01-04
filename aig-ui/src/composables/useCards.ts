import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { cardsApi } from '@/api'
import type { CardRequestCreate } from '@/types'

export function useCards() {
  const queryClient = useQueryClient()

  const { data: cards, isLoading, error, refetch } = useQuery({
    queryKey: ['cards'],
    queryFn: () => cardsApi.getCards(),
  })

  const requestCardMutation = useMutation({
    mutationFn: (data: CardRequestCreate) => cardsApi.requestCard(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] })
    },
  })

  const revealCardMutation = useMutation({
    mutationFn: (cardId: string) => cardsApi.revealCard(cardId),
  })

  return {
    cards,
    isLoading,
    error,
    refetch,
    requestCard: requestCardMutation.mutateAsync,
    isRequestingCard: requestCardMutation.isPending,
    revealCard: revealCardMutation.mutateAsync,
    isRevealingCard: revealCardMutation.isPending,
    revealedCard: revealCardMutation.data,
  }
}

