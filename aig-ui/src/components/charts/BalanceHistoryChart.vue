<template>
  <div class="balance-history-chart">
    <div v-if="!transactions || transactions.length === 0" class="text-center pa-8 text-medium-emphasis">
      No transaction history available
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
import type { TransactionRead } from '@/types'
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
  transactions: TransactionRead[] | undefined
  currentBalance: number // balance in cents
}>()

const theme = useTheme()

const balanceHistory = computed(() => {
  if (!props.transactions || props.transactions.length === 0) {
    return { labels: [], data: [] }
  }

  // Sort all transactions by date (oldest first)
  const sortedTransactions = [...props.transactions].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )

  // Calculate the starting balance (before first transaction)
  // Start from current balance and subtract all transactions
  let startingBalance = props.currentBalance
  for (let i = sortedTransactions.length - 1; i >= 0; i--) {
    startingBalance -= sortedTransactions[i].amount_cents
  }

  // Build the chart data
  const balances: number[] = [startingBalance]
  const labels: string[] = []
  let runningBalance = startingBalance

  // Add starting point
  if (sortedTransactions.length > 0) {
    const firstDate = new Date(sortedTransactions[0].created_at)
    labels.push(firstDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
  }

  // Add all transactions
  for (const txn of sortedTransactions) {
    runningBalance += txn.amount_cents
    balances.push(runningBalance)
    const date = new Date(txn.created_at)
    labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
  }

  return {
    labels,
    data: balances.map((balance) => balance / 100), // Convert to dollars
  }
})

const chartData = computed<ChartData<'line'>>(() => {
  const primaryColor = theme.current.value.colors.primary
  
  return {
    labels: balanceHistory.value.labels,
    datasets: [
      {
        label: 'Account Balance',
        data: balanceHistory.value.data,
        borderColor: primaryColor,
        backgroundColor: `${primaryColor}33`, // 20% opacity
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: primaryColor,
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
      callbacks: {
        label: (context) => {
          const value = context.parsed.y
          return value !== null ? `Balance: $${value.toFixed(2)}` : 'Balance: $0.00'
        },
      },
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
        maxRotation: 45,
        minRotation: 45,
      },
    },
    y: {
      beginAtZero: false,
      ticks: {
        color: theme.current.value.dark ? '#FFFFFF' : '#000000',
        callback: (value) => {
          return '$' + Number(value).toFixed(0)
        },
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
.balance-history-chart {
  min-height: 300px;
}

.chart-container {
  padding: 16px;
  height: 300px;
}
</style>

