<script setup lang="ts">
import { ref } from 'vue'
import { useSavingsPlans, useOpenSavingsPlan } from '@/composables/useSavingsPlans'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'
import { formatMoney, getErrorMessage } from '@/utils/format'
import EmptyState from '@/components/EmptyState.vue'
import MoneyInput from '@/components/MoneyInput.vue'
import type { SavingsPlanInfo } from '@/types'

const { plans, isLoading } = useSavingsPlans()
const { openPlanAsync, isLoading: isOpening } = useOpenSavingsPlan()
const { account } = useAuth()
const { showToast } = useToast()

// Dialog state
const openDialog = ref(false)
const selectedPlan = ref<SavingsPlanInfo | null>(null)
const depositAmount = ref(0)
const successMessage = ref('')
const showSuccessDialog = ref(false)

const handleOpenPlan = (plan: SavingsPlanInfo) => {
  selectedPlan.value = plan
  depositAmount.value = 0
  openDialog.value = true
}

const handleSubmit = async () => {
  if (!selectedPlan.value || depositAmount.value <= 0) return

  try {
    const result = await openPlanAsync({
      plan_id: selectedPlan.value.id,
      amount_cents: depositAmount.value,
    })
    
    openDialog.value = false
    successMessage.value = result.message
    showSuccessDialog.value = true
  } catch (error: unknown) {
    showToast(getErrorMessage(error, 'Failed to open savings plan'), 'error')
  }
}

const handleSuccessClose = () => {
  showSuccessDialog.value = false
  successMessage.value = ''
  selectedPlan.value = null
  depositAmount.value = 0
}

const canAfford = (amount: number) => {
  if (!account.value) return false
  return account.value.balance_cents >= amount
}
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">Savings Plans</h1>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading">
      <v-row>
        <v-col v-for="i in 3" :key="i" cols="12" md="4">
          <v-skeleton-loader type="card" />
        </v-col>
      </v-row>
    </div>

    <!-- Empty State -->
    <EmptyState
      v-else-if="!plans || plans.plans.length === 0"
      icon="mdi-piggy-bank-outline"
      title="No Savings Plans Available"
      message="There are currently no savings plans available. Please check back later."
    />

    <!-- Plans Grid -->
    <v-row v-else>
      <v-col
        v-for="plan in plans.plans"
        :key="plan.id"
        cols="12"
        md="4"
      >
        <v-card variant="outlined" class="h-100 d-flex flex-column">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-piggy-bank-outline" class="mr-2" color="primary" />
            {{ plan.display_name }}
          </v-card-title>
          
          <v-card-subtitle class="text-medium-emphasis">
            {{ plan.tagline }}
          </v-card-subtitle>

          <v-card-text class="flex-grow-1">
            <p class="text-body-2">{{ plan.description }}</p>
          </v-card-text>

          <v-card-actions>
            <v-btn
              color="primary"
              variant="flat"
              block
              @click="handleOpenPlan(plan)"
            >
              Open Plan
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Open Savings Plan Dialog -->
    <v-dialog
      v-model="openDialog"
      max-width="500"
      persistent
    >
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-piggy-bank-outline" class="mr-2" />
          Open Savings Plan
        </v-card-title>

        <v-card-text>
          <div v-if="selectedPlan" class="mb-4">
            <h3 class="text-h6 mb-2">{{ selectedPlan.display_name }}</h3>
            <p class="text-body-2 text-medium-emphasis mb-4">
              {{ selectedPlan.description }}
            </p>

            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              <div class="text-body-2">
                <strong>Available Balance:</strong> {{ formatMoney(account?.balance_cents || 0) }}
              </div>
            </v-alert>

            <MoneyInput
              v-model="depositAmount"
              label="Deposit Amount"
              :error="depositAmount > 0 && !canAfford(depositAmount)"
              :error-messages="depositAmount > 0 && !canAfford(depositAmount) ? 'Insufficient funds' : ''"
            />

            <div v-if="depositAmount > 0 && canAfford(depositAmount)" class="mt-4">
              <v-divider class="mb-3" />
              <div class="d-flex justify-space-between text-body-2">
                <span>Current Balance:</span>
                <span>{{ formatMoney(account?.balance_cents || 0) }}</span>
              </div>
              <div class="d-flex justify-space-between text-body-2 mt-2">
                <span>After Deposit:</span>
                <span :class="depositAmount > 0 ? 'text-primary' : ''">
                  {{ formatMoney((account?.balance_cents || 0) - depositAmount) }}
                </span>
              </div>
            </div>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-btn
            variant="text"
            @click="openDialog = false"
            :disabled="isOpening"
          >
            Cancel
          </v-btn>
          <v-spacer />
          <v-btn
            color="primary"
            variant="flat"
            @click="handleSubmit"
            :loading="isOpening"
            :disabled="depositAmount <= 0 || !canAfford(depositAmount)"
          >
            Open Plan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Dialog -->
    <v-dialog
      v-model="showSuccessDialog"
      max-width="600"
    >
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-check-circle" color="success" class="mr-2" />
          Savings Plan Opened Successfully
        </v-card-title>

        <v-card-text>
          <v-alert
            type="success"
            variant="tonal"
            class="mb-4"
          >
            <div class="text-body-1">
              {{ successMessage }}
            </div>
          </v-alert>

          <p class="text-body-2 text-medium-emphasis">
            Your deposit has been processed and your savings plan is now active.
          </p>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn
            color="primary"
            variant="flat"
            @click="handleSuccessClose"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
