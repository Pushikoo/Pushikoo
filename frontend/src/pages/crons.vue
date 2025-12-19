<template>
  <v-container fluid>
    <!-- Page Header -->
    <v-row class="mb-6">
      <v-col cols="12">
        <div class="d-flex align-center justify-space-between flex-wrap ga-4">
          <div>
            <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('crons.title') }}</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              {{ $t('crons.description') }}
            </p>
          </div>
          <div class="d-flex ga-2">
            <v-btn color="primary" variant="tonal" prepend-icon="mdi-refresh" @click="refreshData" :loading="loading">
              {{ $t('common.refresh') }}
            </v-btn>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
              {{ $t('crons.createCron') }}
            </v-btn>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Crons Table -->
    <v-row>
      <v-col cols="12">
        <v-card class="card-outlined">
          <v-card-text v-if="initialLoading" class="pa-0">
            <LoadingSpinner :text="$t('crons.loadingCrons')" />
          </v-card-text>
          <v-data-table v-show="!initialLoading" :items="crons" :headers="headers" :loading="loading"
            :items-per-page-text="$t('common.itemsPerPage')" :items-per-page-options="[10, 25, 50, 100]"
            class="elevation-0">
            <template v-slot:item.flow_id="{ item }">
              <div class="d-flex align-center">
                <v-avatar :color="item.enabled ? 'primary' : 'grey'" variant="tonal" size="32" class="mr-3">
                  <v-icon icon="mdi-sitemap" size="16"></v-icon>
                </v-avatar>
                <span class="font-weight-medium" :class="{ 'text-medium-emphasis': !item.enabled }">{{
                  getFlowDisplayName(item.flow_id) }}</span>
              </div>
            </template>

            <template v-slot:item.cron="{ item }">
              <v-chip :color="item.enabled ? 'info' : 'grey'" variant="tonal" size="small" label>
                <v-icon icon="mdi-clock-outline" size="small" class="mr-1"></v-icon>
                {{ item.cron }}
              </v-chip>
            </template>

            <template v-slot:item.id="{ item }">
              <code class="text-caption" :class="{ 'text-medium-emphasis': !item.enabled }">{{ item.id }}</code>
            </template>

            <template v-slot:item.actions="{ item }">
              <div class="d-flex flex-nowrap align-center">
                <v-btn :icon="item.enabled ? 'mdi-pause' : 'mdi-play'" variant="text" size="small"
                  :color="item.enabled ? 'warning' : 'success'" @click="confirmToggleEnabled(item)" />
                <v-btn icon="mdi-pencil-outline" variant="text" size="small" @click="openEditDialog(item)" />
                <v-btn icon="mdi-delete-outline" variant="text" size="small" color="error"
                  @click="confirmDeleteItem(item)" />
              </div>
            </template>

            <template v-slot:no-data>
              <div class="text-center py-8">
                <v-icon icon="mdi-clock-outline" size="64" color="medium-emphasis" class="mb-4"></v-icon>
                <div class="text-h6 text-medium-emphasis">{{ $t('crons.noScheduledTasks') }}</div>
                <div class="text-body-2 text-medium-emphasis mb-4">
                  {{ $t('crons.createCronJobToAutomateFlowExecution') }}
                </div>
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
                  {{ $t('crons.createCron') }}
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create Dialog -->
    <v-dialog v-model="dialog" max-width="500px" persistent :fullscreen="$vuetify.display.smAndDown">
      <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-plus-circle" class="mr-2"></v-icon>
          {{ $t('crons.createScheduledTask') }}
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="closeDialog"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form ref="form" @submit.prevent="saveItem">
            <v-autocomplete v-model="newItem.flow_id" :items="availableFlows" item-title="displayName" item-value="id"
              :label="$t('crons.flow')" prepend-inner-icon="mdi-sitemap" :rules="[v => !!v || $t('common.required')]"
              class="mb-4">
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" class="flow-dropdown-item">
                  <template v-slot:title>
                    <div class="flow-dropdown-title">{{ item.raw.displayName }}</div>
                  </template>
                </v-list-item>
              </template>
              <template v-slot:selection="{ item }">
                <div class="flow-dropdown-selection">{{ item.raw.displayName }}</div>
              </template>
            </v-autocomplete>

            <v-text-field v-model="newItem.cron" :label="$t('crons.cronExpression')" placeholder="*/30 * * * *"
              prepend-inner-icon="mdi-clock-outline" :rules="[v => !!v || $t('common.required')]"
              :hint="$t('crons.standardCronFormatHint')" persistent-hint></v-text-field>

            <v-alert type="info" variant="tonal" density="compact" class="mt-4">
              <div class="text-caption">
                <strong>{{ $t('crons.cronFieldsTitle') }}</strong><br>
                • 5 {{ $t('crons.fields') }}: <code>min hr day month week</code><br>
                • 6 {{ $t('crons.fields') }}: <code>sec min hr day month week</code><br>
                • 7 {{ $t('crons.fields') }}: <code>sec min hr day month week year</code><br>
                <br>
                <strong>{{ $t('crons.examples') }}</strong><br>
                • <code>*/5 * * * *</code> - {{ $t('crons.everyFiveMinutes') }}<br>
                • <code>30 * * * * *</code> - {{ $t('crons.everyMinuteAt30s') }}<br>
                • <code>0 0 * * *</code> - {{ $t('crons.dailyAtMidnight') }}
              </div>
            </v-alert>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-2 pa-sm-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeDialog">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" @click="saveItem" :loading="saving" :disabled="!newItem.flow_id || !newItem.cron">
            {{ $t('common.create') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="deleteDialog" max-width="400px" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-alert-circle" color="error" class="mr-2"></v-icon>
          {{ $t('crons.deleteScheduledTask') }}
        </v-card-title>
        <v-card-text>
          {{ $t('crons.confirmDeleteMessage') }}
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="tonal" @click="deleteItem" :loading="deleting">
            {{ $t('common.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Dialog -->
    <v-dialog v-model="editDialog" max-width="500px" persistent :fullscreen="$vuetify.display.smAndDown">
      <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-pencil" class="mr-2"></v-icon>
          {{ $t('crons.editScheduledTask') }}
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="closeEditDialog"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form ref="editForm" @submit.prevent="saveEditItem">
            <v-text-field v-model="editItem.cron" :label="$t('crons.cronExpression')" placeholder="*/30 * * * *"
              prepend-inner-icon="mdi-clock-outline" :rules="[v => !!v || $t('common.required')]"
              :hint="$t('crons.standardCronFormatHint')" persistent-hint></v-text-field>

            <v-alert type="info" variant="tonal" density="compact" class="mt-4">
              <div class="text-caption">
                <strong>{{ $t('crons.cronFieldsTitle') }}</strong><br>
                • 5 {{ $t('crons.fields') }}: <code>min hr day month week</code><br>
                • 6 {{ $t('crons.fields') }}: <code>sec min hr day month week</code><br>
                • 7 {{ $t('crons.fields') }}: <code>sec min hr day month week year</code><br>
                <br>
                <strong>{{ $t('crons.examples') }}</strong><br>
                • <code>*/5 * * * *</code> - {{ $t('crons.everyFiveMinutes') }}<br>
                • <code>30 * * * * *</code> - {{ $t('crons.everyMinuteAt30s') }}<br>
                • <code>0 0 * * *</code> - {{ $t('crons.dailyAtMidnight') }}
              </div>
            </v-alert>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-2 pa-sm-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeEditDialog">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" @click="saveEditItem" :loading="editSaving" :disabled="!editItem.cron">
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Enable/Disable Confirmation -->
    <v-dialog v-model="toggleDialog" max-width="400px" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon :icon="itemToToggle?.enabled ? 'mdi-pause' : 'mdi-play'"
            :color="itemToToggle?.enabled ? 'warning' : 'success'" class="mr-2"></v-icon>
          {{ itemToToggle?.enabled ? $t('crons.disableScheduledTask') : $t('crons.enableScheduledTask') }}
        </v-card-title>
        <v-card-text>
          {{ itemToToggle?.enabled ? $t('crons.confirmDisableMessage') : $t('crons.confirmEnableMessage') }}
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="toggleDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn :color="itemToToggle?.enabled ? 'warning' : 'success'" variant="tonal" @click="executeToggleEnabled"
            :loading="toggling">
            {{ itemToToggle?.enabled ? $t('crons.disable') : $t('crons.enable') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted, onActivated, inject, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CronsService, FlowsService, InstancesService, type Cron, type Flow } from '@/client'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const showSnackbar = inject<(text: string, color?: string) => void>('showSnackbar', () => { })
const { t } = useI18n()

const crons = ref<Cron[]>([])
const loading = ref(false)
const initialLoading = ref(true)
const saving = ref(false)
const dialog = ref(false)
const deleteDialog = ref(false)
const newItem = ref<{ flow_id: string; cron: string }>({ flow_id: '', cron: '' })
const itemToDelete = ref<Cron | null>(null)
const deleting = ref(false)
const togglingCrons = ref<Set<string>>(new Set())
const editDialog = ref(false)
const editItem = ref<{ id: string; cron: string }>({ id: '', cron: '' })
const editSaving = ref(false)
const toggleDialog = ref(false)
const itemToToggle = ref<Cron | null>(null)
const toggling = ref(false)

const flowMap = ref<Record<string, string>>({})
const availableFlows = ref<{ id: string; displayName: string }[]>([])

const headers = computed(() => [
  { title: t('crons.tableHeaderFlow'), key: 'flow_id' },
  { title: t('crons.tableHeaderSchedule'), key: 'cron', width: '200px' },
  { title: t('crons.tableHeaderId'), key: 'id', width: '250px' },
  { title: t('common.actions'), key: 'actions', align: 'end' as const, sortable: false, width: '160px' },
])

onMounted(async () => {
  await loadMetadata()
  await loadData()
})

onActivated(async () => {
  await refreshData()
})

const loadMetadata = async () => {
  try {
    // Load all flows
    const flowsResponse = await FlowsService.listFlowsApiV1FlowsGet({})
    const flows: Flow[] = flowsResponse.items || []

    // Load all adapter instances to display node names
    const instancesResponse = await InstancesService.listInstancesApiV1InstancesGet({})
    const instanceNameMap: Record<string, string> = {}

    for (const inst of instancesResponse.items || []) {
      instanceNameMap[inst.id] = `${inst.adapter_name} / ${inst.identifier}`
    }

    // Build flow display name mapping
    const map: Record<string, string> = {}
    const list: { id: string; displayName: string }[] = []

    for (const flow of flows) {
      const nodeNames = flow.nodes.map(nodeId => instanceNameMap[nodeId] || nodeId)
      const pipelineStr = nodeNames.length > 0
        ? nodeNames.join(' → ')
        : 'Empty'
      const displayName = `${flow.name} (${flow.id})`

      map[flow.id] = displayName
      list.push({ id: flow.id, displayName })
    }

    flowMap.value = map
    availableFlows.value = list
  } catch (e) {
    console.error('Failed to load metadata', e)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const response = await CronsService.listCronsApiV1CronsGet({})
    crons.value = response.items || []
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to load crons', 'error')
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

const refreshData = async () => {
  await loadMetadata()
  await loadData()
}

const getFlowDisplayName = (id: string) => {
  return flowMap.value[id] || id
}

const openCreateDialog = () => {
  newItem.value = { flow_id: '', cron: '' }
  dialog.value = true
}

const closeDialog = () => {
  dialog.value = false
}

const saveItem = async () => {
  if (!newItem.value.flow_id || !newItem.value.cron) return

  saving.value = true
  try {
    await CronsService.createCronApiV1CronsPost({
      requestBody: newItem.value
    })
    dialog.value = false
    await loadData()
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to create cron', 'error')
  } finally {
    saving.value = false
  }
}

const confirmDeleteItem = (item: Cron) => {
  itemToDelete.value = item
  deleteDialog.value = true
}

const deleteItem = async () => {
  if (!itemToDelete.value) return
  deleting.value = true
  try {
    await CronsService.deleteCronApiV1CronsCronIdDelete({ cronId: itemToDelete.value.id })
    deleteDialog.value = false
    itemToDelete.value = null
    await loadData()
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to delete cron', 'error')
  } finally {
    deleting.value = false
  }
}

const confirmToggleEnabled = (item: Cron) => {
  itemToToggle.value = item
  toggleDialog.value = true
}

const executeToggleEnabled = async () => {
  if (!itemToToggle.value) return
  const item = itemToToggle.value
  const newValue = !item.enabled
  toggling.value = true
  try {
    await CronsService.updateCronApiV1CronsCronIdPatch({
      cronId: item.id,
      requestBody: { enabled: newValue }
    })
    item.enabled = newValue
    toggleDialog.value = false
    itemToToggle.value = null
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to update cron', 'error')
  } finally {
    toggling.value = false
  }
}

const openEditDialog = (item: Cron) => {
  editItem.value = { id: item.id, cron: item.cron }
  editDialog.value = true
}

const closeEditDialog = () => {
  editDialog.value = false
}

const saveEditItem = async () => {
  if (!editItem.value.cron) return

  editSaving.value = true
  try {
    await CronsService.updateCronApiV1CronsCronIdPatch({
      cronId: editItem.value.id,
      requestBody: { cron: editItem.value.cron }
    })
    editDialog.value = false
    await loadData()
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to update cron', 'error')
  } finally {
    editSaving.value = false
  }
}
</script>

<style scoped>
.card-outlined {
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.flow-dropdown-title {
  font-size: 0.85rem;
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
  max-width: 450px;
}

.flow-dropdown-selection {
  font-size: 0.85rem;
  white-space: normal;
  word-break: break-word;
  max-width: 100%;
}

.flow-dropdown-item {
  min-height: auto !important;
  padding-top: 8px !important;
  padding-bottom: 8px !important;
  max-width: 500px;
}
</style>
