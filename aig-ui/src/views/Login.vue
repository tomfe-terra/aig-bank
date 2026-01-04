<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useAuth } from '@/composables/useAuth'
import { UserRole } from '@/types'

const router = useRouter()
const theme = useTheme()
const { login, error, isLoading } = useAuth()

// Logo handling - switch based on theme
const logoSrc = computed(() => {
  return theme.global.current.value.dark ? '/dark-logo.png' : '/logo.png'
})

const username = ref('')
const password = ref('')
const otpCode = ref('')
const showPassword = ref(false)

const handleLogin = async () => {
  try {
    const user = await login({
      username: username.value,
      password: password.value,
      otp_code: otpCode.value,
    })
    
    // Redirect based on role
    if (user.role === UserRole.USER) {
      router.push('/user/dashboard')
    } else if (user.role === UserRole.BANKER) {
      router.push('/banker/dashboard')
    } else if (user.role === UserRole.ADMIN) {
      router.push('/admin/dashboard')
    }
  } catch (e) {
    console.error('Login failed:', e)
  }
}
</script>

<template>
  <v-app>
    <v-main>
      <v-container class="fill-height py-8 px-4">
        <v-row align="center" justify="center" class="fill-height">
          <v-col cols="12" sm="10" md="8" lg="6" xl="5">
            <v-card variant="outlined" class="mx-auto" max-width="600">
              <v-card-title class="d-flex justify-center align-center pt-8 pb-6 px-6">
                <img
                  :src="logoSrc"
                  alt="AIG Bank"
                  style="max-width: 180px; height: auto; object-fit: contain;"
                />
              </v-card-title>
              
              <v-card-text class="px-6 pb-6">
                <v-form @submit.prevent="handleLogin">
                  <v-text-field
                    v-model="username"
                    label="Username"
                    prepend-inner-icon="mdi-account"
                    variant="outlined"
                    :disabled="isLoading"
                    required
                  />
                  
                  <v-text-field
                    v-model="password"
                    label="Password"
                    prepend-inner-icon="mdi-lock"
                    :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    :type="showPassword ? 'text' : 'password'"
                    variant="outlined"
                    :disabled="isLoading"
                    required
                    @click:append-inner="showPassword = !showPassword"
                  />
                  
                  <v-text-field
                    v-model="otpCode"
                    label="OTP Code"
                    prepend-inner-icon="mdi-shield-key"
                    variant="outlined"
                    :disabled="isLoading"
                    maxlength="6"
                    placeholder="123456"
                    hint="6-digit code from authenticator app"
                    persistent-hint
                    required
                  />
                  
                  <v-alert
                    v-if="error"
                    type="error"
                    variant="tonal"
                    class="mb-4"
                  >
                    {{ error }}
                  </v-alert>
                  
                  <v-btn
                    type="submit"
                    color="primary"
                    block
                    size="large"
                    :loading="isLoading"
                  >
                    Login
                  </v-btn>
                  
                  <div class="text-center mt-4">
                    <v-btn
                      variant="text"
                      to="/forgot-password"
                      :disabled="isLoading"
                      size="small"
                    >
                      Forgot Password?
                    </v-btn>
                  </div>
                  
                  <v-divider class="my-4" />
                  
                  <div class="text-center">
                    <v-btn
                      variant="text"
                      to="/register"
                      :disabled="isLoading"
                    >
                      Don't have an account? Register
                    </v-btn>
                  </div>
                </v-form>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<style scoped>
</style>

