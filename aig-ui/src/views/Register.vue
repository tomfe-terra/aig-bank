<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { authApi } from '@/api'
import type { SecurityQuestion } from '@/types'
import { getErrorMessage } from '@/utils/format'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const theme = useTheme()
const { success, error: showError } = useToast()

// Logo handling - switch based on theme
const logoSrc = computed(() => {
  return theme.global.current.value.dark ? '/dark-logo.png' : '/logo.png'
})

const step = ref(1)
const uiStep = ref(1) // UI step for display (splits step 1 into 1 and 2)
const isLoading = ref(false)

// Step 1: Basic Info
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const phone = ref('')
const address = ref('')
const showPassword = ref(false)
const registrationToken = ref('')

// Password complexity requirements
const passwordRequirements = computed(() => {
  const pwd = password.value
  return {
    minLength: pwd.length >= 8,
    hasUppercase: /[A-Z]/.test(pwd),
    hasLowercase: /[a-z]/.test(pwd),
    hasNumber: /[0-9]/.test(pwd),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(pwd),
  }
})

const passwordStrength = computed(() => {
  const reqs = passwordRequirements.value
  const score = Object.values(reqs).filter(Boolean).length
  
  if (score === 5) return { label: 'Strong', color: 'success', value: 100 }
  if (score >= 4) return { label: 'Good', color: 'info', value: 80 }
  if (score >= 3) return { label: 'Fair', color: 'warning', value: 60 }
  if (score >= 2) return { label: 'Weak', color: 'orange', value: 40 }
  return { label: 'Very Weak', color: 'error', value: 20 }
})

const isPasswordValid = computed(() => {
  return Object.values(passwordRequirements.value).every(Boolean) && passwordsMatch.value
})

const passwordsMatch = computed(() => {
  if (!password.value || !confirmPassword.value) return false
  return password.value === confirmPassword.value
})

// Step 2: Security Questions
const availableQuestions = ref<SecurityQuestion[]>([])
const selectedQuestion1 = ref<number | null>(null)
const selectedQuestion2 = ref<number | null>(null)
const selectedQuestion3 = ref<number | null>(null)
const answer1 = ref('')
const answer2 = ref('')
const answer3 = ref('')

// Step 3: OTP Setup
const otpSecret = ref('')
const otpUri = ref('')
const otpCode = ref('')

onMounted(async () => {
  try {
    const questions = await authApi.getSecurityQuestions()
    availableQuestions.value = questions.questions
  } catch (e) {
    console.error('Failed to load security questions:', e)
  }
})

// Handle UI step 1 (basic info) - just move to next UI step
const handleUIStep1 = () => {
  if (!firstName.value || !lastName.value || !username.value) {
    showError('Please fill in all required fields')
    return
  }
  uiStep.value = 2
}

// Handle UI step 2 (password) - actually submit step 1 to backend
const handleStep1 = async () => {
  if (!isPasswordValid.value) {
    showError('Password does not meet complexity requirements')
    return
  }
  
  if (password.value !== confirmPassword.value) {
    showError('Passwords do not match')
    return
  }
  
  isLoading.value = true
  
  try {
    const response = await authApi.startRegistration({
      username: username.value,
      password: password.value,
      first_name: firstName.value,
      last_name: lastName.value,
      email: email.value || null,
      phone: phone.value || null,
      address: address.value || null,
    })
    
    registrationToken.value = response.token
    step.value = 2
    uiStep.value = 3
    success('Account created! Please set up security questions.')
  } catch (e: unknown) {
    showError(getErrorMessage(e, 'Registration failed'))
  } finally {
    isLoading.value = false
  }
}

const handleStep2 = async () => {
  if (!selectedQuestion1.value || !selectedQuestion2.value || !selectedQuestion3.value) {
    showError('Please select all 3 security questions')
    return
  }
  
  if (!answer1.value || !answer2.value || !answer3.value) {
    showError('Please answer all security questions')
    return
  }
  
  isLoading.value = true
  
  try {
    const response = await authApi.setSecurityQuestions({
      token: registrationToken.value,
      security_questions: [
        { question_id: selectedQuestion1.value, answer: answer1.value },
        { question_id: selectedQuestion2.value, answer: answer2.value },
        { question_id: selectedQuestion3.value, answer: answer3.value },
      ],
    })
    
    registrationToken.value = response.token
    otpSecret.value = response.otp_secret
    otpUri.value = response.otp_uri
    step.value = 3
    uiStep.value = 4
    success('Security questions set! Now set up 2FA.')
  } catch (e: unknown) {
    showError(getErrorMessage(e, 'Failed to set security questions'))
  } finally {
    isLoading.value = false
  }
}

