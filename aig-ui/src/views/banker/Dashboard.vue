<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useBankerRequests } from '@/composables/useBankerRequests'
import { formatDate, getStatusColor } from '@/utils/format'
import { RequestKind } from '@/types'
import RequestStatusChart from '@/components/charts/RequestStatusChart.vue'

const router = useRouter()
const { requests, isLoading } = useBankerRequests()

const allRequests = computed(() => {
  if (!requests.value) return []
  return requests.value.requests
})

const pendingRequests = computed(() => {
  if (!requests.value) return []
  return requests.value.requests.filter(req => req.status === 'PENDING')
})

const cardRequests = computed(() => {
  return pendingRequests.value.filter(req => req.kind === RequestKind.CREDIT_CARD)
})

const loanRequests = computed(() => {
  return pendingRequests.value.filter(req => req.kind === RequestKind.LOAN)
})

const viewAllRequests = () => {
  router.push('/banker/requests')
}
</script>

<template>
  <div>
    <h1 class="text-h4 mb-6">Banker Dashboard</h1>

    <v-row>
      <!-- Summary Cards -->
      <v-col cols="12" md="4">
        <v-card variant="outlined">
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-caption text-medium-emphasis mb-1">Pending Requests</div>
                <div class="text-h4 font-weight-bold">
                  {{ pendingRequests.length }}
                </div>
              </div>
              <v-avatar color="warning" size="56">
                <v-icon icon="mdi-clock-outline" size="32" />
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card variant="outlined">
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-caption text-medium-emphasis mb-1">Card Orders</div>
                <div class="text-h4 font-weight-bold">
                  {{ cardRequests.length }}
                </div>
              </div>
              <v-avatar color="primary" size="56">
                <v-icon icon="mdi-credit-card" size="32" />
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card variant="outlined">
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-caption text-medium-emphasis mb-1">Loan Requests</div>
                <div class="text-h4 font-weight-bold">
                  {{ loanRequests.length }}
                </div>
              </div>
              <v-avatar color="success" size="56">
                <v-icon icon="mdi-cash-multiple" size="32" />
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Request Status Overview Chart -->
    <v-card variant="outlined" class="mt-6">
      <v-card-title>
        <v-icon icon="mdi-chart-donut" class="mr-2" />
        Request Status Overview
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-skeleton-loader v-if="isLoading" type="image" />
        <RequestStatusChart v-else :requests="allRequests" />
      </v-card-text>
    </v-card>

    <!-- Recent Pending Requests -->
    <v-card variant="outlined" class="mt-6">
      <v-card-title class="d-flex justify-space-between align-center">
        <span>Recent Pending Requests</span>
        <v-btn
          variant="text"
          color="primary"
          @click="viewAllRequests"
        >
          View All
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-skeleton-loader v-if="isLoading" type="table-row@5" />

      <div v-else-if="pendingRequests.length === 0" class="pa-8 text-center">
        <v-icon icon="mdi-check-circle" size="64" color="success" class="mb-4" />
        <div class="text-h6 mb-2">All Caught Up!</div>
        <div class="text-body-2 text-medium-emphasis">
          There are no pending requests to review at the moment.
        </div>
      </div>

      <v-table v-else>
        <thead>
          <tr>
            <th>Type</th>
            <th>Details</th>
            <th>Requested By</th>
            <th>Date</th>
            <th>Status</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="request in pendingRequests.slice(0, 10)" :key="request.id">
            <td>
              <v-chip
                :color="request.kind === RequestKind.CREDIT_CARD ? 'primary' : 'success'"
                size="small"
                variant="tonal"
              >
                <v-icon
                  :icon="request.kind === RequestKind.CREDIT_CARD ? 'mdi-credit-card' : 'mdi-cash-multiple'"
                  size="x-small"
                  class="mr-1"
                />
                {{ request.kind === RequestKind.CREDIT_CARD ? 'Card' : 'Loan' }}
              </v-chip>
            </td>
            <td>
              <div v-if="request.kind === RequestKind.CREDIT_CARD" class="text-body-2">
                {{ request.payload.card_type }}
              </div>
              <div v-else class="text-body-2">
                ${{ (request.payload.principal_cents / 100).toFixed(2) }}
                <span class="text-caption text-medium-emphasis">
                  / {{ request.payload.repayment_cycles }} cycles
                </span>
              </div>
            </td>
            <td>
              <div v-if="request.requester">
                <div class="text-body-2 font-weight-medium">
                  {{ request.requester.first_name }} {{ request.requester.last_name }}
                </div>
                <div class="text-caption text-medium-emphasis">
                  @{{ request.requester.username }}
                </div>
                <div v-if="request.requester.email" class="text-caption text-medium-emphasis">
                  {{ request.requester.email }}
                </div>
              </div>
              <div v-else class="text-body-2 font-mono text-caption">
                {{ request.requested_by.substring(0, 8) }}...
              </div>
            </td>
            <td>
              <div class="text-body-2">{{ formatDate(request.created_at) }}</div>
            </td>
            <td>
              <v-chip
                :color="getStatusColor(request.status)"
                size="small"
                variant="tonal"
              >
                <v-icon icon="mdi-clock-outline" size="x-small" class="mr-1" />
                {{ request.status }}
              </v-chip>
            </td>
            <td class="text-right">
              <v-btn
                variant="text"
                color="primary"
                size="small"
                @click="router.push('/banker/requests')"
              >
                Review
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </div>
</template>
