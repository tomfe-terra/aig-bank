import { ref } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { getBankerCards, cancelCard } from '@/api'
import type { BankerCardList } from '@/types'

export const useBankerCards = () => {
  const queryClient = useQueryClient()
  const limit = ref(50)
  const offset = ref(0)

  const {
    data: cardList,
    isLoading,
    error,
    refetch,
  } = useQuery<BankerCardList>({
    queryKey: ['banker-cards', limit, offset],
    queryFn: () => getBankerCards({ limit: limit.value, offset: offset.value }),
  })

  const { mutateAsync: cancel, isPending: isCanceling } = useMutation({
    mutationFn: cancelCard,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['banker-cards'] })
    },
  })

  return {
    cardList,
    cards: cardList,
    isLoading,
    error,
    refetch,
    cancel,
    isCanceling,
    limit,
    offset,
  }
}

