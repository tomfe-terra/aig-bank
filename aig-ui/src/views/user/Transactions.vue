<script setup lang="ts">
import { ref, watch } from 'vue'
import { useTransactions } from '@/composables/useTransactions'
import { formatMoney, formatDate, getTransactionIcon, getTransactionColor } from '@/utils/format'
import EmptyState from '@/components/EmptyState.vue'
import { TransactionType } from '@/types'

const { 
  transactions, 
  isLoading, 
  transactionType, 
  startDate, 
  endDate,
  loadMore,
  resetFilters
} = useTransactions()

const transactionTypes = [
  { title: 'All Types', value: '' },
  { title: 'Transfer In', value: TransactionType.TRANSFER_IN },
  { title: 'Transfer Out', value: TransactionType.TRANSFER_OUT },
  { title: 'Card Payment', value: TransactionType.CARD_PAYMENT },
  { title: 'Loan Disbursement', value: TransactionType.LOAN_DISBURSEMENT },
  { title: 'Loan Repayment', value: TransactionType.LOAN_REPAYMENT },
  { title: 'Fee', value: TransactionType.FEE },
  { title: 'Refund', value: TransactionType.REFUND },
]

// Date range presets
const dateRangePresets = [
  { title: 'All Time', value: 'all' },
  { title: 'Today', value: 'today' },
  { title: 'Last 7 Days', value: 'week' },
  { title: 'Last 30 Days', value: 'month' },
  { title: 'Last 90 Days', value: 'quarter' },
  { title: 'Custom Range', value: 'custom' },
]

const selectedDateRange = ref('all')
const showCustomDatePicker = ref(false)
const customStartDate = ref<string>('')
const customEndDate = ref<string>('')
const searchQuery = ref('')

// Handle date range preset selection
const handleDateRangeChange = (value: string) => {
  const today = new Date()
  today.setHours(23, 59, 59, 999) // End of today
  
  switch (value) {
    case 'all':
      startDate.value = undefined
      endDate.value = undefined
      showCustomDatePicker.value = false
      break
    case 'today':
      const startOfToday = new Date()
      startOfToday.setHours(0, 0, 0, 0)
      startDate.value = startOfToday.toISOString()
      endDate.value = today.toISOString()
      showCustomDatePicker.value = false
      break
    case 'week':
      const weekAgo = new Date()
      weekAgo.setDate(weekAgo.getDate() - 7)
      weekAgo.setHours(0, 0, 0, 0)
      startDate.value = weekAgo.toISOString()
      endDate.value = today.toISOString()
      showCustomDatePicker.value = false
      break
    case 'month':
      const monthAgo = new Date()
      monthAgo.setDate(monthAgo.getDate() - 30)
      monthAgo.setHours(0, 0, 0, 0)
      startDate.value = monthAgo.toISOString()
      endDate.value = today.toISOString()
      showCustomDatePicker.value = false
      break
    case 'quarter':
      const quarterAgo = new Date()
      quarterAgo.setDate(quarterAgo.getDate() - 90)
      quarterAgo.setHours(0, 0, 0, 0)
      startDate.value = quarterAgo.toISOString()
      endDate.value = today.toISOString()
      showCustomDatePicker.value = false
      break
    case 'custom':
      showCustomDatePicker.value = true
      break
  }
}

// Apply custom date range
const applyCustomDateRange = () => {
  if (customStartDate.value) {
    const start = new Date(customStartDate.value)
    start.setHours(0, 0, 0, 0)
    startDate.value = start.toISOString()
  }
  if (customEndDate.value) {
    const end = new Date(customEndDate.value)
    end.setHours(23, 59, 59, 999)
    endDate.value = end.toISOString()
  }
}

// Clear all filters
const handleClearFilters = () => {
  resetFilters()
  selectedDateRange.value = 'all'
  showCustomDatePicker.value = false
  customStartDate.value = ''
  customEndDate.value = ''
  searchQuery.value = ''
}

// Check if any filters are active
const hasActiveFilters = ref(false)
watch([transactionType, startDate, endDate, searchQuery], () => {
  hasActiveFilters.value = !!(
    transactionType.value || 
    startDate.value || 
    endDate.value || 
    searchQuery.value
  )
})

// Filter transactions by search query (client-side)
const filteredTransactions = ref<any[]>([])
watch([transactions, searchQuery], () => {
  if (!transactions.value) {
    filteredTransactions.value = []
    return
  }
  
  if (!searchQuery.value) {
    filteredTransactions.value = transactions.value.transactions
    return
  }
  
  const query = searchQuery.value.toLowerCase()
  filteredTransactions.value = transactions.value.transactions.filter((t: any) => {
    return (
      t.type.toLowerCase().includes(query) ||
      t.id?.toLowerCase().includes(query) ||
      t.related_account_id?.account_number?.toLowerCase().includes(query) ||
      t.related_account_id?.username?.toLowerCase().includes(query) ||
      t.meta?.note?.toLowerCase().includes(query) ||
      formatMoney(t.amount_cents).toLowerCase().includes(query)
    )
  })
}, { immediate: true })

