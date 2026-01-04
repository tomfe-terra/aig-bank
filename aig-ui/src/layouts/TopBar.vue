<script setup lang="ts">
import { useTheme } from 'vuetify'
import { useAuth } from '@/composables/useAuth'
import { useRouter } from 'vue-router'

const theme = useTheme()
const { logout } = useAuth()
const router = useRouter()

const emit = defineEmits<{
  toggleDrawer: []
}>()

const toggleTheme = () => {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
  localStorage.setItem('theme', theme.global.name.value)
}

const handleLogout = async () => {
  await logout()
  router.push('/login')
}
</script>

<template>
  <v-app-bar elevation="1" color="surface">
    <v-app-bar-nav-icon @click="emit('toggleDrawer')" />
    
    <v-toolbar-title class="text-h6 font-weight-bold">
      AIG Bank
    </v-toolbar-title>

    <v-spacer />

    <v-btn
      :icon="theme.global.current.value.dark ? 'mdi-white-balance-sunny' : 'mdi-weather-night'"
      @click="toggleTheme"
    />

    <v-btn
      icon="mdi-logout"
      @click="handleLogout"
    />
  </v-app-bar>
</template>

<style scoped>
</style>

