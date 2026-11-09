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
            <v-btn color="primary" variant="tonal" :icon="$vuetify.display.xs" @click="refreshData" :loading="loading">
              <v-icon icon="mdi-refresh"></v-icon>
              <span class="d-none d-sm-inline ml-2">{{ $t('common.refresh') }}</span>
            </v-btn>
            <v-btn color="primary" :icon="$vuetify.display.xs" @click="openCreateDialog">
              <v-icon icon="mdi-plus"></v-icon>
              <span class="d-none d-sm-inline ml-2">{{ $t('flows.createFlow') }}</span>
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
              <div class="d-flex flex-wrap align-center ga-1 pa-3">
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
              <draggable v-model="editedItem.nodes" handle=".handle" :item-key="flowNodeItemKey" :animation="200"
                ghost-class="flow-node-ghost" chosen-class="flow-node-chosen" drag-class="flow-node-drag">
                <template #item="{ element, index }">
                  <v-list-item class="flow-node-item mb-2 pa-2 rounded-lg border bg-surface" elevation="0">
                    <template v-slot:prepend>
                      <span class="text-caption font-weight-bold text-primary ml-1 mr-2" style="min-width: 20px;">
                        {{ String(index + 1).padStart(2, '0') }}
                      </span>
                      <div class="d-flex align-center handle cursor-move mr-3">
                        <v-icon icon="mdi-drag" color="medium-emphasis" size="small"></v-icon>
                      </div>
                    </template>
                    <v-list-item-title class="font-weight-medium text-body-2">
                      {{ getInstanceName(element) }}
                    </v-list-item-title>
                    <template v-slot:append>
                      <v-btn icon="mdi-close" variant="text" size="small" color="medium-emphasis" class="ml-2"
                        @click="removeNode(index)" />
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
          <v-btn icon="mdi-alert-circle-outline" variant="text" size="small" @click="openFailedItems"
            :title="$t('flows.failedMessages')" class="mr-1"></v-btn>
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
              <v-list-item-title class="font-weight-medium d-flex flex-wrap align-center ga-1">
                <v-chip :color="statusColors[instance.status]" size="small" label variant="tonal">
                  {{ instance.status }}
                </v-chip>
                <v-chip v-if="instance.kind === 'retry'" color="info" size="x-small" label>{{ $t('flows.retryKind') }}</v-chip>
                <v-chip v-for="entry in instanceCountEntries(instance)" :key="entry.status" :color="itemStatusColors[entry.status]"
                  size="x-small" variant="tonal">{{ itemStatusLabel(entry.status) }} {{ entry.count }}</v-chip>
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption mt-1">
                {{ formatDateTime(instance.created_at) }}
              </v-list-item-subtitle>
              <template v-slot:append>
                <v-btn icon="mdi-eye" variant="text" size="small" color="primary" @click="openInstanceDetail(instance)"
                  :loading="loadingInstanceDetail && selectedInstanceId === instance.id"
                  :title="$t('flows.viewDetail')" />
              </template>
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
          <div class="mb-3">
            <div class="d-flex flex-wrap ga-2 mb-3">
              <v-btn size="small" variant="tonal" prepend-icon="mdi-checkbox-multiple-marked" @click="selectAllNodes">
                {{ $t('flows.selectAll') }}
              </v-btn>
              <v-btn size="small" variant="tonal" prepend-icon="mdi-checkbox-multiple-blank-outline"
                @click="selectNoneNodes">
                {{ $t('flows.selectNone') }}
              </v-btn>
              <v-btn size="small" variant="tonal" prepend-icon="mdi-swap-horizontal" @click="invertNodeSelection">
                {{ $t('flows.invertSelection') }}
              </v-btn>
            </div>
            <v-card variant="outlined" class="pa-2 node-selection-card" rounded="lg">
              <v-checkbox v-for="node in executeFlowNodes" :key="node.id" v-model="selectedNodes" :value="node.id"
                :label="node.displayName" density="compact" hide-details class="mb-1"></v-checkbox>
            </v-card>
            <p class="text-caption text-medium-emphasis mt-2">{{ $t('flows.selectNodesHint') }}</p>
          </div>
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

    <!-- Instance Detail Dialog -->
    <v-dialog v-model="instanceDetailDialog" max-width="700px" :fullscreen="$vuetify.display.smAndDown">
      <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-file-tree" class="mr-2"></v-icon>
          {{ $t('flows.instanceDetail') }}
          <v-spacer></v-spacer>
          <v-btn v-if="selectedInstanceItems.some(item => item.status === 'failed')" color="error" variant="tonal"
            size="small" prepend-icon="mdi-refresh" @click="retryInstanceFailed" :loading="itemActionLoading" class="mr-2">
            {{ $t('flows.retryAllFailed') }}
          </v-btn>
          <v-btn icon="mdi-refresh" variant="text" size="small" @click="refreshInstanceDetail"
            :loading="loadingInstanceDetail" class="mr-1"></v-btn>
          <v-btn icon="mdi-close" variant="text" size="small" @click="instanceDetailDialog = false"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <div v-if="loadingInstanceDetail" class="text-center py-6">
            <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
            <div class="text-body-2 text-medium-emphasis mt-2">{{ $t('common.loading') }}</div>
          </div>

          <div v-else-if="selectedInstanceDetail">
            <div class="d-flex align-center flex-wrap ga-2 mb-4">
              <v-chip :color="statusColors[selectedInstanceDetail.status]" size="small" label variant="tonal">
                {{ selectedInstanceDetail.status }}
              </v-chip>
              <v-chip v-if="selectedInstanceDetail.kind === 'retry'" color="info" size="small" label>{{ $t('flows.retryKind') }}</v-chip>
              <v-btn v-if="selectedInstanceDetail.parent_instance_id" variant="text" size="small"
                prepend-icon="mdi-arrow-left" @click="openInstanceDetailById(selectedInstanceDetail.parent_instance_id)">
                {{ $t('flows.parentInstance') }}
              </v-btn>
              <span class="text-caption text-medium-emphasis">{{ formatDateTime(selectedInstanceDetail.created_at) }}</span>
            </div>

            <v-timeline density="compact" side="end" v-if="selectedInstanceDetail.node_executions.length > 0">
              <v-timeline-item v-for="execution in selectedInstanceDetail.node_executions" :key="execution.id"
                :dot-color="getNodeStatusColor(execution.status)" size="small">
                <template v-slot:icon>
                  <v-icon
                    :icon="execution.status === 'success' ? 'mdi-check' : execution.status === 'running' ? 'mdi-play' : 'mdi-close'"
                    size="12"></v-icon>
                </template>
                <v-card variant="outlined" class="mb-2 card-outlined" rounded="lg">
                  <v-card-text class="pa-3">
                    <div class="d-flex align-center mb-2">
                      <v-chip :color="getNodeStatusColor(execution.status)" size="x-small" label variant="tonal"
                        class="mr-2">
                        {{ execution.status }}
                      </v-chip>
                      <span class="font-weight-medium">{{ getInstanceName(execution.adapter_instance_id) }}</span>
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      <span v-if="execution.finished_at">
                        {{ $t('flows.duration') }}: {{ formatDuration(execution.started_at, execution.finished_at) }}
                      </span>
                      <span class="mx-2">|</span>
                      <span>{{ $t('flows.itemsIn') }}: {{ execution.items_in }}</span>
                      <span class="mx-2">|</span>
                      <span>{{ $t('flows.itemsOut') }}: {{ execution.items_out }}</span>
                    </div>
                    <div v-if="execution.message" class="text-caption mt-1 text-grey">
                      {{ execution.message }}
                    </div>
                    <v-alert v-if="execution.error_message" type="error" variant="tonal" density="compact" class="mt-2">
                      {{ execution.error_message }}
                    </v-alert>
                  </v-card-text>
                </v-card>
              </v-timeline-item>
            </v-timeline>

            <div v-else class="text-center py-6">
              <v-icon icon="mdi-information-outline" size="32" color="medium-emphasis" class="mb-2"></v-icon>
              <div class="text-body-2 text-medium-emphasis">{{ $t('flows.noNodeExecutions') }}</div>
            </div>

            <v-divider class="my-4"></v-divider>
            <h3 class="text-subtitle-1 font-weight-bold mb-3">{{ $t('flows.items') }}</h3>
            <v-list v-if="selectedInstanceItems.length" class="bg-transparent" lines="three">
              <v-list-item v-for="item in selectedInstanceItems" :key="item.id" class="mb-2 border rounded-lg">
                <v-list-item-title class="d-flex align-center flex-wrap ga-2">
                  <v-chip :color="itemStatusColors[item.status]" size="x-small" label>{{ itemStatusLabel(item.status) }}</v-chip>
                  <span class="text-caption">{{ $t('flows.stuckNode') }}: {{ item.adapter_instance_id ? getInstanceName(item.adapter_instance_id) : '-' }}</span>
                </v-list-item-title>
                <v-list-item-subtitle class="mt-1 item-preview">{{ getItemPreview(item) }}</v-list-item-subtitle>
                <v-alert v-if="item.status === 'failed' && item.last_error" type="error" variant="tonal" density="compact" class="mt-2">{{ item.last_error }}</v-alert>
                <v-btn v-if="item.retried_by_instance_id" variant="text" size="x-small" class="mt-1"
                  @click="openInstanceDetailById(item.retried_by_instance_id)">{{ $t('flows.viewRetryInstance') }}</v-btn>
                <template v-if="item.status === 'failed'" v-slot:append>
                  <div class="d-flex flex-column ga-1">
                    <v-btn size="x-small" color="primary" variant="tonal" @click="retryItems([item.id])" :loading="itemActionLoading">{{ $t('common.retry') }}</v-btn>
                    <v-btn size="x-small" color="warning" variant="tonal" @click="dismissItems([item.id])" :loading="itemActionLoading">{{ $t('flows.dismiss') }}</v-btn>
                  </div>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-body-2 text-medium-emphasis">{{ $t('flows.noItems') }}</div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Failed Items Dialog -->
    <v-dialog v-model="failedItemsDialog" max-width="850px" :fullscreen="$vuetify.display.smAndDown">
      <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-alert-circle-outline" color="error" class="mr-2"></v-icon>
          {{ $t('flows.failedMessages') }}
          <v-spacer></v-spacer>
          <v-btn variant="tonal" color="primary" size="small" class="mr-2" @click="retryAllFlowFailed" :loading="itemActionLoading">{{ $t('flows.retryAll') }}</v-btn>
          <v-btn icon="mdi-close" variant="text" size="small" @click="failedItemsDialog = false"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <div class="d-flex ga-2 mb-3">
            <v-btn :disabled="!selectedFailedItemIds.length" color="primary" variant="tonal" size="small" @click="retryItems(selectedFailedItemIds)">{{ $t('common.retry') }}</v-btn>
            <v-btn :disabled="!selectedFailedItemIds.length" color="warning" variant="tonal" size="small" @click="dismissItems(selectedFailedItemIds)">{{ $t('flows.dismiss') }}</v-btn>
          </div>
          <v-list v-if="failedItems.length" class="bg-transparent">
            <v-list-item v-for="item in failedItems" :key="item.id" class="mb-2 border rounded-lg">
              <template v-slot:prepend><v-checkbox-btn v-model="selectedFailedItemIds" :value="item.id"></v-checkbox-btn></template>
              <v-list-item-title>{{ getItemPreview(item) }}</v-list-item-title>
              <v-list-item-subtitle>{{ getInstanceName(item.adapter_instance_id || '') }} · {{ formatDateTime(item.created_at) }}</v-list-item-subtitle>
              <v-alert v-if="item.last_error" type="error" variant="tonal" density="compact" class="mt-2">{{ item.last_error }}</v-alert>
            </v-list-item>
          </v-list>
          <div v-else class="text-center text-medium-emphasis py-6">{{ $t('flows.noFailedMessages') }}</div>
          <v-pagination v-if="failedItemsTotal > failedItemsPerPage" v-model="failedItemsPage"
            :length="Math.ceil(failedItemsTotal / failedItemsPerPage)" class="mt-3"></v-pagination>
        </v-card-text>
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
import { FlowsService, InstancesService, type Flow, type FlowInstance, type FlowInstanceDetail, type FlowInstanceStatus, type FlowItem, type FlowItemStatus } from '@/client'
import draggable from 'vuedraggable'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { getApiErrorMessage } from '@/utils/apiErrorHelper'
import { structAsPlainText, type Struct } from '@/utils/structRenderer'

