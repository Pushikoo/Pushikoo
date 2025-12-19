<template>
  <v-container fluid>
    <!-- Page Header -->
    <v-row class="mb-6">
      <v-col cols="12">
        <div class="d-flex align-center justify-space-between flex-wrap ga-4">
          <div>
            <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('flows.title') }}</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              {{ $t('flows.description') }}
            </p>
          </div>
          <div class="d-flex ga-2">
            <v-btn color="primary" variant="tonal" prepend-icon="mdi-refresh" @click="refreshData" :loading="loading">
              {{ $t('common.refresh') }}
            </v-btn>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
              {{ $t('flows.createFlow') }}
            </v-btn>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Flows Table -->
    <v-row>
      <v-col cols="12">
        <v-card class="card-outlined">
          <v-card-text v-if="initialLoading" class="pa-0">
            <LoadingSpinner :text="$t('flows.loadingFlows')" />
          </v-card-text>
          <v-data-table v-show="!initialLoading" :items="flows" :headers="headers" :loading="loading"
            :items-per-page-text="$t('common.itemsPerPage')" :items-per-page-options="[10, 25, 50, 100]"
            class="elevation-0">
            <template v-slot:item.id="{ item }">
              <code class="text-caption">{{ item.id }}</code>
            </template>

            <template v-slot:item.nodes="{ item }">
              <div class="d-flex flex-wrap ga-1">
                <template v-for="(nodeId, index) in item.nodes" :key="nodeId">
                  <v-chip size="small" color="primary" variant="tonal" label>
                    {{ getInstanceName(nodeId) }}
                  </v-chip>
                  <v-icon v-if="index < item.nodes.length - 1" icon="mdi-arrow-right" size="small"
                    class="mx-1 text-medium-emphasis"></v-icon>
                </template>
                <span v-if="item.nodes.length === 0" class="text-medium-emphasis text-caption">
                  {{ $t('flows.noNodes') }}
                </span>
              </div>
            </template>

            <template v-slot:item.actions="{ item }">
              <div class="d-flex flex-nowrap">
                <v-btn icon="mdi-play" variant="text" size="small" color="success" @click="executeFlow(item)"
                  :loading="executingFlowId === item.id" :title="$t('flows.execute')" />
                <v-btn icon="mdi-pencil-outline" variant="text" size="small" color="primary" @click="editFlow(item)" />
                <v-btn icon="mdi-history" variant="text" size="small" color="info" @click="openHistoryDialog(item)"
                  :title="$t('flows.executionHistory')" />
                <v-btn icon="mdi-delete-outline" variant="text" size="small" color="error"
                  @click="confirmDeleteFlow(item)" />
              </div>
            </template>

            <template v-slot:no-data>
              <div class="text-center py-8">
                <v-icon icon="mdi-sitemap-outline" size="64" color="medium-emphasis" class="mb-4"></v-icon>
                <div class="text-h6 text-medium-emphasis">{{ $t('flows.noFlowsText') }}</div>
                <div class="text-body-2 text-medium-emphasis mb-4">
                  {{ $t('flows.createFirstFlowText') }}
                </div>
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
                  {{ $t('flows.createFlow') }}
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="700px" persistent :fullscreen="$vuetify.display.smAndDown">
      <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon :icon="isEditing ? 'mdi-pencil' : 'mdi-plus-circle'" class="mr-2"></v-icon>
          {{ isEditing ? $t('flows.editFlow') : $t('flows.createFlow') }}
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="closeDialog"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-text-field v-model="editedItem.name" :label="$t('flows.flowName')" prepend-inner-icon="mdi-tag-outline"
            variant="outlined" density="comfortable" class="mb-4" :placeholder="$t('flows.flowName')"></v-text-field>
          <div class="d-flex align-center mb-2">
            <v-icon icon="mdi-sitemap" class="mr-2"></v-icon>
            <span class="text-subtitle-1 font-weight-bold">{{ $t('flows.pipelineNodes') }}</span>
            <v-spacer></v-spacer>
            <v-chip size="small" color="info" variant="tonal">
              {{ $t('flows.nodesCount', { count: editedItem.nodes?.length || 0 }) }}
            </v-chip>
          </div>
          <p class="text-caption text-medium-emphasis mb-4">{{ $t('flows.pipelineHint') }}</p>

          <v-card variant="flat" class="mb-4 flow-nodes-card" rounded="lg">
            <v-list v-if="editedItem.nodes && editedItem.nodes.length > 0" density="compact" class="bg-transparent">
              <draggable v-model="editedItem.nodes" handle=".handle" item-key="element">
                <template #item="{ element, index }">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon class="handle cursor-move mr-2" icon="mdi-drag-vertical"></v-icon>
                      <v-avatar color="primary" variant="tonal" size="32" class="mr-3">
                        {{ index + 1 }}
                      </v-avatar>
                    </template>
                    <v-list-item-title class="font-weight-medium">
                      {{ getInstanceName(element) }}
                    </v-list-item-title>
                    <template v-slot:append>
                      <v-btn icon="mdi-close" variant="text" size="small" color="error" @click="removeNode(index)" />
                    </template>
                  </v-list-item>
                </template>
              </draggable>
            </v-list>
            <div v-else class="text-center text-medium-emphasis py-6">
              <v-icon icon="mdi-package-variant" size="32" class="mb-2"></v-icon>
              <div>{{ $t('flows.noNodesAddedYet') }}</div>
              <div class="text-caption">{{ $t('flows.addAdapterInstancesToBuildPipeline') }}</div>
            </div>
          </v-card>

          <v-autocomplete v-model="nodeToAdd" :items="availableInstances" item-title="displayName" item-value="id"
            :label="$t('flows.addNodeLabel')" prepend-inner-icon="mdi-plus" return-object
            :placeholder="$t('flows.selectAdapterInstancePlaceholder')" hide-details clearable>
            <template v-slot:append>
              <v-btn color="primary" variant="tonal" @click="addNode" :disabled="!nodeToAdd">
                {{ $t('common.add') }}
              </v-btn>
            </template>
          </v-autocomplete>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-2 pa-sm-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeDialog">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" @click="saveFlow" :loading="saving">
            {{ isEditing ? $t('common.save') : $t('flows.createFlow') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Execution History Dialog -->
    <v-dialog v-model="historyDialog" max-width="600px" :fullscreen="$vuetify.display.smAndDown">
      <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-history" class="mr-2"></v-icon>
          {{ $t('flows.executionHistory') }}
          <v-spacer></v-spacer>
          <v-btn icon="mdi-refresh" variant="text" size="small" @click="loadFlowInstances" :loading="loadingHistory"
            class="mr-1"></v-btn>
          <v-btn icon="mdi-close" variant="text" size="small" @click="historyDialog = false"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <!-- Status Filter -->
          <v-chip-group v-model="statusFilter" selected-class="text-primary" class="mb-4">
            <v-chip value="" variant="tonal" size="small" filter>{{ $t('flows.filterAll') }}</v-chip>
            <v-chip v-for="status in allStatuses" :key="status" :value="status" :color="statusColors[status]"
              variant="tonal" size="small" filter>
              {{ status }}
            </v-chip>
          </v-chip-group>

          <!-- Instances List -->
          <div v-if="loadingHistory" class="text-center py-6">
            <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
            <div class="text-body-2 text-medium-emphasis mt-2">{{ $t('flows.loadingHistory') }}</div>
          </div>

          <v-list v-else-if="flowInstances.length > 0" density="compact" class="bg-transparent">
            <v-list-item v-for="instance in flowInstances" :key="instance.id" class="mb-2 rounded-lg"
              style="border: 1px solid rgba(0,0,0,0.12);">
              <template v-slot:prepend>
                <v-avatar :color="statusColors[instance.status]" variant="tonal" size="36">
                  <v-icon :icon="statusIcons[instance.status]" size="18"></v-icon>
                </v-avatar>
              </template>
              <v-list-item-title class="font-weight-medium">
                <v-chip :color="statusColors[instance.status]" size="small" label variant="tonal">
                  {{ instance.status }}
                </v-chip>
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption mt-1">
                {{ formatDateTime(instance.created_at) }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>

          <div v-else class="text-center py-6">
            <v-icon icon="mdi-history" size="48" color="medium-emphasis" class="mb-2"></v-icon>
            <div class="text-body-2 text-medium-emphasis">{{ $t('flows.noExecutionRecords') }}</div>
          </div>

          <div v-if="totalHistoryItems > 0" class="d-flex align-center justify-space-between mt-4">
            <div class="text-caption text-medium-emphasis">
              {{ $t('common.paginationInfo', {
                from: historyOffset + 1,
                to: Math.min(historyOffset + historyItemsPerPage, totalHistoryItems),
                total: totalHistoryItems
              }) }}
            </div>
            <v-pagination v-model="historyPage" :length="Math.ceil(totalHistoryItems / historyItemsPerPage)"
              :total-visible="5" size="small" density="comfortable"></v-pagination>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Execute Confirmation Dialog -->
    <v-dialog v-model="executeDialog" max-width="500px" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-play-circle" color="success" class="mr-2"></v-icon>
          {{ $t('flows.executeFlow') }}
        </v-card-title>
        <v-card-text>
          <p class="text-body-2 mb-4">{{ $t('flows.executeConfirmMessage') }}</p>
          <v-select v-model="excludeNodes" :items="executeFlowNodes" item-title="displayName" item-value="id" multiple
            chips closable-chips :label="$t('flows.excludeNodesLabel')" variant="outlined" density="comfortable"
            clearable :hint="$t('flows.excludeNodesHint')" persistent-hint>
          </v-select>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="executeDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="success" variant="tonal" @click="confirmExecuteFlow" :loading="executingFlowId !== null">
            {{ $t('flows.execute') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="deleteDialog" max-width="400px" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-alert-circle" color="error" class="mr-2"></v-icon>
          {{ $t('flows.deleteFlow') }}
        </v-card-title>
        <v-card-text>
          {{ $t('flows.confirmDeleteMessage') }}
          <v-alert type="info" variant="tonal" density="compact" class="mt-3">
            <div class="text-caption">
              {{ $t('flows.associatedCronsWillBeDeleted') }}
            </div>
          </v-alert>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="tonal" @click="deleteFlow" :loading="deleting">
            {{ $t('common.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted, onActivated, inject, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { FlowsService, InstancesService, type Flow, type FlowInstance, type FlowInstanceStatus } from '@/client'
import draggable from 'vuedraggable'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const showSnackbar = inject<(text: string, color?: string) => void>('showSnackbar', () => { })
const { t } = useI18n()

const flows = ref<Flow[]>([])
const loading = ref(false)
const initialLoading = ref(true)
const saving = ref(false)
const dialog = ref(false)
const deleteDialog = ref(false)
const isEditing = ref(false)
const editedItem = ref<{ id?: string; name: string; nodes: string[] }>({ name: '', nodes: [] })
const nodeToAdd = ref<{ id: string; displayName: string } | null>(null)
const itemToDelete = ref<Flow | null>(null)
const deleting = ref(false)
const executingFlowId = ref<string | null>(null)

// Execute Dialog
const executeDialog = ref(false)
const flowToExecute = ref<Flow | null>(null)
const excludeNodes = ref<string[]>([])
const executeFlowNodes = computed(() => {
  if (!flowToExecute.value) return []
  return flowToExecute.value.nodes.map(nodeId => ({
    id: nodeId,
    displayName: getInstanceName(nodeId)
  }))
})

const instanceMap = ref<Record<string, string>>({})
const availableInstances = ref<{ id: string; displayName: string }[]>([])

// Execution History
const historyDialog = ref(false)
const selectedFlowForHistory = ref<Flow | null>(null)
const flowInstances = ref<FlowInstance[]>([])
const loadingHistory = ref(false)
const historyPage = ref(1)
const historyItemsPerPage = ref(10)
const totalHistoryItems = ref(0)
const historyOffset = computed(() => (historyPage.value - 1) * historyItemsPerPage.value)
const statusFilter = ref<FlowInstanceStatus | ''>('')

const allStatuses: FlowInstanceStatus[] = ['waiting', 'running', 'completed', 'failed', 'cancelled']

const statusColors: Record<FlowInstanceStatus, string> = {
  waiting: 'grey',
  running: 'blue',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning'
}

const statusIcons: Record<FlowInstanceStatus, string> = {
  waiting: 'mdi-clock-outline',
  running: 'mdi-play-circle-outline',
  completed: 'mdi-check-circle-outline',
  failed: 'mdi-close-circle-outline',
  cancelled: 'mdi-cancel'
}

const headers = computed(() => [
  { title: t('flows.tableHeaderName'), key: 'name', width: '200px' },
  { title: t('flows.tableHeaderId'), key: 'id', width: '250px' },
  { title: t('flows.tableHeaderPipeline'), key: 'nodes' },
  { title: t('common.actions'), key: 'actions', align: 'end' as const, sortable: false, width: '150px' },
])

onMounted(async () => {
  await Promise.all([loadMetadata(), loadFlows()])
})

onActivated(async () => {
  await refreshData()
})

// Watch status filter changes
watch(statusFilter, () => {
  if (historyDialog.value) {
    historyPage.value = 1  // Reset to first page when filter changes
    loadFlowInstances()
  }
})

// Watch page changes
watch(historyPage, () => {
  if (historyDialog.value) {
    loadFlowInstances()
  }
})

const loadMetadata = async () => {
  try {
    const response = await InstancesService.listInstancesApiV1InstancesGet({})
    const allInstances = response.items || []

    const map: Record<string, string> = {}
    const list: { id: string; displayName: string }[] = []

    for (const inst of allInstances) {
      const name = `${inst.adapter_name} / ${inst.identifier}`
      map[inst.id] = name
      list.push({ id: inst.id, displayName: name })
    }
    instanceMap.value = map
    availableInstances.value = list
  } catch (e) {
    console.error('Failed to load metadata', e)
  }
}

const loadFlows = async () => {
  loading.value = true
  try {
    const response = await FlowsService.listFlowsApiV1FlowsGet({})
    flows.value = response.items || []
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to load flows', 'error')
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

const refreshData = async () => {
  await Promise.all([loadMetadata(), loadFlows()])
}

const getInstanceName = (id: string) => {
  return instanceMap.value[id] || id
}

const formatDateTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleString()
}

const openCreateDialog = () => {
  isEditing.value = false
  editedItem.value = { name: '', nodes: [] }
  nodeToAdd.value = null
  dialog.value = true
}

const editFlow = (item: Flow) => {
  isEditing.value = true
  editedItem.value = { ...item, nodes: [...item.nodes] }
  nodeToAdd.value = null
  dialog.value = true
}

const executeFlow = (item: Flow) => {
  flowToExecute.value = item
  excludeNodes.value = []
  executeDialog.value = true
}

const confirmExecuteFlow = async () => {
  if (!flowToExecute.value) return
  executingFlowId.value = flowToExecute.value.id
  try {
    await FlowsService.executeFlowApiV1FlowsFlowIdExecutePost({
      flowId: flowToExecute.value.id,
      requestBody: { exclude_nodes: excludeNodes.value }
    })
    showSnackbar(t('flows.executionStarted'), 'success')
    executeDialog.value = false
  } catch (e) {
    console.error('Failed to execute flow', e)
    showSnackbar(t('flows.executionFailed'), 'error')
  } finally {
    executingFlowId.value = null
  }
}

const addNode = () => {
  if (nodeToAdd.value) {
    editedItem.value.nodes.push(nodeToAdd.value.id)
    nodeToAdd.value = null
  }
}

const removeNode = (index: number) => {
  editedItem.value.nodes.splice(index, 1)
}

const closeDialog = () => {
  dialog.value = false
}

const saveFlow = async () => {
  saving.value = true
  try {
    if (isEditing.value && editedItem.value.id) {
      await FlowsService.updateFlowApiV1FlowsFlowIdPut({
        flowId: editedItem.value.id,
        requestBody: { name: editedItem.value.name, nodes: editedItem.value.nodes }
      })
    } else {
      await FlowsService.createFlowApiV1FlowsPost({
        requestBody: { name: editedItem.value.name, nodes: editedItem.value.nodes }
      })
    }
    dialog.value = false
    await loadFlows()
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to save flow', 'error')
  } finally {
    saving.value = false
  }
}

const confirmDeleteFlow = (item: Flow) => {
  itemToDelete.value = item
  deleteDialog.value = true
}

const deleteFlow = async () => {
  if (!itemToDelete.value) return
  deleting.value = true
  try {
    await FlowsService.deleteFlowApiV1FlowsFlowIdDelete({ flowId: itemToDelete.value.id })
    deleteDialog.value = false
    itemToDelete.value = null
    await loadFlows()
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to delete flow', 'error')
  } finally {
    deleting.value = false
  }
}

// Execution History Functions
const openHistoryDialog = async (flow: Flow) => {
  selectedFlowForHistory.value = flow
  statusFilter.value = ''
  flowInstances.value = []
  historyDialog.value = true
  await loadFlowInstances()
}

const loadFlowInstances = async () => {
  if (!selectedFlowForHistory.value) return
  loadingHistory.value = true
  try {
    const response = await FlowsService.listFlowInstancesApiV1FlowsInstancesGet({
      flowId: selectedFlowForHistory.value.id,
      status: statusFilter.value || undefined,
      limit: historyItemsPerPage.value,
      offset: historyOffset.value
    })
    flowInstances.value = response.items || []
    totalHistoryItems.value = response.total || 0
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to load execution history', 'error')
  } finally {
    loadingHistory.value = false
  }
}
</script>

<style scoped>
.card-outlined {
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.cursor-move {
  cursor: move;
}

.flow-nodes-card {
  border: 1px solid rgba(0, 0, 0, 0.12);
}

:root.v-theme--dark .flow-nodes-card {
  border-color: rgba(255, 255, 255, 0.12);
}
</style>
