import { ref, computed } from 'vue'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { authApi } from '@/api'
import { useAuth } from './useAuth'
import type { ProfileUpdate } from '@/types'
import { getErrorMessage } from '@/utils/format'

export function useProfile() {
  const queryClient = useQueryClient()
  const { user, refreshProfile } = useAuth()
  
  const avatarUrl = ref<string | null>(null)
  const isLoadingAvatar = ref(false)
  const avatarError = ref<string | null>(null)

  const hasAvatar = computed(() => user.value?.has_avatar ?? false)

  const updateProfileMutation = useMutation({
    mutationFn: (data: ProfileUpdate) => authApi.updateProfile(data),
    onSuccess: async () => {
      await refreshProfile()
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
  })

  const uploadAvatarMutation = useMutation({
    mutationFn: (file: File) => authApi.uploadAvatar(file),
    onSuccess: async () => {
      await refreshProfile()
      await loadAvatar()
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
  })

  const deleteAvatarMutation = useMutation({
    mutationFn: () => authApi.deleteAvatar(),
    onSuccess: async () => {
      avatarUrl.value = null
      await refreshProfile()
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
  })

  const loadAvatar = async () => {
    if (!hasAvatar.value) {
      avatarUrl.value = null
      return
    }

    isLoadingAvatar.value = true
    avatarError.value = null

    try {
      const blob = await authApi.getAvatar()
      if (avatarUrl.value) {
        URL.revokeObjectURL(avatarUrl.value)
      }
      avatarUrl.value = URL.createObjectURL(blob)
    } catch (e: unknown) {
      console.error('Failed to load avatar:', e)
      avatarError.value = getErrorMessage(e, 'Failed to load avatar')
      avatarUrl.value = null
    } finally {
      isLoadingAvatar.value = false
    }
  }

  const updateProfile = async (data: ProfileUpdate) => {
    return updateProfileMutation.mutateAsync(data)
  }

  const uploadAvatar = async (file: File) => {
    return uploadAvatarMutation.mutateAsync(file)
  }

  const deleteAvatar = async () => {
    return deleteAvatarMutation.mutateAsync()
  }

  return {
    user,
    hasAvatar,
    avatarUrl,
    isLoadingAvatar,
    avatarError,
    loadAvatar,
    updateProfile,
    isUpdatingProfile: computed(() => updateProfileMutation.isPending.value),
    uploadAvatar,
    isUploadingAvatar: computed(() => uploadAvatarMutation.isPending.value),
    deleteAvatar,
    isDeletingAvatar: computed(() => deleteAvatarMutation.isPending.value),
  }
}

