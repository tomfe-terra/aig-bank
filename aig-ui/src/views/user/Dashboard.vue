<script setup lang="ts">
import { useAuth } from '@/composables/useAuth'
import { useTransactions } from '@/composables/useTransactions'
import { useCards } from '@/composables/useCards'
import { useLoans } from '@/composables/useLoans'
import { formatMoney, formatDate, getTransactionIcon, getTransactionColor } from '@/utils/format'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import LoanProgressChart from '@/components/charts/LoanProgressChart.vue'
import CardsByBrandChart from '@/components/charts/CardsByBrandChart.vue'
import BalanceHistoryChart from '@/components/charts/BalanceHistoryChart.vue'

const router = useRouter()
const { user, account, refreshProfile } = useAuth()
const { transactions, isLoading: isLoadingTransactions, limit } = useTransactions()
const { cards, isLoading: isLoadingCards } = useCards()
const { loans, isLoading: isLoadingLoans } = useLoans()

// Increase transaction limit for balance history chart
limit.value = 200

// Refresh profile data when dashboard loads
onMounted(async () => {
  try {
    await refreshProfile()
  } catch (e) {
    console.error('Failed to refresh profile on dashboard:', e)
  }
})

const recentTransactions = computed(() => {
  return transactions.value?.transactions.slice(0, 5) || []
})

const activeCardsCount = computed(() => {
  return cards.value?.filter(c => c.status === 'ACTIVE').length || 0
})

const activeLoansCount = computed(() => {
  return loans.value?.filter(l => l.status === 'ACTIVE' || l.status === 'PENDING').length || 0
})

