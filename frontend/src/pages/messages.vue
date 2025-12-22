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
          <v-btn color="primary" :icon="$vuetify.display.xs" @click="refreshData" :loading="loading">
            <v-icon icon="mdi-refresh"></v-icon>
            <span class="d-none d-sm-inline ml-2">{{ $t('common.refresh') }}</span>
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
            <div v-if="getRenderedContent(editedItem)" v-html="getRenderedHtml(editedItem)" class="markdown-content"
              @click="handleMarkdownClick" />
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

    <!-- Image Preview Dialog -->
    <v-dialog v-model="imagePreviewDialog" :fullscreen="$vuetify.display.smAndDown" max-width="90vw" max-height="90vh">
      <v-card :rounded="$vuetify.display.smAndDown ? '0' : 'xl'" class="image-preview-card">
        <v-card-title class="d-flex align-center pa-2 pa-sm-3 image-preview-title">
          <v-icon icon="mdi-image" class="mr-2" size="small"></v-icon>
          <span class="text-body-2 text-sm-body-1">{{ $t('common.imagePreview') }}</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-minus" variant="text" size="small" @click="zoomOut" :disabled="imageZoom <= 0.25"></v-btn>
          <span class="text-caption text-sm-body-2 mx-1 mx-sm-2">{{ Math.round(imageZoom * 100) }}%</span>
          <v-btn icon="mdi-plus" variant="text" size="small" @click="zoomIn" :disabled="imageZoom >= 5"></v-btn>
          <v-btn icon="mdi-refresh" variant="text" size="small" @click="resetZoom" class="ml-1 ml-sm-2"></v-btn>
          <v-btn icon="mdi-close" variant="text" size="small" @click="closeImagePreview" class="ml-1 ml-sm-2"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-0 image-preview-container" ref="imageContainerRef" @wheel.prevent="handleWheel"
          @mousedown="startDrag" @mousemove="onDrag" @mouseup="stopDrag" @mouseleave="stopDrag"
          @touchstart.prevent="handleTouchStart" @touchmove.prevent="handleTouchMove" @touchend="handleTouchEnd">
          <img :src="previewImageSrc" :style="imagePreviewStyle" class="preview-image" draggable="false"
            ref="previewImageRef" @load="onImageLoad" />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, onActivated, inject, computed, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { MessagesService, type Message } from '@/client'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { structAsMarkdown, structAsPlainText, type Struct } from '@/utils/structRenderer'
import { marked } from 'marked'

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
const imagePreviewDialog = ref(false)
const previewImageSrc = ref('')
const imageZoom = ref(1)
const imagePosition = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const imageContainerRef = ref<HTMLElement | null>(null)
const previewImageRef = ref<HTMLImageElement | null>(null)
const lastTouchDistance = ref(0)
const lastTouchCenter = ref({ x: 0, y: 0 })
const initialFitZoom = ref(1)

const imagePreviewStyle = computed(() => ({
  transform: `translate(${imagePosition.value.x}px, ${imagePosition.value.y}px) scale(${imageZoom.value})`,
  cursor: isDragging.value ? 'grabbing' : 'grab',
  transformOrigin: 'center center',
}))

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
  if (!item.content) return ''
  const text = structAsPlainText(item.content as Struct)
  return text || 'Media/Mixed Content'
}

const getContentPreview = (item: Message): string => {
  const full = getFullContentPreview(item)
  if (full.length <= 30) return full
  return full.slice(0, 30) + '...'
}

const getRenderedContent = (item: Message): string => {
  if (!item.content) return ''
  return structAsMarkdown(item.content as Struct)
}

