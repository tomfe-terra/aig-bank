export enum UserRole {
  USER = 'USER',
  BANKER = 'BANKER',
  ADMIN = 'ADMIN',
}

export enum UserStatus {
  ENABLED = 'ENABLED',
  DISABLED = 'DISABLED',
}

export interface UserRead {
  id: string
  username: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  address: string | null
  role: UserRole
  status: UserStatus
  has_avatar: boolean
}

export interface ProfileUpdate {
  first_name?: string | null
  last_name?: string | null
  email?: string | null
  phone?: string | null
  address?: string | null
}

export interface ProfileUpdateResult {
  message: string
  user: UserRead
}

export interface AvatarUploadResult {
  message: string
  has_avatar: boolean
}

export interface ProfileRead {
  user: UserRead
  account: {
    id: string
    number: string
    user_id: string
    balance_cents: number
    balance_dollars: number
    created_at: string
    updated_at: string | null
  } | null
  api_keys: Array<{
    id: string
    name: string
    description: string | null
    user_id: string
    is_active: boolean
    created_at: string
    last_used: string | null
  }>
}

export interface LoginRequest {
  username: string
  password: string
  otp_code: string
}

export interface TokenPair {
  access_token: string
  access_token_expires_at: string
  refresh_token: string
  refresh_token_expires_at: string
}

export interface AccessToken {
  access_token: string
  access_token_expires_at: string
}

export interface StartRegistrationRequest {
  username: string
  password: string
  first_name: string
  last_name: string
  email?: string | null
  phone?: string | null
  address?: string | null
}

export interface RegistrationToken {
  message: string
  token: string
}

export interface SecurityQuestionAnswer {
  question_id: number
  answer: string
}

export interface SetSecurityQuestionsRequest {
  token: string
  security_questions: SecurityQuestionAnswer[]
}

export interface OTPSetup {
  message: string
  token: string
  otp_uri: string
  otp_secret: string
}

export interface VerifyOTPRequest {
  token: string
  otp_code: string
}

export interface RegistrationComplete {
  message: string
  id: string
  username: string
}

export interface SecurityQuestion {
  id: number
  question: string
}

export interface SecurityQuestionsList {
  questions: SecurityQuestion[]
}

export interface SecurityQuestionsLookup {
  username: string
}

export interface SecurityQuestionsForReset {
  questions: string[]
  message: string
}

export interface PasswordResetWithAnswers {
  username: string
  answers: string[]
  new_password: string
}

export interface PasswordResetConfirmation {
  message: string
}

