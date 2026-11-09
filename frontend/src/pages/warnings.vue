<template>
  <v-container fluid>
    <v-row class="mb-6">
      <v-col cols="12">
        <div class="d-flex align-center justify-space-between flex-wrap ga-4">
          <div>
            <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('warnings.title') }}</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">{{ $t('warnings.description') }}</p>
          </div>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openAddDialog">{{ $t('warnings.addRecipient') }}</v-btn>
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card class="card-outlined">
          <v-card-title>{{ $t('warnings.recipients') }}</v-card-title>
          <v-card-text v-if="loadingRecipients"><LoadingSpinner :text="$t('warnings.loadingRecipients')" /></v-card-text>
          <v-list v-else-if="recipients.length" class="bg-transparent">
            <v-list-item v-for="recipient in recipients" :key="recipient.id" border rounded="lg" class="mx-2 my-1">
              <template #prepend><v-avatar color="warning" variant="tonal"><v-icon icon="mdi-bell-outline" /></v-avatar></template>
              <v-list-item-title>{{ recipient.identifier }}</v-list-item-title>
              <v-list-item-subtitle>{{ recipient.adapter_name }} · {{ recipient.id }}</v-list-item-subtitle>
              <template #append><v-btn icon="mdi-delete-outline" variant="text" color="error" @click="confirmRemoveRecipient(recipient)" /></template>
            </v-list-item>
          </v-list>
          <div v-else class="text-center text-medium-emphasis py-8">{{ $t('warnings.noRecipientsConfigured') }}</div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="card-outlined">
          <v-card-title class="d-flex align-center">
            {{ $t('warnings.records') }}
            <v-spacer />
            <v-btn icon="mdi-refresh" variant="text" :loading="loadingWarnings" @click="loadWarnings" />
          </v-card-title>
          <v-card-text v-if="loadingWarnings"><LoadingSpinner :text="$t('warnings.loadingRecords')" /></v-card-text>
          <v-list v-else-if="warnings.length" lines="three" class="bg-transparent">
            <v-list-item v-for="warning in warnings" :key="warning.id" class="mb-3 border rounded-lg">
              <v-list-item-title class="text-body-2 font-weight-medium warning-preview">{{ warningPreview(warning) }}</v-list-item-title>
              <v-list-item-subtitle class="mt-1">{{ formatDate(warning.created_at) }}</v-list-item-subtitle>
              <div v-if="warning.deliveries.length" class="d-flex flex-wrap ga-2 mt-3">
                <v-chip v-for="delivery in warning.deliveries" :key="delivery.id" :color="deliveryColor(delivery.status)" variant="tonal" size="small">
                  {{ delivery.recipient_name }} · {{ $t(`warnings.deliveryStatus.${delivery.status}`) }} · {{ $t('warnings.attempts', { count: delivery.attempts }) }}
                  <v-tooltip v-if="delivery.last_error" activator="parent">{{ delivery.last_error }}</v-tooltip>
                  <v-icon v-if="delivery.status !== 'sent'" icon="mdi-refresh" end @click.stop="retryDelivery(delivery.id)" />
                </v-chip>
              </div>
              <v-chip v-else size="small" color="grey" variant="tonal" class="mt-3">{{ $t('warnings.noDeliveries') }}</v-chip>
            </v-list-item>
          </v-list>
          <div v-else class="text-center text-medium-emphasis py-8">{{ $t('warnings.noRecords') }}</div>
          <v-pagination v-if="warningTotal > warningLimit" v-model="warningPage" :length="Math.ceil(warningTotal / warningLimit)" class="pa-3" />
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="dialog" max-width="500" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4"><v-icon icon="mdi-bell-plus" class="mr-2" />{{ $t('warnings.addRecipient') }}<v-spacer /><v-btn icon="mdi-close" variant="text" @click="dialog = false" /></v-card-title>
        <v-divider />
        <v-card-text>
          <v-select v-model="selectedInstanceId" :items="availableInstances" item-title="identifier" item-value="id" :label="$t('warnings.selectAdapterInstance')" :loading="loadingInstances">
            <template #item="{ props, item }"><v-list-item v-bind="props" :subtitle="item.raw.adapter_name" /></template>
          </v-select>
        </v-card-text>
        <v-card-actions class="pa-4"><v-spacer /><v-btn variant="text" @click="dialog = false">{{ $t('common.cancel') }}</v-btn><v-btn color="primary" :disabled="!selectedInstanceId" :loading="adding" @click="addRecipient">{{ $t('common.add') }}</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="removeDialog" max-width="400" persistent>
      <v-card rounded="xl">
        <v-card-title>{{ $t('warnings.removeRecipient') }}</v-card-title>
        <v-card-text>{{ $t('warnings.confirmRemoveMessage', { identifier: recipientToRemove?.identifier }) }}</v-card-text>
        <v-card-actions class="pa-4"><v-spacer /><v-btn variant="text" @click="removeDialog = false">{{ $t('common.cancel') }}</v-btn><v-btn color="error" :loading="removing" @click="removeRecipient">{{ $t('common.remove') }}</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts" setup>
