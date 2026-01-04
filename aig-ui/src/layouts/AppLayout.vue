<script setup lang="ts">
import { ref } from 'vue'
import { useDisplay } from 'vuetify'
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'
import { useToast } from '@/composables/useToast'

const { mobile } = useDisplay()
const drawer = ref(!mobile.value)
const { show, message, type, timeout } = useToast()

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
    <TopBar @toggle-drawer="drawer = !drawer" />
    
    <Sidebar v-model="drawer" />
    
    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>

    <!-- Global Toast Notification -->
    <v-snackbar
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

<style scoped>
</style>

