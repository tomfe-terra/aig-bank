import { useInfiniteQuery } from '@tanstack/vue-query'
import { transactionsApi } from '@/api'
import { ref, computed } from 'vue'

export function useTransactions() {
  const limit = ref(50)
  const transactionType = ref<string>('')
  const startDate = ref<string | undefined>(undefined)
  const endDate = ref<string | undefined>(undefined)

  const { data, isLoading, error, fetchNextPage, hasNextPage, refetch } = useInfiniteQuery({
    queryKey: ['transactions', { limit, transactionType, startDate, endDate }],
    queryFn: ({ pageParam = 0 }) => {
      const params: {
        limit: number
        offset: number
        transaction_type?: string
        start_date?: string
        end_date?: string
      } = {
        limit: limit.value,
        offset: pageParam,
      }
      
      if (transactionType.value) {
        params.transaction_type = transactionType.value
      }
      if (startDate.value) {
        params.start_date = startDate.value
      }
      if (endDate.value) {
        params.end_date = endDate.value
      }
      
      return transactionsApi.getTransactions(params)
    },
    getNextPageParam: (lastPage) => {
      const nextOffset = lastPage.offset + lastPage.limit
      if (nextOffset >= lastPage.total) return undefined
      return nextOffset
    },
    initialPageParam: 0,
  })

  const transactions = computed(() => {
    if (!data.value?.pages || data.value.pages.length === 0) {
      return {
        transactions: [],
        total: 0,
        limit: limit.value,
        offset: 0,
      }
    }
    
    const allTransactions = data.value.pages.flatMap(page => page.transactions)
    const firstPage = data.value.pages[0]
    
    return {
      transactions: allTransactions,
      total: firstPage.total,
      limit: firstPage.limit,
      offset: data.value.pages[data.value.pages.length - 1].offset,
    }
  })

  const loadMore = () => {
    if (hasNextPage.value) {
      fetchNextPage()
    }
  }

  const resetFilters = () => {
    transactionType.value = ''
    startDate.value = undefined
    endDate.value = undefined
  }

  return {
    transactions,
    isLoading,
    error,
    refetch,
    loadMore,
    resetFilters,
    hasNextPage,
    limit,
    offset: computed(() => transactions.value?.offset || 0),
    transactionType,
    startDate,
    endDate,
  }
}