</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">Transaction History</h1>
      <v-btn
        v-if="hasActiveFilters"
        variant="outlined"
        prepend-icon="mdi-filter-off"
        @click="handleClearFilters"
      >
        Clear Filters
      </v-btn>
    </div>

    <v-card variant="outlined">
      <!-- Filters -->
      <v-card-title>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="transactionType"
              :items="transactionTypes"
              label="Transaction Type"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
          
          <v-col cols="12" md="3">
            <v-select
              v-model="selectedDateRange"
              :items="dateRangePresets"
              label="Date Range"
              variant="outlined"
              density="compact"
              hide-details
              @update:model-value="handleDateRangeChange"
            />
          </v-col>
          
          <v-col cols="12" md="6">
            <v-text-field
              v-model="searchQuery"
              label="Search transactions"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              placeholder="Search by type, ID, account, or note..."
            />
          </v-col>
        </v-row>
        
        <!-- Custom Date Range Picker -->
        <v-row v-if="showCustomDatePicker" class="mt-2">
          <v-col cols="12" md="3">
            <v-text-field
              v-model="customStartDate"
              label="Start Date"
              type="date"
              variant="outlined"
              density="compact"
              hide-details
            />
          </v-col>
          
          <v-col cols="12" md="3">
            <v-text-field
              v-model="customEndDate"
              label="End Date"
              type="date"
              variant="outlined"
              density="compact"
              hide-details
            />
          </v-col>
          
          <v-col cols="12" md="2">
            <v-btn
              color="primary"
              variant="flat"
              block
              @click="applyCustomDateRange"
            >
              Apply
            </v-btn>
          </v-col>
        </v-row>
      </v-card-title>

      <!-- Transactions Table -->
      <v-card-text>
        <v-skeleton-loader v-if="isLoading" type="table-row@10" />
        
        <EmptyState
          v-else-if="!transactions || transactions.transactions.length === 0"
          icon="mdi-format-list-bulleted"
          title="No transactions found"
          message="No transactions match your current filters. Try adjusting your search criteria."
          action-text="Clear Filters"
          @action="handleClearFilters"
        />
        
        <div v-else>
          <!-- Results Summary -->
          <div class="mb-4 d-flex justify-space-between align-center">
            <div class="text-body-2 text-medium-emphasis">
              Showing {{ filteredTransactions.length }} of {{ transactions.total }} transactions
            </div>
            <div v-if="startDate || endDate" class="text-caption text-medium-emphasis">
              <v-icon icon="mdi-calendar-range" size="small" class="mr-1" />
              {{ startDate ? formatDate(startDate) : 'Start' }} - {{ endDate ? formatDate(endDate) : 'End' }}
            </div>
          </div>
          
          <v-table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Related Account</th>
                <th>Metadata</th>
                <th class="text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="transaction in filteredTransactions" :key="transaction.id">
                <td>
                  <div class="d-flex align-center">
                    <v-icon
                      :icon="getTransactionIcon(transaction.type)"
                      :color="getTransactionColor(transaction.type, transaction.amount_cents)"
                      class="mr-2"
                      size="small"
                    />
                    {{ formatDate(transaction.created_at) }}
                  </div>
                </td>
                <td>
                  <v-chip size="small" variant="tonal">
                    {{ transaction.type.replace(/_/g, ' ') }}
                  </v-chip>
                </td>
                <td>
                  <div v-if="transaction.related_account_id">
                    <div class="text-body-2 font-weight-medium">
                      {{ transaction.related_account_id.username }}
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      {{ transaction.related_account_id.account_number }}
                    </div>
                  </div>
                  <span v-else class="text-medium-emphasis">—</span>
                </td>
                <td>
                  <div v-if="transaction.meta && Object.keys(transaction.meta).length > 0" class="text-caption">
                    <v-tooltip location="top">
                      <template #activator="{ props }">
                        <v-chip
                          v-bind="props"
                          size="x-small"
                          variant="tonal"
                          class="cursor-pointer"
                        >
                          {{ Object.keys(transaction.meta).length }} field{{ Object.keys(transaction.meta).length > 1 ? 's' : '' }}
                        </v-chip>
                      </template>
                      <div class="pa-2">
                        <div v-for="(value, key) in transaction.meta" :key="key" class="mb-1">
                          <strong>{{ key }}:</strong> {{ value }}
                        </div>
                      </div>
                    </v-tooltip>
                  </div>
                  <span v-else class="text-medium-emphasis">—</span>
                </td>
                <td class="text-right">
                  <span
                    :class="transaction.amount_cents > 0 ? 'text-success' : 'text-error'"
                    class="font-weight-bold"
                  >
                    {{ formatMoney(transaction.amount_cents) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </v-table>

          <!-- Load More Button -->
          <div v-if="transactions.transactions.length > 0" class="text-center mt-4">
            <v-btn
              v-if="transactions.transactions.length < transactions.total"
              variant="outlined"
              @click="loadMore"
              :loading="isLoading"
              prepend-icon="mdi-refresh"
            >
              Load More ({{ transactions.total - transactions.transactions.length }} remaining)
            </v-btn>
            <div v-else class="text-caption text-medium-emphasis">
              All {{ transactions.total }} transactions loaded
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<style scoped>
.font-mono {
  font-family: 'Courier New', monospace;
}
</style>