const handleStep3 = async () => {
  if (!otpCode.value || otpCode.value.length !== 6) {
    showError('Please enter a valid 6-digit OTP code')
    return
  }
  
  isLoading.value = true
  
  try {
    await authApi.verifyOTP({
      token: registrationToken.value,
      otp_code: otpCode.value,
    })
    
    // Registration complete, redirect to login
    success('Registration complete! Please log in.')
    router.push({
      path: '/login',
      query: { registered: 'true' },
    })
  } catch (e: unknown) {
    showError(getErrorMessage(e, 'Invalid OTP code'))
  } finally {
    isLoading.value = false
  }
}

const getAvailableQuestions = (excludeIds: (number | null)[]) => {
  return availableQuestions.value.filter(q => !excludeIds.includes(q.id))
}
</script>

<template>
  <v-app>
    <v-main class="d-flex flex-column" style="min-height: 100vh;">
      <!-- Header with Logo -->
      <div class="d-flex justify-center align-center py-8">
        <img
          :src="logoSrc"
          alt="AIG Bank"
          style="max-width: 200px; height: auto; object-fit: contain;"
        />
      </div>
      
      <!-- Main Content Area -->
      <v-container class="flex-grow-1 py-0" style="max-width: 900px;">
        <v-stepper 
          v-model="uiStep" 
          alt-labels
          hide-actions
          flat
          class="elevation-0"
        >
          <v-stepper-header>
            <v-stepper-item title="Basic Info" :value="1" :complete="uiStep > 1" />
            <v-divider />
            <v-stepper-item title="Set Password" :value="2" :complete="uiStep > 2" />
            <v-divider />
            <v-stepper-item title="Security Questions" :value="3" :complete="uiStep > 3" />
            <v-divider />
            <v-stepper-item title="Setup 2FA" :value="4" :complete="uiStep > 4" />
          </v-stepper-header>

          <v-stepper-window v-model="uiStep">
                <!-- UI Step 1: Basic Info -->
                <v-stepper-window-item :value="1">
                  <v-card flat class="mx-auto" style="max-width: 700px;">
                    <v-card-text class="px-8 pt-6 pb-8">
                        <v-row dense>
                          <v-col cols="12" sm="6">
                            <v-text-field
                              v-model="firstName"
                              label="First Name"
                              prepend-inner-icon="mdi-account"
                              variant="outlined"
                              :disabled="isLoading"
                              required
                              density="comfortable"
                            />
                          </v-col>
                          <v-col cols="12" sm="6">
                            <v-text-field
                              v-model="lastName"
                              label="Last Name"
                              prepend-inner-icon="mdi-account"
                              variant="outlined"
                              :disabled="isLoading"
                              required
                              density="comfortable"
                            />
                          </v-col>
                        </v-row>
                        
                        <v-text-field
                          v-model="username"
                          label="Username"
                          prepend-inner-icon="mdi-account-circle"
                          variant="outlined"
                          :disabled="isLoading"
                          required
                          density="comfortable"
                          class="mt-2"
                        />
                        
                        <v-row dense class="mt-2">
                          <v-col cols="12" sm="6">
                            <v-text-field
                              v-model="email"
                              label="Email (optional)"
                              prepend-inner-icon="mdi-email"
                              variant="outlined"
                              type="email"
                              :disabled="isLoading"
                              density="comfortable"
                            />
                          </v-col>
                          <v-col cols="12" sm="6">
                            <v-text-field
                              v-model="phone"
                              label="Phone (optional)"
                              prepend-inner-icon="mdi-phone"
                              variant="outlined"
                              :disabled="isLoading"
                              density="comfortable"
                            />
                          </v-col>
                        </v-row>
                        
                        <div class="d-flex justify-end mt-4">
                          <v-btn
                            color="primary"
                            :disabled="!username || !firstName || !lastName"
                            @click="handleUIStep1"
                          >
                            Continue
                            <v-icon end icon="mdi-arrow-right" />
                          </v-btn>
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-stepper-window-item>
                  
                  <!-- UI Step 2: Set Password -->
                  <v-stepper-window-item :value="2">
                    <v-card flat class="mx-auto" style="max-width: 900px;">
                      <v-card-text class="px-8 pt-6 pb-8">
                        <p class="text-h6 mb-6">Create a secure password for your account</p>
                        
                        <v-row>
                          <!-- Left side: Password fields -->
                          <v-col cols="12" md="6">
                            <v-text-field
                              v-model="password"
                              label="Password"
                              prepend-inner-icon="mdi-lock"
                              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                              :type="showPassword ? 'text' : 'password'"
                              variant="outlined"
                              :disabled="isLoading"
                              required
                              density="comfortable"
                              class="mb-4"
                              @click:append-inner="showPassword = !showPassword"
                            />
                            
                            <v-text-field
                              v-model="confirmPassword"
                              label="Confirm Password"
                              prepend-inner-icon="mdi-lock-check"
                              :type="showPassword ? 'text' : 'password'"
                              variant="outlined"
                              :disabled="isLoading"
                              required
                              density="comfortable"
                            />
                            
                            <!-- Password Strength Indicator -->
                            <div v-if="password" class="mt-4">
                              <div class="d-flex justify-space-between align-center mb-2">
                                <span class="text-body-2 font-weight-medium">Password Strength:</span>
                                <span class="text-body-2 font-weight-bold" :class="`text-${passwordStrength.color}`">
                                  {{ passwordStrength.label }}
                                </span>
                              </div>
                              <v-progress-linear
                                :model-value="passwordStrength.value"
                                :color="passwordStrength.color"
                                height="8"
                                rounded
                              />
                            </div>
                          </v-col>
                          
                          <!-- Right side: Requirements -->
                          <v-col cols="12" md="6">
                            <v-card variant="tonal" class="pa-4">
                              <div class="text-body-2 font-weight-bold mb-3">Password Requirements:</div>
                              <v-list density="compact" class="bg-transparent pa-0">
                                <v-list-item class="px-0 py-1 min-height-0">
                                  <template #prepend>
                                    <v-icon 
                                      :icon="passwordRequirements.minLength ? 'mdi-check-circle' : 'mdi-circle-outline'" 
                                      :color="passwordRequirements.minLength ? 'success' : 'medium-emphasis'"
                                      size="small"
                                      class="mr-2"
                                    />
                                  </template>
                                  <span class="text-body-2">At least 8 characters</span>
                                </v-list-item>
                                <v-list-item class="px-0 py-1 min-height-0">
                                  <template #prepend>
                                    <v-icon 
                                      :icon="passwordRequirements.hasUppercase ? 'mdi-check-circle' : 'mdi-circle-outline'" 
                                      :color="passwordRequirements.hasUppercase ? 'success' : 'medium-emphasis'"
                                      size="small"
                                      class="mr-2"
                                    />
                                  </template>
                                  <span class="text-body-2">One uppercase letter (A-Z)</span>
                                </v-list-item>
                                <v-list-item class="px-0 py-1 min-height-0">
                                  <template #prepend>
                                    <v-icon 
                                      :icon="passwordRequirements.hasLowercase ? 'mdi-check-circle' : 'mdi-circle-outline'" 
                                      :color="passwordRequirements.hasLowercase ? 'success' : 'medium-emphasis'"
                                      size="small"
                                      class="mr-2"
                                    />
                                  </template>
                                  <span class="text-body-2">One lowercase letter (a-z)</span>
                                </v-list-item>
                                <v-list-item class="px-0 py-1 min-height-0">
                                  <template #prepend>
                                    <v-icon 
                                      :icon="passwordRequirements.hasNumber ? 'mdi-check-circle' : 'mdi-circle-outline'" 
                                      :color="passwordRequirements.hasNumber ? 'success' : 'medium-emphasis'"
                                      size="small"
                                      class="mr-2"
                                    />
                                  </template>
                                  <span class="text-body-2">One number (0-9)</span>
                                </v-list-item>
                                <v-list-item class="px-0 py-1 min-height-0">
                                  <template #prepend>
                                    <v-icon 
                                      :icon="passwordRequirements.hasSpecial ? 'mdi-check-circle' : 'mdi-circle-outline'" 
                                      :color="passwordRequirements.hasSpecial ? 'success' : 'medium-emphasis'"
                                      size="small"
                                      class="mr-2"
                                    />
                                  </template>
                                  <span class="text-body-2">One special character (!@#$%^&*...)</span>
                                </v-list-item>
                                
                                <v-divider class="my-3" />
                                
                                <!-- Password Match Verification -->
                                <v-list-item class="px-0 py-1 min-height-0">
                                  <template #prepend>
                                    <v-icon 
                                      :icon="passwordsMatch ? 'mdi-check-circle' : 'mdi-circle-outline'" 
                                      :color="passwordsMatch ? 'success' : 'medium-emphasis'"
                                      size="small"
                                      class="mr-2"
                                    />
                                  </template>
                                  <span class="text-body-2">Passwords match</span>
                                </v-list-item>
                              </v-list>
                            </v-card>
                          </v-col>
                        </v-row>
                        
                        <div class="d-flex justify-space-between mt-4">
                          <v-btn
                            variant="text"
                            @click="uiStep = 1"
                            :disabled="isLoading"
                          >
                            <v-icon start icon="mdi-arrow-left" />
                            Back
                          </v-btn>
                          <v-btn
                            color="primary"
                            :loading="isLoading"
                            :disabled="!isPasswordValid"
                            @click="handleStep1"
                          >
                            Continue
                            <v-icon end icon="mdi-arrow-right" />
                          </v-btn>
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-stepper-window-item>
                  
                  <!-- UI Step 3: Security Questions (Backend Step 2) -->
                  <v-stepper-window-item :value="3">
                  <v-card flat class="mx-auto" style="max-width: 700px;">
                    <v-card-text class="px-8 pt-6 pb-8">
                        <p class="text-body-2 mb-4">Select and answer 3 security questions for account recovery:</p>
                        
                        <v-select
                          v-model="selectedQuestion1"
                          :items="getAvailableQuestions([selectedQuestion2, selectedQuestion3])"
                          item-title="question"
                          item-value="id"
                          label="Security Question 1"
                          variant="outlined"
                          :disabled="isLoading"
                          required
                        />
                        
                        <v-text-field
                          v-model="answer1"
                          label="Answer 1"
                          variant="outlined"
                          :disabled="isLoading || !selectedQuestion1"
                          required
                        />
                        
                        <v-select
                          v-model="selectedQuestion2"
                          :items="getAvailableQuestions([selectedQuestion1, selectedQuestion3])"
                          item-title="question"
                          item-value="id"
                          label="Security Question 2"
                          variant="outlined"
                          :disabled="isLoading"
                          required
                        />
                        
                        <v-text-field
                          v-model="answer2"
                          label="Answer 2"
                          variant="outlined"
                          :disabled="isLoading || !selectedQuestion2"
                          required
                        />
                        
                        <v-select
                          v-model="selectedQuestion3"
                          :items="getAvailableQuestions([selectedQuestion1, selectedQuestion2])"
                          item-title="question"
                          item-value="id"
                          label="Security Question 3"
                          variant="outlined"
                          :disabled="isLoading"
                          required
                        />
                        
                        <v-text-field
                          v-model="answer3"
                          label="Answer 3"
                          variant="outlined"
                          :disabled="isLoading || !selectedQuestion3"
                          required
                        />
                        
                        <div class="d-flex justify-space-between mt-4">
                          <v-btn
                            variant="text"
                            :disabled="isLoading"
                            @click="uiStep = 2"
                          >
                            <v-icon start icon="mdi-arrow-left" />
                            Back
                          </v-btn>
                          <v-btn
                            color="primary"
                            :loading="isLoading"
                            :disabled="!selectedQuestion1 || !selectedQuestion2 || !selectedQuestion3 || !answer1 || !answer2 || !answer3"
                            @click="handleStep2"
                          >
                            Continue
                            <v-icon end icon="mdi-arrow-right" />
                          </v-btn>
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-stepper-window-item>
                  
                  <!-- UI Step 4: Setup 2FA (Backend Step 3) -->
                  <v-stepper-window-item :value="4">
                  <v-card flat class="mx-auto" style="max-width: 700px;">
                    <v-card-text class="px-8 pt-6 pb-8">
                        <p class="text-body-2 mb-4">Set up two-factor authentication (2FA):</p>
                        
                        <v-alert type="info" variant="tonal" class="mb-4">
                          <p class="font-weight-bold">Scan this QR code with your authenticator app:</p>
                          <p class="text-caption">Google Authenticator, Authy, or similar</p>
                        </v-alert>
                        
                        <div v-if="otpUri" class="text-center my-4">
                          <img :src="`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(otpUri)}`" alt="QR Code" />
                        </div>
                        
                        <v-text-field
                          v-model="otpSecret"
                          label="Manual Entry Code"
                          variant="outlined"
                          readonly
                          hint="Use this if you can't scan the QR code"
                          persistent-hint
                          class="mb-4"
                        />
                        
                        <v-text-field
                          v-model="otpCode"
                          label="Enter 6-digit OTP Code"
                          prepend-inner-icon="mdi-shield-key"
                          variant="outlined"
                          :disabled="isLoading"
                          maxlength="6"
                          placeholder="123456"
                          hint="Enter the code from your authenticator app"
                          persistent-hint
                          required
                        />
                        
                        <div class="d-flex justify-space-between mt-4">
                          <v-btn
                            variant="text"
                            :disabled="isLoading"
                            @click="uiStep = 3"
                          >
                            <v-icon start icon="mdi-arrow-left" />
                            Back
                          </v-btn>
                          <v-btn
                            color="primary"
                            :loading="isLoading"
                            :disabled="!otpCode || otpCode.length !== 6"
                            @click="handleStep3"
                          >
                            Complete Registration
                            <v-icon end icon="mdi-check" />
                          </v-btn>
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-stepper-window-item>
          </v-stepper-window>
        </v-stepper>
        
        <!-- Footer with Login Link -->
        <div class="text-center py-8">
          <v-btn
            variant="text"
            color="primary"
            to="/login"
            :disabled="isLoading"
          >
            Already have an account? Login
          </v-btn>
        </div>
      </v-container>
    </v-main>
  </v-app>
</template>

<style scoped>
</style>
