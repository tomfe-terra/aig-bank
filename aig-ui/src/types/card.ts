export enum CardBrand {
  VISA = 'VISA',
  MASTERCARD = 'MASTERCARD',
  AMERICAN_EXPRESS = 'AMERICAN_EXPRESS',
  DISCOVER = 'DISCOVER',
  UNKNOWN = 'UNKNOWN',
}

export enum CardStatus {
  ACTIVE = 'ACTIVE',
  CANCELLED = 'CANCELLED',
  EXPIRED = 'EXPIRED',
}

export interface CardRead {
  id: string
  account_id: string
  last4: string
  brand: CardBrand
  exp_month: number
  exp_year: number
  status: CardStatus
  created_at: string
  is_expired: boolean
}

export interface CardRequestCreate {
  card_type: CardBrand
}

export interface CardReveal {
  card_id: string
  pan: string
  cvv: string
  brand: string
  exp_month: number
  exp_year: number
}

export interface CardOwnerInfo {
  id: string
  username: string
  first_name: string
  last_name: string
  email: string | null
  role: string
}

export interface BankerCardView {
  id: string
  last4: string
  brand: CardBrand
  status: CardStatus
  created_at: string
  owner: CardOwnerInfo
}

export interface BankerCardList {
  cards: BankerCardView[]
  total: number
}

