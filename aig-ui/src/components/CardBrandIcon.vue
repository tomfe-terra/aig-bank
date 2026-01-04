<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  brand: string
  size?: number | string
}>()

const sizeValue = computed(() => {
  if (typeof props.size === 'number') return `${props.size}px`
  return props.size || '32px'
})

// SVG paths for each brand (simplified versions based on official logos)
const brandSvg = computed(() => {
  switch (props.brand) {
    case 'VISA':
      return {
        viewBox: '0 0 48 32',
        bg: '#1A1F71',
        content: `
          <rect width="48" height="32" rx="4" fill="#1A1F71"/>
          <text x="24" y="20" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="white" text-anchor="middle">VISA</text>
        `
      }
    case 'MASTERCARD':
      return {
        viewBox: '0 0 48 32',
        bg: '#000000',
        content: `
          <rect width="48" height="32" rx="4" fill="#000000"/>
          <circle cx="18" cy="16" r="8" fill="#EB001B"/>
          <circle cx="30" cy="16" r="8" fill="#FF5F00"/>
          <circle cx="24" cy="16" r="8" fill="#F79E1B" opacity="0.5"/>
        `
      }
    case 'AMERICAN_EXPRESS':
      return {
        viewBox: '0 0 48 32',
        bg: '#006FCF',
        content: `
          <rect width="48" height="32" rx="4" fill="#006FCF"/>
          <text x="24" y="14" font-family="Arial, sans-serif" font-size="7" font-weight="bold" fill="white" text-anchor="middle">AMERICAN</text>
          <text x="24" y="22" font-family="Arial, sans-serif" font-size="7" font-weight="bold" fill="white" text-anchor="middle">EXPRESS</text>
        `
      }
    case 'DISCOVER':
      return {
        viewBox: '0 0 48 32',
        bg: '#FF6000',
        content: `
          <rect width="48" height="32" rx="4" fill="#FF6000"/>
          <text x="24" y="20" font-family="Arial, sans-serif" font-size="9" font-weight="bold" fill="white" text-anchor="middle">DISCOVER</text>
        `
      }
    default:
      return {
        viewBox: '0 0 48 32',
        bg: '#CCCCCC',
        content: `
          <rect width="48" height="32" rx="4" fill="#CCCCCC"/>
          <rect x="4" y="10" width="40" height="12" rx="2" fill="white" opacity="0.8"/>
        `
      }
  }
})
</script>

<template>
  <svg 
    :width="sizeValue" 
    :height="sizeValue"
    :viewBox="brandSvg.viewBox"
    xmlns="http://www.w3.org/2000/svg"
    style="display: inline-block; vertical-align: middle;"
  >
    <g v-html="brandSvg.content"></g>
  </svg>
</template>

