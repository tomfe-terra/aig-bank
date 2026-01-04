import { apiClient } from './client'
import type {
  UserList,
  UserRoleUpdate,
  UserRoleUpdateResult,
  BankCapitalBalance,
  LogFileList,
  BankSettings,
} from '@/types'

export const getUsers = async (params?: {
  limit?: number
  offset?: number
}): Promise<UserList> => {
  const response = await apiClient.get<UserList>('/admin/users', { params })
  return response.data
}

export const updateUserRole = async (
  userId: string,
  data: UserRoleUpdate
): Promise<UserRoleUpdateResult> => {
  const response = await apiClient.patch<UserRoleUpdateResult>(`/admin/users/${userId}/role`, data)
  return response.data
}

export const unlockUser = async (userId: string): Promise<{ message: string; id: string }> => {
  const response = await apiClient.post<{ message: string; id: string }>(`/admin/users/${userId}/unlock`)
  return response.data
}

export const getUserAvatar = async (userId: string): Promise<Blob> => {
  const response = await apiClient.get(`/admin/users/${userId}/avatar`, {
    responseType: 'blob',
  })
  return response.data
}

export const getBankCapital = async (): Promise<BankCapitalBalance> => {
  const response = await apiClient.get<BankCapitalBalance>('/admin/bank/capital')
  return response.data
}

export const getLogFiles = async (): Promise<LogFileList> => {
  const response = await apiClient.get<LogFileList>('/admin/logs/files')
  return response.data
}

export const getLogFileContent = async (filename: string): Promise<string> => {
  const response = await apiClient.post<Blob>(
    '/admin/logs/download',
    { filename },
    { responseType: 'blob' }
  )
  return await response.data.text()
}

export const downloadLogFile = async (filename: string): Promise<Blob> => {
  const response = await apiClient.post<Blob>(
    '/admin/logs/download',
    { filename },
    { responseType: 'blob' }
  )
  return response.data
}

export const getSettings = async (): Promise<BankSettings> => {
  const response = await apiClient.get<BankSettings>('/admin/settings')
  return response.data
}

export const getTokenBlacklist = async (): Promise<any> => {
  const response = await apiClient.get('/admin/token-blacklist')
  return response.data
}

