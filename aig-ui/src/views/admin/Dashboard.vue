<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminUsers } from '@/composables/useAdminUsers'
import { useAdminBank } from '@/composables/useAdminBank'
import { formatMoney } from '@/utils/format'
import UserGrowthChart from '@/components/charts/UserGrowthChart.vue'

const router = useRouter()
const { userList, isLoading: isLoadingUsers } = useAdminUsers()
const { bankCapital, isLoading: isLoadingBank } = useAdminBank()

const allUsers = computed(() => {
  return userList.value?.users || []
})
</script>

<template>
  <div>
    <h1 class="text-h4 mb-6">Admin Dashboard</h1>

    <v-row>
      <!-- Bank Capital -->
      <v-col cols="12" md="6">
        <v-card variant="outlined">
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-caption text-medium-emphasis mb-1">Bank Capital</div>
                <v-skeleton-loader v-if="isLoadingBank" type="heading" width="200" />
                <div v-else class="text-h4 font-weight-bold">
                  {{ bankCapital ? formatMoney(bankCapital.balance_cents) : '$0.00' }}
                </div>
              </div>
              <v-avatar color="success" size="56">
                <v-icon icon="mdi-bank" size="32" />
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Total Users -->
      <v-col cols="12" md="6">
        <v-card variant="outlined">
          <v-card-text>
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-caption text-medium-emphasis mb-1">Total Users</div>
                <v-skeleton-loader v-if="isLoadingUsers" type="heading" width="100" />
                <div v-else class="text-h4 font-weight-bold">
                  {{ userList?.total || 0 }}
                </div>
              </div>
              <v-avatar color="primary" size="56">
                <v-icon icon="mdi-account-multiple" size="32" />
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- User Growth Chart -->
    <v-card variant="outlined" class="mt-6">
      <v-card-title>
        <v-icon icon="mdi-chart-line" class="mr-2" />
        User Growth
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-skeleton-loader v-if="isLoadingUsers" type="image" height="300" />
        <UserGrowthChart v-else :users="allUsers" />
      </v-card-text>
    </v-card>

    <!-- Quick Actions -->
    <v-card variant="outlined" class="mt-6">
      <v-card-title>Quick Actions</v-card-title>
      <v-divider />
      <v-card-text>
        <v-row>
          <v-col cols="12" sm="6" md="3">
            <v-btn
              block
              variant="outlined"
              size="large"
              prepend-icon="mdi-account-multiple"
              @click="router.push('/admin/users')"
            >
              Manage Users
            </v-btn>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-btn
              block
              variant="outlined"
              size="large"
              prepend-icon="mdi-file-document-multiple"
              @click="router.push('/admin/logs')"
            >
              View Logs
            </v-btn>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-btn
              block
              variant="outlined"
              size="large"
              prepend-icon="mdi-cog"
              @click="router.push('/admin/settings')"
            >
              Settings
            </v-btn>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-btn
              block
              variant="outlined"
              size="large"
              prepend-icon="mdi-bank"
              @click="router.push('/admin/capital')"
            >
              Bank Capital
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Recent Users -->
    <v-card variant="outlined" class="mt-6">
      <v-card-title class="d-flex justify-space-between align-center">
        <span>Recent Users</span>
        <v-btn
          variant="text"
          color="primary"
          @click="router.push('/admin/users')"
        >
          View All
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-skeleton-loader v-if="isLoadingUsers" type="table-row@5" />

      <v-table v-else-if="userList && userList.users.length > 0">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in userList.users.slice(0, 5)" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.email || 'N/A' }}</td>
            <td>
              <v-chip size="small" variant="tonal">{{ user.role }}</v-chip>
            </td>
            <td>
              <v-chip
                :color="user.status === 'ENABLED' ? 'success' : 'error'"
                size="small"
                variant="tonal"
              >
                {{ user.status }}
              </v-chip>
            </td>
          </tr>
        </tbody>
      </v-table>

      <div v-else class="pa-8 text-center">
        <div class="text-body-2 text-medium-emphasis">No users found</div>
      </div>
    </v-card>
  </div>
</template>
