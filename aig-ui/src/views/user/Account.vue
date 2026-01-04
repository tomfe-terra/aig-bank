<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useProfile } from '@/composables/useProfile'
import { useAuth } from '@/composables/useAuth'
import { useAPIKeys } from '@/composables/useAPIKeys'
import { useToast } from '@/composables/useToast'
import { formatDate, formatMoney, getErrorMessage } from '@/utils/format'
import EmptyState from '@/components/EmptyState.vue'

// Profile composable
const { 
  user, 
  hasAvatar,
  avatarUrl, 
  isLoadingAvatar,
  loadAvatar,
  updateProfile, 
  isUpdatingProfile,
  uploadAvatar,
  isUploadingAvatar,
  deleteAvatar,
  isDeletingAvatar,
} = useProfile()

// Auth composable for account data
const { account } = useAuth()

// API Keys composable
const { 
  apiKeys, 
  isLoading: isLoadingApiKeys, 
  includeRevoked, 
  createAPIKey, 
  isCreating, 
  updateAPIKey, 
  isUpdating, 
  deleteAPIKey, 
  refetchAPIKeys 
} = useAPIKeys()

const { showToast } = useToast()

// Current tab
const currentTab = ref('account')

// Profile form fields
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const phone = ref('')
const address = ref('')

// File input ref
const fileInput = ref<HTMLInputElement | null>(null)
const showDeleteAvatarDialog = ref(false)

// API Keys dialogs
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDeleteKeyDialog = ref(false)
const keyName = ref('')
const keyDescription = ref('')
const createdKey = ref<string | null>(null)
const editingKeyId = ref<string | null>(null)
const deletingKeyId = ref<string | null>(null)

// Form validation
const firstNameRules = [
  (v: string) => !!v || 'First name is required',
  (v: string) => v.length <= 50 || 'First name must be less than 50 characters',
]

const lastNameRules = [
  (v: string) => !!v || 'Last name is required',
  (v: string) => v.length <= 50 || 'Last name must be less than 50 characters',
]

const emailRules = [
  (v: string) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email format',
]

const phoneRules = [
  (v: string) => !v || /^[+]?[\d\s()-]{7,20}$/.test(v) || 'Invalid phone number format',
]

// Check if form has changes
const hasChanges = computed(() => {
  if (!user.value) return false
  return (
    firstName.value !== user.value.first_name ||
    lastName.value !== user.value.last_name ||
    (email.value || null) !== user.value.email ||
    (phone.value || null) !== user.value.phone ||
    (address.value || null) !== user.value.address
  )
})

// Populate form with user data
const populateForm = () => {
  if (user.value) {
    firstName.value = user.value.first_name
    lastName.value = user.value.last_name
    email.value = user.value.email || ''
    phone.value = user.value.phone || ''
    address.value = user.value.address || ''
  }
}

// Watch for user changes
watch(user, () => {
  populateForm()
}, { immediate: true })

// Load avatar on mount
onMounted(async () => {
  if (hasAvatar.value) {
    await loadAvatar()
  }
})

// Watch for avatar changes
watch(hasAvatar, async (newVal) => {
  if (newVal) {
    await loadAvatar()
  }
})

// Get user initials for avatar placeholder
const userInitials = computed(() => {
  if (!user.value) return '?'
  return `${user.value.first_name.charAt(0)}${user.value.last_name.charAt(0)}`.toUpperCase()
})

// Handle profile form submission
const handleSubmit = async () => {
  if (!firstName.value.trim() || !lastName.value.trim()) {
    showToast('First name and last name are required', 'error')
    return
  }

  try {
    await updateProfile({
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
      email: email.value.trim() || null,
      phone: phone.value.trim() || null,
      address: address.value.trim() || null,
    })
    showToast('Profile updated successfully', 'success')
  } catch (e: unknown) {
    console.error('Failed to update profile:', e)
    showToast(getErrorMessage(e, 'Failed to update profile'), 'error')
  }
}

// Reset form
const resetForm = () => {
  populateForm()
}

