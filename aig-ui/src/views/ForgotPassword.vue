<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { authApi } from '@/api'
import { getErrorMessage } from '@/utils/format'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const theme = useTheme()
const { error: showError, success: showSuccess } = useToast()

// Logo handling - switch based on theme
const logoSrc = computed(() => {
  return theme.global.current.value.dark ? '/dark-logo.png' : '/logo.png'
})

// Stepper state
const step = ref(1)
const isLoading = ref(false)
const successMessage = ref<string | null>(null)

// Step 1: Username
const username = ref('')

// Step 2: Security Questions
const questions = ref<string[]>([])
const answers = ref(['', '', ''])

// Step 3: New Password
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)

// Password complexity requirements
const passwordRequirements = computed(() => {
  const pwd = newPassword.value
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

const passwordsMatch = computed(() => {
  if (!newPassword.value || !confirmPassword.value) return false
  return newPassword.value === confirmPassword.value
})

// Validation rules
const usernameRules = [
  (v: string) => !!v || 'Username is required',
  (v: string) => v.length >= 3 || 'Username must be at least 3 characters',
]

const canProceedStep1 = computed(() => username.value.trim().length >= 3)
const canProceedStep2 = computed(() => answers.value.every(a => a.trim().length > 0))
const canProceedStep3 = computed(() => {
  return Object.values(passwordRequirements.value).every(Boolean) && passwordsMatch.value
})

// Step 1: Fetch security questions
const fetchSecurityQuestions = async () => {
  isLoading.value = true

  try {
    const result = await authApi.getSecurityQuestionsForReset(username.value.trim())
    questions.value = result.questions
    step.value = 2
  } catch (e: unknown) {
    console.error('Failed to fetch security questions:', e)
    showError(getErrorMessage(e, 'Failed to fetch security questions. Please check your username.'))
  } finally {
    isLoading.value = false
  }
}

// Step 2 & 3: Reset password
const resetPassword = async () => {
  isLoading.value = true

  try {
    const result = await authApi.resetPasswordWithAnswers({
      username: username.value.trim(),
      answers: answers.value.map(a => a.trim()),
      new_password: newPassword.value,
    })
    successMessage.value = result.message || 'Password has been successfully reset!'
    showSuccess('Password reset successful!')
    step.value = 4 // Success step
  } catch (e: unknown) {
    console.error('Failed to reset password:', e)
    showError(getErrorMessage(e, 'Failed to reset password. Please check your answers.'))
    // Go back to step 2 if answers were wrong
    const err = e as { response?: { status?: number } }
    if (err.response?.status === 401) {
      step.value = 2
    }
  } finally {
    isLoading.value = false
  }
}

const goBack = () => {
  if (step.value > 1 && step.value < 4) {
    step.value--
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <v-app>
    <v-main>
      <v-container class="fill-height py-8 px-4">
        <v-row align="center" justify="center" class="fill-height">
          <v-col cols="12" md="10" lg="9" xl="8">
            <v-card variant="outlined" class="mx-auto" max-width="1000">
              <v-card-title class="d-flex justify-center align-center pt-8 pb-4 px-6">
                <img
                  :src="logoSrc"
                  alt="AIG Bank"
                  style="max-width: 180px; height: auto; object-fit: contain;"
                />
              </v-card-title>

              <!-- Stepper -->
              <v-stepper 
                v-model="step" 
                :items="['Username', 'Security Questions', 'New Password', 'Complete']"
                hide-actions
                flat
                alt-labels
              >
                <!-- Step 1: Enter Username -->
                <template #item.1>
                  <v-card-text class="pa-6">
                    <div class="text-body-1 text-medium-emphasis mb-4">
                      Enter your username to retrieve your security questions.
                    </div>

                    <v-text-field
                      v-model="username"
                      label="Username"
                      prepend-inner-icon="mdi-account"
                      variant="outlined"
                      :rules="usernameRules"
                      :disabled="isLoading"
                      @keyup.enter="canProceedStep1 && fetchSecurityQuestions()"
                    />

                    <div class="d-flex justify-space-between mt-4">
                      <v-btn
                        variant="text"
                        @click="goToLogin"
                        :disabled="isLoading"
                      >
                        <v-icon start icon="mdi-arrow-left" />
                        Back to Login
                      </v-btn>
                      <v-btn
                        color="primary"
                        :loading="isLoading"
                        :disabled="!canProceedStep1"
                        @click="fetchSecurityQuestions"
                      >
                        Continue
                        <v-icon end icon="mdi-arrow-right" />
                      </v-btn>
                    </div>
                  </v-card-text>
                </template>

                <!-- Step 2: Answer Security Questions -->
                <template #item.2>
                  <v-card-text class="pa-6">
                    <div class="text-body-1 text-medium-emphasis mb-4">
                      Answer all three security questions to verify your identity.
                    </div>

                    <v-alert
                      type="info"
                      variant="tonal"
                      class="mb-4"
                    >
                      <strong>Account:</strong> {{ username }}
                    </v-alert>

                    <div v-for="(question, index) in questions" :key="index" class="mb-4">
                      <div class="text-subtitle-2 mb-2">
                        <v-icon icon="mdi-help-circle" size="small" class="mr-1" />
                        Question {{ index + 1 }}: {{ question }}
                      </div>
                      <v-text-field
                        v-model="answers[index]"
                        :label="`Answer ${index + 1}`"
                        variant="outlined"
                        :disabled="isLoading"
                        density="comfortable"
                      />
                    </div>

                    <div class="d-flex justify-space-between mt-4">
                      <v-btn
                        variant="text"
                        @click="goBack"
                        :disabled="isLoading"
                      >
                        <v-icon start icon="mdi-arrow-left" />
                        Back
                      </v-btn>
                      <v-btn
                        color="primary"
                        :disabled="!canProceedStep2"
                        @click="step = 3"
                      >
                        Continue
                        <v-icon end icon="mdi-arrow-right" />
                      </v-btn>
                    </div>
                  </v-card-text>
                </template>

                <!-- Step 3: Set New Password -->
                <template #item.3>
                  <v-card-text class="pa-6">
                    <p class="text-h6 mb-6">Create a new password for your account</p>
                    
                    <v-row>
                      <!-- Left side: Password fields -->
                      <v-col cols="12" md="6">
                        <v-text-field
                          v-model="newPassword"
                          label="New Password"
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
                          label="Confirm New Password"
                          prepend-inner-icon="mdi-lock-check"
                          :type="showPassword ? 'text' : 'password'"
                          variant="outlined"
                          :disabled="isLoading"
                          required
                          density="comfortable"
                          @keyup.enter="canProceedStep3 && resetPassword()"
                        />
                        
                        <!-- Password Strength Indicator -->
                        <div v-if="newPassword" class="mt-4">
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
                        @click="goBack"
                        :disabled="isLoading"
                      >
                        <v-icon start icon="mdi-arrow-left" />
                        Back
                      </v-btn>
                      <v-btn
                        color="primary"
                        :loading="isLoading"
                        :disabled="!canProceedStep3"
                        @click="resetPassword"
                      >
                        Reset Password
                        <v-icon end icon="mdi-check" />
                      </v-btn>
                    </div>
                  </v-card-text>
                </template>

                <!-- Step 4: Success -->
                <template #item.4>
                  <v-card-text class="pa-6 text-center">
                    <v-icon
                      icon="mdi-check-circle"
                      color="success"
                      size="80"
                      class="mb-4"
                    />

                    <div class="text-h5 mb-2">Password Reset Successful!</div>
                    
                    <div class="text-body-1 text-medium-emphasis mb-6">
                      {{ successMessage || 'Your password has been successfully reset.' }}
                      <br />
                      You can now log in with your new password.
                    </div>

                    <v-btn
                      color="primary"
                      size="large"
                      @click="goToLogin"
                    >
                      <v-icon start icon="mdi-login" />
                      Go to Login
                    </v-btn>
                  </v-card-text>
                </template>
              </v-stepper>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<style scoped>
</style>

