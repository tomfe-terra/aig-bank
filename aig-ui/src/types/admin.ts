import type { UserRole, UserStatus } from './auth'

export interface UserListItem {
  id: string
  username: string
  email: string | null
  role: UserRole
  status: UserStatus
  is_locked: boolean
  created_at: string
  has_avatar: boolean
}

export interface UserList {
  users: UserListItem[]
  total: number
  limit: number
  offset: number
}

export interface UserRoleUpdate {
  role: UserRole
}

export interface UserRoleUpdateResult {
  user_id: string
  old_role: UserRole
  new_role: UserRole
  updated_at: string
}

export interface BankCapitalBalance {
  account_number: string
  balance_cents: number
  balance_dollars: number
  updated_at: string | null
}

export interface LogFileInfo {
  filename: string
  size_bytes: number
  modified_at: string
}

export interface LogFileList {
  files: LogFileInfo[]
}

export interface LogFileContent {
  filename: string
  lines: string[]
  total_lines: number
  returned_lines: number
}

export interface BankSettings {
  [key: string]: any
}

