<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCards } from '@/composables/useCards'
import { useToast } from '@/composables/useToast'
import { CardBrand } from '@/types'
import { getErrorMessage } from '@/utils/format'
import CardBrandIcon from '@/components/CardBrandIcon.vue'

const router = useRouter()
const { requestCard, isRequestingCard } = useCards()
const { success, error } = useToast()

const selectedCardBrand = ref<CardBrand>(CardBrand.VISA)

const cardBrands = [
  { 
    title: 'Visa', 
    value: CardBrand.VISA, 
    icon: 'mdi-credit-card-chip',
    color: '#1A1F71',
    description: 'Accepted worldwide with excellent security features'
  },
  { 
    title: 'Mastercard', 
    value: CardBrand.MASTERCARD, 
    icon: 'mdi-credit-card-wireless',
    color: '#EB001B',
    description: 'Global acceptance with premium benefits'
  },
  { 
    title: 'American Express', 
    value: CardBrand.AMERICAN_EXPRESS, 
    icon: 'mdi-credit-card-marker',
    color: '#006FCF',
    description: 'Premium card with exclusive rewards'
  },
  { 
    title: 'Discover', 
    value: CardBrand.DISCOVER, 
    icon: 'mdi-credit-card-search',
    color: '#FF6000',
    description: 'Cashback rewards and no annual fee'
  },
]

const selectBrand = (brand: CardBrand) => {
  selectedCardBrand.value = brand
}

const handleRequestCard = async () => {
  try {
    await requestCard({ card_type: selectedCardBrand.value })
    success('Card order submitted successfully! Your card will be reviewed and activated soon.')
    router.push('/user/cards')
  } catch (e: unknown) {
    console.error('Failed to order card:', e)
    error(getErrorMessage(e, 'Failed to order card'))
  }
}

const handleCancel = () => {
  router.back()
}
</script>

<template>
  <div>
    <div class="mb-6">
      <v-btn
        variant="text"
        prepend-icon="mdi-arrow-left"
        @click="handleCancel"
        :disabled="isRequestingCard"
      >
        Back to Cards
      </v-btn>
    </div>

    <h1 class="text-h4 mb-2">Order New Card</h1>
    <p class="text-body-1 text-medium-emphasis mb-6">
      Choose your preferred card brand. Your card will be reviewed and activated within 24-48 hours.
    </p>

    <v-row>
      <v-col cols="12" md="8" lg="6">
        <v-card variant="outlined">
          <v-card-title>Select Card Brand</v-card-title>
          
          <v-card-text>
            <v-alert type="info" variant="tonal" class="mb-6">
              <strong>Note:</strong> All our cards come with 0% interest, fraud protection, and worldwide acceptance.
            </v-alert>

            <p class="text-subtitle-2 mb-4">Choose your card brand:</p>

            <v-row>
              <v-col
                v-for="brand in cardBrands"
                :key="brand.value"
                cols="6"
                sm="6"
                md="6"
              >
                <v-card
                  variant="outlined"
                  class="card-brand-option text-center pa-6"
                  :class="{ 'selected': selectedCardBrand === brand.value }"
                  @click="selectBrand(brand.value)"
                  hover
                >
                  <div class="mb-3">
                    <CardBrandIcon :brand="brand.value" :size="80" />
                  </div>
                  <div class="text-h6 mb-2">{{ brand.title }}</div>
                  <div class="text-caption text-medium-emphasis">
                    {{ brand.description }}
                  </div>
                  <v-icon
                    v-if="selectedCardBrand === brand.value"
                    icon="mdi-check-circle"
                    color="primary"
                    size="small"
                    class="selected-icon"
                  />
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions class="px-4 pb-4">
            <v-spacer />
            <v-btn
              variant="outlined"
              @click="handleCancel"
              :disabled="isRequestingCard"
            >
              Cancel
            </v-btn>
            <v-btn
              color="primary"
              @click="handleRequestCard"
              :loading="isRequestingCard"
              prepend-icon="mdi-credit-card-plus"
            >
              Order Card
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="4" lg="6">
        <v-card variant="outlined">
          <v-card-title>Card Benefits</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-shield-check">
                <v-list-item-title>Fraud Protection</v-list-item-title>
                <v-list-item-subtitle>24/7 monitoring and alerts</v-list-item-subtitle>
              </v-list-item>
              
              <v-list-item prepend-icon="mdi-earth">
                <v-list-item-title>Worldwide Acceptance</v-list-item-title>
                <v-list-item-subtitle>Use anywhere cards are accepted</v-list-item-subtitle>
              </v-list-item>
              
              <v-list-item prepend-icon="mdi-percent">
                <v-list-item-title>0% Interest</v-list-item-title>
                <v-list-item-subtitle>No interest charges ever</v-list-item-subtitle>
              </v-list-item>
              
              <v-list-item prepend-icon="mdi-cash-remove">
                <v-list-item-title>No Annual Fee</v-list-item-title>
                <v-list-item-subtitle>Free to use and maintain</v-list-item-subtitle>
              </v-list-item>
              
              <v-list-item prepend-icon="mdi-lock">
                <v-list-item-title>Secure Transactions</v-list-item-title>
                <v-list-item-subtitle>EMV chip and contactless payment</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.card-brand-option {
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.card-brand-option:hover {
  border-color: rgb(var(--v-theme-primary));
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-brand-option.selected {
  border-color: rgb(var(--v-theme-primary));
  border-width: 2px;
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.selected-icon {
  position: absolute;
  top: 8px;
  right: 8px;
}
</style>