// For learning purposes: Vulnerability demonstration
const vulnerableUserId = ref('')
const fetchVulnerableData = async () => {
  if (!vulnerableUserId.value) return
  try {
    // Calling the existing /me endpoint but with the new IDOR parameter
    const response = await fetch(`/api/v1/users/auth/me?user_id=${vulnerableUserId.value}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    const data = await response.json()
    console.log('Vulnerable Data Retrieved (IDOR from /me):', data)
    alert(`Successfully retrieved data for user ${data.user.username} (ID: ${data.user.id}) via IDOR on /me endpoint! Check console for full profile.`)
  } catch (e) {
    console.error('Failed to fetch vulnerable data:', e)
    alert('Failed to fetch data. Check console.')
  }
}
</script>

<template>
  <div>
    <!-- Welcome Header -->
    <h1 class="text-h4 mb-6">
      Welcome back, {{ user?.first_name }}!
    </h1>

    <!-- Account Balance Card -->
    <v-card variant="outlined" class="mb-6">
      <v-card-title class="text-h5">
        <v-icon icon="mdi-wallet" class="mr-2" />
        Account Balance
      </v-card-title>
      
      <v-card-text>
        <v-skeleton-loader v-if="!account" type="heading" />
        <div v-else>
          <div class="text-h3 mb-4">
            {{ formatMoney(account.balance_cents) }}
          </div>
          <div class="text-caption text-medium-emphasis mb-4">
            Account: {{ account.number }}
          </div>
          <div class="d-flex gap-2">
            <v-btn
              color="primary"
              prepend-icon="mdi-bank-transfer"
              @click="router.push('/user/transfer')"
            >
              Transfer Money
            </v-btn>
            <v-btn
              color="primary"
              variant="outlined"
              prepend-icon="mdi-credit-card-plus"
              @click="router.push('/user/cards')"
            >
              Order Card
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <v-row>
      <!-- Recent Transactions Card -->
      <v-col cols="12" md="8">
        <v-card variant="outlined">
          <v-card-title class="d-flex justify-space-between align-center">
            <span>
              <v-icon icon="mdi-format-list-bulleted" class="mr-2" />
              Recent Transactions
            </span>
            <v-btn
              variant="text"
              size="small"
              @click="router.push('/user/transactions')"
            >
              View All
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <v-skeleton-loader v-if="isLoadingTransactions" type="list-item@5" />
            
            <v-list v-else-if="recentTransactions.length > 0" lines="two">
              <v-list-item
                v-for="transaction in recentTransactions"
                :key="transaction.id ?? transaction.created_at"
              >
                <template #prepend>
                  <v-icon
                    :icon="getTransactionIcon(transaction.type)"
                    :color="getTransactionColor(transaction.type, transaction.amount_cents)"
                  />
                </template>
                
                <v-list-item-title>
                  {{ transaction.type.replace(/_/g, ' ') }}
                </v-list-item-title>
                
                <v-list-item-subtitle>
                  {{ formatDate(transaction.created_at) }}
                </v-list-item-subtitle>
                
                <template #append>
                  <span
                    :class="transaction.amount_cents > 0 ? 'text-success' : 'text-error'"
                    class="font-weight-bold"
                  >
                    {{ formatMoney(transaction.amount_cents) }}
                  </span>
                </template>
              </v-list-item>
            </v-list>
            
            <div v-else class="text-center pa-4 text-medium-emphasis">
              No transactions yet
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Summary Cards -->
      <v-col cols="12" md="4">
        <v-card variant="outlined" class="mb-4" color="warning">
          <v-card-title>Learning: VULNERABILITY</v-card-title>
          <v-card-text>
            <div class="text-caption mb-2">
              The <code>/users/auth/me</code> endpoint now has an IDOR vulnerability. You can fetch any user's profile by ID.
            </div>
            <v-text-field
              label="User ID (IDOR test)"
              density="compact"
              hide-details
              class="mb-2"
              v-model="vulnerableUserId"
            />
            <v-btn
              color="warning"
              size="small"
              block
              @click="fetchVulnerableData"
            >
              Fetch other user's data
            </v-btn>
          </v-card-text>
        </v-card>

        <v-card variant="outlined" class="mb-4">
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-medium-emphasis">Active Cards</div>
                <v-skeleton-loader v-if="isLoadingCards" type="heading" />
                <div v-else class="text-h4">{{ activeCardsCount }}</div>
              </div>
              <v-icon icon="mdi-credit-card-multiple" size="48" color="primary" />
            </div>
          </v-card-text>
        </v-card>

        <v-card variant="outlined">
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-medium-emphasis">Active Loans</div>
                <v-skeleton-loader v-if="isLoadingLoans" type="heading" />
                <div v-else class="text-h4">{{ activeLoansCount }}</div>
              </div>
              <v-icon icon="mdi-cash-multiple" size="48" color="primary" />
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Balance History Chart -->
    <v-card variant="outlined" class="mt-6">
      <v-card-title>
        <v-icon icon="mdi-chart-line" class="mr-2" />
        Account Balance History
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-skeleton-loader v-if="isLoadingTransactions || !account" type="image" height="300" />
        <BalanceHistoryChart 
          v-else 
          :transactions="transactions?.transactions" 
          :current-balance="account.balance_cents"
        />
      </v-card-text>
    </v-card>

    <!-- Charts Row -->
    <v-row class="mt-6">
      <!-- Loan Progress Chart -->
      <v-col cols="12" md="8">
        <v-card variant="outlined">
          <v-card-title>
            <v-icon icon="mdi-chart-bar" class="mr-2" />
            Loan Repayment Progress
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-skeleton-loader v-if="isLoadingLoans" type="list-item@3" />
            <LoanProgressChart v-else :loans="loans" />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Cards by Brand Chart -->
      <v-col cols="12" md="4">
        <v-card variant="outlined">
          <v-card-title>
            <v-icon icon="mdi-chart-donut" class="mr-2" />
            Active Cards by Brand
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-skeleton-loader v-if="isLoadingCards" type="image" />
            <CardsByBrandChart v-else :cards="cards" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}
</style>