// Handle avatar upload
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  
  if (!file) return
  
  // Validate file type
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!validTypes.includes(file.type)) {
    showToast('Please select a valid image file (JPEG, PNG, GIF, or WebP)', 'error')
    return
  }
  
  // Validate file size (5MB max)
  if (file.size > 5 * 1024 * 1024) {
    showToast('File size must be less than 5MB', 'error')
    return
  }
  
  try {
    await uploadAvatar(file)
    showToast('Avatar uploaded successfully', 'success')
  } catch (e: unknown) {
    console.error('Failed to upload avatar:', e)
    showToast(getErrorMessage(e, 'Failed to upload avatar'), 'error')
  }
  
  // Reset file input
  input.value = ''
}

// Handle avatar deletion
const confirmDeleteAvatar = async () => {
  try {
    await deleteAvatar()
    showDeleteAvatarDialog.value = false
    showToast('Avatar deleted successfully', 'success')
  } catch (e: unknown) {
    console.error('Failed to delete avatar:', e)
    showToast(getErrorMessage(e, 'Failed to delete avatar'), 'error')
  }
}

// API Keys handlers
const handleCreateKey = async () => {
  if (!keyName.value.trim()) {
    showToast('Please enter a name for your API key', 'error')
    return
  }
  
  try {
    const payload: any = { name: keyName.value }
    if (keyDescription.value.trim()) {
      payload.description = keyDescription.value
    }
    const result = await createAPIKey(payload)
    createdKey.value = result.secret
    keyName.value = ''
    keyDescription.value = ''
    showToast('API key created successfully! Make sure to copy it now.', 'success')
    refetchAPIKeys()
  } catch (e: unknown) {
    console.error('Failed to create API key:', e)
    showToast(getErrorMessage(e, 'Failed to create API key'), 'error')
  }
}

const openDeleteKeyDialog = (apiKeyId: string) => {
  deletingKeyId.value = apiKeyId
  showDeleteKeyDialog.value = true
}

const confirmDeleteKey = async () => {
  if (!deletingKeyId.value) return
  
  try {
    await deleteAPIKey(deletingKeyId.value)
    showDeleteKeyDialog.value = false
    deletingKeyId.value = null
    showToast('API key revoked successfully.', 'success')
    refetchAPIKeys()
  } catch (e: unknown) {
    console.error('Failed to delete API key:', e)
    showToast(getErrorMessage(e, 'Failed to revoke API key'), 'error')
    showDeleteKeyDialog.value = false
  }
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text)
  showToast('Copied to clipboard!', 'info')
}

const closeCreateDialog = () => {
  showCreateDialog.value = false
  createdKey.value = null
  keyName.value = ''
  keyDescription.value = ''
}

const openEditDialog = (apiKey: any) => {
  editingKeyId.value = apiKey.id
  keyName.value = apiKey.name
  keyDescription.value = apiKey.description || ''
  showEditDialog.value = true
}

const handleUpdateKey = async () => {
  if (!keyName.value.trim()) {
    showToast('Please enter a name for your API key', 'error')
    return
  }
  
  if (!editingKeyId.value) return
  
  try {
    const payload: any = {}
    if (keyName.value.trim()) {
      payload.name = keyName.value
    }
    if (keyDescription.value.trim()) {
      payload.description = keyDescription.value
    } else {
      payload.description = null
    }
    
    await updateAPIKey({ apiKeyId: editingKeyId.value, data: payload })
    showEditDialog.value = false
    keyName.value = ''
    keyDescription.value = ''
    editingKeyId.value = null
    showToast('API key updated successfully!', 'success')
    refetchAPIKeys()
  } catch (e: unknown) {
    console.error('Failed to update API key:', e)
    showToast(getErrorMessage(e, 'Failed to update API key'), 'error')
  }
}

const closeEditDialog = () => {
  showEditDialog.value = false
  keyName.value = ''
  keyDescription.value = ''
  editingKeyId.value = null
}

// Count active API keys
const activeKeysCount = computed(() => {
  if (!apiKeys.value) return 0
  return apiKeys.value.filter(k => k.is_active).length
})
</script>

