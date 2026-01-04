import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

const show = ref(false)
const message = ref('')
const type = ref<ToastType>('info')
const timeout = ref(3000)

export function useToast() {
  const showToast = (msg: string, toastType: ToastType = 'info', toastTimeout?: number) => {
    message.value = msg
    type.value = toastType
    timeout.value = toastTimeout || (toastType === 'error' ? 5000 : 3000)
    show.value = true
  }

  const success = (msg: string) => {
    showToast(msg, 'success')
  }

  const error = (msg: string) => {
    showToast(msg, 'error', 5000)
  }

  const warning = (msg: string) => {
    showToast(msg, 'warning')
  }

  const info = (msg: string) => {
    showToast(msg, 'info')
  }

  return {
    show,
    message,
    type,
    timeout,
    showToast,
    success,
    error,
    warning,
    info,
  }
}

