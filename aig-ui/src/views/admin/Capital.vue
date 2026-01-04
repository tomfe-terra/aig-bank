<script setup lang="ts">
import { useAdminBank } from '@/composables/useAdminBank'
import { formatMoney, formatDate } from '@/utils/format'

const { bankCapital, isLoading, refetch } = useAdminBank()
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">Bank Capital</h1>
      <v-btn
        prepend-icon="mdi-refresh"
        variant="outlined"
        @click="refetch"
        :loading="isLoading"
      >
        Refresh
      </v-btn>
    </div>

    <v-skeleton-loader v-if="isLoading" type="card" />

    <v-card v-else-if="bankCapital" variant="outlined">
      <v-card-text class="pa-8">
        <div class="text-center mb-6">
          <v-icon icon="mdi-bank" size="80" color="success" class="mb-4" />
          <div class="text-h3 font-weight-bold mb-2">
            {{ formatMoney(bankCapital.balance_cents) }}
          </div>
          <div class="text-body-1 text-medium-emphasis">
            Current Bank Capital Balance
          </div>
        </div>

        <v-divider class="my-6" />

        <v-row>
          <v-col cols="12" md="4">
            <v-card variant="tonal" color="primary">
              <v-card-text>
                <div class="text-caption text-medium-emphasis mb-1">Account Number</div>
                <div class="text-h6 font-mono">{{ bankCapital.account_number }}</div>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card variant="tonal" color="success">
              <v-card-text>
                <div class="text-caption text-medium-emphasis mb-1">Balance (Dollars)</div>
                <div class="text-h6">${{ bankCapital.balance_dollars.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</div>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card variant="tonal" color="info">
              <v-card-text>
                <div class="text-caption text-medium-emphasis mb-1">Last Updated</div>
                <div class="text-h6">
                  {{ bankCapital.updated_at ? formatDate(bankCapital.updated_at) : 'Never' }}
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <v-alert type="info" variant="tonal" class="mt-6">
          <strong>Note:</strong> The bank capital represents the total funds available in the bank's reserve account.
          This balance is used to fund loans and manage the bank's operations.
        </v-alert>
      </v-card-text>
    </v-card>

    <div v-else class="text-center pa-12">
      <v-icon icon="mdi-alert-circle" size="64" color="error" class="mb-4" />
      <div class="text-h6 mb-2">Failed to Load Bank Capital</div>
      <div class="text-body-2 text-medium-emphasis">
        Unable to retrieve bank capital information
      </div>
    </div>
  </div>
</template>

