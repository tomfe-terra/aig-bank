import type { Request } from './request'

export interface RequestList {
  requests: Request[]
  total: number
}

export interface RequestDecision {
  request_id: string
  decided_by: string
  decided_at: string
  status: string
}

export interface RequestRejection {
  reason?: string
}

