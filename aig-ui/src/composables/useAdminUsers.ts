import { ref } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { getUsers, updateUserRole, unlockUser } from '@/api'
import type { UserList, UserRoleUpdate } from '@/types'

export const useAdminUsers = () => {
  const queryClient = useQueryClient()
  const limit = ref(50)
  const offset = ref(0)

  const {
    data: userList,
    isLoading,
    error,
    refetch,
  } = useQuery<UserList>({
    queryKey: ['admin-users', limit, offset],
    queryFn: () => getUsers({ limit: limit.value, offset: offset.value }),
  })

  const { mutateAsync: changeUserRole, isPending: isUpdatingRole } = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UserRoleUpdate }) =>
      updateUserRole(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
  })

  const { mutateAsync: unlockUserAccount, isPending: isUnlocking } = useMutation({
    mutationFn: (userId: string) => unlockUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
  })

  return {
    userList,
    isLoading,
    error,
    refetch,
    changeUserRole,
    isUpdatingRole,
    unlockUserAccount,
    isUnlocking,
    limit,
    offset,
  }
}

