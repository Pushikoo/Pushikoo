<template>
    <v-container fluid>
        <!-- Page Header -->
        <v-row class="mb-6">
            <v-col cols="12">
                <div class="d-flex align-center justify-space-between flex-wrap ga-4">
                    <div>
                        <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('instances.title') }}</h1>
                        <p class="text-body-2 text-medium-emphasis mb-0">
                            {{ $t('instances.description') }}
                        </p>
                    </div>
                    <div class="d-flex ga-2">
                        <v-btn color="primary" variant="tonal" :icon="$vuetify.display.xs" @click="loadAllInstances"
                            :loading="loadingInstances">
                            <v-icon icon="mdi-refresh"></v-icon>
                            <span class="d-none d-sm-inline ml-2">{{ $t('common.refresh') }}</span>
                        </v-btn>
                        <v-btn color="primary" :icon="$vuetify.display.xs" @click="openCreateDialog">
                            <v-icon icon="mdi-plus"></v-icon>
                            <span class="d-none d-sm-inline ml-2">{{ $t('instances.createInstance') }}</span>
                        </v-btn>
                    </div>
                </div>
            </v-col>
        </v-row>

        <!-- Instances Table -->
        <v-row>
            <v-col cols="12">
                <v-card class="card-outlined">
                    <v-card-text v-if="initialLoading" class="pa-0">
                        <LoadingSpinner :text="$t('messages.loadingMessages')" />
                    </v-card-text>
                    <v-data-table v-show="!initialLoading" :items="instances" :headers="instanceHeaders"
                        :loading="loadingInstances" :items-per-page-text="$t('common.itemsPerPage')"
                        :items-per-page-options="[10, 25, 50, 100]" class="elevation-0">
                        <template v-slot:item.adapter_name="{ item }">
                            <v-chip :color="getAdapterTypeColor(getAdapterType(item.adapter_name))" variant="tonal"
                                size="small" label>
                                <v-icon :icon="getAdapterTypeIcon(getAdapterType(item.adapter_name))" size="small"
                                    start></v-icon>
                                {{ item.adapter_name }}
                            </v-chip>
                        </template>

                        <template v-slot:item.identifier="{ item }">
                            <div class="d-flex align-center">
                                <v-icon icon="mdi-identifier" size="small" class="mr-2 text-medium-emphasis"></v-icon>
                                <span class="font-weight-medium">{{ item.identifier }}</span>
                            </div>
                        </template>

                        <template v-slot:item.id="{ item }">
                            <code class="text-caption">{{ item.id }}</code>
                        </template>

                        <template v-slot:item.actions="{ item }">
                            <div class="d-flex flex-nowrap">
                                <v-btn icon="mdi-cog-outline" variant="text" size="small" color="primary"
                                    @click="editInstance(item)" />
                                <v-btn icon="mdi-delete-outline" variant="text" size="small" color="error"
                                    @click="deleteInstance(item)" />
                            </div>
                        </template>

                        <template v-slot:no-data>
                            <div class="text-center py-8">
                                <v-icon icon="mdi-server-off" size="64" color="medium-emphasis" class="mb-4"></v-icon>
                                <div class="text-h6 text-medium-emphasis">{{ $t('instances.noInstances') }}</div>
                                <div class="text-body-2 text-medium-emphasis mb-4">
                                    {{ $t('instances.noInstancesText') }}
                                </div>
                                <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
                                    {{ $t('instances.createInstance') }}
                                </v-btn>
                            </div>
                        </template>
                    </v-data-table>
                </v-card>
            </v-col>
        </v-row>

        <!-- Create/Edit Dialog -->
        <v-dialog v-model="dialog" max-width="800px" scrollable persistent :fullscreen="$vuetify.display.smAndDown">
            <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'" class="d-flex flex-column"
                :style="$vuetify.display.smAndDown ? 'height: 100%' : ''">
                <v-card-title class="d-flex align-center pa-3 pa-sm-4">
                    <v-icon :icon="isEditing ? 'mdi-pencil' : 'mdi-plus-circle'" class="mr-2"></v-icon>
                    {{ isEditing ? $t('instances.editInstance') : $t('instances.createInstance') }}
                    <v-spacer></v-spacer>
                    <v-btn icon="mdi-close" variant="text" size="small" @click="closeDialog"></v-btn>
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text :style="$vuetify.display.smAndDown ? 'flex: 1; overflow-y: auto;' : 'max-height: 60vh;'"
                    class="pa-3 pa-sm-4">
                    <v-form ref="form">
                        <v-row>
                            <v-col cols="12" md="6">
                                <v-select v-if="!isEditing" v-model="selectedAdapterName" :items="adapters"
                                    item-title="name" item-value="name" :label="$t('instances.adapterType')"
                                    prepend-inner-icon="mdi-puzzle-outline" :rules="[v => !!v || $t('crons.required')]"
                                    @update:model-value="onAdapterSelect">
                                    <template v-slot:item="{ props, item }">
                                        <v-list-item v-bind="props"
                                            :subtitle="item.raw.summary || item.raw.description || ''">
                                            <template v-slot:prepend>
                                                <v-icon :icon="getAdapterTypeIcon(item.raw.type)"
                                                    :color="getAdapterTypeColor(item.raw.type)" class="mr-2"></v-icon>
                                            </template>
                                            <template v-slot:append>
                                                <v-chip size="x-small" :color="getAdapterTypeColor(item.raw.type)"
                                                    variant="tonal">
                                                    {{ item.raw.type }}
                                                </v-chip>
                                            </template>
                                        </v-list-item>
                                    </template>
                                    <template v-slot:selection="{ item }">
                                        <v-icon :icon="getAdapterTypeIcon(item.raw.type)"
                                            :color="getAdapterTypeColor(item.raw.type)" size="small"
                                            class="mr-2"></v-icon>
                                        {{ item.raw.name }}
                                    </template>
                                </v-select>
                                <v-text-field v-else v-model="selectedAdapterName" :label="$t('instances.adapterType')"
                                    prepend-inner-icon="mdi-puzzle-outline" readonly disabled></v-text-field>
                            </v-col>
                            <v-col cols="12" md="6">
                                <v-text-field v-model="editedItem.identifier" :label="$t('instances.instanceName')"
                                    prepend-inner-icon="mdi-identifier" :rules="[v => !!v || $t('crons.required')]"
                                    :readonly="isEditing" :disabled="isEditing" persistent-hint></v-text-field>
                            </v-col>
                        </v-row>

                        <v-divider class="my-6"></v-divider>

                        <div class="d-flex align-center mb-4">
                            <v-icon icon="mdi-cog" class="mr-2"></v-icon>
                            <span class="text-subtitle-1 font-weight-bold">{{ $t('system.configuration') }}</span>
                        </div>

                        <LoadingSpinner v-if="loadingSchema" :text="$t('system.loadingSystemStatus')" size="40"
                            class="my-4" />

                        <SchemaForm v-if="instanceSchema && !loadingSchema" v-model="configData"
                            :schema="instanceSchema" :root-schema="instanceSchema" />

                        <v-alert v-if="!instanceSchema && !loadingSchema && selectedAdapterName" type="info"
                            variant="tonal" density="compact">
                            {{ $t('adapters.noConfigurationSchema') }}
                        </v-alert>

                        <div v-if="!selectedAdapterName && !loadingSchema"
                            class="text-center text-medium-emphasis py-4">
                            {{ $t('instances.selectAdapterToViewOptions') }}
                        </div>
                    </v-form>
                </v-card-text>
                <v-divider></v-divider>
                <v-card-actions class="pa-2 pa-sm-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="closeDialog">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="primary" @click="saveInstance" :loading="saving"
                        :disabled="!selectedAdapterName || !editedItem.identifier">
                        {{ isEditing ? $t('common.save') : $t('instances.createInstance') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Delete Confirmation -->
        <v-dialog v-model="deleteDialog" max-width="400px" persistent>
            <v-card rounded="xl">
                <v-card-title class="d-flex align-center pa-4">
                    <v-icon icon="mdi-alert-circle" color="error" class="mr-2"></v-icon>
                    {{ $t('instances.deleteInstance') }}
                </v-card-title>
                <v-card-text>
                    {{ $t('instances.confirmDelete') }}
                </v-card-text>
                <v-card-actions class="pa-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="error" variant="tonal" @click="confirmDelete" :loading="deleting">
                        {{ $t('common.delete') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted, onActivated, inject, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { AdaptersService, InstancesService, type AdapterMeta, type AdapterInstance, type AdapterType } from '@/client'
import SchemaForm from '@/components/SchemaForm.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const showSnackbar = inject<(text: string, color?: string) => void>('showSnackbar', () => { })
const { t } = useI18n()

// Adapter type helpers
const getAdapterTypeColor = (type: AdapterType | undefined): string => {
    switch (type) {
        case 'getter': return 'success'
        case 'pusher': return 'info'
        case 'processer': return 'warning'
        default: return 'primary'
    }
}

const getAdapterTypeIcon = (type: AdapterType | undefined): string => {
    switch (type) {
        case 'getter': return 'mdi-download-outline'
        case 'pusher': return 'mdi-upload-outline'
        case 'processer': return 'mdi-cog-outline'
        default: return 'mdi-puzzle-outline'
    }
}

const getAdapterType = (adapterName: string | undefined): AdapterType | undefined => {
    if (!adapterName) return undefined
    return adapters.value.find(a => a.name === adapterName)?.type
}

const adapters = ref<AdapterMeta[]>([])
const instances = ref<(AdapterInstance & { adapter_name?: string })[]>([])
const instanceHeaders = computed(() => [
    { title: t('instances.tableHeaderAdapter'), key: 'adapter_name', width: '200px' },
    { title: t('instances.tableHeaderIdentifier'), key: 'identifier' },
    { title: t('instances.tableHeaderId'), key: 'id', width: '300px' },
    { title: t('common.actions'), key: 'actions', align: 'end' as const, sortable: false, width: '120px' },
])

const loadingInstances = ref(false)
const initialLoading = ref(true)
const loadingSchema = ref(false)
const saving = ref(false)

const dialog = ref(false)
const deleteDialog = ref(false)
const isEditing = ref(false)
const editedItem = ref<Partial<AdapterInstance>>({})
const selectedAdapterName = ref<string>('')
const itemToDelete = ref<(AdapterInstance & { adapter_name?: string }) | null>(null)
const deleting = ref(false)

const instanceSchema = ref<any>(null)
const configData = ref<any>({})

onMounted(async () => {
    await loadAdapters()
    await loadAllInstances()
})

onActivated(async () => {
    await loadAllInstances()
})

const loadAdapters = async () => {
    try {
        const list = await AdaptersService.listAdaptersApiV1AdaptersGet()
        adapters.value = list || []
    } catch (e) {
        console.error(e)
        throw e // Re-throw to propagate to caller
    }
}

const loadAllInstances = async () => {
    loadingInstances.value = true
    instances.value = []
    try {
        if (adapters.value.length === 0) await loadAdapters()
        const response = await InstancesService.listInstancesApiV1InstancesGet({})
        instances.value = response.items || []
    } catch (e) {
        console.error(e)
        showSnackbar('Failed to load instances', 'error')
    } finally {
        loadingInstances.value = false
        initialLoading.value = false
    }
}

const onAdapterSelect = async (name: string | null) => {
    if (!name) {
        instanceSchema.value = null
        return
    }
    loadingSchema.value = true
    try {
        const schema = await AdaptersService.getAdapterInstanceConfigSchemaApiV1AdaptersAdapterNameInstanceConfigSchemaGet({
            adapterName: name
        })
        instanceSchema.value = schema

        if (!isEditing.value) {
            configData.value = {}
        }
    } catch (e) {
        console.error(e)
        instanceSchema.value = null
    } finally {
        loadingSchema.value = false
    }
}

const openCreateDialog = () => {
    isEditing.value = false
    editedItem.value = { identifier: '' }
    selectedAdapterName.value = ''
    instanceSchema.value = null
    configData.value = {}
    dialog.value = true
}

const editInstance = async (item: AdapterInstance & { adapter_name?: string }) => {
    const adpName = item.adapter_name
    if (!adpName || !item.id) return

    isEditing.value = true
    editedItem.value = { ...item }
    selectedAdapterName.value = adpName
    dialog.value = true

    await onAdapterSelect(adpName)

    try {
        const config = await InstancesService.getInstanceConfigApiV1InstancesInstanceIdConfigGet({
            instanceId: item.id
        })
        configData.value = config || {}
    } catch (e) {
        console.error(e)
    }
}

const closeDialog = () => {
    dialog.value = false
}

const saveInstance = async () => {
    if (!selectedAdapterName.value || !editedItem.value.identifier) return
    saving.value = true
    try {
        if (isEditing.value && editedItem.value.id) {
            // Update config for existing instance
            await InstancesService.setInstanceConfigApiV1InstancesInstanceIdConfigPut({
                instanceId: editedItem.value.id,
                requestBody: configData.value
            })
        } else {
            // Create new instance, then set config
            const newInstance = await InstancesService.createInstanceApiV1InstancesPost({
                requestBody: {
                    adapter_name: selectedAdapterName.value,
                    identifier: editedItem.value.identifier
                }
            })
            await InstancesService.setInstanceConfigApiV1InstancesInstanceIdConfigPut({
                instanceId: newInstance.id,
                requestBody: configData.value
            })
        }

        dialog.value = false
        await loadAllInstances()
    } catch (e) {
        console.error(e)
        showSnackbar('Failed to save instance', 'error')
    } finally {
        saving.value = false
    }
}

const deleteInstance = (item: AdapterInstance & { adapter_name?: string }) => {
    itemToDelete.value = item
    deleteDialog.value = true
}

const confirmDelete = async () => {
    if (!itemToDelete.value?.id) return
    deleting.value = true
    try {
        await InstancesService.deleteInstanceApiV1InstancesInstanceIdDelete({
            instanceId: itemToDelete.value.id
        })
        deleteDialog.value = false
        itemToDelete.value = null
        await loadAllInstances()
    } catch (e) {
        console.error(e)
        showSnackbar('Failed to delete instance', 'error')
    } finally {
        deleting.value = false
    }
}
</script>

<style scoped>
.card-outlined {
    border: 1px solid rgba(0, 0, 0, 0.12);
}
</style>
