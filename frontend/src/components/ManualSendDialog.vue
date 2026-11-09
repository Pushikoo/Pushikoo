<template>
  <v-dialog :model-value="modelValue" max-width="560" persistent @update:model-value="$emit('update:modelValue', $event)">
    <v-card rounded="xl">
      <v-card-title class="d-flex align-center pa-4">
        <v-icon icon="mdi-send" class="mr-2" />
        {{ $t('manualSend.title') }}
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" size="small" @click="close" />
      </v-card-title>
      <v-divider />
      <v-card-text class="pa-4">
        <v-select
          v-model="selectedPusherIds"
          :items="pushers"
          item-title="displayName"
          item-value="id"
          :label="$t('manualSend.selectPushers')"
          :loading="loadingPushers"
          multiple
          chips
          closable-chips
          prepend-inner-icon="mdi-bullhorn"
        />
        <div class="text-caption text-medium-emphasis">
          {{ $t('manualSend.itemCount', { count: sourceCount }) }}
        </div>
      </v-card-text>
      <v-divider />
      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="text" @click="close">{{ $t('common.cancel') }}</v-btn>
        <v-btn color="primary" :disabled="!selectedPusherIds.length || !sourceCount" :loading="submitting" @click="submit">
          {{ $t('manualSend.send') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts" setup>
import { computed, inject, ref, watch } from 'vue'
import { AdaptersService, FlowsService, InstancesService, type AdapterMeta } from '@/client'
import { getApiErrorMessage } from '@/utils/apiErrorHelper'
import { useI18n } from 'vue-i18n'

const props = withDefaults(defineProps<{
  modelValue: boolean
  messageIds?: string[]
  itemIds?: string[]
}>(), {
  messageIds: () => [],
  itemIds: () => [],
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  created: [instanceIds: string[]]
}>()

const { t } = useI18n()
const showSnackbar = inject<(text: string, color?: string) => void>('showSnackbar', () => { })
const pushers = ref<{ id: string; displayName: string }[]>([])
const selectedPusherIds = ref<string[]>([])
const loadingPushers = ref(false)
const submitting = ref(false)
const sourceCount = computed(() => props.messageIds.length || props.itemIds.length)

watch(() => props.modelValue, async open => {
  if (!open) return
  selectedPusherIds.value = []
  await loadPushers()
})

const loadPushers = async () => {
  loadingPushers.value = true
  try {
    const [adapters, instances] = await Promise.all([
      AdaptersService.listAdaptersApiV1AdaptersGet(),
      InstancesService.listInstancesApiV1InstancesGet({}),
    ])
    const names = new Set(
      adapters.filter((adapter: AdapterMeta) => adapter.type === 'pusher').map(adapter => adapter.name)
    )
    pushers.value = instances.items
      .filter(instance => names.has(instance.adapter_name))
      .map(instance => ({
        id: instance.id,
        displayName: `${instance.adapter_name} / ${instance.identifier}`,
      }))
  } catch (error) {
    showSnackbar(getApiErrorMessage(error, t('manualSend.loadFailed')), 'error')
  } finally {
    loadingPushers.value = false
  }
}

const close = () => emit('update:modelValue', false)

const submit = async () => {
  submitting.value = true
  try {
    const result = await FlowsService.manualSendApiV1FlowsManualSendPost({
      requestBody: {
        pusher_ids: selectedPusherIds.value,
        message_ids: props.messageIds.length ? props.messageIds : undefined,
        item_ids: props.itemIds.length ? props.itemIds : undefined,
      },
    })
    showSnackbar(t('manualSend.created', { count: result.instance_ids.length }), 'success')
    emit('created', result.instance_ids)
    close()
  } catch (error) {
    showSnackbar(getApiErrorMessage(error, t('manualSend.createFailed')), 'error')
  } finally {
    submitting.value = false
  }
}
</script>
