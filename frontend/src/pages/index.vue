<template>
  <v-container fluid>
    <!-- Page Header -->
    <v-row class="mb-6">
      <v-col cols="12">
        <div class="d-flex align-center justify-space-between flex-wrap ga-4">
          <div>
            <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('dashboard.title') }}</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              {{ $t('dashboard.welcome') }}
            </p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Quick Stats Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="h-100" color="primary" variant="tonal">
          <v-card-text class="d-flex flex-column">
            <div class="d-flex align-center justify-space-between mb-2">
              <v-icon icon="mdi-message-text-outline" size="32"></v-icon>
              <v-chip size="small" color="primary" variant="elevated">Live</v-chip>
            </div>
            <div class="text-h4 font-weight-bold mb-1">{{ $t('nav.messages') }}</div>
            <div class="text-body-2 text-medium-emphasis">{{ $t('dashboard.messagesProcessed') }}</div>
          </v-card-text>
          <v-card-actions>
            <v-btn variant="text" color="primary" to="/messages" append-icon="mdi-arrow-right">
              {{ $t('common.viewAll') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="h-100" color="secondary" variant="tonal">
          <v-card-text class="d-flex flex-column">
            <div class="d-flex align-center justify-space-between mb-2">
              <v-icon icon="mdi-connection" size="32"></v-icon>
              <v-chip size="small" color="secondary" variant="elevated">Active</v-chip>
            </div>
            <div class="text-h4 font-weight-bold mb-1">{{ $t('nav.adapters') }}</div>
            <div class="text-body-2 text-medium-emphasis">{{ $t('dashboard.manageAdapters') }}</div>
          </v-card-text>
          <v-card-actions>
            <v-btn variant="text" color="secondary" to="/adapters" append-icon="mdi-arrow-right">
              {{ $t('common.manage') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="h-100" color="info" variant="tonal">
          <v-card-text class="d-flex flex-column">
            <div class="d-flex align-center justify-space-between mb-2">
              <v-icon icon="mdi-server-outline" size="32"></v-icon>
            </div>
            <div class="text-h4 font-weight-bold mb-1">{{ $t('nav.instances') }}</div>
            <div class="text-body-2 text-medium-emphasis">{{ $t('dashboard.activeInstances') }}</div>
          </v-card-text>
          <v-card-actions>
            <v-btn variant="text" color="info" to="/instances" append-icon="mdi-arrow-right">
              {{ $t('common.configure') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="h-100" color="warning" variant="tonal">
          <v-card-text class="d-flex flex-column">
            <div class="d-flex align-center justify-space-between mb-2">
              <v-icon icon="mdi-sitemap-outline" size="32"></v-icon>
            </div>
            <div class="text-h4 font-weight-bold mb-1">{{ $t('nav.flows') }}</div>
            <div class="text-body-2 text-medium-emphasis">{{ $t('dashboard.messageFlows') }}</div>
          </v-card-text>
          <v-card-actions>
            <v-btn variant="text" color="warning" to="/flows" append-icon="mdi-arrow-right">
              {{ $t('common.setup') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Navigation Cards Grid -->
    <v-row class="">
      <v-col cols="12">
        <h2 class="text-h6 font-weight-bold">{{ $t('dashboard.quickNavigation') }}</h2>
      </v-col>
      <v-col cols="12" sm="6" md="4" v-for="item in navigationItems" :key="item.title">
        <v-card :to="item.to" hover class="h-100 transition-swing card-outlined">
          <v-card-text class="d-flex align-center">
            <v-avatar :color="item.color" variant="tonal" size="48" class="mr-4">
              <v-icon :icon="item.icon" size="24"></v-icon>
            </v-avatar>
            <div class="flex-grow-1">
              <div class="text-subtitle-1 font-weight-bold">{{ item.title }}</div>
              <div class="text-body-2 text-medium-emphasis">{{ item.subtitle }}</div>
            </div>
            <v-icon icon="mdi-chevron-right" color="medium-emphasis"></v-icon>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

  </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted, onActivated, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()

const navigationItems = computed(() => [
  { title: t('nav.crons'), subtitle: t('dashboard.quickNavCronsSubtitle'), icon: 'mdi-clock-outline', to: '/crons', color: 'tertiary' },
  { title: t('nav.warnings'), subtitle: t('dashboard.quickNavWarningsSubtitle'), icon: 'mdi-alert-outline', to: '/warnings', color: 'error' },
  { title: t('nav.system'), subtitle: t('dashboard.quickNavSystemSubtitle'), icon: 'mdi-cog-outline', to: '/system', color: 'primary' },
])

onMounted(async () => {
  auth.initializeFromStorage()

  if (!auth.token) {
    router.replace('/login')
    return
  }


})

</script>

<style scoped>
.card-outlined {
  border: 1px solid rgba(0, 0, 0, 0.12);
}
</style>
