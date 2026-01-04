<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  message: string
  actionText?: string
}>()

const emit = defineEmits<{
  action: []
}>()
</script>

<template>
  <v-card variant="outlined" class="text-center pa-8">
    <v-icon :icon="icon" size="64" color="grey" class="mb-4" />
    <h3 class="text-h6 mb-2">{{ title }}</h3>
    <p class="text-body-2 text-medium-emphasis mb-4">{{ message }}</p>
    <v-btn
      v-if="actionText"
      color="primary"
      @click="emit('action')"
    >
      {{ actionText }}
    </v-btn>
  </v-card>
</template>