<template>
  <div>
    <!-- Profile Header -->
    <v-card variant="outlined" class="mb-6">
      <v-card-text class="d-flex align-center pa-4">
        <div class="avatar-section mr-4">
          <v-avatar size="80" color="primary" class="avatar-main">
            <v-img v-if="avatarUrl" :src="avatarUrl" cover />
            <span v-else class="text-h4 text-white">{{ userInitials }}</span>
            
            <v-overlay
              :model-value="isLoadingAvatar || isUploadingAvatar"
              contained
              class="align-center justify-center"
              scrim="rgba(0,0,0,0.5)"
            >
              <v-progress-circular indeterminate color="white" size="24" />
            </v-overlay>
          </v-avatar>
        </div>
        
        <div class="flex-grow-1">
          <div class="text-h5 font-weight-medium">{{ user?.first_name }} {{ user?.last_name }}</div>
          <div class="text-body-2 text-medium-emphasis">@{{ user?.username }}</div>
          <div class="d-flex align-center gap-2 mt-1">
            <v-chip
              :color="user?.role === 'ADMIN' ? 'error' : user?.role === 'BANKER' ? 'warning' : 'primary'"
              size="small"
              variant="tonal"
            >
              {{ user?.role }}
            </v-chip>
            <v-chip
              :color="user?.status === 'ENABLED' ? 'success' : 'error'"
              size="small"
              variant="tonal"
            >
              {{ user?.status }}
            </v-chip>
          </div>
        </div>
        
        <div class="d-flex flex-column gap-2">
          <v-btn
            variant="outlined"
            size="small"
            prepend-icon="mdi-camera"
            @click="triggerFileInput"
            :loading="isUploadingAvatar"
          >
            {{ hasAvatar ? 'Change' : 'Upload' }}
          </v-btn>
          <v-btn
            v-if="hasAvatar"
            variant="text"
            size="small"
            color="error"
            prepend-icon="mdi-delete"
            @click="showDeleteAvatarDialog = true"
            :disabled="isDeletingAvatar"
          >
            Remove
          </v-btn>
        </div>
        
        <input
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          class="d-none"
          @change="handleFileSelect"
        />
      </v-card-text>
    </v-card>

    <!-- Tabs -->
    <v-card variant="outlined">
      <v-tabs v-model="currentTab" bg-color="transparent">
        <v-tab value="account" prepend-icon="mdi-account-circle">
          Account Info
        </v-tab>
        <v-tab value="profile" prepend-icon="mdi-account-edit">
          Profile
        </v-tab>
        <v-tab value="apikeys" prepend-icon="mdi-key-variant">
          API Keys
          <v-badge
            v-if="activeKeysCount > 0"
            :content="activeKeysCount"
            color="primary"
            inline
            class="ml-2"
          />
        </v-tab>
      </v-tabs>

      <v-divider />

      <v-tabs-window v-model="currentTab">
        <!-- Account Info Tab -->
        <v-tabs-window-item value="account">
          <v-card-text class="pa-6">
            <!-- Bank Account Section -->
            <div class="d-flex align-center mb-4">
              <v-icon icon="mdi-bank" class="mr-2" color="primary" />
              <div class="text-h6">Bank Account</div>
            </div>
            
            <v-card variant="tonal" color="primary" class="mb-6">
              <v-card-text>
                <v-row align="center">
                  <v-col cols="12" md="6">
                    <div class="text-caption text-medium-emphasis mb-1">Current Balance</div>
                    <div class="text-h3 font-weight-bold">
                      {{ account ? formatMoney(account.balance_cents) : '—' }}
                    </div>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-row>
                      <v-col cols="12" sm="6">
                        <div class="text-caption text-medium-emphasis">Account Number</div>
                        <div class="text-body-1 font-weight-medium d-flex align-center">
                          <span class="font-mono">{{ account?.number || '—' }}</span>
                          <v-btn
                            v-if="account?.number"
                            icon="mdi-content-copy"
                            variant="text"
                            size="x-small"
                            @click="copyToClipboard(account.number)"
                            class="ml-1"
                          />
                        </div>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <div class="text-caption text-medium-emphasis">Account Opened</div>
                        <div class="text-body-1">{{ account?.created_at ? formatDate(account.created_at) : '—' }}</div>
                      </v-col>
                    </v-row>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <v-divider class="my-6" />

            <!-- User Information Section -->
            <div class="d-flex align-center mb-4">
              <v-icon icon="mdi-account" class="mr-2" color="primary" />
              <div class="text-h6">User Information</div>
            </div>
            
            <v-row>
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-medium-emphasis">Full Name</div>
                <div class="text-body-1 font-weight-medium">{{ user?.first_name }} {{ user?.last_name }}</div>
              </v-col>
              
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-medium-emphasis">Username</div>
                <div class="text-body-1 font-weight-medium">@{{ user?.username }}</div>
              </v-col>
              
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-medium-emphasis">User ID</div>
                <div class="text-body-2 text-medium-emphasis font-mono d-flex align-center">
                  <span class="text-truncate" style="max-width: 200px;">{{ user?.id }}</span>
                  <v-btn
                    icon="mdi-content-copy"
                    variant="text"
                    size="x-small"
                    @click="copyToClipboard(user?.id || '')"
                    class="ml-1"
                  />
                </div>
              </v-col>
            </v-row>

            <v-row class="mt-2">
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-medium-emphasis">Role</div>
                <v-chip
                  :color="user?.role === 'ADMIN' ? 'error' : user?.role === 'BANKER' ? 'warning' : 'primary'"
                  size="small"
                  variant="tonal"
                  class="mt-1"
                >
                  <v-icon start :icon="user?.role === 'ADMIN' ? 'mdi-shield-crown' : user?.role === 'BANKER' ? 'mdi-briefcase' : 'mdi-account'" size="small" />
                  {{ user?.role }}
                </v-chip>
              </v-col>
              
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-medium-emphasis">Account Status</div>
                <v-chip
                  :color="user?.status === 'ENABLED' ? 'success' : 'error'"
                  size="small"
                  variant="tonal"
                  class="mt-1"
                >
                  <v-icon start :icon="user?.status === 'ENABLED' ? 'mdi-check-circle' : 'mdi-close-circle'" size="small" />
                  {{ user?.status }}
                </v-chip>
              </v-col>
              
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-medium-emphasis">Avatar</div>
                <v-chip
                  :color="hasAvatar ? 'success' : 'default'"
                  size="small"
                  variant="tonal"
                  class="mt-1"
                >
                  <v-icon start :icon="hasAvatar ? 'mdi-image-check' : 'mdi-image-off'" size="small" />
                  {{ hasAvatar ? 'Uploaded' : 'Not Set' }}
                </v-chip>
              </v-col>
            </v-row>

            <v-divider class="my-6" />

            <!-- Contact Information Section -->
            <div class="d-flex align-center mb-4">
              <v-icon icon="mdi-card-account-details" class="mr-2" color="primary" />
              <div class="text-h6">Contact Information</div>
            </div>
            
            <v-row>
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-medium-emphasis">Email</div>
                <div class="text-body-1 d-flex align-center">
                  <v-icon v-if="user?.email" icon="mdi-email" size="small" class="mr-2 text-medium-emphasis" />
                  {{ user?.email || '—' }}
                </div>
              </v-col>
              
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-medium-emphasis">Phone</div>
                <div class="text-body-1 d-flex align-center">
                  <v-icon v-if="user?.phone" icon="mdi-phone" size="small" class="mr-2 text-medium-emphasis" />
                  {{ user?.phone || '—' }}
                </div>
              </v-col>
              
              <v-col cols="12" md="4">
                <div class="text-caption text-medium-emphasis">Address</div>
                <div class="text-body-1 d-flex align-center">
                  <v-icon v-if="user?.address" icon="mdi-map-marker" size="small" class="mr-2 text-medium-emphasis" />
                  {{ user?.address || '—' }}
                </div>
              </v-col>
            </v-row>

            <div class="mt-6">
              <v-btn
                variant="outlined"
                prepend-icon="mdi-pencil"
                @click="currentTab = 'profile'"
              >
                Edit Profile
              </v-btn>
            </div>
          </v-card-text>
        </v-tabs-window-item>

        <!-- Profile Tab -->
        <v-tabs-window-item value="profile">
          <v-card-text class="pa-6">
            <div class="text-h6 mb-4">Edit Profile</div>
            
            <v-form @submit.prevent="handleSubmit">
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="firstName"
                    label="First Name"
                    variant="outlined"
                    :rules="firstNameRules"
                    :disabled="isUpdatingProfile"
                    required
                  />
                </v-col>
                
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="lastName"
                    label="Last Name"
                    variant="outlined"
                    :rules="lastNameRules"
                    :disabled="isUpdatingProfile"
                    required
                  />
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="email"
                    label="Email"
                    type="email"
                    variant="outlined"
                    :rules="emailRules"
                    :disabled="isUpdatingProfile"
                    placeholder="john.doe@example.com"
                  />
                </v-col>
                
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="phone"
                    label="Phone"
                    variant="outlined"
                    :rules="phoneRules"
                    :disabled="isUpdatingProfile"
                    placeholder="+1 234 567 8900"
                  />
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12">
                  <v-textarea
                    v-model="address"
                    label="Address"
                    variant="outlined"
                    :disabled="isUpdatingProfile"
                    rows="3"
                  />
                </v-col>
              </v-row>

              <div class="d-flex justify-end gap-2 mt-2">
                <v-btn
                  variant="text"
                  @click="resetForm"
                  :disabled="!hasChanges || isUpdatingProfile"
                >
                  Reset
                </v-btn>
                <v-btn
                  color="primary"
                  variant="flat"
                  type="submit"
                  :loading="isUpdatingProfile"
                  :disabled="!hasChanges || isUpdatingProfile"
                >
                  Save Changes
                </v-btn>
              </div>
            </v-form>
          </v-card-text>
        </v-tabs-window-item>

        <!-- API Keys Tab -->
        <v-tabs-window-item value="apikeys">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-center mb-4">
              <div class="text-h6">API Keys</div>
              <div class="d-flex align-center" style="gap: 24px;">
                <v-switch
                  v-model="includeRevoked"
                  label="Show revoked"
                  color="primary"
                  hide-details
                  density="compact"
                />
                <v-btn
                  color="primary"
                  prepend-icon="mdi-key-plus"
                  @click="showCreateDialog = true"
                >
                  Create API Key
                </v-btn>
              </div>
            </div>

            <v-skeleton-loader v-if="isLoadingApiKeys" type="table-row@3" />
            
            <EmptyState
              v-else-if="!apiKeys || apiKeys.length === 0"
              icon="mdi-key-off"
              title="No API keys yet"
              message="Create an API key to access the AIG Bank API programmatically."
              action-text="Create API Key"
              @action="showCreateDialog = true"
            />
            
            <div v-else class="api-keys-list">
              <v-card
                v-for="apiKey in apiKeys"
                :key="apiKey.id"
                variant="outlined"
                class="mb-3"
              >
                <v-card-text class="d-flex align-center">
                  <v-icon
                    :icon="apiKey.is_active ? 'mdi-key' : 'mdi-key-remove'"
                    :color="apiKey.is_active ? 'primary' : 'grey'"
                    size="large"
                    class="mr-4"
                  />
                  
                  <div class="flex-grow-1">
                    <div class="d-flex align-center gap-2">
                      <span class="text-body-1 font-weight-medium">{{ apiKey.name }}</span>
                      <v-chip
                        :color="apiKey.is_active ? 'success' : 'error'"
                        size="x-small"
                        variant="tonal"
                      >
                        {{ apiKey.is_active ? 'Active' : 'Revoked' }}
                      </v-chip>
                    </div>
                    <div v-if="apiKey.description" class="text-body-2 text-medium-emphasis">
                      {{ apiKey.description }}
                    </div>
                    <div class="text-caption text-medium-emphasis mt-1">
                      Created: {{ formatDate(apiKey.created_at) }}
                      <span v-if="apiKey.last_used"> · Last used: {{ formatDate(apiKey.last_used) }}</span>
                      <span v-else> · Never used</span>
                    </div>
                  </div>
                  
                  <div class="d-flex gap-1">
                    <v-btn
                      icon="mdi-content-copy"
                      variant="text"
                      size="small"
                      @click="copyToClipboard(apiKey.id)"
                      title="Copy API Key ID"
                    />
                    <v-btn
                      v-if="apiKey.is_active"
                      icon="mdi-pencil"
                      variant="text"
                      size="small"
                      @click="openEditDialog(apiKey)"
                      title="Edit API Key"
                    />
                    <v-btn
                      v-if="apiKey.is_active"
                      icon="mdi-cancel"
                      variant="text"
                      color="error"
                      size="small"
                      @click="openDeleteKeyDialog(apiKey.id)"
                      title="Revoke API Key"
                    />
                  </div>
                </v-card-text>
              </v-card>
            </div>
          </v-card-text>
        </v-tabs-window-item>
      </v-tabs-window>
    </v-card>

    <!-- Delete Avatar Dialog -->
    <v-dialog v-model="showDeleteAvatarDialog" max-width="400" persistent>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">Remove Avatar?</span>
          <v-btn icon="mdi-close" variant="text" @click="showDeleteAvatarDialog = false" />
        </v-card-title>
        
        <v-divider />
        
        <v-card-text class="pt-4">
          <p class="text-body-1">Are you sure you want to remove your profile avatar?</p>
          <p class="text-body-2 text-medium-emphasis mt-2">Your initials will be shown instead.</p>
        </v-card-text>
        
        <v-divider />
        
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="showDeleteAvatarDialog = false"
            :disabled="isDeletingAvatar"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            @click="confirmDeleteAvatar"
            :loading="isDeletingAvatar"
          >
            Remove
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create API Key Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">{{ createdKey ? 'API Key Created' : 'Create API Key' }}</span>
          <v-btn icon="mdi-close" variant="text" @click="closeCreateDialog" :disabled="isCreating" />
        </v-card-title>
        
        <v-divider />
        
        <v-card-text class="pt-4">
          <v-alert v-if="createdKey" type="success" variant="tonal" class="mb-4">
            <div class="text-subtitle-1 font-weight-bold mb-2">Success!</div>
            <div class="text-body-2 mb-3">
              Make sure to copy your API key now. You won't be able to see it again!
            </div>
            <v-text-field
              :model-value="createdKey"
              readonly
              variant="outlined"
              density="compact"
              class="font-mono mt-2"
              hide-details
            >
              <template #append-inner>
                <v-btn
                  icon="mdi-content-copy"
                  variant="text"
                  size="small"
                  @click="copyToClipboard(createdKey)"
                />
              </template>
            </v-text-field>
          </v-alert>
          
          <div v-if="!createdKey">
            <v-text-field
              v-model="keyName"
              label="API Key Name"
              variant="outlined"
              :disabled="isCreating"
              placeholder="e.g., Production API, Mobile App"
              required
              class="mb-3"
            />
            
            <v-textarea
              v-model="keyDescription"
              label="Description (Optional)"
              variant="outlined"
              :disabled="isCreating"
              rows="3"
              hint="e.g., Used for production server integration"
              persistent-hint
            />
          </div>
        </v-card-text>
        
        <v-divider />
        
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="closeCreateDialog"
            :disabled="isCreating"
          >
            {{ createdKey ? 'Close' : 'Cancel' }}
          </v-btn>
          <v-btn
            v-if="!createdKey"
            color="primary"
            variant="flat"
            @click="handleCreateKey"
            :loading="isCreating"
            :disabled="!keyName"
          >
            Create
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit API Key Dialog -->
    <v-dialog v-model="showEditDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">Edit API Key</span>
          <v-btn icon="mdi-close" variant="text" @click="closeEditDialog" :disabled="isUpdating" />
        </v-card-title>
        
        <v-divider />
        
        <v-card-text class="pt-4">
          <v-text-field
            v-model="keyName"
            label="API Key Name"
            variant="outlined"
            :disabled="isUpdating"
            placeholder="e.g., Production API, Mobile App"
            required
            class="mb-3"
          />
          
          <v-textarea
            v-model="keyDescription"
            label="Description (Optional)"
            variant="outlined"
            :disabled="isUpdating"
            rows="3"
            hint="e.g., Used for production server integration"
            persistent-hint
          />
        </v-card-text>
        
        <v-divider />
        
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="closeEditDialog"
            :disabled="isUpdating"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="handleUpdateKey"
            :loading="isUpdating"
            :disabled="!keyName"
          >
            Update
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete API Key Dialog -->
    <v-dialog v-model="showDeleteKeyDialog" max-width="400" persistent>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h5">Revoke API Key?</span>
          <v-btn icon="mdi-close" variant="text" @click="showDeleteKeyDialog = false" />
        </v-card-title>
        
        <v-divider />
        
        <v-card-text class="pt-4">
          <p class="text-body-1">Are you sure you want to revoke this API key?</p>
          <p class="text-body-2 text-medium-emphasis mt-2">This action cannot be undone. Any applications using this key will no longer have access.</p>
        </v-card-text>
        
        <v-divider />
        
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="showDeleteKeyDialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            @click="confirmDeleteKey"
          >
            Revoke
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.avatar-main {
  border: 3px solid rgb(var(--v-theme-surface-variant));
  position: relative;
}

.font-mono {
  font-family: 'Courier New', monospace;
}

.api-keys-list .v-card:last-child {
  margin-bottom: 0 !important;
}
</style>

