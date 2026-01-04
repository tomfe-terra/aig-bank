<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from './layouts/AppLayout.vue'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const { show, message, type, timeout } = useToast()

// Check if current route requires layout
const requiresLayout = computed(() => {
  return route.meta.requiresAuth !== false
})

const getColor = (toastType: string) => {
  switch (toastType) {
    case 'success': return 'success'
    case 'error': return 'error'
    case 'warning': return 'warning'
    case 'info': return 'info'
    default: return 'info'
  }
}
</script>

<template>
  <v-app>
    <AppLayout v-if="requiresLayout" />
    <router-view v-else />
    
    <!-- Global Toast Notification (for pages without layout) -->
    <v-snackbar
      v-if="!requiresLayout"
      v-model="show"
      :color="getColor(type)"
      :timeout="timeout"
      location="top right"
    >
      {{ message }}
      <template #actions>
        <v-btn
          variant="text"
          icon="mdi-close"
          @click="show = false"
        />
      </template>
    </v-snackbar>
  </v-app>
</template>


