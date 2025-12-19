<template>
  <v-app>
    <!-- Navigation Drawer -->
    <v-navigation-drawer v-model="drawer" :temporary="isMobile" :permanent="!isMobile" color="surface" class="nav-drawer">
      <!-- Header -->
      <div class="d-flex align-center pa-4">
        <!-- <v-icon icon="mdi-rocket-launch" color="primary" class="mr-2"></v-icon> -->
        <span class="text-h6 font-weight-bold">Pushikoo</span>
      </div>

      <v-divider></v-divider>

      <!-- Navigation Items -->
      <div class="nav-items pa-2">
        <div v-for="item in navItems" :key="item.to" class="nav-item"
          :class="{ 'nav-item--active': route.path === item.to }" @click="navigateTo(item.to)">
          <v-icon :icon="item.icon" size="20"></v-icon>
          <span class="nav-item-text">{{ $t(`nav.${item.key}`) }}</span>
        </div>
      </div>

      <!-- Footer -->
      <template v-slot:append>
        <v-divider></v-divider>
        <div class="pa-2">
          <!-- Language Switcher -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <div class="nav-item" v-bind="props">
                <v-icon icon="mdi-translate" size="20"></v-icon>
                <span class="nav-item-text">{{ $t('language.title') }}</span>
                <v-chip size="x-small" color="secondary" variant="tonal" class="ml-auto">
                  {{ currentLocaleName }}
                </v-chip>
              </div>
            </template>
            <v-list density="compact">
              <v-list-item v-for="loc in locales" :key="loc.code" @click="changeLocale(loc.code)">
                <v-list-item-title>{{ loc.name }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <div class="nav-item" @click="toggleTheme">
            <v-icon icon="mdi-theme-light-dark" size="20"></v-icon>
            <span class="nav-item-text">{{ $t('nav.theme') }}</span>
            <v-chip size="x-small" :color="isDark ? 'warning' : 'info'" variant="tonal" class="ml-auto">
              {{ isDark ? $t('nav.dark') : $t('nav.light') }}
            </v-chip>
          </div>
          <div class="nav-item nav-item--danger" @click="handleLogout">
            <v-icon icon="mdi-logout" size="20"></v-icon>
            <span class="nav-item-text">{{ $t('nav.logout') }}</span>
          </div>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- App Bar -->
    <v-app-bar flat color="surface">
      <v-app-bar-nav-icon @click="drawer = !drawer" v-if="$vuetify.display.mobile"></v-app-bar-nav-icon>

      <v-app-bar-title class="d-flex align-center">
        <span class="text-h6 font-weight-bold">
          {{ currentPageTitle }}
        </span>
      </v-app-bar-title>

      <v-spacer></v-spacer>
    </v-app-bar>

    <!-- Main Content with scroll -->
    <v-main class="bg-background" style="overflow-y: auto;">
      <v-container fluid class="pa-2 pa-sm-4 pa-md-6">
        <router-view v-slot="{ Component }">
          <keep-alive :max="10">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </v-container>
    </v-main>

    <!-- Global Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="snackbar.timeout" location="top right"
      rounded="lg">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">
          {{ $t('common.close') }}
        </v-btn>
      </template>
    </v-snackbar>

    <!-- Logout Confirmation Dialog -->
    <v-dialog v-model="logoutDialog" max-width="400px">
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-logout" color="warning" class="mr-2"></v-icon>
          {{ $t('nav.logoutConfirmTitle') }}
        </v-card-title>
        <v-card-text>
          {{ $t('nav.logoutConfirmMessage') }}
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="logoutDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="warning" variant="tonal" @click="confirmLogout">
            {{ $t('nav.logout') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script lang="ts" setup>
import { ref, computed, provide, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTheme, useDisplay } from 'vuetify'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const { mobile } = useDisplay()
const isMobile = computed(() => mobile.value)
const drawer = ref(true)
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const theme = useTheme()
const logoutDialog = ref(false)

// Initialize drawer state based on screen size
onMounted(() => {
  if (isMobile.value) {
    drawer.value = false
  }
})

// Navigation with mobile drawer close
const navigateTo = (to: string) => {
  router.push(to)
  if (isMobile.value) {
    drawer.value = false
  }
}

// Navigation items
const navItems = [
  { key: 'dashboard', icon: 'mdi-view-dashboard-outline', to: '/' },
  { key: 'messages', icon: 'mdi-message-text-outline', to: '/messages' },
  { key: 'adapters', icon: 'mdi-connection', to: '/adapters' },
  { key: 'instances', icon: 'mdi-server-outline', to: '/instances' },
  { key: 'flows', icon: 'mdi-sitemap-outline', to: '/flows' },
  { key: 'crons', icon: 'mdi-clock-outline', to: '/crons' },
  { key: 'warnings', icon: 'mdi-alert-outline', to: '/warnings' },
  { key: 'system', icon: 'mdi-cog-outline', to: '/system' },
]

// Locales
const locales = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'ja', name: '日本語' },
]

const currentLocaleName = computed(() => {
  return locales.find(l => l.code === locale.value)?.name || 'English'
})

const changeLocale = (code: string) => {
  locale.value = code
  localStorage.setItem('locale', code)
}

// Current page title
const currentPageTitle = computed(() => {
  const path = route.path
  const item = navItems.find(n => n.to === path)
  return item ? t(`nav.${item.key}`) : 'Pushikoo'
})

// Theme
const isDark = computed(() => theme.global.current.value.dark)

const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
}

// Snackbar
const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
  timeout: 3000
})

// Show snackbar function
const showSnackbar = (text: string, color = 'success') => {
  snackbar.value.text = text
  snackbar.value.color = color
  snackbar.value.show = true
}

// Provide snackbar to child components
provide('showSnackbar', showSnackbar)

// Logout
const handleLogout = () => {
  logoutDialog.value = true
}

const confirmLogout = () => {
  logoutDialog.value = false
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.nav-drawer {
  border-right: 1px solid rgba(0, 0, 0, 0.12) !important;
  height: 100vh !important;
  position: fixed !important;
}

:root.v-theme--dark .nav-drawer {
  border-right: 1px solid rgba(255, 255, 255, 0.12) !important;
}

.nav-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.nav-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.nav-item--active {
  background: rgb(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
}

.nav-item--active:hover {
  background: rgb(var(--v-theme-primary), 0.16);
}

.nav-item--danger:hover {
  background: rgba(var(--v-theme-error), 0.08);
  color: rgb(var(--v-theme-error));
}

.nav-item-text {
  font-size: 14px;
  font-weight: 500;
}
</style>
