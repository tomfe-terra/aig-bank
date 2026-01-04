import { apiClient } from './client'
import type {
  LoginRequest,
  TokenPair,
  AccessToken,
  ProfileRead,
  ProfileUpdate,
  ProfileUpdateResult,
  AvatarUploadResult,
  StartRegistrationRequest,
  RegistrationToken,
  SetSecurityQuestionsRequest,
  OTPSetup,
  VerifyOTPRequest,
  RegistrationComplete,
  SecurityQuestionsList,
  SecurityQuestionsForReset,
  PasswordResetWithAnswers,
  PasswordResetConfirmation,
} from '@/types'

export const authApi = {
  async login(credentials: LoginRequest): Promise<TokenPair> {
    const response = await apiClient.post<TokenPair>('/users/auth/login', credentials)
    return response.data
  },

  async refreshToken(refreshToken: string): Promise<AccessToken> {
    const response = await apiClient.post<AccessToken>('/users/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  async logout(refreshToken?: string): Promise<{ message: string }> {
    const response = await apiClient.post('/users/auth/logout', {
      refresh_token: refreshToken || null,
    })
    return response.data
  },

  async getCurrentUser(): Promise<ProfileRead> {
    const response = await apiClient.get<ProfileRead>('/users/auth/me')
    return response.data
  },

  async updateProfile(data: ProfileUpdate): Promise<ProfileUpdateResult> {
    const response = await apiClient.patch<ProfileUpdateResult>('/users/profile', data)
    return response.data
  },

  async getAvatar(): Promise<Blob> {
    const response = await apiClient.get('/users/profile/avatar', {
      responseType: 'blob',
    })
    return response.data
  },

  async uploadAvatar(file: File): Promise<AvatarUploadResult> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<AvatarUploadResult>('/users/profile/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async deleteAvatar(): Promise<{ message: string }> {
    const response = await apiClient.delete('/users/profile/avatar')
    return response.data
  },

  async startRegistration(data: StartRegistrationRequest): Promise<RegistrationToken> {
    const response = await apiClient.post<RegistrationToken>('/users/register/start', data)
    return response.data
  },

  async getSecurityQuestions(): Promise<SecurityQuestionsList> {
    const response = await apiClient.get<SecurityQuestionsList>('/users/register/security-questions')
    return response.data
  },

  async setSecurityQuestions(data: SetSecurityQuestionsRequest): Promise<OTPSetup> {
    const response = await apiClient.post<OTPSetup>('/users/register/security-questions', data)
    return response.data
  },

  async verifyOTP(data: VerifyOTPRequest): Promise<RegistrationComplete> {
    const response = await apiClient.post<RegistrationComplete>('/users/register/verify-otp', data)
    return response.data
  },

  async getSecurityQuestionsForReset(username: string): Promise<SecurityQuestionsForReset> {
    const response = await apiClient.post<SecurityQuestionsForReset>(
      '/users/auth/password-reset/security-questions',
      { username }
    )
    return response.data
  },

  async resetPasswordWithAnswers(data: PasswordResetWithAnswers): Promise<PasswordResetConfirmation> {
    const response = await apiClient.post<PasswordResetConfirmation>(
      '/users/auth/password-reset/security-answers',
      data
    )
    return response.data
  },
}