const showSnackbar = inject<(text: string, color?: string) => void>('showSnackbar', () => { })
const { t } = useI18n()

const flowNodeItemKey = (nodeId: string) => nodeId

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
const selectedNodes = ref<string[]>([])
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
const failedItemsDialog = ref(false)
const failedItems = ref<FlowItem[]>([])
const selectedFailedItemIds = ref<string[]>([])
const failedItemsPage = ref(1)
const failedItemsPerPage = 10
const failedItemsTotal = ref(0)
const itemActionLoading = ref(false)

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

const itemStatusColors: Record<FlowItemStatus, string> = {
  pending: 'grey',
  done: 'success',
  dropped: 'warning',
  failed: 'error',
  retried: 'info'
}

const instanceCountEntries = (instance: FlowInstance) =>
  (Object.entries(instance.item_counts) as [FlowItemStatus, number][])
    .filter(([, count]) => count > 0)
    .map(([status, count]) => ({ status, count }))

const itemStatusLabel = (status: FlowItemStatus) => t(`flows.itemStatus.${status}`)

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

watch(failedItemsPage, () => {
  if (failedItemsDialog.value) loadFailedItems()
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
    showSnackbar(getApiErrorMessage(e, 'Failed to load flows'), 'error')
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
  // Select all nodes by default
  selectedNodes.value = [...item.nodes]
  executeDialog.value = true
}

const selectAllNodes = () => {
  if (flowToExecute.value) {
    selectedNodes.value = [...flowToExecute.value.nodes]
  }
}

const selectNoneNodes = () => {
  selectedNodes.value = []
}

const invertNodeSelection = () => {
  if (flowToExecute.value) {
    const allNodes = flowToExecute.value.nodes
    selectedNodes.value = allNodes.filter(n => !selectedNodes.value.includes(n))
  }
}

const confirmExecuteFlow = async () => {
  if (!flowToExecute.value) return
  executingFlowId.value = flowToExecute.value.id
  try {
    // Pass selected nodes (empty array means nothing will run)
    const includeNodes = selectedNodes.value.length > 0 ? selectedNodes.value : undefined
    await FlowsService.executeFlowApiV1FlowsFlowIdExecutePost({
      flowId: flowToExecute.value.id,
      requestBody: includeNodes ? { include_nodes: includeNodes } : {}
    })
    showSnackbar(t('flows.executionStarted'), 'success')
    executeDialog.value = false
  } catch (e) {
    console.error('Failed to execute flow', e)
    showSnackbar(getApiErrorMessage(e, t('flows.executionFailed')), 'error')
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
    showSnackbar(getApiErrorMessage(e, 'Failed to save flow'), 'error')
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
    showSnackbar(getApiErrorMessage(e, 'Failed to delete flow'), 'error')
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
    showSnackbar(getApiErrorMessage(e, 'Failed to load execution history'), 'error')
  } finally {
    loadingHistory.value = false
  }
}

// Instance Detail
const instanceDetailDialog = ref(false)
const selectedInstanceDetail = ref<FlowInstanceDetail | null>(null)
const selectedInstanceItems = ref<FlowItem[]>([])
const loadingInstanceDetail = ref(false)
const selectedInstanceId = ref<string | null>(null)

const openInstanceDetail = async (instance: FlowInstance) => {
  selectedInstanceId.value = instance.id
  loadingInstanceDetail.value = true
  instanceDetailDialog.value = true
  try {
    const [detail, items] = await Promise.all([
      FlowsService.getFlowInstanceDetailApiV1FlowsInstancesInstanceIdDetailGet({ instanceId: instance.id }),
      FlowsService.listFlowInstanceItemsApiV1FlowsInstancesInstanceIdItemsGet({ instanceId: instance.id })
    ])
    selectedInstanceDetail.value = detail
    selectedInstanceItems.value = items
  } catch (e) {
    console.error(e)
    showSnackbar(getApiErrorMessage(e, 'Failed to load instance detail'), 'error')
    instanceDetailDialog.value = false
  } finally {
    loadingInstanceDetail.value = false
    selectedInstanceId.value = null
  }
}

const openInstanceDetailById = async (instanceId: string) => {
  await openInstanceDetail({ id: instanceId } as FlowInstance)
}

const getItemPreview = (item: FlowItem) => {
  const value = structAsPlainText(item.content as unknown as Struct) || t('flows.mediaContent')
  return value.length > 140 ? `${value.slice(0, 140)}…` : value
}

const refreshAfterItemAction = async () => {
  await loadFlowInstances()
  if (instanceDetailDialog.value && selectedInstanceDetail.value) {
    await openInstanceDetailById(selectedInstanceDetail.value.id)
  }
  if (failedItemsDialog.value) await loadFailedItems()
}

const retryItems = async (itemIds: string[]) => {
  itemActionLoading.value = true
  try {
    const result = await FlowsService.retryFlowItemsApiV1FlowsItemsRetryPost({ requestBody: { item_ids: itemIds } })
    showSnackbar(t('flows.retryResult', { retried: result.retried, skipped: result.skipped }), 'success')
    selectedFailedItemIds.value = []
    await refreshAfterItemAction()
  } catch (e) {
    showSnackbar(getApiErrorMessage(e, t('flows.itemActionFailed')), 'error')
  } finally {
    itemActionLoading.value = false
  }
}

const dismissItems = async (itemIds: string[]) => {
  itemActionLoading.value = true
  try {
    const result = await FlowsService.dismissFlowItemsApiV1FlowsItemsDismissPost({ requestBody: { item_ids: itemIds } })
    showSnackbar(t('flows.dismissResult', { dismissed: result.dismissed, skipped: result.skipped }), 'success')
    selectedFailedItemIds.value = []
    await refreshAfterItemAction()
  } catch (e) {
    showSnackbar(getApiErrorMessage(e, t('flows.itemActionFailed')), 'error')
  } finally {
    itemActionLoading.value = false
  }
}

const retryInstanceFailed = async () => {
  if (!selectedInstanceDetail.value) return
  itemActionLoading.value = true
  try {
    const result = await FlowsService.retryFlowItemsApiV1FlowsItemsRetryPost({ requestBody: { instance_id: selectedInstanceDetail.value.id } })
    showSnackbar(t('flows.retryResult', { retried: result.retried, skipped: result.skipped }), 'success')
    await refreshAfterItemAction()
  } catch (e) {
    showSnackbar(getApiErrorMessage(e, t('flows.itemActionFailed')), 'error')
  } finally {
    itemActionLoading.value = false
  }
}

const loadFailedItems = async () => {
  if (!selectedFlowForHistory.value) return
  const response = await FlowsService.listFlowItemsApiV1FlowsItemsGet({
    flowId: selectedFlowForHistory.value.id,
    status: 'failed',
    limit: failedItemsPerPage,
    offset: (failedItemsPage.value - 1) * failedItemsPerPage
  })
  failedItems.value = response.items
  failedItemsTotal.value = response.total
}

const openFailedItems = async () => {
  failedItemsPage.value = 1
  selectedFailedItemIds.value = []
  failedItemsDialog.value = true
  try {
    await loadFailedItems()
  } catch (e) {
    showSnackbar(getApiErrorMessage(e, t('flows.failedToLoadItems')), 'error')
  }
}

const retryAllFlowFailed = async () => {
  if (!selectedFlowForHistory.value) return
  itemActionLoading.value = true
  try {
    const result = await FlowsService.retryFlowItemsApiV1FlowsItemsRetryPost({ requestBody: { flow_id: selectedFlowForHistory.value.id } })
    showSnackbar(t('flows.retryResult', { retried: result.retried, skipped: result.skipped }), 'success')
    await refreshAfterItemAction()
  } catch (e) {
    showSnackbar(getApiErrorMessage(e, t('flows.itemActionFailed')), 'error')
  } finally {
    itemActionLoading.value = false
  }
}

const getNodeStatusColor = (status: string) => {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'error'
  if (status === 'running') return 'primary'
  return 'grey'
}

const refreshInstanceDetail = async () => {
  if (selectedInstanceDetail.value) {
    await openInstanceDetail({ id: selectedInstanceDetail.value.id } as any)
  }
}

const formatDuration = (startTime: string, endTime: string) => {
  const start = new Date(startTime).getTime()
  const end = new Date(endTime).getTime()
  const duration = end - start
  if (duration < 1000) {
    return `${duration}ms`
  } else if (duration < 60000) {
    return `${(duration / 1000).toFixed(1)}s`
  } else {
    return `${(duration / 60000).toFixed(1)}min`
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

.flow-node-item {
  will-change: transform;
}

.flow-node-ghost {
  opacity: 0.55;
}

.flow-node-chosen {
  background: rgba(var(--v-theme-primary), 0.06);
}

.flow-node-drag {
  opacity: 0.95;
}

.item-preview {
  white-space: normal;
  overflow-wrap: anywhere;
}

.flow-nodes-card {
  border: 1px solid rgba(0, 0, 0, 0.12);
}

:root.v-theme--dark .flow-nodes-card {
  border-color: rgba(255, 255, 255, 0.12);
}

.node-selection-card {
  max-height: 200px;
  overflow-y: auto;
  border-color: rgba(0, 0, 0, 0.24) !important;
}

:root.v-theme--dark .node-selection-card {
  border-color: rgba(255, 255, 255, 0.24) !important;
}
</style>
