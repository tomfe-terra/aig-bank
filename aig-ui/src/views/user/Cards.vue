<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCards } from '@/composables/useCards'
import { useToast } from '@/composables/useToast'
import { getStatusColor, getErrorMessage } from '@/utils/format'
import EmptyState from '@/components/EmptyState.vue'
import CardBrandIcon from '@/components/CardBrandIcon.vue'
import type { CardReveal } from '@/types'

const router = useRouter()
const { cards, isLoading, revealCard } = useCards()
const { showToast } = useToast()

// Track revealed cards by card ID (fetched data)
const revealedCards = ref<Map<string, CardReveal>>(new Map())
// Track which cards are currently shown (visible state)
const visibleCards = ref<Set<string>>(new Set())
const revealingCardId = ref<string | null>(null)

// Confirm dialog state
const showConfirmDialog = ref(false)
const cardToReveal = ref<string | null>(null)

const isCardRevealed = (cardId: string) => visibleCards.value.has(cardId)
const getRevealedCard = (cardId: string) => revealedCards.value.get(cardId)
const hasCardData = (cardId: string) => revealedCards.value.has(cardId)

// Format card number with spaces (e.g., "4953 7231 0449 9682")
const formatCardNumber = (pan: string) => {
  return pan.replace(/(\d{4})(?=\d)/g, '$1 ')
}

const handleRevealCard = async (cardId: string) => {
  if (isCardRevealed(cardId)) {
    // Hide the card (but keep the data)
    visibleCards.value.delete(cardId)
    return
  }

  // If we already have the data, just show it without confirmation
  if (hasCardData(cardId)) {
    visibleCards.value.add(cardId)
    return
  }

  // First time: show confirmation dialog
  cardToReveal.value = cardId
  showConfirmDialog.value = true
}

const confirmReveal = async () => {
  if (!cardToReveal.value) return

  showConfirmDialog.value = false
  revealingCardId.value = cardToReveal.value

  try {
    const revealed = await revealCard(cardToReveal.value)
    revealedCards.value.set(cardToReveal.value, revealed)
    visibleCards.value.add(cardToReveal.value)
    showToast('Card details revealed. Keep them secure!', 'info')
  } catch (e: unknown) {
    console.error('Failed to reveal card:', e)
    showToast(getErrorMessage(e, 'Failed to reveal card details'), 'error')
  } finally {
    revealingCardId.value = null
    cardToReveal.value = null
  }
}

const cancelReveal = () => {
  showConfirmDialog.value = false
  cardToReveal.value = null
}

const navigateToRequestCard = () => {
  router.push('/user/cards/request')
}
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">My Cards</h1>
      <v-btn
        color="primary"
        prepend-icon="mdi-credit-card-plus"
        @click="navigateToRequestCard"
      >
        Order Card
      </v-btn>
    </div>

    <v-skeleton-loader v-if="isLoading" type="card@3" />
    
    <div v-else-if="!cards || cards.length === 0">
      <EmptyState
        icon="mdi-credit-card-off"
        title="No cards yet"
          message="Order a credit card to start making purchases."
          action-text="Order Card"
          @action="navigateToRequestCard"
        />
    </div>
    
    <div v-else>
      <v-alert v-if="cards.some(c => c.status === 'ACTIVE' && false)" type="info" variant="tonal" class="mb-4" style="display: none">
        <strong>Card Status:</strong> Newly ordered cards are in PENDING status and will be reviewed by our team. 
        Once approved, they will be activated and ready to use.
      </v-alert>
      
      <v-row>
        <v-col
          v-for="card in cards"
          :key="card.id"
          cols="12"
          md="6"
          lg="4"
        >
        <v-card variant="outlined" class="card-display">
          <v-card-text>
            <div class="d-flex justify-space-between align-center mb-4">
              <CardBrandIcon :brand="card.brand" :size="64" />
              <v-chip
                :color="getStatusColor(card.status)"
                size="small"
              >
                {{ card.status }}
              </v-chip>
            </div>
            
            <div class="text-h6 mb-2">{{ card.brand }}</div>
            
            <!-- Card Number (always in same format) -->
            <div class="text-h5 mb-4 font-mono">
              <template v-if="isCardRevealed(card.id)">
                {{ formatCardNumber(getRevealedCard(card.id)?.pan || '') }}
              </template>
              <template v-else>
                •••• •••• •••• {{ card.last4 }}
              </template>
            </div>
            
            <!-- Card Details Row -->
            <div class="d-flex justify-space-between text-caption text-medium-emphasis">
              <div>
                <div>EXPIRES</div>
                <div class="font-weight-bold">
                  <template v-if="isCardRevealed(card.id)">
                    {{ getRevealedCard(card.id)?.exp_month }}/{{ getRevealedCard(card.id)?.exp_year }}
                  </template>
                  <template v-else>
                    {{ card.exp_month }}/{{ card.exp_year }}
                  </template>
                </div>
              </div>
              <div v-if="isCardRevealed(card.id)">
                <div>CVV</div>
                <div class="font-weight-bold">{{ getRevealedCard(card.id)?.cvv }}</div>
              </div>
              <div v-else-if="card.is_expired" class="text-error">
                EXPIRED
              </div>
            </div>
          </v-card-text>
          
          <v-card-actions>
            <v-btn
              v-if="card.status === 'ACTIVE' && !card.is_expired"
              variant="text"
              size="small"
              :prepend-icon="isCardRevealed(card.id) ? 'mdi-eye-off' : 'mdi-eye'"
              @click="handleRevealCard(card.id)"
              :loading="revealingCardId === card.id"
            >
              {{ isCardRevealed(card.id) ? 'Hide Details' : 'Reveal Details' }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    </div>

    <!-- Confirm Reveal Dialog -->
    <v-dialog v-model="showConfirmDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6">
          Reveal Card Details?
        </v-card-title>
        <v-card-text>
          Are you sure you want to reveal the full card details including PAN and CVV?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="cancelReveal">Cancel</v-btn>
          <v-btn color="primary" variant="flat" @click="confirmReveal">Reveal</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.card-display {
  min-height: 200px;
}

.font-mono {
  font-family: 'Courier New', monospace;
}
</style>

