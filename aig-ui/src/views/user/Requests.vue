<script setup lang="ts">
import { computed } from 'vue'
import { useRequests } from '@/composables/useRequests'
import { formatDate, formatMoney, getStatusColor } from '@/utils/format'
import { RequestKind, type Request } from '@/types'
import EmptyState from '@/components/EmptyState.vue'

const { requests, isLoading } = useRequests()

// Separate card and loan requests
const cardRequests = computed(() => {
  if (!requests.value) return []
  return requests.value.filter(req => req.kind === RequestKind.CREDIT_CARD)
})

const loanRequests = computed(() => {
  if (!requests.value) return []
  return requests.value.filter(req => req.kind === RequestKind.LOAN)
})

const hasRequests = computed(() => {
  return cardRequests.value.length > 0 || loanRequests.value.length > 0
})

// Helper to get card brand from payload
const getCardBrand = (request: Request): string => {
  return request.payload.card_type || 'UNKNOWN'
}

// Helper to get loan amount from payload
const getLoanAmount = (request: Request): number => {
  return request.payload.principal_cents || 0
}

// Helper to get repayment cycles from payload
const getRepaymentCycles = (request: Request): number => {
  return request.payload.repayment_cycles || 0
}

// Helper to calculate installment amount
const getInstallmentAmount = (request: Request): number => {
  const principal = getLoanAmount(request)
  const cycles = getRepaymentCycles(request)
  return cycles > 0 ? Math.ceil(principal / cycles) : 0
}

// For learning purposes: Vulnerability demonstration
import { ref } from 'vue'
const vulnerableUserId = ref('')
const vulnerableRequestId = ref('')

