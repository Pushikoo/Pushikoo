<template>
    <v-container fluid>
        <!-- Page Header -->
        <v-row class="mb-6">
            <v-col cols="12">
                <div class="d-flex align-center justify-space-between flex-wrap ga-4">
                    <div>
                        <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('warnings.title') }}</h1>
                        <p class="text-body-2 text-medium-emphasis mb-0">
                            {{ $t('warnings.description') }}
                        </p>
                    </div>
                    <v-btn color="primary" prepend-icon="mdi-plus" @click="openAddDialog">
                        {{ $t('warnings.addRecipient') }}
                    </v-btn>
                </div>
            </v-col>
        </v-row>

        <!-- Recipients List -->
        <v-row>
            <v-col cols="12">
                <v-card class="card-outlined">
                    <v-card-text v-if="loadingRecipients">
                        <LoadingSpinner :text="$t('warnings.loadingRecipients')" />
                    </v-card-text>

                    <v-list v-else-if="recipients.length > 0" lines="two" class="bg-transparent">
                        <v-list-item v-for="recipient in recipients" :key="recipient.id" rounded="lg" class="mx-2 my-1"
                            border>
                            <template v-slot:prepend>
                                <v-avatar color="warning" variant="tonal" size="48">
                                    <v-icon icon="mdi-bell-outline"></v-icon>
                                </v-avatar>
                            </template>
                            <v-list-item-title class="font-weight-bold">{{ recipient.identifier }}</v-list-item-title>
                            <v-list-item-subtitle>
                                <v-chip size="x-small" color="primary" variant="tonal" label class="mr-2">
                                    {{ recipient.adapter_name }}
                                </v-chip>
                                <span class="text-caption">{{ recipient.id }}</span>
                            </v-list-item-subtitle>
                            <template v-slot:append>
                                <v-btn icon="mdi-delete-outline" variant="text" color="error" size="small"
                                    @click="confirmRemoveRecipient(recipient)" />
                            </template>
                        </v-list-item>
                    </v-list>

                    <div v-else class="text-center py-12">
                        <v-icon icon="mdi-bell-off-outline" size="64" color="medium-emphasis" class="mb-4"></v-icon>
                        <div class="text-h6 text-medium-emphasis">{{ $t('warnings.noRecipientsConfigured') }}</div>
                        <div class="text-body-2 text-medium-emphasis mb-4">
                            {{ $t('warnings.addAdapterInstancesToReceiveWarningNotifications') }}
                        </div>
                        <v-btn color="primary" prepend-icon="mdi-plus" @click="openAddDialog">
                            {{ $t('warnings.addRecipient') }}
                        </v-btn>
                    </div>
                </v-card>
            </v-col>
        </v-row>

        <!-- Add Recipient Dialog -->
        <v-dialog v-model="dialog" max-width="500px" persistent :fullscreen="$vuetify.display.smAndDown">
            <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
                <v-card-title class="d-flex align-center pa-4">
                    <v-icon icon="mdi-bell-plus" class="mr-2"></v-icon>
                    {{ $t('warnings.addRecipient') }}
                    <v-spacer></v-spacer>
                    <v-btn icon="mdi-close" variant="text" size="small" @click="dialog = false"></v-btn>
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-4">
                    <v-select v-model="selectedInstanceId" :items="availableInstances" item-title="identifier"
                        item-value="id" :label="$t('warnings.selectAdapterInstance')" prepend-inner-icon="mdi-server"
                        :loading="loadingInstances"
                        :hint="availableInstances.length > 0 ? $t('warnings.instancesAvailable', { count: availableInstances.length }) : $t('warnings.noInstancesAvailable')"
                        persistent-hint>
                        <template v-slot:item="{ props, item }">
                            <v-list-item v-bind="props">
                                <template v-slot:subtitle>
                                    <v-chip size="x-small" color="primary" variant="tonal" label>
                                        {{ item.raw.adapter_name }}
                                    </v-chip>
                                </template>
                            </v-list-item>
                        </template>
                        <template v-slot:selection="{ item }">
                            <div class="d-flex align-center">
                                <span>{{ item.raw.identifier }}</span>
                                <v-chip size="x-small" color="primary" variant="tonal" label class="ml-2">
                                    {{ item.raw.adapter_name }}
                                </v-chip>
                            </div>
                        </template>
                    </v-select>

                    <v-alert v-if="availableInstances.length === 0 && !loadingInstances" type="info" variant="tonal"
                        density="compact" class="mt-4">
                        {{ $t('warnings.allInstancesAlreadyConfiguredOrNotExist') }}
                    </v-alert>
                </v-card-text>
                <v-divider></v-divider>
                <v-card-actions class="pa-2 pa-sm-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="dialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="primary" @click="addRecipient" :disabled="!selectedInstanceId" :loading="adding">
                        {{ $t('common.add') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Remove Confirmation -->
        <v-dialog v-model="removeDialog" max-width="400px" persistent>
            <v-card rounded="xl">
                <v-card-title class="d-flex align-center pa-4">
                    <v-icon icon="mdi-alert-circle" color="error" class="mr-2"></v-icon>
                    {{ $t('warnings.removeRecipient') }}
                </v-card-title>
                <v-card-text>
                    {{ $t('warnings.confirmRemoveMessage', { identifier: recipientToRemove?.identifier }) }}
                </v-card-text>
                <v-card-actions class="pa-4">
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="removeDialog = false">{{ $t('common.cancel') }}</v-btn>
                    <v-btn color="error" variant="tonal" @click="removeRecipient" :loading="removing">
                        {{ $t('common.remove') }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted, onActivated } from 'vue'
import { WarningsService, InstancesService, AdaptersService, type AdapterInstance, type AdapterMeta } from '@/client'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const recipients = ref<(AdapterInstance & { adapter_name?: string })[]>([])
const loadingRecipients = ref(false)

const dialog = ref(false)
const removeDialog = ref(false)
const availableInstances = ref<(AdapterInstance & { adapter_name?: string })[]>([])
const loadingInstances = ref(false)
const selectedInstanceId = ref<string | null>(null)
const adding = ref(false)
const recipientToRemove = ref<(AdapterInstance & { adapter_name?: string }) | null>(null)
const removing = ref(false)

onMounted(async () => {
    await loadRecipients()
})

onActivated(async () => {
    await loadRecipients()
})

const loadRecipients = async () => {
    loadingRecipients.value = true
    try {
        const response = await WarningsService.listRecipientsApiV1WarningsRecipientsGet({})
        recipients.value = response.items || []
    } catch (e) {
        console.error(e)
    } finally {
        loadingRecipients.value = false
    }
}

const openAddDialog = async () => {
    dialog.value = true
    selectedInstanceId.value = null
    loadingInstances.value = true
    try {
        // Load all adapters to get type info
        const adapters = await AdaptersService.listAdaptersApiV1AdaptersGet()
        const pusherAdapterNames = new Set(
            (adapters || [])
                .filter((a: AdapterMeta) => a.type === 'pusher')
                .map((a: AdapterMeta) => a.name)
        )

        const response = await InstancesService.listInstancesApiV1InstancesGet({})
        const all = response.items || []
        const recipientIds = new Set(recipients.value.map(r => r.id))
        // Only show instances whose adapter is a pusher and not already a recipient
        availableInstances.value = all.filter(i =>
            pusherAdapterNames.has(i.adapter_name) && !recipientIds.has(i.id)
        )
    } catch (e) {
        console.error(e)
    } finally {
        loadingInstances.value = false
    }
}

const addRecipient = async () => {
    if (!selectedInstanceId.value) return
    adding.value = true
    try {
        await WarningsService.addRecipientApiV1WarningsRecipientsPost({
            requestBody: { adapter_instance_id: selectedInstanceId.value }
        })
        dialog.value = false
        await loadRecipients()
    } catch (e) {
        console.error(e)
    } finally {
        adding.value = false
    }
}

const confirmRemoveRecipient = (recipient: AdapterInstance & { adapter_name?: string }) => {
    recipientToRemove.value = recipient
    removeDialog.value = true
}

const removeRecipient = async () => {
    if (!recipientToRemove.value) return
    removing.value = true
    try {
        await WarningsService.deleteRecipientApiV1WarningsRecipientsAdapterInstanceIdDelete({
            adapterInstanceId: recipientToRemove.value.id
        })
        removeDialog.value = false
        recipientToRemove.value = null
        await loadRecipients()
    } catch (e) {
        console.error(e)
    } finally {
        removing.value = false
    }
}
</script>

<style scoped>
.card-outlined {
    border: 1px solid rgba(0, 0, 0, 0.12);
}
</style>
