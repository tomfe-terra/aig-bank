<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: number
  label?: string
  disabled?: boolean
  error?: boolean
  errorMessages?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const displayValue = computed({
  get: () => {
    if (props.modelValue === 0) return ''
    return (props.modelValue / 100).toFixed(2)
  },
  set: (value: string) => {
    const num = parseFloat(value) || 0
    emit('update:modelValue', Math.round(num * 100))
  }
})

const formattedValue = computed(() => {
  if (!props.modelValue) return '$0.00'
  return `$${(props.modelValue / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
})
</script>

<template>
  <v-text-field
    v-model="displayValue"
    :label="label || 'Amount'"
    :disabled="disabled"
    :error="error"
    :error-messages="errorMessages"
    variant="outlined"
    prepend-inner-icon="mdi-currency-usd"
    type="number"
    step="0.01"
    min="0"
    :hint="`${formattedValue}`"
    persistent-hint
  />
</template>

