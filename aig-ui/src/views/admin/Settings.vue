<script setup lang="ts">
import { computed } from 'vue'
import { useAdminSettings } from '@/composables/useAdminSettings'

const { settings, isLoading, error, refetch } = useAdminSettings()

// Get the type of a value for proper display
const getValueType = (value: any): 'boolean' | 'number' | 'string' | 'object' | 'array' => {
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') return 'number'
  if (typeof value === 'string') return 'string'
  if (Array.isArray(value)) return 'array'
  return 'object'
}

// Format label from key (e.g., "max_transfer_amount" -> "Max Transfer Amount")
const formatLabel = (key: string): string => {
  return key
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Format value for display
const formatValue = (value: any): string => {
  const type = getValueType(value)
  if (type === 'boolean') return value ? 'Enabled' : 'Disabled'
  if (type === 'object' || type === 'array') return JSON.stringify(value, null, 2)
  return String(value)
}

// Get badge color for boolean values
const getBooleanColor = (value: boolean): string => {
  return value ? 'success' : 'grey'
}

// Settings entries for rendering
const settingsEntries = computed(() => {
  if (!settings.value) return []
  return Object.entries(settings.value).map(([key, value]) => ({
    key,
    value,
    type: getValueType(value),
    label: formatLabel(key),
    displayValue: formatValue(value),
  }))
})
</script>

<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <h1 class="text-h4">System Settings</h1>
          <v-btn
            color="primary"
            variant="outlined"
            prepend-icon="mdi-refresh"
            @click="refetch"
            :loading="isLoading"
          >
            Refresh
          </v-btn>
        </div>

        <!-- Loading State -->
        <v-card v-if="isLoading" variant="outlined">
          <v-card-text>
            <v-skeleton-loader type="list-item@8" />
          </v-card-text>
        </v-card>

        <!-- Error State -->
        <v-alert v-else-if="error" type="error" variant="tonal" class="mb-4">
          Failed to load settings: {{ error.message }}
        </v-alert>

        <!-- Empty State -->
        <v-card v-else-if="!settingsEntries.length" variant="outlined">
          <v-card-text class="text-center py-12">
            <v-icon size="64" color="grey-lighten-1" class="mb-4">
              mdi-cog-outline
            </v-icon>
            <p class="text-h6 text-grey">No settings available</p>
            <p class="text-body-2 text-grey-darken-1">
              System settings will appear here once configured
            </p>
          </v-card-text>
        </v-card>

        <!-- Settings Display -->
        <v-card v-else variant="outlined">
          <v-list>
            <template v-for="(entry, index) in settingsEntries" :key="entry.key">
              <v-divider v-if="index > 0" />
              
              <v-list-item>
                <template #prepend>
                  <v-icon 
                    :color="entry.type === 'boolean' ? getBooleanColor(entry.value) : 'grey'"
                  >
                    {{
                      entry.type === 'boolean' ? 'mdi-toggle-switch' :
                      entry.type === 'number' ? 'mdi-numeric' :
                      entry.type === 'string' ? 'mdi-text' :
                      entry.type === 'array' ? 'mdi-code-brackets' :
                      'mdi-code-braces'
                    }}
                  </v-icon>
                </template>

                <v-list-item-title class="font-weight-medium mb-2">
                  {{ entry.label }}
                </v-list-item-title>

                <!-- Boolean value -->
                <v-list-item-subtitle v-if="entry.type === 'boolean'" class="mt-1">
                  <v-chip
                    :color="getBooleanColor(entry.value)"
                    size="small"
                    variant="flat"
                  >
                    {{ entry.displayValue }}
                  </v-chip>
                </v-list-item-subtitle>
                
                <!-- Array or Object value -->
                <v-list-item-subtitle v-else-if="entry.type === 'object' || entry.type === 'array'" class="mt-1">
                  <div class="settings-json-wrapper">
                    <pre class="settings-json">{{ entry.displayValue }}</pre>
                  </div>
                </v-list-item-subtitle>
                
                <!-- Simple value (string/number) -->
                <v-list-item-subtitle v-else class="text-body-1 mt-1">
                  {{ entry.displayValue }}
                </v-list-item-subtitle>
              </v-list-item>
            </template>
          </v-list>
        </v-card>

        <!-- Info Card -->
        <v-card variant="outlined" class="mt-4">
          <v-card-text>
            <div class="d-flex ga-2 align-start">
              <v-icon color="info">mdi-information</v-icon>
              <div>
                <p class="text-body-2 mb-2">
                  <strong>System Settings (Read-Only)</strong>
                </p>
                <p class="text-body-2 text-grey-darken-1">
                  These settings display the current application configuration for monitoring and 
                  debugging purposes. Settings are configured at the application level and cannot 
                  be modified through this interface.
                </p>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.settings-json-wrapper {
  width: 100%;
  overflow: hidden;
}

.settings-json {
  font-family: 'Courier New', 'Courier', monospace;
  font-size: 0.8125rem;
  line-height: 1.5;
  background-color: rgba(0, 0, 0, 0.05);
  padding: 12px;
  border-radius: 4px;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  overflow-x: auto;
  display: block;
  width: 100%;
}

:deep(.v-theme--dark) .settings-json {
  background-color: rgba(255, 255, 255, 0.08);
}
</style>
