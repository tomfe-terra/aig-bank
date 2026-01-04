import { ref, computed } from 'vue'
import { authApi } from '@/api'
import type { ProfileRead, LoginRequest, UserRole } from '@/types'
import { getErrorMessage } from '@/utils/format'

const profile = ref<ProfileRead | null>(null)
const user = computed(() => profile.value?.user || null)
const isLoading = ref(false)
const error = ref<string | null>(null)

let refreshTimer: ReturnType<typeof setTimeout> | null = null

const clearRefreshTimer = () => {
  if (refreshTimer) {
    clearTimeout(refreshTimer)
    refreshTimer = null
  }
}

const performTokenRefresh = async () => {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    clearRefreshTimer()
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('access_token_expires_at')
    localStorage.removeItem('refresh_token_expires_at')
    localStorage.removeItem('profile')
    profile.value = null
    window.location.href = '/login'
    return
  }

  try {
    const { access_token, access_token_expires_at } = await authApi.refreshToken(refreshToken)
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('access_token_expires_at', access_token_expires_at)
    scheduleTokenRefresh()
  } catch (e) {
    console.error('Token refresh failed:', e)
    clearRefreshTimer()
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('access_token_expires_at')
    localStorage.removeItem('refresh_token_expires_at')
    localStorage.removeItem('profile')
    profile.value = null
    window.location.href = '/login'
  }
}

const scheduleTokenRefresh = () => {
  clearRefreshTimer()

  const expiresAt = localStorage.getItem('access_token_expires_at')
  if (!expiresAt) return

  const expiresAtMs = new Date(expiresAt).getTime()
  const now = Date.now()
  const refreshAt = expiresAtMs - 60 * 1000

  if (refreshAt <= now) {
    performTokenRefresh()
  } else {
    refreshTimer = setTimeout(performTokenRefresh, refreshAt - now)
  }
}

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value)
  const userRole = computed(() => user.value?.role)
  const account = computed(() => profile.value?.account || null)

  const initAuth = async () => {
    const storedProfile = localStorage.getItem('profile')
    const token = localStorage.getItem('access_token')
    
    if (storedProfile) {
      try {
        profile.value = JSON.parse(storedProfile)
      } catch (e) {
        console.error('Failed to parse stored profile:', e)
        localStorage.removeItem('profile')
      }
    }
    
    if (token && !profile.value) {
      try {
        const userProfile = await authApi.getCurrentUser()
        profile.value = userProfile
        localStorage.setItem('profile', JSON.stringify(userProfile))
      } catch (e) {
        console.error('Failed to fetch user profile:', e)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('access_token_expires_at')
        localStorage.removeItem('refresh_token_expires_at')
      }
    }

    if (localStorage.getItem('access_token')) {
      scheduleTokenRefresh()
    }
  }

  const login = async (credentials: LoginRequest) => {
    isLoading.value = true
    error.value = null
    
    try {
      const tokens = await authApi.login(credentials)
      
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      localStorage.setItem('access_token_expires_at', tokens.access_token_expires_at)
      localStorage.setItem('refresh_token_expires_at', tokens.refresh_token_expires_at)
      
      const userProfile = await authApi.getCurrentUser()
      localStorage.setItem('profile', JSON.stringify(userProfile))
      profile.value = userProfile
      
      scheduleTokenRefresh()
      
      return userProfile.user
    } catch (e: unknown) {
      error.value = getErrorMessage(e, 'Login failed')
      throw e
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    
    clearRefreshTimer()
    
    try {
      await authApi.logout(refreshToken || undefined)
    } catch (e) {
      console.error('Logout error:', e)
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('access_token_expires_at')
      localStorage.removeItem('refresh_token_expires_at')
      localStorage.removeItem('profile')
      profile.value = null
    }
  }

  const refreshProfile = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    
    try {
      const userProfile = await authApi.getCurrentUser()
      profile.value = userProfile
      localStorage.setItem('profile', JSON.stringify(userProfile))
    } catch (e) {
      console.error('Failed to refresh profile:', e)
      throw e
    }
  }

  const hasRole = (role: UserRole) => {
    return user.value?.role === role
  }

  const isUser = computed(() => hasRole('USER' as UserRole))
  const isBanker = computed(() => hasRole('BANKER' as UserRole))
  const isAdmin = computed(() => hasRole('ADMIN' as UserRole))

  return {
    profile,
    user,
    account,
    isLoading,
    error,
    isAuthenticated,
    userRole,
    isUser,
    isBanker,
    isAdmin,
    initAuth,
    login,
    logout,
    refreshProfile,
    hasRole,
    scheduleTokenRefresh,
  }
}

