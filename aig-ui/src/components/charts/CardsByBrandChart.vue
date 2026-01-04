<template>
  <div class="cards-by-brand-chart">
    <div v-if="activeCards.length === 0" class="text-center pa-8 text-medium-emphasis">
      No active cards
    </div>
    <div v-else class="chart-container">
      <Doughnut :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  type ChartOptions,
  type ChartData,
} from 'chart.js'
import type { CardRead } from '@/types'
import { useTheme } from 'vuetify'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  cards: CardRead[] | undefined
}>()

const theme = useTheme()

const activeCards = computed(() => {
  if (!props.cards) return []
  return props.cards.filter((card) => card.status === 'ACTIVE')
})

const brandColors: Record<string, string> = {
  VISA: '#1A1F71',
  MASTERCARD: '#EB001B',
  AMERICAN_EXPRESS: '#006FCF',
  DISCOVER: '#FF6000',
  UNKNOWN: '#9E9E9E',
}

const brandData = computed(() => {
  const counts: Record<string, number> = {}
  
  activeCards.value.forEach((card) => {
    const brand = card.brand || 'UNKNOWN'
    counts[brand] = (counts[brand] || 0) + 1
  })
  
  return counts
})

const chartData = computed<ChartData<'doughnut'>>(() => {
  const labels = Object.keys(brandData.value).map((brand) =>
    brand.replace(/_/g, ' ')
  )
  const data = Object.values(brandData.value)
  const backgroundColor = Object.keys(brandData.value).map(
    (brand) => brandColors[brand] || brandColors.UNKNOWN
  )
  
  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor,
        borderWidth: 2,
        borderColor: theme.current.value.dark ? '#1E1E1E' : '#FFFFFF',
      },
    ],
  }
})

const chartOptions = computed<ChartOptions<'doughnut'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: theme.current.value.dark ? '#FFFFFF' : '#000000',
        padding: 16,
        font: {
          size: 12,
        },
      },
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const label = context.label || ''
          const value = context.parsed || 0
          const total = (context.dataset.data as number[]).reduce(
            (acc, val) => acc + val,
            0
          )
          const percentage = ((value / total) * 100).toFixed(1)
          return `${label}: ${value} (${percentage}%)`
        },
      },
    },
  },
}))
</script>

<style scoped>
.cards-by-brand-chart {
  min-height: 200px;
}

.chart-container {
  padding: 16px;
  max-width: 400px;
  margin: 0 auto;
}
</style>

