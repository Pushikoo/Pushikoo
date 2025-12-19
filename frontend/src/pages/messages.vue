<template>
  <v-container fluid>
    <!-- Page Header -->
    <v-row class="mb-6">
      <v-col cols="12">
        <div class="d-flex align-center justify-space-between flex-wrap ga-4">
          <div>
            <h1 class="text-h5 text-sm-h4 font-weight-bold mb-1">{{ $t('messages.title') }}</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              {{ $t('messages.description') }}
            </p>
          </div>
          <v-btn color="primary" prepend-icon="mdi-refresh" @click="refreshData" :loading="loading">
            {{ $t('common.refresh') }}
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Filters Card -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-card class="card-outlined">
          <v-card-text>
            <v-row align="center">
              <v-col cols="12" md="3">
                <v-text-field v-model="keywords" prepend-inner-icon="mdi-magnify"
                  :label="$t('messages.searchByKeywords')" hide-details clearable @click:clear="refreshData" />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field v-model="identifierFilter" prepend-inner-icon="mdi-identifier"
                  :label="$t('messages.searchByIdentifier')" hide-details clearable />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field v-model="getterFilter" prepend-inner-icon="mdi-filter-variant"
                  :label="$t('messages.filterByGetter')" hide-details clearable />
              </v-col>
              <v-col cols="12" md="3">
                <v-btn block color="primary" variant="tonal" @click="refreshData">
                  {{ $t('common.apply') }}
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Data Table -->
    <v-row>
      <v-col cols="12">
        <v-card class="card-outlined">
          <v-card-text v-if="initialLoading" class="pa-0">
            <LoadingSpinner :text="$t('messages.loadingMessages')" />
          </v-card-text>
          <v-data-table-server v-show="!initialLoading" v-model:items-per-page="itemsPerPage" :headers="headers"
            :items="items" :items-length="totalItems" :loading="loading" @update:options="loadItems"
            :items-per-page-text="$t('common.itemsPerPage')" :items-per-page-options="[10, 25, 50, 100]"
            class="elevation-0">
            <template v-slot:item.ts="{ item }">
              <div class="d-flex align-center text-no-wrap">
                <v-icon icon="mdi-clock-outline" size="small" class="mr-2 text-medium-emphasis"></v-icon>
                <span>{{ formatDate(item.ts) }}</span>
              </div>
            </template>

            <template v-slot:item.getter_name="{ item }">
              <v-chip size="small" color="secondary" variant="tonal" label>
                {{ item.getter_name }}
              </v-chip>
            </template>

            <template v-slot:item.message_identifier="{ item }">
              <div class="text-truncate text-no-wrap" style="max-width: 300px;" :title="item.message_identifier">
                {{ item.message_identifier }}
              </div>
            </template>

            <template v-slot:item.content="{ item }">
              <div class="text-truncate" :title="getFullContentPreview(item)">
                {{ getFullContentPreview(item) }}
              </div>
            </template>

            <template v-slot:item.actions="{ item }">
              <div class="d-flex flex-nowrap text-no-wrap">
                <v-btn icon="mdi-eye-outline" variant="text" size="small" color="primary" @click="viewItem(item)" />
                <v-btn icon="mdi-delete-outline" variant="text" size="small" color="error" @click="deleteItem(item)" />
              </div>
            </template>

            <template v-slot:no-data>
              <div class="text-center py-8">
                <v-icon icon="mdi-message-text-outline" size="64" color="medium-emphasis" class="mb-4"></v-icon>
                <div class="text-h6 text-medium-emphasis">{{ $t('messages.noMessagesFound') }}</div>
                <div class="text-body-2 text-medium-emphasis">{{ $t('messages.tryAdjustingFilters') }}</div>
              </div>
            </template>
          </v-data-table-server>
        </v-card>
      </v-col>
    </v-row>

    <!-- View Dialog -->
    <v-dialog v-model="dialog" max-width="800px" scrollable :fullscreen="$vuetify.display.smAndDown">
      <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-message-text" class="mr-2"></v-icon>
          {{ $t('messages.messageDetails') }}
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="close"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text v-if="editedItem" class="pa-4">
          <v-row>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">{{ $t('messages.messageId') }}</div>
              <div class="text-body-1 font-weight-medium">{{ editedItem.id }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">{{ $t('messages.source') }}</div>
              <v-chip size="small" color="secondary" variant="tonal" label>
                {{ editedItem.getter_name }}
              </v-chip>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">{{ $t('messages.messageIdentifier') }}</div>
              <div class="text-body-1">{{ editedItem.message_identifier }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">{{ $t('messages.timestamp') }}</div>
              <div class="text-body-1">{{ formatDate(editedItem.ts) }}</div>
            </v-col>
          </v-row>
          <v-divider class="my-4"></v-divider>
          <div class="text-subtitle-2 font-weight-bold mb-2">{{ $t('messages.content') }}</div>
          <v-sheet color="surface-light" rounded="lg" class="pa-4 mb-4">
            <div v-if="getRenderedContent(editedItem)" style="white-space: pre-wrap; word-break: break-word;">
              {{ getRenderedContent(editedItem) }}
            </div>
            <div v-else class="text-medium-emphasis">{{ $t('messages.noTextContent') }}</div>
          </v-sheet>
          <div class="d-flex align-center justify-space-between mb-2">
            <div class="text-subtitle-2 font-weight-bold">JSON</div>
            <v-btn size="small" variant="tonal" prepend-icon="mdi-content-copy" @click="copyJson">
              {{ $t('common.copy') }}
            </v-btn>
          </div>
          <v-sheet color="surface-light" rounded="lg" class="pa-4 overflow-auto" style="max-height: 300px;">
            <pre class="text-body-2" style="white-space: pre-wrap; word-break: break-word; margin: 0;">{{
              JSON.stringify(editedItem.content, null, 2) }}</pre>
          </v-sheet>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-2 pa-sm-4">
          <v-spacer></v-spacer>
          <v-btn variant="tonal" @click="close">{{ $t('common.close') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400px" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon icon="mdi-alert-circle" color="error" class="mr-2"></v-icon>
          {{ $t('messages.confirmDeleteTitle') }}
        </v-card-title>
        <v-card-text>
          {{ $t('messages.confirmDelete') }}
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
import { ref, onActivated, inject, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { MessagesService, type Message } from '@/client'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const showSnackbar = inject<(text: string, color?: string) => void>('showSnackbar', () => { })
const { t } = useI18n()

const headers = computed(() => [
  { title: t('messages.tableHeaderDate'), key: 'ts', width: '1%', minWidth: '160px' },
  { title: t('messages.tableHeaderGetter'), key: 'getter_name', width: '1%', minWidth: '100px' },
  { title: t('messages.tableHeaderIdentifier'), key: 'message_identifier', width: '1%', minWidth: '150px' },
  { title: t('messages.tableHeaderContent'), key: 'content', sortable: false, maxWidth: '0' },
  { title: t('messages.tableHeaderActions'), key: 'actions', sortable: false, align: 'end' as const, width: '1%', minWidth: '80px' },
])

const items = ref<Message[]>([])
const loading = ref(false)
const initialLoading = ref(true)
const totalItems = ref(0)
const itemsPerPage = ref(10)
const keywords = ref('')
const identifierFilter = ref('')
const getterFilter = ref('')

const dialog = ref(false)
const deleteDialog = ref(false)
const editedItem = ref<Message | null>(null)
const itemToDelete = ref<Message | null>(null)
const deleting = ref(false)

const formatDate = (ts: number) => {
  return new Date(ts * 1000).toLocaleString()
}

const loadItems = async ({ page, itemsPerPage, sortBy }: any) => {
  loading.value = true
  try {
    const offset = (page - 1) * itemsPerPage

    // Map Vuetify sortBy to backend order parameter
    let order = 'ts_desc'  // Default order (lowercase!)
    if (sortBy && sortBy.length > 0) {
      const sort = sortBy[0]
      const key = sort.key
      const direction = sort.order === 'asc' ? 'asc' : 'desc'

      // Map column keys to backend order values (lowercase with underscores)
      const orderMap: Record<string, string> = {
        'ts': `ts_${direction}`,
        'message_identifier': `identifier_${direction}`,
        'getter_name': `getter_name_${direction}`
      }

      if (orderMap[key]) {
        order = orderMap[key]
      }
    }

    const response = await MessagesService.listMessagesApiV1MessagesGet({
      limit: itemsPerPage,
      offset: offset,
      getterName: getterFilter.value || undefined,
      messageIdentifier: identifierFilter.value || undefined,
      keywords: keywords.value || undefined,
      order: order as any
    } as any)

    // Response is now a Page object with items and total
    items.value = response.items
    totalItems.value = response.total
  } catch (error) {
    console.error('Error loading messages:', error)
    showSnackbar('Failed to load messages', 'error')
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

const refreshData = () => {
  loadItems({ page: 1, itemsPerPage: itemsPerPage.value, sortBy: [] })
}

onActivated(() => {
  refreshData()
})

const getMessagePreview = (item: Message) => {
  if (!item.content?.content) return ''
  const firstText = item.content.content.find((c: any) => c.type === 'text' || c.type === 'title')
  if (firstText && 'text' in firstText) {
    return firstText.text
  }
  return 'Media/Mixed Content'
}

const getFullContentPreview = (item: Message): string => {
  if (!item.content?.content) return ''
  const texts = item.content.content
    .filter((c: any) => c.type === 'text' || c.type === 'title')
    .map((c: any) => c.text || '')
    .join(' ')
  return texts || 'Media/Mixed Content'
}

const getContentPreview = (item: Message): string => {
  const full = getFullContentPreview(item)
  if (full.length <= 30) return full
  return full.slice(0, 30) + '...'
}

const getRenderedContent = (item: Message): string => {
  if (!item.content?.content) return ''
  const texts = item.content.content
    .filter((c: any) => c.type === 'text' || c.type === 'title')
    .map((c: any) => c.text || '')
    .join('\n\n')
  return texts
}

const copyJson = async () => {
  if (!editedItem.value) return
  try {
    await navigator.clipboard.writeText(JSON.stringify(editedItem.value.content, null, 2))
    showSnackbar(t('common.copied'), 'success')
  } catch (e) {
    showSnackbar(t('common.copyFailed'), 'error')
  }
}

const viewItem = (item: Message) => {
  editedItem.value = item
  dialog.value = true
}

const close = () => {
  dialog.value = false
  editedItem.value = null
}

const deleteItem = (item: Message) => {
  itemToDelete.value = item
  deleteDialog.value = true
}

const confirmDelete = async () => {
  if (!itemToDelete.value) return
  deleting.value = true
  try {
    await MessagesService.deleteMessageApiV1MessagesMessageIdDelete({ messageId: itemToDelete.value.id })
    deleteDialog.value = false
    itemToDelete.value = null
    refreshData()
  } catch (e) {
    console.error(e)
    showSnackbar('Failed to delete message', 'error')
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.card-outlined {
  border: 1px solid rgba(0, 0, 0, 0.12);
}

/* Ensure minimum width for table columns */
:deep(.v-data-table th) {
  white-space: nowrap;
}

:deep(.v-data-table th:nth-child(1)) {
  min-width: 160px;
}

:deep(.v-data-table th:nth-child(2)) {
  min-width: 100px;
}

:deep(.v-data-table th:nth-child(3)) {
  min-width: 150px;
}

:deep(.v-data-table th:nth-child(5)) {
  min-width: 80px;
}
</style>
