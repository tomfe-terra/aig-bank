<template>
  <div class="request-status-chart">
    <div v-if="!requests || requests.length === 0" class="text-center pa-8 text-medium-emphasis">
      No requests data available
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
import type { Request } from '@/types'
import { useTheme } from 'vuetify'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  requests: Request[] | undefined
}>()

const theme = useTheme()

const statusData = computed(() => {
  if (!props.requests) return { PENDING: 0, APPROVED: 0, REJECTED: 0 }
  
  const counts = {
    PENDING: 0,
    APPROVED: 0,
    REJECTED: 0,
  }
  
  props.requests.forEach((request) => {
    if (request.status in counts) {
      counts[request.status as keyof typeof counts]++
    }
  })
  
  return counts
})

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'PENDING':
      return '#FB8C00' // warning
    case 'APPROVED':
      return '#4CAF50' // success
    case 'REJECTED':
      return '#F44336' // error
    default:
      return '#9E9E9E'
  }
}

const chartData = computed<ChartData<'doughnut'>>(() => {
  const labels = Object.keys(statusData.value)
  const data = Object.values(statusData.value)
  const backgroundColor = labels.map(getStatusColor)
  
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
          const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
          return `${label}: ${value} (${percentage}%)`
        },
      },
    },
  },
}))
</script>

<style scoped>
.request-status-chart {
  min-height: 200px;
}

.chart-container {
  padding: 16px;
  max-width: 400px;
  margin: 0 auto;
}
</style>

