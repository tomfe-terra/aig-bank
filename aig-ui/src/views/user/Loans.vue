<script setup lang="ts">
import { ref, computed } from 'vue'
import { useLoans } from '@/composables/useLoans'
import { useToast } from '@/composables/useToast'
import { formatMoney, formatDate, getStatusColor, getErrorMessage } from '@/utils/format'
import EmptyState from '@/components/EmptyState.vue'

const { loans, isLoading, requestLoan, isRequestingLoan } = useLoans()
const { success, error } = useToast()

const showRequestDialog = ref(false)
const principalCents = ref(100000) // Default $1,000
const repaymentCycles = ref(24) // Default 24 hours

const principalDollars = computed({
  get: () => principalCents.value / 100,
  set: (value) => {
    principalCents.value = Math.round(value * 100)
  }
})

const installmentAmount = computed(() => {
  return Math.ceil(principalCents.value / repaymentCycles.value)
})

const handleRequestLoan = async () => {
  try {
    await requestLoan({
      principal_cents: principalCents.value,
      repayment_cycles: repaymentCycles.value,
    })
    showRequestDialog.value = false
    success(`Loan request for ${formatMoney(principalCents.value)} submitted successfully! Your loan will be reviewed shortly.`)
  } catch (e: unknown) {
    console.error('Failed to request loan:', e)
    error(getErrorMessage(e, 'Failed to request loan'))
  }
}
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">My Loans</h1>
      <v-btn
        color="primary"
        prepend-icon="mdi-cash-plus"
        @click="showRequestDialog = true"
      >
        Request Loan
      </v-btn>
    </div>

    <v-skeleton-loader v-if="isLoading" type="table-row@5" />
    
    <EmptyState
      v-else-if="!loans || loans.length === 0"
      icon="mdi-cash-off"
      title="No loans yet"
      message="Request a loan to get started. Our non-profit bank offers 0% interest loans!"
      action-text="Request Loan"
      @action="showRequestDialog = true"
    />
    
    <v-card v-else variant="outlined">
      <v-table>
        <thead>
          <tr>
            <th>Amount</th>
            <th>Installment</th>
            <th>Cycles</th>
            <th>Remaining</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="loan in loans" :key="loan.id ?? loan.created_at">
            <td class="font-weight-bold">
              {{ formatMoney(loan.principal_cents) }}
            </td>
            <td>
              {{ formatMoney(loan.installment_amount_cents) }}
            </td>
            <td>
              {{ loan.repayment_cycles }} hours
            </td>
            <td>
              {{ formatMoney(loan.remaining_balance_cents) }}
            </td>
            <td>
              <v-chip
                :color="getStatusColor(loan.status)"
                size="small"
              >
                {{ loan.status }}
              </v-chip>
            </td>
            <td>
              {{ formatDate(loan.created_at) }}
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <!-- Request Loan Dialog -->
    <v-dialog v-model="showRequestDialog" max-width="550" persistent>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">Request Loan</span>
          <v-btn icon="mdi-close" variant="text" @click="showRequestDialog = false" :disabled="isRequestingLoan" />
        </v-card-title>
        
        <v-divider />
        
        <v-card-text class="pt-4">
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">
            <strong>0% Interest!</strong> Interest-free loans with automatic hourly repayments.
          </v-alert>
          
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">Loan Amount</div>
            <v-slider
              v-model="principalDollars"
              :min="100"
              :max="10000"
              :step="100"
              thumb-label
              color="primary"
              class="mb-2"
            >
              <template #thumb-label="{ modelValue }">
                ${{ modelValue }}
              </template>
            </v-slider>
            <v-text-field
              v-model.number="principalDollars"
              type="number"
              variant="outlined"
              prefix="$"
              :min="100"
              :max="10000"
              :step="100"
              density="compact"
              hide-details
            />
          </div>

          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">Repayment Cycles (Hours)</div>
            <v-slider
              v-model="repaymentCycles"
              :min="1"
              :max="720"
              :step="1"
              thumb-label
              color="primary"
              class="mb-2"
            />
            <v-text-field
              v-model.number="repaymentCycles"
              type="number"
              variant="outlined"
              suffix="hours"
              :min="1"
              :max="720"
              density="compact"
              hide-details
            />
          </div>

          <v-sheet color="grey-lighten-4" rounded class="pa-3">
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>Loan Amount:</span>
              <span class="font-weight-bold">{{ formatMoney(principalCents) }}</span>
            </div>
            <div class="d-flex justify-space-between text-body-2 mb-2">
              <span>Repayment Cycles:</span>
              <span class="font-weight-bold">{{ repaymentCycles }} hours</span>
            </div>
            <v-divider class="my-2" />
            <div class="d-flex justify-space-between">
              <span class="text-body-2">Installment Amount:</span>
              <span class="text-h6 text-primary font-weight-bold">{{ formatMoney(installmentAmount) }}/hour</span>
            </div>
          </v-sheet>
        </v-card-text>
        
        <v-divider />
        
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="showRequestDialog = false"
            :disabled="isRequestingLoan"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="handleRequestLoan"
            :loading="isRequestingLoan"
          >
            Request Loan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

