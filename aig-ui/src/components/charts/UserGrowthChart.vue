<template>
  <div class="user-growth-chart">
    <div v-if="!users || users.length === 0" class="text-center pa-8 text-medium-emphasis">
      No user data available
    </div>
    <div v-else class="chart-container">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
  type ChartData,
} from 'chart.js'
import type { UserListItem } from '@/types'
import { useTheme } from 'vuetify'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps<{
  users: UserListItem[] | undefined
}>()

const theme = useTheme()

const growthData = computed(() => {
  if (!props.users || props.users.length === 0) return { labels: [], data: [] }
  
  // Sort users by created_at
  const sortedUsers = [...props.users].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )
  
  // Group by date and calculate cumulative count
  const dateMap = new Map<string, number>()
  let cumulativeCount = 0
  
  sortedUsers.forEach((user) => {
    const date = new Date(user.created_at).toISOString().split('T')[0]
    cumulativeCount++
    dateMap.set(date, cumulativeCount)
  })
  
  // Get last 30 days of data if available, otherwise show all
  const entries = Array.from(dateMap.entries())
  const recentEntries = entries.slice(-30)
  
  return {
    labels: recentEntries.map(([date]) => {
      const d = new Date(date)
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }),
    data: recentEntries.map(([, count]) => count),
  }
})

const chartData = computed<ChartData<'line'>>(() => {
  const primaryColor = theme.current.value.colors.primary
  
  return {
    labels: growthData.value.labels,
    datasets: [
      {
        label: 'Total Users',
        data: growthData.value.data,
        borderColor: primaryColor,
        backgroundColor: `${primaryColor}33`, // 20% opacity
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  }
})

const chartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      mode: 'index',
      intersect: false,
    },
  },
  scales: {
    x: {
      grid: {
        color: theme.current.value.dark
          ? 'rgba(255, 255, 255, 0.1)'
          : 'rgba(0, 0, 0, 0.1)',
      },
      ticks: {
        color: theme.current.value.dark ? '#FFFFFF' : '#000000',
      },
    },
    y: {
      beginAtZero: true,
      ticks: {
        color: theme.current.value.dark ? '#FFFFFF' : '#000000',
        precision: 0,
      },
      grid: {
        color: theme.current.value.dark
          ? 'rgba(255, 255, 255, 0.1)'
          : 'rgba(0, 0, 0, 0.1)',
      },
    },
  },
}))
</script>

<style scoped>
.user-growth-chart {
  min-height: 300px;
}

.chart-container {
  padding: 16px;
  height: 300px;
}
</style>

