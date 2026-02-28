<template>
    <v-container fluid>
        <!-- Page Header -->
        <v-row class="mb-6">
            <v-col cols="12">
                <div>
                    <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('system.title') }}</h1>
                    <p class="text-body-2 text-medium-emphasis mb-0">
                        {{ $t('system.description') }}
                    </p>
                </div>
            </v-col>
        </v-row>

        <!-- Tabs Card -->
        <v-card class="card-outlined">
            <v-tabs v-model="tab" color="primary" align-tabs="start">
                <v-tab value="configuration" prepend-icon="mdi-cog">{{ $t('system.configuration') }}</v-tab>
                <v-tab value="common" prepend-icon="mdi-toolbox">{{ $t('system.common') }}</v-tab>
            </v-tabs>

            <v-divider></v-divider>

            <v-window v-model="tab">
                <!-- Configuration Tab -->
                <v-window-item value="configuration">
                    <v-card-text>
                        <!-- Loading State -->
                        <LoadingSpinner v-if="loading" :text="$t('system.loadingSystemStatus')" />

                        <!-- Error State -->
                        <div v-else-if="!schema" class="text-center py-12">
                            <v-icon icon="mdi-alert-circle-outline" size="64" color="error" class="mb-4"></v-icon>
                            <div class="text-h6 text-medium-emphasis mb-2">
                                {{ $t('system.failedToLoadConfiguration') }}
                            </div>
                            <div class="text-body-2 text-medium-emphasis mb-4">
                                {{ $t('system.couldNotLoadSchema') }}
                            </div>
                            <v-btn color="primary" variant="tonal" prepend-icon="mdi-refresh" @click="loadConfig">
                                {{ $t('common.retry') }}
                            </v-btn>
                        </div>

                        <!-- Config Form -->
                        <template v-else>
                            <SchemaForm v-model="config" :schema="schema" :root-schema="schema" />
                        </template>
                    </v-card-text>
                    <v-card-actions v-if="schema && !loading">
                        <v-spacer />
                        <v-btn color="primary" :loading="saving" @click="saveConfig"
                            prepend-icon="mdi-content-save">
                            {{ $t('system.saveSettings') }}
                        </v-btn>
                    </v-card-actions>
                </v-window-item>

                <!-- Common Tab -->
                <v-window-item value="common">
                    <v-card-text>
                        <v-card variant="flat" class="section-card">
                            <v-card-title class="d-flex align-center">
                                <v-icon icon="mdi-delete-sweep" class="mr-2"></v-icon>
                                {{ $t('system.pruneDatabase') }}
                            </v-card-title>
                            <v-divider></v-divider>
                            <v-card-text>
                                <p class="text-body-2 text-medium-emphasis mb-4">
                                    {{ $t('system.pruneHint') }}
                                </p>
                                <v-btn color="warning" variant="tonal" :loading="pruning" @click="confirmPrune"
                                    prepend-icon="mdi-delete-sweep">
                                    {{ $t('system.pruneDatabase') }}
                                </v-btn>
                            </v-card-text>
                        </v-card>
                    </v-card-text>
                </v-window-item>
            </v-window>
        </v-card>

        <!-- Prune Confirm Dialog -->
        <v-dialog v-model="pruneDialog" max-width="400" persistent>
            <v-card>
                <v-card-title>{{ $t('system.confirmPrune') }}</v-card-title>
                <v-card-text>{{ $t('system.pruneDescription') }}</v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn @click="pruneDialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="warning" @click="doPrune">{{ $t('common.confirm') }}</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

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
import { getApiErrorMessage } from '@/utils/apiErrorHelper'

const tab = ref('configuration')
const config = ref<any>({})
const schema = ref<any>(null)
const loading = ref(false)
const saving = ref(false)
const pruning = ref(false)
const pruneDialog = ref(false)

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
        showSnackbar(getApiErrorMessage(e, t('system.failedToSaveConfiguration')), 'error')
    } finally {
        saving.value = false
    }
}

const confirmPrune = () => {
    pruneDialog.value = true
}

const doPrune = async () => {
    pruneDialog.value = false
    pruning.value = true
    try {
        await SystemService.pruneApiV1SystemPrunePost({ seconds: 14 * 24 * 3600 })
        showSnackbar(t('system.pruneSuccess'))
    } catch (e) {
        console.error(e)
        showSnackbar(getApiErrorMessage(e, t('system.pruneFailed')), 'error')
    } finally {
        pruning.value = false
    }
}
</script>

<style scoped>
.card-outlined {
    border: 1px solid rgba(0, 0, 0, 0.12);
    background-color: white;
}

.section-card {
    border: 1px solid rgba(0, 0, 0, 0.15) !important;
    border-radius: 6px !important;
}

:root.v-theme--dark .section-card {
    border-color: rgba(255, 255, 255, 0.15) !important;
}

:deep(.v-tabs .v-tab) {
    border-radius: 8px 8px 0 0 !important;
}
</style>
