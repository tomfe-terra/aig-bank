<script setup lang="ts">
import { ref, computed } from 'vue'
import { useBankerRequests } from '@/composables/useBankerRequests'
import { useToast } from '@/composables/useToast'
import { formatDate, formatMoney, getStatusColor, getErrorMessage } from '@/utils/format'
import { RequestKind, type Request } from '@/types'

const { showToast } = useToast()
const filterKind = ref<string | undefined>(undefined)
const { requests, isLoading, approve, reject, isApproving, isRejecting } = useBankerRequests(filterKind.value)

const showApproveDialog = ref(false)
const showRejectDialog = ref(false)
const selectedRequest = ref<Request | null>(null)
const rejectReason = ref('')

const filteredRequests = computed(() => {
  if (!requests.value) return []
  let result = requests.value.requests
  
  if (filterKind.value) {
    result = result.filter(req => req.kind === filterKind.value)
  }
  
  return result
})

const openApproveDialog = (request: Request) => {
  selectedRequest.value = request
  showApproveDialog.value = true
}

const openRejectDialog = (request: Request) => {
  selectedRequest.value = request
  rejectReason.value = ''
  showRejectDialog.value = true
}

const handleApprove = async () => {
  if (!selectedRequest.value) return
  
  try {
    await approve(selectedRequest.value.id)
    showToast('Request approved successfully!', 'success')
    showApproveDialog.value = false
    selectedRequest.value = null
  } catch (e: unknown) {
    console.error('Failed to approve request:', e)
    showToast(getErrorMessage(e, 'Failed to approve request'), 'error')
  }
}

const handleReject = async () => {
  if (!selectedRequest.value) return
  
  try {
    await reject({ requestId: selectedRequest.value.id, reason: rejectReason.value || undefined })
    showToast('Request rejected.', 'info')
    showRejectDialog.value = false
    selectedRequest.value = null
    rejectReason.value = ''
  } catch (e: unknown) {
    console.error('Failed to reject request:', e)
    showToast(getErrorMessage(e, 'Failed to reject request'), 'error')
  }
}

