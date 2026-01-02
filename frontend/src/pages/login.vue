<route lang="yaml">
meta:
  layout: blank
</route>

<template>
  <v-app>
    <v-main class="bg-grey-lighten-3 d-flex align-center justify-center fill-height">
      <v-container fluid class="pa-0 fill-height d-flex align-center justify-center">

        <v-card max-width="1100" width="100%" class="mx-0 mx-md-4 overflow-hidden login-card"
          :rounded="$vuetify.display.mdAndUp ? 'xl' : '0'">
          <v-row no-gutters class="fill-height">

            <v-col cols="12" md="6" class="bg-primary position-relative d-flex align-center">
              <v-img cover class="fill-height h-100"
                gradient="to bottom right, rgba(var(--v-theme-primary), .85), rgba(var(--v-theme-primary), .5)"
                style="min-height: 150px;">
                <div class="d-flex flex-column justify-center align-center fill-height text-white pa-10 text-center">
                  <v-icon icon="mdi-account-circle" size="80" class="mb-6"></v-icon>
                </div>
              </v-img>
            </v-col>

            <v-col cols="12" md="6" class="bg-white text-black">
              <div class="pa-8 pa-sm-12 py-sm-16 d-flex align-center fill-height">
                <div class="w-100">
                  <div class="mb-8">
                    <h3 class="text-h4 font-weight-bold text-primary mb-2">
                      {{ $t('login.title') }}
                    </h3>
                    <p class="text-body-1 text-medium-emphasis">
                      {{ $t('login.subtitle') }}
                    </p>
                  </div>

                  <v-form @submit.prevent="handleSubmit">

                    <v-text-field v-model="token" :label="$t('login.signInToken') || 'Token'" variant="outlined"
                      color="primary" bgColor="grey-lighten-5" :type="showToken ? 'text' : 'password'"
                      :append-inner-icon="showToken ? 'mdi-eye-off' : 'mdi-eye'"
                      prepend-inner-icon="mdi-key-chain-variant" @click:append-inner="showToken = !showToken"
                      autocomplete="off" class="mb-2" persistent-hint :error-messages="errorMessage"
                      @update:model-value="errorMessage = null" />

                    <v-btn block color="primary" size="large" type="submit" class="text-body-1 font-weight-bold"
                      elevation="4" :loading="loading" :disabled="!token.trim()" prepend-icon="mdi-arrow-right">
                      {{ $t('login.signInToken') }}
                    </v-btn>
                  </v-form>

                  <div class="d-flex align-center my-2">
                    <v-divider></v-divider>
                    <span class="text-overline text-medium-emphasis mx-4">{{ $t('login.or') }}</span>
                    <v-divider></v-divider>
                  </div>

                  <v-btn block variant="tonal" color="secondary" size="large" height="56" @click="handleSsoLogin"
                    class="text-body-1 font-weight-medium" prepend-icon="mdi-account-check">
                    {{ $t('login.signInSso') }}
                  </v-btn>

                </div>
              </div>
            </v-col>
          </v-row>
        </v-card>

      </v-container>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'


const { t } = useI18n({ useScope: 'global', missing: (locale, key) => key })
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const token = ref('')
const loading = ref(false)
const errorMessage = ref<string | null>(null)
const showToken = ref(false)

onMounted(async () => {

  if (auth) {
    auth.initializeFromStorage()

    const queryToken = route.query.token
    if (typeof queryToken === 'string' && queryToken) {
      await handleTokenLogin(queryToken)

      const { token: _, ...rest } = route.query
      router.replace({ path: route.path, query: rest })
    }
  }
})

const handleTokenLogin = async (rawToken?: string) => {
  if (loading.value || !auth) return
  const value = (rawToken ?? token.value).trim()
  if (!value) return

  loading.value = true
  errorMessage.value = null

  try {
    await auth.loginWithToken(value)

    const redirectPath = (route.query.redirect as string) || '/'
    await router.isReady()
    await router.replace(redirectPath)
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
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
  border: none !important;
}

@media (min-width: 960px) {
  .login-card {
    border: 1px solid rgb(var(--v-theme-primary)) !important;
  }
}
</style>