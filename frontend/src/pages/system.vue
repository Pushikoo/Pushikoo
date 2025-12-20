<template>
    <v-container fluid>
        <!-- Page Header -->
        <v-row class="mb-6">
            <v-col cols="12">
                <div class="d-flex align-center justify-space-between flex-wrap ga-4">
                    <div>
                        <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('system.title') }}</h1>
                        <p class="text-body-2 text-medium-emphasis mb-0">
                            {{ $t('system.description') }}
                        </p>
                    </div>
                    <v-btn color="primary" size="large" :icon="$vuetify.display.xs" :loading="saving"
                        :disabled="!schema" @click="saveConfig">
                        <v-icon icon="mdi-content-save"></v-icon>
                        <span class="d-none d-sm-inline ml-2">{{ $t('system.saveSettings') }}</span>
                    </v-btn>
                </div>
            </v-col>
        </v-row>

        <!-- Content -->
        <v-row>
            <v-col cols="12">
                <!-- Loading State -->
                <v-card v-if="loading" class="card-outlined">
                    <v-card-text>
                        <LoadingSpinner :text="$t('system.loadingSystemStatus')" />
                    </v-card-text>
                </v-card>

                <!-- Error State -->
                <v-card v-else-if="!schema" class="card-outlined">
                    <v-card-text class="text-center py-12">
                        <v-icon icon="mdi-alert-circle-outline" size="64" color="error" class="mb-4"></v-icon>
                        <div class="text-h6 text-medium-emphasis mb-2">{{ $t('system.failedToLoadConfiguration') }}
                        </div>
                        <div class="text-body-2 text-medium-emphasis mb-4">
                            {{ $t('system.couldNotLoadSchema') }}
                        </div>
                        <v-btn color="primary" variant="tonal" prepend-icon="mdi-refresh" @click="loadConfig">
                            {{ $t('common.retry') }}
                        </v-btn>
                    </v-card-text>
                </v-card>

                <!-- Config Form -->
                <v-card v-else class="card-outlined">
                    <v-card-text>
                        <SchemaForm v-model="config" :schema="schema" :root-schema="schema" />
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>

        <!-- Success Snackbar -->
        <v-snackbar v-model="snackbar.show" :color="snackbar.color" location="bottom right" rounded="lg">
            {{ snackbar.text }}
            <template v-slot:actions>
                <v-btn variant="text" @click="snackbar.show = false">{{ $t('common.close') }}</v-btn>
            </template>
        </v-snackbar>
    </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted, onActivated } from 'vue'
import { useI18n } from 'vue-i18n'
import { SystemService } from '@/client'
import SchemaForm from '@/components/SchemaForm.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const config = ref<any>({})
const schema = ref<any>(null)
const loading = ref(false)
const saving = ref(false)

const snackbar = ref({
    show: false,
    text: '',
    color: 'success'
})

const { t } = useI18n()
const showSnackbar = (text: string, color = 'success') => {
    snackbar.value.text = text
    snackbar.value.color = color
    snackbar.value.show = true
}

const loadConfig = async () => {
    loading.value = true
    try {
        const [conf, sch] = await Promise.all([
            SystemService.getSystemConfigApiV1SystemConfigGet(),
            SystemService.getSystemConfigSchemaApiV1SystemConfigSchemaGet().catch(() => null)
        ])
        config.value = conf || {}
        schema.value = sch
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    loadConfig()
})

onActivated(() => {
    loadConfig()
})

const saveConfig = async () => {
    saving.value = true
    try {
        await SystemService.setSystemConfigApiV1SystemConfigPut({
            requestBody: config.value
        })
        showSnackbar(t('system.configurationSavedSuccessfully'), 'success')
    } catch (e) {
        console.error(e)
        showSnackbar(t('system.failedToSaveConfiguration'), 'error')
    } finally {
        saving.value = false
    }
}
</script>

<style scoped>
.card-outlined {
    border: 1px solid rgba(0, 0, 0, 0.12);
    background-color: white;
}
</style>