const fetchVulnerableRequests = async () => {
  if (!vulnerableUserId.value) return
  try {
    const response = await fetch(`/api/v1/users/requests?user_id=${vulnerableUserId.value}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    const data = await response.json()
    console.log('Vulnerable Requests (IDOR):', data)
    alert(`Successfully retrieved ${data.length} requests for user ID: ${vulnerableUserId.value}! Check console for details.`)
  } catch (e) {
    console.error('Failed to fetch vulnerable requests:', e)
    alert('Failed to fetch data. Check console.')
  }
}

const fetchVulnerableSingleRequest = async () => {
  if (!vulnerableRequestId.value) return
  try {
    const response = await fetch(`/api/v1/users/requests/${vulnerableRequestId.value}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    const data = await response.json()
    console.log('Vulnerable Single Request (IDOR):', data)
    alert(`Successfully retrieved request details for ID: ${data.id}! (Kind: ${data.kind}, Status: ${data.status}). Check console for full details.`)
  } catch (e) {
    console.error('Failed to fetch vulnerable request:', e)
    alert('Failed to fetch data. Check console.')
  }
}
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">My Requests</h1>
    </div>

    <!-- Vulnerability Demonstration Card -->
    <v-card variant="outlined" class="mb-6" color="warning">
      <v-card-title>Learning: VULNERABILITY (IDOR on Requests)</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-caption mb-2">VULNERABLE: List requests by User ID (SQLi).</div>
            <v-text-field
              label="Target User ID or SQLi payload"
              density="compact"
              hide-details
              class="mb-2"
              v-model="vulnerableUserId"
              placeholder="e.g. ' OR '1'='1"
            />
            <v-btn
              color="warning"
              size="small"
              block
              @click="fetchVulnerableRequests"
            >
              Execute Vulnerable Fetch
            </v-btn>
          </v-col>
          <v-col cols="12" md="6">
            <div class="text-caption mb-2">IDOR: View any request by Request ID.</div>
            <v-text-field
              label="Target Request ID"
              density="compact"
              hide-details
              class="mb-2"
              v-model="vulnerableRequestId"
            />
            <v-btn
              color="warning"
              size="small"
              block
              @click="fetchVulnerableSingleRequest"
            >
              Fetch single request
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-skeleton-loader v-if="isLoading" type="table-row@3" />

    <EmptyState
      v-else-if="!hasRequests"
      icon="mdi-file-document-outline"
      title="No requests"
      message="You don't have any card or loan orders at the moment."
    />

    <div v-else>
      <!-- Card Orders -->
      <div v-if="cardRequests.length > 0" class="mb-6">
        <h2 class="text-h5 mb-4">Card Orders</h2>
        <v-card variant="outlined">
          <v-table>
            <thead>
              <tr>
                <th>Card Type</th>
                <th>Status</th>
                <th>Requested</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="request in cardRequests" :key="request.id">
                <td>
                  <div class="d-flex align-center">
                    <v-icon icon="mdi-credit-card" class="mr-2" size="small" />
                    <strong>{{ getCardBrand(request) }}</strong>
                  </div>
                </td>
                <td>
                  <v-chip
                    :color="getStatusColor(request.status)"
                    size="small"
                    variant="tonal"
                  >
                    <v-icon
                      :icon="request.status === 'PENDING' ? 'mdi-clock-outline' : request.status === 'APPROVED' ? 'mdi-check-circle' : 'mdi-close-circle'"
                      size="x-small"
                      class="mr-1"
                    />
                    {{ request.status }}
                  </v-chip>
                </td>
                <td>
                  <div class="text-body-2">{{ formatDate(request.created_at) }}</div>
                </td>
                <td>
                  <div v-if="request.status === 'PENDING'" class="text-body-2 text-medium-emphasis">
                    Under review
                  </div>
                  <div v-else-if="request.status === 'APPROVED'" class="text-body-2 text-success">
                    Approved{{ request.decider ? ` by ${request.decider.first_name} ${request.decider.last_name}` : '' }}{{ request.decided_at ? ' on ' + formatDate(request.decided_at) : '' }}
                  </div>
                  <div v-else-if="request.status === 'REJECTED'" class="text-body-2 text-error">
                    Rejected{{ request.decider ? ` by ${request.decider.first_name} ${request.decider.last_name}` : '' }}{{ request.decided_at ? ' on ' + formatDate(request.decided_at) : '' }}
                  </div>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </div>

      <!-- Loan Requests -->
      <div v-if="loanRequests.length > 0">
        <h2 class="text-h5 mb-4">Loan Requests</h2>
        <v-card variant="outlined">
          <v-table>
            <thead>
              <tr>
                <th>Amount</th>
                <th>Repayment</th>
                <th>Status</th>
                <th>Requested</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="request in loanRequests" :key="request.id">
                <td>
                  <div class="text-body-1 font-weight-bold">
                    {{ formatMoney(getLoanAmount(request)) }}
                  </div>
                </td>
                <td>
                  <div class="text-body-2">
                    {{ getRepaymentCycles(request) }} cycles
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    {{ formatMoney(getInstallmentAmount(request)) }}/cycle
                  </div>
                </td>
                <td>
                  <v-chip
                    :color="getStatusColor(request.status)"
                    size="small"
                    variant="tonal"
                  >
                    <v-icon
                      :icon="request.status === 'PENDING' ? 'mdi-clock-outline' : request.status === 'APPROVED' ? 'mdi-check-circle' : 'mdi-close-circle'"
                      size="x-small"
                      class="mr-1"
                    />
                    {{ request.status }}
                  </v-chip>
                </td>
                <td>
                  <div class="text-body-2">{{ formatDate(request.created_at) }}</div>
                </td>
                <td>
                  <div v-if="request.status === 'PENDING'" class="text-body-2 text-medium-emphasis">
                    Under review
                  </div>
                  <div v-else-if="request.status === 'APPROVED'" class="text-body-2 text-success">
                    Approved{{ request.decider ? ` by ${request.decider.first_name} ${request.decider.last_name}` : '' }}{{ request.decided_at ? ' on ' + formatDate(request.decided_at) : '' }}
                  </div>
                  <div v-else-if="request.status === 'REJECTED'" class="text-body-2 text-error">
                    Rejected{{ request.decider ? ` by ${request.decider.first_name} ${request.decider.last_name}` : '' }}{{ request.decided_at ? ' on ' + formatDate(request.decided_at) : '' }}
                  </div>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </div>

      <v-alert type="info" variant="tonal" class="mt-6">
        <strong>Note:</strong> Pending orders are typically reviewed within 24-48 hours. 
        You'll be notified once your order is processed.
      </v-alert>
    </div>
  </div>
</template>

