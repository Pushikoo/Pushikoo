<template>
    <v-container fluid>
        <!-- Page Header -->
        <v-row class="mb-6">
            <v-col cols="12">
                <div class="d-flex align-center justify-space-between flex-wrap ga-4">
                    <div>
                        <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('adapters.title') }}</h1>
                        <p class="text-body-2 text-medium-emphasis mb-0">
                            {{ $t('adapters.description') }}
                        </p>
                    </div>
                    <div class="d-flex ga-2">
                        <v-btn color="primary" variant="tonal" prepend-icon="mdi-refresh" @click="loadAdapters"
                            :loading="loadingAdapters">
                            {{ $t('common.refresh') }}
                        </v-btn>
                        <v-btn color="primary" prepend-icon="mdi-plus" @click="openInstallDialog">
                            {{ $t('adapters.install') }}
                        </v-btn>
                    </div>
                </div>
            </v-col>
        </v-row>

        <!-- Tabs Card -->
        <v-card class="card-outlined">
            <v-tabs v-model="tab" color="primary" align-tabs="start">
                <v-tab value="adapters" prepend-icon="mdi-puzzle">{{ $t('adapters.adaptersTab') }}</v-tab>
                <v-tab value="pip" prepend-icon="mdi-package-variant">{{ $t('adapters.pipTab') }}</v-tab>
            </v-tabs>

            <v-divider></v-divider>

            <v-window v-model="tab">
                <!-- Adapters Tab -->
                <v-window-item value="adapters">
                    <v-card-text>
                        <LoadingSpinner v-if="loadingAdapters" :text="$t('adapters.loadingAdapters')" />

                        <v-list v-else-if="adapters.length > 0" lines="two" class="bg-transparent">
                            <v-list-item v-for="adapter in adapters" :key="adapter.name" rounded="lg" class="mb-2"
                                border>
                                <template v-slot:prepend>
                                    <v-avatar :color="getAdapterTypeColor(adapter.type)" variant="tonal" size="48"
                                        class="d-none d-sm-flex">
                                        <v-icon :icon="getAdapterTypeIcon(adapter.type)"></v-icon>
                                    </v-avatar>
                                    <v-avatar :color="getAdapterTypeColor(adapter.type)" variant="tonal" size="36"
                                        class="d-flex d-sm-none">
                                        <v-icon :icon="getAdapterTypeIcon(adapter.type)" size="18"></v-icon>
                                    </v-avatar>
                                </template>
                                <v-list-item-title class="font-weight-bold">{{ adapter.name }}</v-list-item-title>
                                <v-list-item-subtitle class="d-flex flex-wrap align-center ga-1 mt-1">
                                    <v-chip size="x-small" :color="getAdapterTypeColor(adapter.type)" variant="tonal">
                                        {{ adapter.type }}
                                    </v-chip>
                                    <v-chip size="x-small" color="grey" variant="tonal">
                                        v{{ adapter.version }}
                                    </v-chip>
                                    <span class="text-caption text-medium-emphasis d-none d-sm-inline ml-1">{{
                                        adapter.summary || adapter.description ||
                                        '' }}</span>
                                </v-list-item-subtitle>
                                <template v-slot:append>
                                    <div class="d-flex flex-nowrap">
                                        <v-btn icon="mdi-cog-outline" variant="text" size="small" color="primary"
                                            @click="openConfig(adapter)" :title="$t('common.configure')" />
                                        <v-btn icon="mdi-arrow-up-bold" variant="text" size="small" color="success"
                                            @click="openUpgradeDialog(adapter)" :title="$t('adapters.upgrade')" />
                                        <v-btn icon="mdi-delete-outline" variant="text" size="small" color="error"
                                            @click="openUninstallDialog(adapter)" :title="$t('adapters.uninstall')" />
                                    </div>
                                </template>
                            </v-list-item>
                        </v-list>

                        <v-empty-state v-else icon="mdi-puzzle-outline" :title="$t('adapters.noAdapters')"
                            :text="$t('adapters.noAdaptersText')"></v-empty-state>
                    </v-card-text>
                </v-window-item>

                <!-- Pip Tab (Index Management Only) -->
                <v-window-item value="pip">
                    <v-card-text>
                        <v-card variant="flat" class="pip-section-card">
                            <v-card-title class="d-flex align-center">
                                <v-icon icon="mdi-link-variant" class="mr-2"></v-icon>
                                {{ $t('adapters.indexes') }}
                            </v-card-title>
                            <v-divider></v-divider>
                            <v-card-text>
                                <v-list v-if="indexes.length > 0" density="compact" class="bg-transparent">
                                    <v-list-item v-for="url in indexes" :key="url" rounded="lg" class="mb-1" border>
                                        <v-list-item-title class="text-body-2 text-truncate">{{ maskAuthUrl(url)
                                        }}</v-list-item-title>
                                        <template v-slot:append>
                                            <v-btn icon="mdi-delete-outline" variant="text" size="small" color="error"
                                                @click="removeIndex(url)"></v-btn>
                                        </template>
                                    </v-list-item>
                                </v-list>
                                <div v-else class="text-center text-medium-emphasis py-4">
                                    {{ $t('adapters.noIndexesConfigured') }}
                                </div>
                                <v-divider class="my-4"></v-divider>
                                <div class="d-flex align-center ga-2">
                                    <v-text-field v-model="newIndexUrl" :placeholder="$t('adapters.placeholderPyPiUrl')"
                                        hide-details density="compact"></v-text-field>
                                    <v-btn color="primary" @click="addIndex" :loading="addingUrl"
                                        :disabled="!newIndexUrl">
                                        {{ $t('common.add') }}
                                    </v-btn>
                                </div>
                            </v-card-text>
                        </v-card>
                    </v-card-text>
                </v-window-item>
            </v-window>
        </v-card>

        <!-- Config Dialog -->
        <v-dialog v-model="configDialog" max-width="800px" scrollable persistent
            :fullscreen="$vuetify.display.smAndDown">
            <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'" class="d-flex flex-column"
                :style="$vuetify.display.smAndDown ? 'height: 100%' : ''">
                <v-card-title class="d-flex align-center pa-3 pa-sm-4">
                    <v-icon icon="mdi-cog" class="mr-2"></v-icon>
                    {{ $t('adapters.configure') }} {{ currentAdapter?.name }}
                    <v-spacer></v-spacer>
                    <v-btn icon="mdi-close" variant="text" size="small" @click="configDialog = false"></v-btn>
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text :style="$vuetify.display.smAndDown ? 'flex: 1; overflow-y: auto;' : 'max-height: 60vh;'"
                    class="pa-3 pa-sm-4">
                    <LoadingSpinner v-if="loadingConfig" :text="$t('system.loadingSystemStatus')" />
                    <v-empty-state v-else-if="!adapterSchema" icon="mdi-file-document-outline"
                        :title="$t('adapters.noSchemaAvailable')"
                        :text="$t('adapters.noConfigurationSchema')"></v-empty-state>
                    <SchemaForm v-else v-model="adapterConfig" :schema="adapterSchema" :root-schema="adapterSchema" />
                </v-card-text>
                <v-divider></v-divider>
                <v-card-actions class="pa-2 pa-sm-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="configDialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="primary" @click="saveConfig" :loading="savingConfig" :disabled="!adapterSchema">
                        {{ $t('common.save') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Install Dialog -->
        <v-dialog v-model="installDialog" max-width="600px" persistent :fullscreen="$vuetify.display.smAndDown">
            <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
                <v-card-title class="d-flex align-center pa-4">
                    <v-icon icon="mdi-download" class="mr-2"></v-icon>
                    {{ $t('adapters.installAdapter') }}
                    <v-spacer></v-spacer>
                    <v-btn icon="mdi-close" variant="text" size="small" @click="installDialog = false"></v-btn>
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-4">
                    <v-tabs v-model="installMode" density="compact" color="primary" class="mb-4">
                        <v-tab value="spec" size="small">{{ $t('adapters.specifier') }}</v-tab>
                        <v-tab value="upload" size="small">{{ $t('adapters.whlFile') }}</v-tab>
                    </v-tabs>

                    <v-window v-model="installMode" class="install-dialog-window">
                        <!-- Install by Spec -->
                        <v-window-item value="spec">
                            <v-text-field v-model="installSpec" :label="$t('adapters.specifier')"
                                :placeholder="$t('adapters.placeholderPackageName')"
                                prepend-inner-icon="mdi-package-variant" class="mb-3"></v-text-field>
                        </v-window-item>
                        <!-- Upload whl -->
                        <v-window-item value="upload">
                            <v-file-input v-model="uploadFile" :label="$t('adapters.selectWhlFile')" accept=".whl"
                                prepend-icon="" prepend-inner-icon="mdi-file-upload" show-size
                                class="mb-3"></v-file-input>
                        </v-window-item>
                    </v-window>

                    <!-- Index URL Selection -->
                    <v-select v-model="selectedIndexUrl" :label="$t('adapters.indexUrl')" :items="indexUrlOptions"
                        item-title="title" item-value="value" density="compact" class="mb-3" clearable
                        hide-details></v-select>

                    <!-- Extra Index URLs Selection -->
                    <v-select v-model="selectedExtraIndexUrls" :label="$t('adapters.extraIndexUrls')"
                        :items="extraIndexUrlOptions" item-title="title" item-value="value" density="compact"
                        class="mb-3" multiple chips closable-chips hide-details></v-select>

                    <v-checkbox v-model="installUpgrade" :label="$t('adapters.upgrade')" hide-details density="compact"
                        class="mb-4"></v-checkbox>

                    <v-expand-transition>
                        <v-alert v-if="installMessage" :type="installMessageType" class="mt-2 pip-alert" closable
                            density="compact" @click:close="installMessage = null">
                            {{ installMessage }}
                        </v-alert>
                    </v-expand-transition>
                </v-card-text>
                <v-divider></v-divider>
                <v-card-actions class="pa-2 pa-sm-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="installDialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="primary" @click="performInstall" :loading="installing"
                        :disabled="installMode === 'spec' ? !installSpec : !uploadFile">
                        {{ $t('adapters.install') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Upgrade Dialog -->
        <v-dialog v-model="upgradeDialog" max-width="500px" persistent>
            <v-card rounded="xl">
                <v-card-title class="d-flex align-center pa-4">
                    <v-icon icon="mdi-arrow-up-bold" color="info" class="mr-2"></v-icon>
                    {{ $t('adapters.upgradeAdapter') }}
                </v-card-title>
                <v-card-text>
                    <p class="mb-4">{{ $t('adapters.upgradeConfirm', { name: adapterToUpgrade?.name }) }}</p>

                    <!-- Index URL Selection -->
                    <v-select v-model="upgradeIndexUrl" :label="$t('adapters.indexUrl')" :items="indexUrlOptions"
                        item-title="title" item-value="value" density="compact" class="mb-3" clearable
                        hide-details></v-select>

                    <!-- Extra Index URLs Selection -->
                    <v-select v-model="upgradeExtraIndexUrls" :label="$t('adapters.extraIndexUrls')"
                        :items="extraIndexUrlOptions" item-title="title" item-value="value" density="compact" multiple
                        chips closable-chips hide-details></v-select>

                    <v-expand-transition>
                        <v-alert v-if="upgradeMessage" :type="upgradeMessageType" class="mt-4 pip-alert" closable
                            density="compact" @click:close="upgradeMessage = null">
                            {{ upgradeMessage }}
                        </v-alert>
                    </v-expand-transition>
                </v-card-text>
                <v-card-actions class="pa-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="upgradeDialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="info" variant="tonal" @click="performUpgrade" :loading="upgrading">
                        {{ $t('adapters.upgrade') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Uninstall Confirmation Dialog -->
        <v-dialog v-model="uninstallDialog" max-width="400px" persistent>
            <v-card rounded="xl">
                <v-card-title class="d-flex align-center pa-4">
                    <v-icon icon="mdi-alert-circle" color="error" class="mr-2"></v-icon>
                    {{ $t('adapters.uninstallAdapter') }}
                </v-card-title>
                <v-card-text>
                    {{ $t('adapters.uninstallConfirm', { name: adapterToUninstall?.name }) }}

                    <v-expand-transition>
                        <v-alert v-if="uninstallMessage" :type="uninstallMessageType" class="mt-4 pip-alert" closable
                            density="compact" @click:close="uninstallMessage = null">
                            {{ uninstallMessage }}
                        </v-alert>
                    </v-expand-transition>
                </v-card-text>
                <v-card-actions class="pa-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="uninstallDialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="error" variant="tonal" @click="performUninstall" :loading="uninstalling">
                        {{ $t('adapters.uninstall') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Remove Index Confirmation Dialog -->
        <v-dialog v-model="removeIndexDialog" max-width="400px" persistent>
            <v-card rounded="xl">
                <v-card-title class="d-flex align-center pa-4">
                    <v-icon icon="mdi-alert-circle" color="error" class="mr-2"></v-icon>
                    {{ $t('adapters.removeIndex') }}
                </v-card-title>
                <v-card-text>
                    {{ $t('adapters.removeIndexConfirm') }}
                </v-card-text>
                <v-card-actions class="pa-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="removeIndexDialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="error" variant="tonal" @click="confirmRemoveIndex" :loading="removingIndex">
                        {{ $t('common.remove') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-container>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onActivated, inject, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { AdaptersService, PipService, type AdapterMeta, type AdapterType } from '@/client'
import SchemaForm from '@/components/SchemaForm.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const { t } = useI18n()
const showSnackbar = inject<(text: string, color?: string) => void>('showSnackbar', () => { })

// Adapter type helpers
const getAdapterTypeColor = (type: AdapterType): string => {
    switch (type) {
        case 'getter': return 'success'
        case 'pusher': return 'info'
        case 'processer': return 'warning'
        default: return 'primary'
    }
}

const getAdapterTypeIcon = (type: AdapterType): string => {
    switch (type) {
        case 'getter': return 'mdi-download-outline'
        case 'pusher': return 'mdi-upload-outline'
        case 'processer': return 'mdi-cog-outline'
        default: return 'mdi-puzzle-outline'
    }
}

// Mask authentication credentials in URL
const maskAuthUrl = (url: string): string => {
    try {
        const urlObj = new URL(url)
        if (urlObj.username || urlObj.password) {
            const maskPart = (str: string): string => {
                if (!str) return str
                const prefixLength = Math.ceil(str.length * 0.25)
                const suffixLength = Math.ceil(str.length * 0.25)
                const maskedLength = str.length - prefixLength - suffixLength
                if (maskedLength <= 0) return str
                const asterisks = '*'.repeat(Math.min(maskedLength, 6))
                return str.substring(0, prefixLength) + asterisks + str.substring(str.length - suffixLength)
            }
            const maskedUsername = maskPart(urlObj.username)
            const maskedPassword = maskPart(urlObj.password)
            const auth = maskedPassword ? `${maskedUsername}:${maskedPassword}@` : `${maskedUsername}@`
            return `${urlObj.protocol}//${auth}${urlObj.host}${urlObj.pathname}${urlObj.search}${urlObj.hash}`
        }
        return url
    } catch {
        return url
    }
}

const tab = ref('adapters')
const adapters = ref<AdapterMeta[]>([])
const loadingAdapters = ref(false)

const loadAdapters = async () => {
    loadingAdapters.value = true
    try {
        const list = await AdaptersService.listAdaptersApiV1AdaptersGet()
        if (list) adapters.value = list
    } catch (e) {
        console.error(e)
    } finally {
        loadingAdapters.value = false
    }
}

// Watch tab changes to refresh adapters when switching to adapters tab
watch(tab, (newTab) => {
    if (newTab === 'adapters') {
        loadAdapters()
    }
})

// Config State
const configDialog = ref(false)
const currentAdapter = ref<AdapterMeta | null>(null)
const adapterSchema = ref<any>(null)
const adapterConfig = ref<any>({})
const loadingConfig = ref(false)
const savingConfig = ref(false)

// Index State
const indexes = ref<string[]>([])
const newIndexUrl = ref('')
const addingUrl = ref(false)
const removeIndexDialog = ref(false)
const indexToRemove = ref<string | null>(null)
const removingIndex = ref(false)

// Computed options for index URL selection
const indexUrlOptions = computed(() => {
    return [
        { title: t('adapters.defaultPyPI'), value: null },
        ...indexes.value.map(url => ({ title: maskAuthUrl(url), value: url }))
    ]
})

const extraIndexUrlOptions = computed(() => {
    return indexes.value.map(url => ({ title: maskAuthUrl(url), value: url }))
})

// Install Dialog State
const installDialog = ref(false)
const installMode = ref<'spec' | 'upload'>('spec')
const installSpec = ref('')
const uploadFile = ref<File[] | null>(null)
const selectedIndexUrl = ref<string | null>(null)
const selectedExtraIndexUrls = ref<string[]>([])
const installUpgrade = ref(false)
const installing = ref(false)
const installMessage = ref<string | null>(null)
const installMessageType = ref<'success' | 'error'>('success')

// Upgrade Dialog State
const upgradeDialog = ref(false)
const adapterToUpgrade = ref<AdapterMeta | null>(null)
const upgradeIndexUrl = ref<string | null>(null)
const upgradeExtraIndexUrls = ref<string[]>([])
const upgrading = ref(false)
const upgradeMessage = ref<string | null>(null)
const upgradeMessageType = ref<'success' | 'error'>('success')

// Uninstall Dialog State
const uninstallDialog = ref(false)
const adapterToUninstall = ref<AdapterMeta | null>(null)
const uninstalling = ref(false)
const uninstallMessage = ref<string | null>(null)
const uninstallMessageType = ref<'success' | 'error'>('success')

onMounted(async () => {
    await loadAdapters()
    loadIndexes()
})

onActivated(async () => {
    await loadAdapters()
    loadIndexes()
})

// Config functions
const openConfig = async (adapter: AdapterMeta) => {
    currentAdapter.value = adapter
    configDialog.value = true
    loadingConfig.value = true
    adapterSchema.value = null
    adapterConfig.value = {}

    try {
        const [schema, config] = await Promise.all([
            AdaptersService.getAdapterConfigSchemaApiV1AdaptersAdapterNameConfigSchemaGet({ adapterName: adapter.name })
                .catch(() => null),
            AdaptersService.getAdapterConfigApiV1AdaptersAdapterNameConfigGet({ adapterName: adapter.name })
                .catch(() => ({}))
        ])
        adapterSchema.value = schema
        adapterConfig.value = config || {}
    } catch (e) {
        console.error(e)
    } finally {
        loadingConfig.value = false
    }
}

const saveConfig = async () => {
    if (!currentAdapter.value) return
    savingConfig.value = true
    try {
        await AdaptersService.setAdapterConfigApiV1AdaptersAdapterNameConfigPut({
            adapterName: currentAdapter.value.name,
            requestBody: adapterConfig.value
        })
        configDialog.value = false
    } catch (e) {
        console.error(e)
        showSnackbar('Failed to save configuration', 'error')
    } finally {
        savingConfig.value = false
    }
}

// Index functions
const loadIndexes = async () => {
    try {
        indexes.value = await PipService.listIndexesApiV1PipIndexesGet({}) || []
        if (indexes.value.length > 0 && selectedIndexUrl.value === null) {
            selectedIndexUrl.value = indexes.value[0] as string
        }
    } catch (e) { console.error(e) }
}

const addIndex = async () => {
    if (!newIndexUrl.value) return
    addingUrl.value = true
    try {
        await PipService.addIndexApiV1PipIndexesUrlPost({ url: newIndexUrl.value })
        newIndexUrl.value = ''
        await loadIndexes()
    } catch (e) {
        console.error(e)
    } finally {
        addingUrl.value = false
    }
}

const removeIndex = (url: string) => {
    indexToRemove.value = url
    removeIndexDialog.value = true
}

const confirmRemoveIndex = async () => {
    if (!indexToRemove.value) return
    removingIndex.value = true
    try {
        await PipService.deleteIndexApiV1PipIndexesUrlDelete({ url: indexToRemove.value })
        removeIndexDialog.value = false
        indexToRemove.value = null
        await loadIndexes()
    } catch (e) {
        console.error(e)
    } finally {
        removingIndex.value = false
    }
}

// Install functions
const openInstallDialog = () => {
    installSpec.value = ''
    uploadFile.value = null
    installMode.value = 'spec'
    installUpgrade.value = false
    installMessage.value = null
    installDialog.value = true
}

const performInstall = async () => {
    installing.value = true
    installMessage.value = null
    try {
        let result
        if (installMode.value === 'spec') {
            if (!installSpec.value) return
            result = await PipService.installPackageApiV1PipPkgsSpecPost({
                spec: installSpec.value,
                force: false,
                upgrade: installUpgrade.value,
                indexUrl: selectedIndexUrl.value ?? undefined,
                extraIndexUrls: selectedExtraIndexUrls.value.length > 0 ? selectedExtraIndexUrls.value : undefined
            })
        } else {
            const files = uploadFile.value
            let file: File | undefined
            if (files instanceof File) {
                file = files
            } else if (Array.isArray(files) && files.length > 0) {
                file = files[0]
            }
            if (!file) {
                installMessage.value = 'Please select a file first'
                installMessageType.value = 'error'
                return
            }
            result = await PipService.installPackageByWhlApiV1PipPkgsWhlPost({
                formData: { file: file },
                force: false,
                upgrade: installUpgrade.value,
                indexUrl: selectedIndexUrl.value ?? undefined,
                extraIndexUrls: selectedExtraIndexUrls.value.length > 0 ? selectedExtraIndexUrls.value : undefined
            })
        }
        installMessage.value = result.output || `Successfully installed ${result.target}`
        installMessageType.value = 'success'
        showSnackbar(t('adapters.installSuccess'), 'success')
        installDialog.value = false
        await loadAdapters()
    } catch (e: any) {
        console.error(e)
        const errorOutput = e?.body?.detail || e?.body?.output || 'Installation failed'
        installMessage.value = errorOutput
        installMessageType.value = 'error'
    } finally {
        installing.value = false
    }
}

// Upgrade functions
const openUpgradeDialog = (adapter: AdapterMeta) => {
    adapterToUpgrade.value = adapter
    upgradeIndexUrl.value = indexes.value.length > 0 ? (indexes.value[0] ?? null) : null
    upgradeExtraIndexUrls.value = []
    upgradeMessage.value = null
    upgradeDialog.value = true
}

const performUpgrade = async () => {
    if (!adapterToUpgrade.value) return
    upgrading.value = true
    upgradeMessage.value = null
    try {
        const result = await PipService.installPackageApiV1PipPkgsSpecPost({
            spec: adapterToUpgrade.value.name,
            force: false,
            upgrade: true,
            indexUrl: upgradeIndexUrl.value ?? undefined,
            extraIndexUrls: upgradeExtraIndexUrls.value.length > 0 ? upgradeExtraIndexUrls.value : undefined
        })
        upgradeMessage.value = result.output || `Successfully upgraded ${result.target}`
        upgradeMessageType.value = 'success'
        showSnackbar(t('adapters.upgradeSuccess'), 'success')
        upgradeDialog.value = false
        await loadAdapters()
    } catch (e: any) {
        console.error(e)
        const errorOutput = e?.body?.detail || e?.body?.output || 'Upgrade failed'
        upgradeMessage.value = errorOutput
        upgradeMessageType.value = 'error'
    } finally {
        upgrading.value = false
    }
}

// Uninstall functions
const openUninstallDialog = (adapter: AdapterMeta) => {
    adapterToUninstall.value = adapter
    uninstallMessage.value = null
    uninstallDialog.value = true
}

const performUninstall = async () => {
    if (!adapterToUninstall.value) return
    uninstalling.value = true
    uninstallMessage.value = null
    try {
        const result = await PipService.uninstallPackageApiV1PipPkgsPackageNameDelete({
            packageName: adapterToUninstall.value.name,
            removeLoadedModules: true
        })
        uninstallMessage.value = result.output || `Successfully uninstalled ${result.target}`
        uninstallMessageType.value = 'success'
        showSnackbar(t('adapters.uninstallSuccess'), 'success')
        uninstallDialog.value = false
        await loadAdapters()
    } catch (e: any) {
        console.error(e)
        const errorOutput = e?.body?.output || e?.body?.detail || 'Uninstall failed'
        uninstallMessage.value = errorOutput
        uninstallMessageType.value = 'error'
    } finally {
        uninstalling.value = false
    }
}
</script>

<style scoped>
.card-outlined {
    border: 1px solid rgba(0, 0, 0, 0.12);
}

.pip-section-card {
    border: 1px solid rgba(0, 0, 0, 0.15) !important;
    border-radius: 6px !important;
}

:root.v-theme--dark .pip-section-card {
    border-color: rgba(255, 255, 255, 0.15) !important;
}

/* Tab styling - rounded top, flat bottom */
:deep(.v-tabs .v-tab) {
    border-radius: 8px 8px 0 0 !important;
}

/* Pip alert text wrapping */
.pip-alert {
    white-space: pre-wrap;
    word-break: break-word;
}

.pip-alert :deep(.v-alert__content) {
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: break-word;
}

/* Fix v-window overflow clipping text field labels in install dialog */
.install-dialog-window {
    overflow: visible;
}

.install-dialog-window :deep(.v-window__container) {
    overflow: visible;
}

.install-dialog-window :deep(.v-window-item) {
    overflow: visible;
}
</style>