const getRenderedHtml = (item: Message): string => {
  const md = getRenderedContent(item)
  if (!md) return ''
  return marked.parse(md, { breaks: true }) as string
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

const openImagePreview = (src: string) => {
  previewImageSrc.value = src
  imageZoom.value = 1
  imagePosition.value = { x: 0, y: 0 }
  initialFitZoom.value = 1
  imagePreviewDialog.value = true
}

const onImageLoad = async () => {
  // Wait for DOM to update
  await nextTick()

  // Calculate fit-to-window zoom
  const img = previewImageRef.value
  const container = imageContainerRef.value

  if (!img) {
    initialFitZoom.value = 1
    imageZoom.value = 1
    return
  }

  const imgWidth = img.naturalWidth
  const imgHeight = img.naturalHeight

  if (imgWidth === 0 || imgHeight === 0) {
    initialFitZoom.value = 1
    imageZoom.value = 1
    return
  }

  // Get container dimensions, fallback to viewport if not available
  const containerWidth = container?.clientWidth || window.innerWidth * 0.9
  const containerHeight = container?.clientHeight || window.innerHeight * 0.75

  const scaleX = containerWidth / imgWidth
  const scaleY = containerHeight / imgHeight
  // Minimum zoom is 50%
  let fitZoom = Math.max(Math.min(scaleX, scaleY, 1) * 0.95, 0.5)

  // Ensure fitZoom is a valid number
  if (isNaN(fitZoom) || fitZoom <= 0) {
    initialFitZoom.value = 1
    imageZoom.value = 1
  } else {
    initialFitZoom.value = fitZoom
    imageZoom.value = fitZoom
  }

  // For tall images (height > width), position from top
  const isLongImage = imgHeight > imgWidth * 1.2
  if (isLongImage && container) {
    // Calculate vertical offset to show from top
    const scaledHeight = imgHeight * fitZoom
    const offsetY = Math.max(0, (scaledHeight - containerHeight) / 2)
    imagePosition.value = { x: 0, y: offsetY }
  } else {
    imagePosition.value = { x: 0, y: 0 }
  }
}

const closeImagePreview = () => {
  imagePreviewDialog.value = false
  resetZoom()
}

const zoomIn = () => {
  imageZoom.value = Math.min(imageZoom.value * 1.25, 5)
}

const zoomOut = () => {
  imageZoom.value = Math.max(imageZoom.value / 1.25, 0.25)
}

const resetZoom = () => {
  imageZoom.value = initialFitZoom.value || 1
  imagePosition.value = { x: 0, y: 0 }
}

const handleWheel = (event: WheelEvent) => {
  const delta = event.deltaY > 0 ? -0.1 : 0.1
  const newZoom = Math.max(0.25, Math.min(5, imageZoom.value + delta))
  imageZoom.value = newZoom
}

const startDrag = (event: MouseEvent) => {
  isDragging.value = true
  dragStart.value = {
    x: event.clientX - imagePosition.value.x,
    y: event.clientY - imagePosition.value.y,
  }
}

const onDrag = (event: MouseEvent) => {
  if (!isDragging.value) return
  imagePosition.value = {
    x: event.clientX - dragStart.value.x,
    y: event.clientY - dragStart.value.y,
  }
}

const stopDrag = () => {
  isDragging.value = false
}

// Touch gesture helpers
const getTouchDistance = (touches: TouchList): number => {
  if (touches.length < 2) return 0
  const t0 = touches[0]
  const t1 = touches[1]
  if (!t0 || !t1) return 0
  const dx = t0.clientX - t1.clientX
  const dy = t0.clientY - t1.clientY
  return Math.sqrt(dx * dx + dy * dy)
}

const getTouchCenter = (touches: TouchList): { x: number; y: number } => {
  const t0 = touches[0]
  if (!t0) return { x: 0, y: 0 }
  if (touches.length < 2) {
    return { x: t0.clientX, y: t0.clientY }
  }
  const t1 = touches[1]
  if (!t1) return { x: t0.clientX, y: t0.clientY }
  return {
    x: (t0.clientX + t1.clientX) / 2,
    y: (t0.clientY + t1.clientY) / 2,
  }
}

const handleTouchStart = (event: TouchEvent) => {
  const t0 = event.touches[0]
  if (!t0) return

  if (event.touches.length === 2) {
    // Pinch zoom start
    lastTouchDistance.value = getTouchDistance(event.touches)
    lastTouchCenter.value = getTouchCenter(event.touches)
  } else if (event.touches.length === 1) {
    // Pan start
    isDragging.value = true
    dragStart.value = {
      x: t0.clientX - imagePosition.value.x,
      y: t0.clientY - imagePosition.value.y,
    }
  }
}

const handleTouchMove = (event: TouchEvent) => {
  if (event.touches.length === 2) {
    // Pinch zoom
    const newDistance = getTouchDistance(event.touches)
    if (lastTouchDistance.value > 0) {
      const scale = newDistance / lastTouchDistance.value
      const newZoom = Math.max(0.25, Math.min(5, imageZoom.value * scale))
      imageZoom.value = newZoom
    }
    lastTouchDistance.value = newDistance

    // Pan while pinching
    const newCenter = getTouchCenter(event.touches)
    imagePosition.value = {
      x: imagePosition.value.x + (newCenter.x - lastTouchCenter.value.x),
      y: imagePosition.value.y + (newCenter.y - lastTouchCenter.value.y),
    }
    lastTouchCenter.value = newCenter
  } else if (event.touches.length === 1 && isDragging.value) {
    // Single finger pan
    const t0 = event.touches[0]
    if (!t0) return
    imagePosition.value = {
      x: t0.clientX - dragStart.value.x,
      y: t0.clientY - dragStart.value.y,
    }
  }
}

const handleTouchEnd = () => {
  isDragging.value = false
  lastTouchDistance.value = 0
}

// Set up click handler for images in markdown content
const handleMarkdownClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (target.tagName === 'IMG') {
    const imgSrc = (target as HTMLImageElement).src
    if (imgSrc) {
      openImagePreview(imgSrc)
    }
  }
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

/* Markdown content styles */
.markdown-content {
  word-break: break-word;
  line-height: 1.6;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 0;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.3;
}

.markdown-content :deep(h1) {
  font-size: 1.5em;
}

.markdown-content :deep(h2) {
  font-size: 1.3em;
}

.markdown-content :deep(h3) {
  font-size: 1.15em;
}

.markdown-content :deep(h4) {
  font-size: 1em;
}

.markdown-content :deep(p) {
  margin: 0 0 0.5em 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(img) {
  min-width: 75px;
  min-height: 75px;
  max-width: 150px;
  max-height: 200px;
  object-fit: cover;
  object-position: top;
  border-radius: 8px;
  margin: 0.5em 0;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.markdown-content :deep(img:hover) {
  opacity: 0.8;
}

.image-preview-card {
  overflow: hidden;
}

.image-preview-title {
  background: rgb(var(--v-theme-surface));
}

.image-preview-container {
  height: 75vh;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(128, 128, 128, 0.15);
  user-select: none;
  touch-action: none;
}

@media (max-width: 600px) {
  .image-preview-container {
    height: calc(100vh - 56px);
  }
}

.preview-image {
  max-width: none;
  max-height: none;
  /* No transition for initial auto-zoom */
}

.markdown-content :deep(a) {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(strong) {
  font-weight: 600;
}

.markdown-content :deep(em) {
  font-style: italic;
}
</style>
