export interface APIKeyRead {
  id: string
  name: string
  description: string | null
  user_id: string
  is_active: boolean
  created_at: string
  last_used: string | null
}

export interface APIKeyCreate {
  name: string
  description?: string | null
}

export interface APIKeyUpdate {
  name?: string | null
  description?: string | null
}

export interface APIKeySecretRead extends APIKeyRead {
  secret: string
}

export interface APIKeyList {
  api_keys: APIKeyRead[]
  total: number
}

