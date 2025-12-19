<route lang="yaml">
meta:
  layout: blank
</route>

<template>
  <v-app>
    <v-main class="d-flex align-center justify-center bg-white">
      <v-card max-width="480" width="100%" class="pa-4 pa-sm-6 mx-2 login-card" rounded="xl">
        <!-- Header -->
        <div class="text-center mb-6">
          <v-icon icon="mdi-account-circle" size="64" class="mb-1 icon-light-blue" />
          <h1 class="text-h5 font-weight-medium">{{ $t('login.title') }}</h1>
          <p class="text-body-2 text-medium-emphasis mt-1"></p>
        </div>

        <!-- Form -->
        <v-form @submit.prevent="handleSubmit">
          <v-text-field v-model="token" :label="$t('login.accessToken')" variant="outlined"
            :type="showToken ? 'text' : 'password'" :append-inner-icon="showToken ? 'mdi-eye-off' : 'mdi-eye'"
            @click:append-inner="showToken = !showToken" autocomplete="off" hide-details="auto" class="mb-4" />

          <v-alert v-if="errorMessage" type="error" variant="tonal" density="compact" closable class="mb-4"
            @click:close="errorMessage = null">
            {{ errorMessage }}
          </v-alert>

          <v-btn block color="primary" size="large" type="submit" :loading="loading" :disabled="!token" class="mb-4">
            <v-icon icon="mdi-key" class="mr-2" />
            {{ $t('login.signInToken') }}
          </v-btn>


          <div class="d-flex align-center my-4">
            <v-spacer />
            <span class="text-caption text-medium-emphasis mx-4">{{ $t('login.or') }}</span>
            <v-spacer />
          </div>

          <v-btn block variant="tonal" size="large" @click="handleSsoLogin">
            <v-icon icon="mdi-shield-account" class="mr-2" />
            {{ $t('login.signInSso') }}
          </v-btn>
        </v-form>
      </v-card>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const token = ref('')
const loading = ref(false)
const errorMessage = ref<string | null>(null)
const showToken = ref(false)

onMounted(async () => {
  auth.initializeFromStorage()

  const queryToken = route.query.token
  if (typeof queryToken === 'string' && queryToken) {
    await handleTokenLogin(queryToken)
    const { token: _, ...rest } = route.query
    router.replace({ path: route.path, query: rest })
  }
})

const handleTokenLogin = async (rawToken?: string) => {
  if (loading.value) return
  const value = (rawToken ?? token.value).trim()
  if (!value) return

  loading.value = true
  errorMessage.value = null

  try {
    await auth.loginWithToken(value)
    await router.isReady()
    await router.replace('/')
  } catch (err) {
    auth.logout()
    errorMessage.value = t('login.invalidToken')
  } finally {
    loading.value = false
  }
}

const handleSubmit = () => handleTokenLogin()

const handleSsoLogin = () => {
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? ''
  const ssoPath = '/api/v1/oauth/login'
  window.location.href = apiBase ? `${apiBase}${ssoPath}` : ssoPath
}
</script>

<style scoped>
.login-card {
  box-shadow: 0 0px 40px rgba(0, 0, 0, 0.12) !important;
  background-color: #fafafa;
}

.icon-light-blue {
  color: #9bd2ff !important;
}
</style>
