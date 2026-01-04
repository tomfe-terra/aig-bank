<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useTransfer } from '@/composables/useTransfer'
import { useToast } from '@/composables/useToast'
import { formatMoney, getErrorMessage } from '@/utils/format'
import { useRouter } from 'vue-router'
import MoneyInput from '@/components/MoneyInput.vue'

const router = useRouter()
const { account } = useAuth()
const { transfer, isTransferring } = useTransfer()
const { success, error: showError } = useToast()

const toAccountNumber = ref('')
const amountCents = ref(0)
const note = ref('')
const showConfirmDialog = ref(false)
const error = ref('')

const availableBalance = computed(() => account.value?.balance_cents || 0)
const balanceAfterTransfer = computed(() => availableBalance.value - amountCents.value)

const canTransfer = computed(() => {
  return toAccountNumber.value.length >= 8 && 
         amountCents.value > 0 && 
         amountCents.value <= availableBalance.value
})

const handleTransfer = () => {
  if (!canTransfer.value) return
  showConfirmDialog.value = true
}

const confirmTransfer = async () => {
  error.value = ''
  try {
    await transfer({
      to_account_number: toAccountNumber.value,
      amount_cents: amountCents.value,
      meta: note.value ? { note: note.value } : null,
    })
    
    showConfirmDialog.value = false
    success(`Successfully transferred ${formatMoney(amountCents.value)} to account ${toAccountNumber.value}`)
    
    // Redirect to transactions
    router.push('/user/transactions')
  } catch (e: unknown) {
    const errorMsg = getErrorMessage(e, 'Transfer failed')
    error.value = errorMsg
    showError(errorMsg)
    showConfirmDialog.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-h4 mb-6">Transfer Money</h1>

    <v-row>
      <!-- Transfer Form -->
      <v-col cols="12" md="8">
        <v-card variant="outlined">
          <v-card-title>Transfer Details</v-card-title>
          
          <v-card-text>
            <v-form @submit.prevent="handleTransfer">
              <v-text-field
                v-model="toAccountNumber"
                label="To Account Number"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                :disabled="isTransferring"
                placeholder="Enter recipient account number"
                required
                class="mb-4"
              />

              <MoneyInput
                v-model="amountCents"
                label="Amount"
                :disabled="isTransferring"
                :error="amountCents > availableBalance"
                :error-messages="amountCents > availableBalance ? 'Insufficient funds' : ''"
                class="mb-4"
              />

              <v-textarea
                v-model="note"
                label="Note (optional)"
                prepend-inner-icon="mdi-note-text"
                variant="outlined"
                :disabled="isTransferring"
                rows="3"
                class="mb-4"
              />

              <v-alert
                v-if="error"
                type="error"
                variant="tonal"
                class="mb-4"
              >
                {{ error }}
              </v-alert>

              <div class="d-flex gap-2">
                <v-btn
                  variant="outlined"
                  @click="router.back()"
                  :disabled="isTransferring"
                >
                  Cancel
                </v-btn>
                <v-btn
                  type="submit"
                  color="primary"
                  :disabled="!canTransfer"
                  :loading="isTransferring"
                >
                  Transfer
                </v-btn>
              </div>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Balance Sidebar -->
      <v-col cols="12" md="4">
        <v-card variant="outlined" class="sticky-card">
          <v-card-title>Your Balance</v-card-title>
          
          <v-card-text>
            <div class="mb-4">
              <div class="text-caption text-medium-emphasis mb-1">Current Balance</div>
              <div class="text-h5">{{ formatMoney(availableBalance) }}</div>
            </div>

            <v-divider class="my-4" />

            <div class="mb-4">
              <div class="text-caption text-medium-emphasis mb-1">Transfer Amount</div>
              <div class="text-h6">{{ formatMoney(amountCents) }}</div>
            </div>

            <v-divider class="my-4" />

            <div>
              <div class="text-caption text-medium-emphasis mb-1">Balance After Transfer</div>
              <div 
                class="text-h5"
                :class="balanceAfterTransfer < 0 ? 'text-error' : ''"
              >
                {{ formatMoney(balanceAfterTransfer) }}
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Confirmation Dialog -->
    <v-dialog v-model="showConfirmDialog" max-width="450" persistent>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">Confirm Transfer</span>
          <v-btn icon="mdi-close" variant="text" @click="showConfirmDialog = false" :disabled="isTransferring" />
        </v-card-title>
        
        <v-divider />
        
        <v-card-text class="pt-4">
          <p class="text-body-2 mb-4">Please review the transfer details:</p>
          
          <div class="transfer-details">
            <div class="detail-row mb-3">
              <div class="text-caption text-medium-emphasis mb-1">To Account</div>
              <div class="text-body-1 font-mono">{{ toAccountNumber }}</div>
            </div>
            
            <div class="detail-row mb-3">
              <div class="text-caption text-medium-emphasis mb-1">Amount</div>
              <div class="text-h6 text-primary">{{ formatMoney(amountCents) }}</div>
            </div>
            
            <div v-if="note" class="detail-row">
              <div class="text-caption text-medium-emphasis mb-1">Note</div>
              <div class="text-body-2">{{ note }}</div>
            </div>
          </div>
        </v-card-text>
        
        <v-divider />
        
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="showConfirmDialog = false"
            :disabled="isTransferring"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="confirmTransfer"
            :loading="isTransferring"
          >
            Confirm Transfer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}

.sticky-card {
  position: sticky;
  top: 1rem;
}
</style>