const getRequestDetails = (request: Request): string => {
  if (request.kind === RequestKind.CREDIT_CARD) {
    return request.payload.card_type || 'Unknown'
  } else {
    const amount = formatMoney(request.payload.principal_cents || 0)
    const cycles = request.payload.repayment_cycles || 0
    return `${amount} / ${cycles} cycles`
  }
}
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">Request Management</h1>
      <v-btn-toggle
        v-model="filterKind"
        variant="outlined"
        divided
        mandatory
      >
        <v-btn value="">All</v-btn>
        <v-btn :value="RequestKind.CREDIT_CARD">Cards</v-btn>
        <v-btn :value="RequestKind.LOAN">Loans</v-btn>
      </v-btn-toggle>
    </div>

    <v-skeleton-loader v-if="isLoading" type="table-row@5" />

    <div v-else-if="filteredRequests.length === 0" class="text-center pa-12">
      <v-icon icon="mdi-check-circle" size="64" color="success" class="mb-4" />
      <div class="text-h6 mb-2">No Requests Found</div>
      <div class="text-body-2 text-medium-emphasis">
        There are no {{ filterKind ? (filterKind === RequestKind.CREDIT_CARD ? 'card' : 'loan') : '' }} requests to review.
      </div>
    </div>

    <v-card v-else variant="outlined">
      <v-table>
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
          <tr v-for="request in filteredRequests" :key="request.id">
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
              <div class="text-body-2">{{ getRequestDetails(request) }}</div>
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
                <v-icon
                  :icon="request.status === 'PENDING' ? 'mdi-clock-outline' : request.status === 'APPROVED' ? 'mdi-check-circle' : 'mdi-close-circle'"
                  size="x-small"
                  class="mr-1"
                />
                {{ request.status }}
              </v-chip>
            </td>
            <td class="text-right">
              <v-btn
                v-if="request.status === 'PENDING'"
                icon="mdi-check"
                variant="text"
                color="success"
                size="small"
                @click="openApproveDialog(request)"
                title="Approve"
              />
              <v-btn
                v-if="request.status === 'PENDING'"
                icon="mdi-close"
                variant="text"
                color="error"
                size="small"
                @click="openRejectDialog(request)"
                title="Reject"
              />
              <span v-if="request.status !== 'PENDING'" class="text-caption text-medium-emphasis">
                {{ request.status === 'APPROVED' ? 'Approved' : 'Rejected' }}
              </span>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <!-- Approve Dialog -->
    <v-dialog v-model="showApproveDialog" max-width="450" persistent scrim="rgba(0, 0, 0, 0.8)">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">Approve Request</span>
          <v-btn icon="mdi-close" variant="text" @click="showApproveDialog = false" :disabled="isApproving" />
        </v-card-title>

        <v-divider />

        <v-card-text class="pt-4">
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">
            <strong>Confirm Approval:</strong> This action will approve the request and create the corresponding resource.
          </v-alert>

          <div v-if="selectedRequest">
            <div class="mb-3">
              <div class="text-caption text-medium-emphasis">Request Type</div>
              <div class="text-body-1 font-weight-medium">
                {{ selectedRequest.kind === RequestKind.CREDIT_CARD ? 'Credit Card' : 'Loan' }}
              </div>
            </div>

            <div class="mb-3">
              <div class="text-caption text-medium-emphasis">Details</div>
              <div class="text-body-1">{{ getRequestDetails(selectedRequest) }}</div>
            </div>

            <div v-if="selectedRequest.requester">
              <div class="text-caption text-medium-emphasis">Requested By</div>
              <div class="text-body-1 font-weight-medium">
                {{ selectedRequest.requester.first_name }} {{ selectedRequest.requester.last_name }}
              </div>
              <div class="text-body-2 text-medium-emphasis">
                @{{ selectedRequest.requester.username }}
              </div>
              <div v-if="selectedRequest.requester.email" class="text-body-2 text-medium-emphasis">
                {{ selectedRequest.requester.email }}
              </div>
            </div>
            <div v-else>
              <div class="text-caption text-medium-emphasis">Requested By</div>
              <div class="text-body-2 font-mono">{{ selectedRequest.requested_by }}</div>
            </div>
          </div>
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="showApproveDialog = false"
            :disabled="isApproving"
          >
            Cancel
          </v-btn>
          <v-btn
            color="success"
            variant="flat"
            @click="handleApprove"
            :loading="isApproving"
          >
            Approve Request
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Reject Dialog -->
    <v-dialog v-model="showRejectDialog" max-width="450" persistent scrim="rgba(0, 0, 0, 0.8)">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">Reject Request</span>
          <v-btn icon="mdi-close" variant="text" @click="showRejectDialog = false" :disabled="isRejecting" />
        </v-card-title>

        <v-divider />

        <v-card-text class="pt-4">
          <v-alert type="warning" variant="tonal" density="compact" class="mb-4">
            <strong>Confirm Rejection:</strong> This action will reject the request. You can optionally provide a reason.
          </v-alert>

          <div v-if="selectedRequest" class="mb-4">
            <div class="mb-3">
              <div class="text-caption text-medium-emphasis">Request Type</div>
              <div class="text-body-1 font-weight-medium">
                {{ selectedRequest.kind === RequestKind.CREDIT_CARD ? 'Credit Card' : 'Loan' }}
              </div>
            </div>

            <div class="mb-3">
              <div class="text-caption text-medium-emphasis">Details</div>
              <div class="text-body-1">{{ getRequestDetails(selectedRequest) }}</div>
            </div>

            <div v-if="selectedRequest.requester" class="mb-3">
              <div class="text-caption text-medium-emphasis">Requested By</div>
              <div class="text-body-1 font-weight-medium">
                {{ selectedRequest.requester.first_name }} {{ selectedRequest.requester.last_name }}
              </div>
              <div class="text-body-2 text-medium-emphasis">
                @{{ selectedRequest.requester.username }}
              </div>
              <div v-if="selectedRequest.requester.email" class="text-body-2 text-medium-emphasis">
                {{ selectedRequest.requester.email }}
              </div>
            </div>
          </div>

          <v-textarea
            v-model="rejectReason"
            label="Rejection Reason (Optional)"
            variant="outlined"
            rows="3"
            :disabled="isRejecting"
            hint="Provide a reason for rejection"
            persistent-hint
          />
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="showRejectDialog = false"
            :disabled="isRejecting"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            @click="handleReject"
            :loading="isRejecting"
          >
            Reject Request
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

