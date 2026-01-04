<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useTheme } from 'vuetify'
import { useAuth } from '@/composables/useAuth'
import { authApi } from '@/api'
import { UserRole } from '@/types'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const drawer = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const { user, userRole } = useAuth()
const theme = useTheme()

// Logo handling - switch based on theme
const logoSrc = computed(() => {
  return theme.global.current.value.dark ? '/dark-logo.png' : '/logo.png'
})

// Avatar handling
const avatarUrl = ref<string | null>(null)

const loadAvatar = async () => {
  if (!user.value?.has_avatar) {
    avatarUrl.value = null
    return
  }
  
  try {
    const blob = await authApi.getAvatar()
    if (avatarUrl.value) {
      URL.revokeObjectURL(avatarUrl.value)
    }
    avatarUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    console.error('Failed to load sidebar avatar:', e)
    avatarUrl.value = null
  }
}

onMounted(() => {
  loadAvatar()
})

watch(() => user.value?.has_avatar, () => {
  loadAvatar()
})

// Navigation items based on role
const userItems = [
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/user/dashboard' },
  { title: 'Transfer Money', icon: 'mdi-bank-transfer', to: '/user/transfer' },
  { title: 'Transactions', icon: 'mdi-format-list-bulleted', to: '/user/transactions' },
  { title: 'Cards', icon: 'mdi-credit-card-multiple', to: '/user/cards' },
  { title: 'Loans', icon: 'mdi-cash-multiple', to: '/user/loans' },
  { title: 'My Requests', icon: 'mdi-file-document-outline', to: '/user/requests' },
  { title: 'Savings Plans', icon: 'mdi-chart-line', to: '/user/savings' },
  { title: 'My Account', icon: 'mdi-account-cog', to: '/user/account' },
]

const bankerItems = [
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/banker/dashboard' },
  { title: 'Manage Requests', icon: 'mdi-file-document-check', to: '/banker/requests' },
  { title: 'Card Management', icon: 'mdi-credit-card-off', to: '/banker/cards' },
]

const adminItems = [
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/admin/dashboard' },
  { title: 'User Management', icon: 'mdi-account-multiple', to: '/admin/users' },
  { title: 'Logs Explorer', icon: 'mdi-file-document-multiple', to: '/admin/logs' },
  { title: 'Bank Capital', icon: 'mdi-bank', to: '/admin/capital' },
  { title: 'Settings', icon: 'mdi-cog', to: '/admin/settings' },
]

// Show sections based on role hierarchy
const showUserSection = computed(() => true) // All roles see user section
const showBankerSection = computed(() => 
  userRole.value === UserRole.BANKER || userRole.value === UserRole.ADMIN
)
const showAdminSection = computed(() => userRole.value === UserRole.ADMIN)

const roleLabel = computed(() => {
  if (userRole.value === UserRole.USER) return 'User'
  if (userRole.value === UserRole.BANKER) return 'Banker'
  if (userRole.value === UserRole.ADMIN) return 'Admin'
  return ''
})
</script>

<template>
  <v-navigation-drawer
    v-model="drawer"
    permanent
  >
    <!-- Logo Section -->
    <div class="pa-6 d-flex justify-center align-center">
      <img
        :src="logoSrc"
        alt="AIG Bank"
        style="width: 100%; max-width: 200px; height: auto; object-fit: contain;"
      />
    </div>

    <v-divider class="mb-2" />

    <v-list>
      <v-list-item
        v-if="user"
        :title="`${user.first_name} ${user.last_name}`"
        :subtitle="roleLabel"
      >
        <template #prepend>
          <v-avatar color="primary">
            <v-img v-if="avatarUrl" :src="avatarUrl" cover />
            <span v-else class="text-h6">{{ user.first_name.charAt(0).toUpperCase() }}</span>
          </v-avatar>
        </template>
      </v-list-item>
    </v-list>

    <v-divider />

    <!-- USER SECTION -->
    <v-list v-if="showUserSection" density="compact" nav>
      <v-list-subheader>USER</v-list-subheader>
      <v-list-item
        v-for="item in userItems"
        :key="item.to"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.title"
      />
    </v-list>

    <!-- BANKER SECTION -->
    <template v-if="showBankerSection">
      <v-divider />
      <v-list density="compact" nav>
        <v-list-subheader>BANKER</v-list-subheader>
        <v-list-item
          v-for="item in bankerItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
        />
      </v-list>
    </template>

    <!-- ADMIN SECTION -->
    <template v-if="showAdminSection">
      <v-divider />
      <v-list density="compact" nav>
        <v-list-subheader>ADMIN</v-list-subheader>
        <v-list-item
          v-for="item in adminItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
        />
      </v-list>
    </template>
  </v-navigation-drawer>
</template>

<style scoped>
</style>