import { inject, onActivated, onMounted, ref, watch } from 'vue'
import { AdaptersService, InstancesService, WarningsService, type AdapterInstance, type AdapterMeta, type Warning } from '@/client'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { structAsPlainText, type Struct } from '@/utils/structRenderer'
import { getApiErrorMessage } from '@/utils/apiErrorHelper'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const showSnackbar = inject<(text: string, color?: string) => void>('showSnackbar', () => { })
const recipients = ref<AdapterInstance[]>([])
const warnings = ref<Warning[]>([])
const warningTotal = ref(0)
const warningPage = ref(1)
const warningLimit = 20
const loadingRecipients = ref(false)
const loadingWarnings = ref(false)
const dialog = ref(false)
const removeDialog = ref(false)
const availableInstances = ref<AdapterInstance[]>([])
const loadingInstances = ref(false)
const selectedInstanceId = ref<string | null>(null)
const adding = ref(false)
const recipientToRemove = ref<AdapterInstance | null>(null)
const removing = ref(false)

const refresh = () => Promise.all([loadRecipients(), loadWarnings()])
onMounted(refresh)
onActivated(refresh)
watch(warningPage, loadWarnings)

async function loadRecipients() {
  loadingRecipients.value = true
  try { recipients.value = (await WarningsService.listRecipientsApiV1WarningsRecipientsGet({})).items }
  catch (error) { showSnackbar(getApiErrorMessage(error, t('warnings.loadFailed')), 'error') }
  finally { loadingRecipients.value = false }
}

async function loadWarnings() {
  loadingWarnings.value = true
  try {
    const response = await WarningsService.listWarningsApiV1WarningsGet({ limit: warningLimit, offset: (warningPage.value - 1) * warningLimit })
    warnings.value = response.items
    warningTotal.value = response.total
  } catch (error) { showSnackbar(getApiErrorMessage(error, t('warnings.loadFailed')), 'error') }
  finally { loadingWarnings.value = false }
}

const warningPreview = (warning: Warning) => structAsPlainText(warning.content as unknown as Struct) || t('warnings.mediaContent')
const formatDate = (value: string) => new Date(value).toLocaleString()
const deliveryColor = (status: string) => status === 'sent' ? 'success' : status === 'failed' ? 'error' : 'warning'

async function openAddDialog() {
  dialog.value = true
  selectedInstanceId.value = null
  loadingInstances.value = true
  try {
    const [adapters, instances] = await Promise.all([AdaptersService.listAdaptersApiV1AdaptersGet(), InstancesService.listInstancesApiV1InstancesGet({})])
    const pusherNames = new Set(adapters.filter((adapter: AdapterMeta) => adapter.type === 'pusher').map(adapter => adapter.name))
    const existing = new Set(recipients.value.map(recipient => recipient.id))
    availableInstances.value = instances.items.filter(instance => pusherNames.has(instance.adapter_name) && !existing.has(instance.id))
  } finally { loadingInstances.value = false }
}

async function addRecipient() {
  if (!selectedInstanceId.value) return
  adding.value = true
  try {
    await WarningsService.addRecipientApiV1WarningsRecipientsPost({ requestBody: { adapter_instance_id: selectedInstanceId.value } })
    dialog.value = false
    await loadRecipients()
  } finally { adding.value = false }
}

function confirmRemoveRecipient(recipient: AdapterInstance) { recipientToRemove.value = recipient; removeDialog.value = true }
async function removeRecipient() {
  if (!recipientToRemove.value) return
  removing.value = true
  try {
    await WarningsService.deleteRecipientApiV1WarningsRecipientsAdapterInstanceIdDelete({ adapterInstanceId: recipientToRemove.value.id })
    removeDialog.value = false
    await Promise.all([loadRecipients(), loadWarnings()])
  } finally { removing.value = false }
}

async function retryDelivery(deliveryId: string) {
  try {
    await WarningsService.retryWarningDeliveryApiV1WarningsDeliveriesDeliveryIdRetryPost({ deliveryId })
    showSnackbar(t('warnings.retryStarted'), 'success')
    await loadWarnings()
  } catch (error) { showSnackbar(getApiErrorMessage(error, t('warnings.retryFailed')), 'error') }
}
</script>

<style scoped>
.card-outlined { border: 1px solid rgba(0, 0, 0, 0.12); }
.warning-preview { white-space: normal; overflow-wrap: anywhere; }
</style>
