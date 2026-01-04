<script setup lang="ts">
import { ref, computed } from 'vue'
import { useBankerCards } from '@/composables/useBankerCards'
import { useToast } from '@/composables/useToast'
import { formatDate, getStatusColor, getErrorMessage } from '@/utils/format'
import { CardStatus, type BankerCardView } from '@/types'
import EmptyState from '@/components/EmptyState.vue'
import CardBrandIcon from '@/components/CardBrandIcon.vue'

const { showToast } = useToast()
const { cardList, isLoading, cancel, isCanceling } = useBankerCards()

const showConfirmDialog = ref(false)
const selectedCard = ref<BankerCardView | null>(null)
const cancelingCardId = ref<string | null>(null)

const cards = computed(() => cardList.value?.cards || [])
const totalCards = computed(() => cardList.value?.total || 0)

const openConfirmDialog = (card: BankerCardView) => {
  selectedCard.value = card
  showConfirmDialog.value = true
}

const handleCancel = async () => {
  if (!selectedCard.value) return
  
  cancelingCardId.value = selectedCard.value.id
  try {
    await cancel(selectedCard.value.id)
    showToast('Card cancelled successfully!', 'success')
    showConfirmDialog.value = false
    selectedCard.value = null
  } catch (e: unknown) {
    console.error('Failed to cancel card:', e)
    showToast(getErrorMessage(e, 'Failed to cancel card'), 'error')
  } finally {
    cancelingCardId.value = null
  }
}

const closeDialog = () => {
  showConfirmDialog.value = false
  selectedCard.value = null
}
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4">Card Management</h1>
        <div class="text-caption text-medium-emphasis mt-1">
          <v-icon icon="mdi-credit-card-multiple" size="small" class="mr-1" />
          {{ totalCards }} total card{{ totalCards !== 1 ? 's' : '' }}
        </div>
      </div>
    </div>

    <v-skeleton-loader v-if="isLoading" type="table-row@5" />

    <EmptyState
      v-else-if="cards.length === 0"
      icon="mdi-credit-card-off-outline"
      title="No cards found"
      message="There are no credit cards in the system yet."
    />

    <v-card v-else variant="outlined">
      <v-table>
        <thead>
          <tr>
            <th>Card</th>
            <th>Cardholder</th>
            <th>Contact</th>
            <th>Status</th>
            <th>Issued</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="card in cards" :key="card.id">
            <td>
              <div class="d-flex align-center">
                <CardBrandIcon :brand="card.brand" :size="48" class="mr-3" />
                <div>
                  <div class="text-body-2 font-weight-medium">{{ card.brand }}</div>
                  <div class="text-caption text-medium-emphasis font-mono">•••• {{ card.last4 }}</div>
                </div>
              </div>
            </td>
            <td>
              <div>
                <div class="text-body-2 font-weight-medium">
                  {{ card.owner.first_name }} {{ card.owner.last_name }}
                </div>
                <div class="text-caption text-medium-emphasis">
                  @{{ card.owner.username }}
                </div>
              </div>
            </td>
            <td>
              <div v-if="card.owner.email" class="text-body-2">
                <v-icon icon="mdi-email-outline" size="x-small" class="mr-1" />
                {{ card.owner.email }}
              </div>
              <div v-else class="text-caption text-medium-emphasis">
                No email
              </div>
            </td>
            <td>
              <v-chip
                :color="getStatusColor(card.status)"
                size="small"
                variant="tonal"
              >
                <v-icon
                  :icon="card.status === CardStatus.ACTIVE ? 'mdi-check-circle' : card.status === CardStatus.CANCELLED ? 'mdi-cancel' : 'mdi-clock-outline'"
                  size="x-small"
                  class="mr-1"
                />
                {{ card.status }}
              </v-chip>
            </td>
            <td>
              <div class="text-body-2">{{ formatDate(card.created_at) }}</div>
            </td>
            <td class="text-right">
              <v-btn
                v-if="card.status === CardStatus.ACTIVE"
                icon="mdi-cancel"
                variant="text"
                color="error"
                size="small"
                @click="openConfirmDialog(card)"
                :loading="cancelingCardId === card.id"
                title="Cancel Card"
              />
              <span v-else class="text-caption text-medium-emphasis">
                {{ card.status === CardStatus.CANCELLED ? 'Cancelled' : 'Not Active' }}
              </span>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <!-- Confirmation Dialog -->
    <v-dialog v-model="showConfirmDialog" max-width="500" persistent scrim="rgba(0, 0, 0, 0.8)">
      <v-card v-if="selectedCard">
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">
            <v-icon icon="mdi-alert-circle" color="error" class="mr-2" />
            Confirm Card Cancellation
          </span>
          <v-btn icon="mdi-close" variant="text" @click="closeDialog" :disabled="isCanceling" />
        </v-card-title>

        <v-divider />

        <v-card-text class="pt-4">
          <v-alert type="error" variant="tonal" density="compact" class="mb-4">
            <strong>Irreversible Action:</strong> This will permanently cancel the credit card. 
            The cardholder will lose access immediately.
          </v-alert>

          <div class="mb-3">
            <div class="text-caption text-medium-emphasis">Card</div>
            <div class="d-flex align-center">
              <CardBrandIcon :brand="selectedCard.brand" :size="48" class="mr-3" />
              <div>
                <span class="text-body-1 font-weight-medium">{{ selectedCard.brand }}</span>
                <div class="text-body-2 font-mono">•••• {{ selectedCard.last4 }}</div>
              </div>
            </div>
          </div>

          <div class="mb-3">
            <div class="text-caption text-medium-emphasis">Cardholder</div>
            <div class="text-body-1">
              {{ selectedCard.owner.first_name }} {{ selectedCard.owner.last_name }}
            </div>
            <div class="text-body-2 text-medium-emphasis">
              @{{ selectedCard.owner.username }}
            </div>
          </div>

          <div v-if="selectedCard.owner.email" class="mb-3">
            <div class="text-caption text-medium-emphasis">Email</div>
            <div class="text-body-2">{{ selectedCard.owner.email }}</div>
          </div>

          <div class="text-body-2 text-medium-emphasis">
            Are you sure you want to cancel this card? The cardholder will be immediately unable to use it for transactions.
          </div>
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="closeDialog"
            :disabled="isCanceling"
          >
            No, Go Back
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            prepend-icon="mdi-cancel"
            @click="handleCancel"
            :loading="isCanceling"
          >
            Yes, Cancel Card
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

