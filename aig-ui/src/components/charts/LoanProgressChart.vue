<template>
  <div class="loan-progress-chart">
    <div v-if="activeLoans.length === 0" class="text-center pa-8 text-medium-emphasis">
      No active loans
    </div>
    <div v-else class="loan-list">
      <div
        v-for="(loan, index) in activeLoans"
        :key="loan.id ?? index"
        class="loan-item mb-6"
      >
        <div class="d-flex justify-space-between align-center mb-2">
          <div>
            <span class="text-subtitle-2 font-weight-bold">
              Loan {{ index + 1 }}
            </span>
            <span class="text-caption text-medium-emphasis ml-2">
              Principal: {{ formatMoney(loan.principal_cents) }}
            </span>
          </div>
          <div class="text-subtitle-2 font-weight-bold">
            {{ calculatePercentage(loan) }}% paid
          </div>
        </div>
        
        <v-progress-linear
          :model-value="calculatePercentage(loan)"
          :color="getProgressColor(loan)"
          height="24"
          rounded
          class="mb-2"
        >
          <template #default>
            <span class="text-caption font-weight-medium">
              {{ formatMoney(loan.paid_amount_cents) }} / {{ formatMoney(loan.principal_cents) }}
            </span>
          </template>
        </v-progress-linear>
        
        <div class="d-flex justify-space-between text-caption text-medium-emphasis">
          <span>
            Remaining: {{ formatMoney(loan.remaining_balance_cents) }}
          </span>
          <span v-if="loan.next_repayment_at">
            Next payment {{ formatFutureDate(loan.next_repayment_at) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { LoanRead } from '@/types'
import { formatMoney, formatFutureDate } from '@/utils/format'

const props = defineProps<{
  loans: LoanRead[] | undefined
}>()

const activeLoans = computed(() => {
  if (!props.loans) return []
  return props.loans.filter(
    (loan) => loan.status === 'ACTIVE' || loan.status === 'APPROVED'
  )
})

const calculatePercentage = (loan: LoanRead): number => {
  if (loan.principal_cents === 0) return 0
  return Math.round((loan.paid_amount_cents / loan.principal_cents) * 100)
}

const getProgressColor = (loan: LoanRead): string => {
  const percentage = calculatePercentage(loan)
  if (percentage >= 75) return 'success'
  if (percentage >= 50) return 'primary'
  if (percentage >= 25) return 'warning'
  return 'error'
}
</script>

<style scoped>
.loan-progress-chart {
  min-height: 200px;
}

.loan-item {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  padding-bottom: 16px;
}

.loan-item:last-child {
  border-bottom: none;
  margin-bottom: 0 !important;
  padding-bottom: 0;
}
</style>

