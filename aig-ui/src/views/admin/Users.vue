<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useAdminUsers } from '@/composables/useAdminUsers'
import { useToast } from '@/composables/useToast'
import { formatDate, getErrorMessage } from '@/utils/format'
import { UserRole, type UserListItem } from '@/types'
import { getUserAvatar } from '@/api/admin'

const { showToast } = useToast()
const { userList, isLoading, changeUserRole, isUpdatingRole, unlockUserAccount, isUnlocking } = useAdminUsers()

// Avatar URLs cache
const avatarUrls = ref<Record<string, string>>({})

// Load avatars for users who have them
const loadAvatars = async () => {
  if (!userList.value?.users) return
  
  for (const user of userList.value.users) {
    if (user.has_avatar && !avatarUrls.value[user.id]) {
      try {
        const blob = await getUserAvatar(user.id)
        avatarUrls.value[user.id] = URL.createObjectURL(blob)
      } catch (e) {
        console.error(`Failed to load avatar for user ${user.id}:`, e)
      }
    }
  }
}

// Watch for user list changes and load avatars
watch(() => userList.value?.users, () => {
  loadAvatars()
}, { immediate: true })

// Cleanup blob URLs on unmount
onUnmounted(() => {
  Object.values(avatarUrls.value).forEach(url => URL.revokeObjectURL(url))
})

const showRoleDialog = ref(false)
const selectedUser = ref<UserListItem | null>(null)
const newRole = ref<UserRole>(UserRole.USER)

const openRoleDialog = (user: UserListItem) => {
  selectedUser.value = user
  newRole.value = user.role
  showRoleDialog.value = true
}

const handleChangeRole = async () => {
  if (!selectedUser.value) return
  
  try {
    await changeUserRole({
      userId: selectedUser.value.id,
      data: { role: newRole.value },
    })
    showToast('User role updated successfully!', 'success')
    showRoleDialog.value = false
    selectedUser.value = null
  } catch (e: unknown) {
    console.error('Failed to update user role:', e)
    showToast(getErrorMessage(e, 'Failed to update user role'), 'error')
  }
}

const getRoleColor = (role: UserRole): string => {
  switch (role) {
    case UserRole.ADMIN:
      return 'error'
    case UserRole.BANKER:
      return 'warning'
    case UserRole.USER:
    default:
      return 'primary'
  }
}

const handleUnlockUser = async (userId: string, username: string) => {
  try {
    await unlockUserAccount(userId)
    showToast(`User ${username} has been unlocked successfully!`, 'success')
  } catch (e: unknown) {
    console.error('Failed to unlock user:', e)
    showToast(getErrorMessage(e, 'Failed to unlock user'), 'error')
  }
}
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">User Management</h1>
    </div>

    <v-skeleton-loader v-if="isLoading" type="table-row@10" />

    <div v-else-if="!userList || userList.users.length === 0" class="text-center pa-12">
      <v-icon icon="mdi-account-off" size="64" color="grey" class="mb-4" />
      <div class="text-h6 mb-2">No Users Found</div>
      <div class="text-body-2 text-medium-emphasis">
        There are no users in the system.
      </div>
    </div>

    <v-card v-else variant="outlined">
      <v-table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Created</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in userList.users" :key="user.id">
            <td>
              <div class="d-flex align-center">
                <v-avatar color="primary" size="32" class="mr-2">
                  <v-img v-if="avatarUrls[user.id]" :src="avatarUrls[user.id]" cover />
                  <span v-else class="text-caption">{{ user.username.charAt(0).toUpperCase() }}</span>
                </v-avatar>
                <strong>{{ user.username }}</strong>
              </div>
            </td>
            <td>{{ user.email || 'N/A' }}</td>
            <td>
              <v-chip
                :color="getRoleColor(user.role)"
                size="small"
                variant="tonal"
              >
                {{ user.role }}
              </v-chip>
            </td>
            <td>
              <v-chip
                v-if="user.is_locked"
                color="warning"
                size="small"
                variant="tonal"
              >
                <v-icon
                  icon="mdi-lock"
                  size="x-small"
                  class="mr-1"
                />
                LOCKED
              </v-chip>
              <v-chip
                v-else
                :color="user.status === 'ENABLED' ? 'success' : 'error'"
                size="small"
                variant="tonal"
              >
                <v-icon
                  :icon="user.status === 'ENABLED' ? 'mdi-check-circle' : 'mdi-close-circle'"
                  size="x-small"
                  class="mr-1"
                />
                {{ user.status }}
              </v-chip>
            </td>
            <td>
              <div class="text-body-2">{{ formatDate(user.created_at) }}</div>
            </td>
            <td class="text-right">
              <v-btn
                v-if="user.is_locked"
                icon="mdi-lock-open"
                variant="text"
                size="small"
                color="warning"
                @click="handleUnlockUser(user.id, user.username)"
                :loading="isUnlocking"
                title="Unlock User"
              />
              <v-btn
                icon="mdi-account-edit"
                variant="text"
                size="small"
                @click="openRoleDialog(user)"
                title="Change Role"
              />
            </td>
          </tr>
        </tbody>
      </v-table>

      <v-divider />

      <div class="pa-4 d-flex justify-space-between align-center">
        <div class="text-body-2 text-medium-emphasis">
          Showing {{ userList.users.length }} of {{ userList.total }} users
        </div>
      </div>
    </v-card>

    <!-- Change Role Dialog -->
    <v-dialog v-model="showRoleDialog" max-width="450" persistent scrim="rgba(0, 0, 0, 0.8)">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">Change User Role</span>
          <v-btn icon="mdi-close" variant="text" @click="showRoleDialog = false" :disabled="isUpdatingRole" />
        </v-card-title>

        <v-divider />

        <v-card-text class="pt-4">
          <v-alert type="warning" variant="tonal" density="compact" class="mb-4">
            <strong>Important:</strong> Changing a user's role will affect their permissions and access level.
          </v-alert>

          <div v-if="selectedUser" class="mb-4">
            <div class="mb-3">
              <div class="text-caption text-medium-emphasis">Username</div>
              <div class="text-body-1 font-weight-medium">{{ selectedUser.username }}</div>
            </div>

            <div class="mb-3">
              <div class="text-caption text-medium-emphasis">Current Role</div>
              <v-chip
                :color="getRoleColor(selectedUser.role)"
                size="small"
                variant="tonal"
              >
                {{ selectedUser.role }}
              </v-chip>
            </div>
          </div>

          <v-select
            v-model="newRole"
            label="New Role"
            :items="[
              { title: 'User', value: UserRole.USER },
              { title: 'Banker', value: UserRole.BANKER },
              { title: 'Admin', value: UserRole.ADMIN },
            ]"
            variant="outlined"
            :disabled="isUpdatingRole"
          />
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="showRoleDialog = false"
            :disabled="isUpdatingRole"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="handleChangeRole"
            :loading="isUpdatingRole"
            :disabled="!!(selectedUser && newRole === selectedUser.role)"
          >
            Update Role
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

