export enum RequestKind {
  CREDIT_CARD = 'CREDIT_CARD',
  LOAN = 'LOAN',
}

export enum RequestStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}

export interface RequesterInfo {
  id: string
  username: string
  first_name: string
  last_name: string
  email: string | null
  role: string
}

export interface Request {
  id: string
  kind: RequestKind
  payload: Record<string, any>
  status: RequestStatus
  requested_by: string
  requester: RequesterInfo | null
  decided_by: string | null
  decider: RequesterInfo | null
  decided_at: string | null
  created_at: string
}

