<template>
    <div class="schema-form" :class="{ 'is-nested': depth > 0 }">
        <div :class="['field-shell', { 'field-shell--bare': !showFrame }]">
            <div v-if="showFrame" class="field-head">
                <div>
                    <div class="title-row">
                        <span class="field-title">{{ displayLabel }}</span>
                        <v-chip v-if="required" size="x-small" color="primary" label variant="tonal" class="chip">
                            Required
                        </v-chip>
                        <v-chip v-if="normalized.const !== undefined" size="x-small" color="primary" label
                            variant="flat" class="chip">
                            Const
                        </v-chip>
                    </div>
                    <p v-if="description" class="field-description">
                        {{ description }}
                    </p>
                </div>
            </div>

            <div class="field-body" :class="{ 'field-body--bare': !showFrame }">
                <!-- Union (anyOf/oneOf with multiple concrete options) -->
                <template v-if="isUnion">
                    <div class="union-header">
                        <div class="union-header__row">
                            <div class="d-flex align-center ga-2 flex-wrap">
                                <v-chip-group v-model="selectedUnion" mandatory selected-class="union-chip-active" column
                                    @update:model-value="onUnionChange">
                                <v-chip v-for="(option, index) in unionOptions" :key="index" :value="index"
                                    variant="elevated" size="small" class="ma-1">
                                    {{ unionOptionLabel(option, index) }}
                                </v-chip>
                            </v-chip-group>
                                <span class="text-caption text-medium-emphasis">
                                    {{ unionOptions.length }} variant{{ unionOptions.length > 1 ? 's' : '' }} available
                                </span>
                            </div>

                        </div>
                    </div>
                    <div class="card-surface pa-3">
                        <div v-if="selectedUnionIsNull" class="null-variant">
                            <span class="text-caption text-medium-emphasis">Empty (null)</span>
                        </div>
                        <SchemaForm v-else-if="selectedUnionSchema" :schema="selectedUnionSchema!"
                            :root-schema="rootSchema" :model-value="localValue"
                            @update:model-value="emit('update:modelValue', $event)" :depth="0"
                            :label="selectedUnionSchema?.title" chrome="bare" />
                    </div>
                </template>

                <!-- Tuples (prefixItems) -->
                <template v-else-if="isTuple">
                    <div class="card-surface pa-3 ga-3 d-flex flex-column">
                        <div class="d-flex align-center justify-space-between flex-wrap ga-2">
                            <span class="text-body-2 text-medium-emphasis">Tuple items</span>
                            <span class="text-caption text-medium-emphasis">
                                {{ normalized.prefixItems.length }} fixed position{{ normalized.prefixItems.length > 1 ?
                                's' : '' }}
                            </span>
                        </div>
                        <div class="tuple-grid">
                            <div v-for="(tupleSchema, index) in normalized.prefixItems" :key="index"
                                class="tuple-cell">
                                <div class="tuple-label text-caption text-medium-emphasis">
                                    {{ tupleSchema.title || `Item ${index + 1}` }}
                                </div>
                                <SchemaForm :schema="tupleSchema" :root-schema="rootSchema"
                                    :model-value="readTupleValue(index)"
                                    @update:model-value="updateTupleValue(index, $event)" :depth="depth + 1"
                                    :label="tupleSchema.title || `Item ${index + 1}`" chrome="bare" />
                            </div>
                        </div>
                    </div>
                </template>

                <!-- Arrays -->
                <template v-else-if="isArrayType">
                    <div class="card-surface pa-3 ga-3 d-flex flex-column">
                        <div class="d-flex align-center justify-space-between flex-wrap ga-2">
                            <div class="d-flex align-center ga-2">
                                <v-chip size="small" label variant="flat" color="primary" class="chip">
                                    Items: {{ arrayValue.length }}
                                </v-chip>
                                <span class="text-caption text-medium-emphasis" v-if="normalized.items?.title">{{
                                    normalized.items.title }}</span>
                            </div>
                            <div class="d-flex ga-1">
                                <v-btn color="primary" variant="tonal" size="small" prepend-icon="mdi-plus"
                                    :disabled="!canAddArray" @click="addArrayItem">
                                    Add item
                                </v-btn>
                            </div>
                        </div>

                        <div v-if="arrayValue.length" class="ga-3 d-flex flex-column">
                            <div v-for="(item, index) in arrayValue" :key="index" class="array-item">
                                <div class="array-item__head">
                                    <div class="d-flex align-center ga-2">
                                        <v-chip size="x-small" label variant="outlined">#{{ index + 1 }}</v-chip>
                                        <span class="text-caption text-medium-emphasis">
                                            {{ itemLabel(index) }}
                                        </span>
                                    </div>
                                    <v-btn icon="mdi-close" color="error" variant="text" size="small"
                                        :disabled="!canRemoveArray"
                                        @click="removeArrayItem(index)" />
                                </div>
                                <SchemaForm :schema="normalized.items || {}" :root-schema="rootSchema"
                                    :model-value="item"
                                    @update:model-value="updateArrayItem(index, $event)" :depth="depth + 1"
                                    chrome="bare" />
                            </div>
                        </div>

                        <div v-else class="empty-state text-center text-medium-emphasis py-4">
                            No items yet
                        </div>
                    </div>
                </template>

                <!-- Objects -->
                <template v-else-if="isObjectType">
                    <div class="card-surface pa-3 ga-4 d-flex flex-column">
                        <div v-if="objectProperties.length" class="property-stack">
                            <div v-for="property in objectProperties" :key="property.key" class="property-card">
                                <div class="property-card__head">
                                    <div class="property-card__headRow">
                                        <div>
                                            <div class="d-flex align-center ga-2 flex-wrap">
                                                <span class="property-title">{{ property.label }}</span>
                                                <v-chip v-if="property.required" size="x-small" color="primary" label
                                                    variant="tonal" class="chip">
                                                    Required
                                                </v-chip>
                                            <v-chip v-if="property.meta.const !== undefined" size="x-small"
                                                color="primary" label variant="flat" class="chip">
                                                Const
                                            </v-chip>
                                            </div>
                                            <p v-if="property.meta.description"
                                                class="text-caption text-medium-emphasis mb-0">
                                                {{ property.meta.description }}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                <SchemaForm :schema="property.schema" :root-schema="rootSchema"
                                    :model-value="readObjectValue(property.key)"
                                    @update:model-value="updateObjectValue(property.key, $event)" :depth="depth + 1"
                                    :label="property.label" :required="property.required" chrome="bare" />
                            </div>
                        </div>

                        <div v-if="hasDictionary" class="dictionary">
                            <div class="dictionary__head">
                                <div>
                                    <div class="d-flex align-center ga-2">
                                        <span class="property-title">Additional entries</span>
                                        <v-chip size="x-small" label variant="outlined" class="chip">Flexible keys
                                        </v-chip>
                                    </div>
                                    <p class="text-caption text-medium-emphasis mb-0">
                                        {{ dictionaryHint }}
                                    </p>
                                </div>
                                <v-btn color="primary" variant="tonal" size="small" prepend-icon="mdi-plus"
                                    @click="addDictionaryEntry">
                                    Add entry
                                </v-btn>
                            </div>
                            <div v-if="dictionaryEntries.length" class="dictionary__list">
                                <div v-for="entry in dictionaryEntries" :key="entry.id"
                                    class="dictionary__row">
                                    <v-text-field :model-value="dictionaryKeyDrafts[entry.id] ?? entry.key"
                                        @update:model-value="val => setDictionaryKeyDraft(entry.id, val)"
                                        @blur="commitDictionaryKeyDraft(entry.id)" density="compact"
                                        @keydown.enter.prevent="commitDictionaryKeyDraft(entry.id)"
                                        label="Key" variant="outlined" hide-details clearable class="dictionary__key" />
                                    <div class="dictionary__value">
                                        <SchemaForm :schema="normalized.additionalProperties" :root-schema="rootSchema"
                                            :model-value="entry.value"
                                            @update:model-value="val => updateDictionaryValue(entry.key, val)"
                                            :depth="depth + 1" chrome="bare" />
                                    </div>
                                    <v-btn icon="mdi-close" variant="text" size="small" color="error"
                                        @click="removeDictionaryEntry(entry.id)" />
                                </div>
                            </div>
                            <div v-else class="empty-state text-center text-medium-emphasis py-4">
                                No additional entries
                            </div>
                        </div>
                    </div>
                </template>

                <!-- Primitive / fallback -->
                <template v-else>
                    <div class="primitive">
                        <v-select v-if="Array.isArray(normalized.enum)" v-model="localValue" :items="normalized.enum"
                            :label="inputLabel" :hint="inputHint || 'Pick one option'"
                            :persistent-hint="!isBare" hide-details="auto" density="comfortable" variant="outlined"
                            :placeholder="inputPlaceholder" chips clearable>
                        </v-select>

                        <v-text-field v-else-if="normalized.const !== undefined" :model-value="normalized.const"
                            :label="inputLabel" :hint="inputHint || 'Read only'" :persistent-hint="!isBare" readonly
                            variant="outlined" density="comfortable" :placeholder="inputPlaceholder" />

                        <v-text-field v-else-if="normalized.type === 'string'" v-model="localValue"
                            :label="inputLabel" :hint="inputHint" :persistent-hint="!isBare" variant="outlined"
                            density="comfortable" :type="stringInputType" :placeholder="inputPlaceholder" />

                        <v-switch v-else-if="normalized.type === 'boolean'" v-model="localValue"
                            :label="inputLabel" color="primary" hide-details :messages="inputHint" />

                        <v-text-field v-else-if="normalized.type === 'integer' || normalized.type === 'number'"
                            v-model.number="localValue" :label="inputLabel" :hint="inputHint"
                            :persistent-hint="!isBare" variant="outlined" density="comfortable" type="number"
                            :placeholder="inputPlaceholder" />

                        <v-textarea v-else v-model="localValue" :label="inputLabel"
                            :hint="inputHint || 'Unsupported type rendered as text'" :persistent-hint="!isBare"
                            variant="outlined" density="comfortable" auto-grow :placeholder="inputPlaceholder" />
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch, watchEffect } from 'vue'

type JSONSchema = Record<string, any>

type NormalizedSchema = JSONSchema & {
    type?: string
    unionOptions?: NormalizedSchema[]
}

type ObjectPropertyItem = {
    key: string
    schema: JSONSchema
    label: string
    meta: NormalizedSchema
    required: boolean
}

type DictionaryEntryMeta = {
    id: string
    key: string
}

type DictionaryEntryItem = {
    id: string
    key: string
    value: any
}

const props = withDefaults(defineProps<{
    modelValue: any
    schema: JSONSchema
    rootSchema?: JSONSchema
    label?: string
    depth?: number
    required?: boolean
    chrome?: 'full' | 'bare'
}>(), {
    depth: 0,
    required: false,
    chrome: 'full'
})

const emit = defineEmits<{
    (event: 'update:modelValue', value: any): void
}>()

const rootSchema = computed(() => props.rootSchema || props.schema)
const normalized = computed(() => normalizeSchema(props.schema, rootSchema.value))

const isBare = computed(() => props.chrome === 'bare')
const displayLabel = computed(() => props.label || normalized.value.title || 'Untitled')
const description = computed(() => normalized.value.description || '')
const inputLabel = computed(() => isBare.value ? undefined : displayLabel.value)
const inputHint = computed(() => isBare.value ? undefined : description.value)
const inputPlaceholder = computed(() => isBare.value ? 'Value' : undefined)

const isUnion = computed(() => normalized.value.type === 'union')
const isTuple = computed(() => Array.isArray(normalized.value.prefixItems) && normalized.value.prefixItems.length > 0)
const isObjectType = computed(() => normalized.value.type === 'object')
const isArrayType = computed(() => normalized.value.type === 'array')
const isComplex = computed(() => isUnion.value || isTuple.value || isObjectType.value || isArrayType.value)
const showFrame = computed(() => !isBare.value && isComplex.value)

const localValue = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
})

// Enforce const/defaults on mount and when schema changes
watchEffect(() => {
    if (normalized.value.const !== undefined && localValue.value !== normalized.value.const) {
        emit('update:modelValue', deepClone(normalized.value.const))
        return
    }
    if (localValue.value === undefined && normalized.value.default !== undefined) {
        emit('update:modelValue', deepClone(normalized.value.default))
    }
})

// Union handling
 const unionOptions = computed(() => normalized.value.unionOptions || [])
 const selectedUnion = ref(0)
const selectedUnionSchema = computed(() => unionOptions.value[selectedUnion.value])

 watch(() => [localValue.value, unionOptions.value], () => {
     if (!unionOptions.value.length) return
     selectedUnion.value = detectUnionSelection(localValue.value, unionOptions.value)
}, { immediate: true, deep: true })

const onUnionChange = (index: number) => {
    selectedUnion.value = index
    const option = unionOptions.value[index]
    if (!option) return
    if (option.type === 'null') {
        emit('update:modelValue', null)
    } else {
        emit('update:modelValue', getDefaultValue(option, rootSchema.value))
    }
}

const selectedUnionIsNull = computed(() => unionOptions.value[selectedUnion.value]?.type === 'null')

// Tuple helpers
const readTupleValue = (index: number) => {
    const arr = Array.isArray(localValue.value) ? localValue.value : []
    return arr[index]
}

const updateTupleValue = (index: number, value: any) => {
    const next = Array.isArray(localValue.value) ? [...localValue.value] : []
    next[index] = value
    emit('update:modelValue', next)
}

// Array helpers
const arrayValue = computed(() => Array.isArray(localValue.value) ? localValue.value : [])
const canAddArray = computed(() => {
    const max = normalized.value.maxItems
    if (typeof max === 'number') return arrayValue.value.length < max
    return true
})
const canRemoveArray = computed(() => {
    const min = normalized.value.minItems
    if (typeof min === 'number') return arrayValue.value.length > min
    return arrayValue.value.length > 0
})

const addArrayItem = () => {
    if (!canAddArray.value) return
    const next = [...arrayValue.value, getDefaultValue(normalizeSchema(normalized.value.items || {}, rootSchema.value), rootSchema.value)]
    emit('update:modelValue', next)
}

const removeArrayItem = (index: number) => {
    if (!canRemoveArray.value) return
    const next = [...arrayValue.value]
    next.splice(index, 1)
    emit('update:modelValue', next)
}

const updateArrayItem = (index: number, value: any) => {
    const next = [...arrayValue.value]
    next[index] = value
    emit('update:modelValue', next)
}

const itemLabel = (index: number) => (normalized.value.items?.title ? normalized.value.items.title : 'Item') + ` #${index + 1}`

// Object helpers
const objectProperties = computed<ObjectPropertyItem[]>(() => {
    if (!isObjectType.value || !normalized.value.properties) return []
    const requiredKeys = Array.isArray(normalized.value.required) ? normalized.value.required : []
    const properties = normalized.value.properties as Record<string, JSONSchema>
    return Object.entries(properties).map(([key, propertySchema]) => {
        const meta = normalizeSchema(propertySchema, rootSchema.value)
        return {
            key,
            schema: propertySchema,
            label: meta.title || formatLabel(key),
            meta,
            required: requiredKeys.includes(key)
        }
    })
})

const readObjectValue = (key: string) => {
    const obj = isPlainObject(localValue.value) ? localValue.value : {}
    return obj[key]
}

const updateObjectValue = (key: string, value: any) => {
    const obj = isPlainObject(localValue.value) ? { ...localValue.value } : {}
    obj[key] = value
    emit('update:modelValue', obj)
}

// Dictionary (additionalProperties)
const hasDictionary = computed(() => isObjectType.value && !!normalized.value.additionalProperties)
const reservedObjectKeys = computed(() => new Set(Object.keys(normalized.value.properties || {})))
const createDictionaryEntryId = () => `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
const dictionaryKeyOrder = ref<DictionaryEntryMeta[]>([])
const dictionaryKeyDrafts = ref<Record<string, string>>({})

watchEffect(() => {
    if (!hasDictionary.value) {
        dictionaryKeyOrder.value = []
        dictionaryKeyDrafts.value = {}
        return
    }

    const obj = isPlainObject(localValue.value) ? (localValue.value as Record<string, any>) : {}
    const reserved = reservedObjectKeys.value
    const keys = Object.keys(obj).filter(key => !reserved.has(key))
    const keySet = new Set(keys)

    const existing = dictionaryKeyOrder.value
    const next: DictionaryEntryMeta[] = []

    for (const meta of existing) {
        if (keySet.has(meta.key)) next.push(meta)
    }

    const known = new Set(next.map(meta => meta.key))
    for (const key of keys) {
        if (known.has(key)) continue
        next.push({ id: createDictionaryEntryId(), key })
    }

    if (
        next.length !== existing.length ||
        next.some((meta, index) => meta.id !== existing[index]?.id || meta.key !== existing[index]?.key)
    ) {
        dictionaryKeyOrder.value = next
    }

    const nextDrafts: Record<string, string> = {}
    const existingDrafts = dictionaryKeyDrafts.value
    for (const meta of next) {
        nextDrafts[meta.id] = existingDrafts[meta.id] ?? meta.key
    }
    if (Object.keys(nextDrafts).length !== Object.keys(existingDrafts).length) {
        dictionaryKeyDrafts.value = nextDrafts
    } else {
        for (const [id, val] of Object.entries(nextDrafts)) {
            if (existingDrafts[id] !== val) {
                dictionaryKeyDrafts.value = nextDrafts
                break
            }
        }
    }
})

const dictionaryEntries = computed<DictionaryEntryItem[]>(() => {
    if (!hasDictionary.value) return []
    const obj = isPlainObject(localValue.value) ? (localValue.value as Record<string, any>) : {}
    const reserved = reservedObjectKeys.value

    return dictionaryKeyOrder.value
        .filter(meta => !reserved.has(meta.key) && meta.key in obj)
        .map(meta => ({ id: meta.id, key: meta.key, value: obj[meta.key] }))
})

const setDictionaryKeyDraft = (entryId: string, draft: string) => {
    dictionaryKeyDrafts.value = { ...dictionaryKeyDrafts.value, [entryId]: String(draft ?? '') }
}

const dictionaryHint = computed(() => {
    const child = normalized.value.additionalProperties
    const childType = normalizeSchema(child || {}, rootSchema.value).type || 'any'
    return `Keys are free-form; values follow ${childType} schema.`
})

const addDictionaryEntry = () => {
    const obj = isPlainObject(localValue.value) ? { ...localValue.value } : {}
    const baseKey = 'key'
    let counter = Object.keys(obj).length + 1
    let candidate = `${baseKey}_${counter}`
    while (obj[candidate] !== undefined) {
        counter += 1
        candidate = `${baseKey}_${counter}`
    }
    obj[candidate] = getDefaultValue(normalizeSchema(normalized.value.additionalProperties || {}, rootSchema.value), rootSchema.value)
    const entryId = createDictionaryEntryId()
    dictionaryKeyOrder.value = [...dictionaryKeyOrder.value, { id: entryId, key: candidate }]
    dictionaryKeyDrafts.value = { ...dictionaryKeyDrafts.value, [entryId]: candidate }
    emit('update:modelValue', obj)
}

const updateDictionaryKey = (entryId: string, newKey: string): boolean => {
    if (!newKey) return false
    if (reservedObjectKeys.value.has(newKey)) return false

    const index = dictionaryKeyOrder.value.findIndex(meta => meta.id === entryId)
    if (index < 0) return false

    const oldKey = dictionaryKeyOrder.value[index]?.key
    if (!oldKey || oldKey === newKey) return true

    const obj = isPlainObject(localValue.value) ? ({ ...localValue.value } as Record<string, any>) : {}
    if (!(oldKey in obj)) return false
    if (newKey in obj) return false

    const value = obj[oldKey]
    delete obj[oldKey]
    obj[newKey] = value

    dictionaryKeyOrder.value = dictionaryKeyOrder.value.map((meta) =>
        meta.id === entryId ? { ...meta, key: newKey } : meta
    )

    emit('update:modelValue', obj)
    return true
}

const commitDictionaryKeyDraft = (entryId: string) => {
    const meta = dictionaryKeyOrder.value.find(item => item.id === entryId)
    if (!meta) return

    const draftRaw = dictionaryKeyDrafts.value[entryId]
    const draft = String(draftRaw ?? '').trim()

    if (!draft) {
        setDictionaryKeyDraft(entryId, meta.key)
        return
    }

    const ok = updateDictionaryKey(entryId, draft)
    if (!ok) {
        setDictionaryKeyDraft(entryId, meta.key)
        return
    }

    setDictionaryKeyDraft(entryId, draft)
}

const updateDictionaryValue = (key: string, value: any) => {
    const obj = isPlainObject(localValue.value) ? { ...localValue.value } : {}
    obj[key] = value
    emit('update:modelValue', obj)
}

const removeDictionaryEntry = (entryId: string) => {
    const meta = dictionaryKeyOrder.value.find(item => item.id === entryId)
    dictionaryKeyOrder.value = dictionaryKeyOrder.value.filter(item => item.id !== entryId)

    if (!meta) return

    const obj = isPlainObject(localValue.value) ? ({ ...localValue.value } as Record<string, any>) : {}
    delete obj[meta.key]
    emit('update:modelValue', obj)
}

// Null handling
const stringInputType = computed(() => {
    if (normalized.value.format === 'date') return 'date'
    if (normalized.value.format === 'time') return 'time'
    if (normalized.value.format === 'date-time') return 'datetime-local'
    return 'text'
})

const formatLabel = (key: string) => key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase())
const unionOptionLabel = (option: NormalizedSchema, index: number) => {
    if (option.type === 'null') return 'Null'
    if (option.title) return String(option.title)
    if (option.const !== undefined) return String(option.const)
    if (option.type) return formatLabel(String(option.type))
    return `Option ${index + 1}`
}

// Helpers
function normalizeSchema(schema: JSONSchema, root: JSONSchema, seen = new Set<string>()): NormalizedSchema {
    const resolved = resolveRef(schema, root, seen)
    const unionOptions = extractUnionOptions(resolved, root, seen)
    if (unionOptions && unionOptions.length > 1) {
        return {
            ...resolved,
            type: 'union',
            unionOptions,
            title: resolved.title,
            description: resolved.description
        }
    }

    const baseType = unwrapType(resolved)
    const base: NormalizedSchema = { ...resolved, type: baseType }
    if (!base.type) base.type = inferTypeFromShape(resolved)
    if (Array.isArray(resolved.prefixItems)) base.prefixItems = resolved.prefixItems
    return base
}

function resolveRef(schema: JSONSchema, root: JSONSchema, seen: Set<string>): JSONSchema {
    if (!schema || !schema.$ref) return schema || {}
    const { $ref, ...siblings } = schema as { $ref: string } & JSONSchema
    const ref = $ref as string
    if (seen.has(ref)) return schema
    seen.add(ref)

    const path = ref.replace(/^#\//, '').split('/')
    let current: any = root
    for (const segment of path) {
        if (current && segment in current) {
            current = current[segment]
        } else {
            return schema
        }
    }

    const resolved = resolveRef(current, root, seen)
    if (!Object.keys(siblings).length) return resolved
    return { ...resolved, ...siblings }
}

function allowsNull(schema?: JSONSchema): boolean {
    if (!schema) return false
    if (schema.type === 'null') return true
    if (Array.isArray(schema.type) && schema.type.includes('null')) return true
    const anyOfNull = Array.isArray(schema.anyOf) && schema.anyOf.some((opt: JSONSchema) => unwrapType(opt) === 'null')
    const oneOfNull = Array.isArray(schema.oneOf) && schema.oneOf.some((opt: JSONSchema) => unwrapType(opt) === 'null')
    return Boolean(anyOfNull || oneOfNull)
}

function unwrapType(schema?: JSONSchema): string | undefined {
    if (!schema) return undefined
    const t = schema.type
    if (Array.isArray(t)) {
        return t.find(entry => entry !== 'null') ?? t[0]
    }
    return t
}

function extractUnionOptions(schema: JSONSchema, root: JSONSchema, seen: Set<string>): NormalizedSchema[] | undefined {
    const collection = schema.anyOf ?? schema.oneOf
    if (Array.isArray(collection) && collection.length > 0) {
        const options = collection.map(opt => normalizeSchema(resolveRef(opt, root, seen), root, seen))
        return sortUnionOptions(options)
    }

    if (Array.isArray(schema.type) && schema.type.length > 1) {
        const { type: _ignored, ...baseWithoutType } = schema
        const options = schema.type.map((t: string) => {
            if (t === 'null') return normalizeSchema({ type: 'null', title: 'Null' }, root, seen)
            return normalizeSchema({ ...baseWithoutType, type: t }, root, seen)
        })
        return sortUnionOptions(options)
    }

    if (allowsNull(schema) && typeof schema.type === 'string' && schema.type !== 'null') {
        return sortUnionOptions([
            normalizeSchema({ ...schema, type: schema.type }, root, seen),
            normalizeSchema({ type: 'null', title: 'Null' }, root, seen)
        ])
    }

    return undefined
}

function sortUnionOptions(options: NormalizedSchema[]): NormalizedSchema[] {
    const nullOptions = options.filter(opt => opt.type === 'null')
    const other = options.filter(opt => opt.type !== 'null')
    return [...other, ...nullOptions]
}

function inferTypeFromShape(schema?: JSONSchema): string | undefined {
    if (!schema) return undefined
    if (schema.properties || schema.additionalProperties) return 'object'
    if (schema.items || schema.prefixItems) return 'array'
    if (schema.enum) return 'string'
    return schema.type
}

function detectUnionSelection(value: any, options: NormalizedSchema[]): number {
    if (value === null) {
        const nullIndex = options.findIndex(opt => opt.type === 'null')
        return nullIndex >= 0 ? nullIndex : 0
    }
    if (value === undefined) return 0
    for (const [index, option] of options.entries()) {
        if (option.const !== undefined && value === option.const) return index
        if (option.type === 'boolean' && typeof value === 'boolean') return index
        if ((option.type === 'number' || option.type === 'integer') && typeof value === 'number') return index
        if (option.type === 'string' && typeof value === 'string') return index
        if (option.type === 'array' && Array.isArray(value)) return index
        if (option.type === 'object' && isPlainObject(value)) {
            const constEntry = option.properties
                ? Object.entries(option.properties).find(([, prop]) => (prop as JSONSchema).const !== undefined)
                : undefined
            if (constEntry) {
                const [key, prop] = constEntry
                if (value[key] === (prop as JSONSchema).const) return index
            } else {
                return index
            }
        }
    }
    return 0
}

function getDefaultValue(schema: NormalizedSchema | undefined, root: JSONSchema): any {
    if (!schema) return null
    if (schema.const !== undefined) return deepClone(schema.const)
    if (schema.default !== undefined) return deepClone(schema.default)
    if (schema.type === 'union' && schema.unionOptions?.length) {
        const preferred = schema.unionOptions.find(opt => opt.type !== 'null') ?? schema.unionOptions[0]
        return getDefaultValue(preferred, root)
    }
    if (Array.isArray(schema.prefixItems) && schema.prefixItems.length) {
        return schema.prefixItems.map((item: JSONSchema) => getDefaultValue(normalizeSchema(item, root), root))
    }
    switch (schema.type) {
        case 'object':
            return buildObjectDefaults(schema, root)
        case 'array':
            return []
        case 'boolean':
            return false
        case 'integer':
        case 'number':
            if (Array.isArray(schema.enum) && schema.enum.length) return deepClone(schema.enum[0])
            return 0
        case 'string':
            if (Array.isArray(schema.enum) && schema.enum.length) return deepClone(schema.enum[0])
            return ''
        default:
            return null
    }
}

function buildObjectDefaults(schema: NormalizedSchema, root: JSONSchema): Record<string, any> {
    const result: Record<string, any> = {}
    const properties = schema.properties && typeof schema.properties === 'object' ? schema.properties : {}
    const requiredKeys = Array.isArray(schema.required) ? schema.required : []

    for (const [key, propSchema] of Object.entries(properties)) {
        const normalizedProp = normalizeSchema(propSchema as JSONSchema, root)
        if (normalizedProp.const !== undefined) {
            result[key] = deepClone(normalizedProp.const)
        } else if (normalizedProp.default !== undefined) {
            result[key] = deepClone(normalizedProp.default)
        } else if (requiredKeys.includes(key)) {
            result[key] = getDefaultValue(normalizedProp, root)
        }
    }

    return result
}

function isPlainObject(val: unknown): val is Record<string, any> {
    return val !== null && typeof val === 'object' && !Array.isArray(val)
}

function deepClone<T>(val: T): T {
    return JSON.parse(JSON.stringify(val))
}
</script>

<script lang="ts">
export default {
    name: 'SchemaForm'
}
</script>

<style scoped>
.schema-form {
    width: 100%;
    position: relative;
}

.schema-form.is-nested {
    margin-left: 12px;
    padding-left: 14px;
    border-left: 2px solid rgba(var(--v-theme-primary), 0.14);
}

:root.v-theme--dark .schema-form.is-nested {
    border-left-color: rgba(var(--v-theme-primary), 0.22);
}

.field-shell {
    border: none;
    background: transparent;
    border-radius: 0;
    padding: 0;
    box-shadow: none;
}

.field-shell--bare {
    border: none;
    background: transparent;
    padding: 0;
    box-shadow: none;
}

.field-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}

.title-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.field-title {
    font-size: 16px;
    font-weight: 700;
}

.field-description {
    margin: 2px 0 0;
    color: rgba(var(--v-theme-on-surface), 0.7);
}

.field-actions {
    display: flex;
    align-items: center;
}

.field-body {
    margin-top: 12px;
}

.field-body--bare {
    margin-top: 0;
}

.chip {
    letter-spacing: 0;
}

.card-surface {
    background: transparent;
    border: none;
    border-radius: 0;
}

.union-header {
    padding: 6px 10px;
    background: rgba(var(--v-theme-primary), 0.06);
    border: 1px dashed rgba(var(--v-theme-primary), 0.3);
    border-radius: 8px;
    margin-bottom: 8px;
}

.union-header__row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.null-variant {
    min-height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.union-chip-active {
    background-color: rgba(var(--v-theme-primary), 0.15) !important;
    color: rgb(var(--v-theme-primary)) !important;
}

.tuple-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
}

.tuple-cell {
    border: none;
    border-radius: 0;
    padding: 0;
    background: transparent;
}

.tuple-label {
    margin-bottom: 4px;
}

.array-item {
    border: none;
    border-radius: 0;
    padding: 0;
    background: transparent;
}

.array-item__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.array-item + .array-item {
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px dashed rgba(var(--v-theme-on-surface), 0.12);
}

.property-stack {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.property-card {
    border: none;
    border-radius: 0;
    padding: 0;
    background: transparent;
}

.property-card__head {
    margin-bottom: 8px;
}

.property-card__headRow {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
}

.property-card + .property-card {
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px dashed rgba(var(--v-theme-on-surface), 0.12);
}

.property-card__actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex: 0 0 auto;
}

.property-title {
    font-weight: 600;
}

.dictionary {
    border: none;
    border-radius: 0;
    padding: 0;
    background: transparent;
}

.dictionary__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}

.dictionary__list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.dictionary__row {
    display: grid;
    grid-template-columns: 200px 1fr auto;
    gap: 10px;
    align-items: center;
}

.dictionary__row + .dictionary__row {
    padding-top: 10px;
    border-top: 1px dashed rgba(var(--v-theme-on-surface), 0.12);
}

.dictionary__key {
    min-width: 140px;
}

.dictionary__value {
    width: 100%;
}

.empty-state {
    border: 1px dashed rgba(var(--v-theme-on-surface), 0.18);
    border-radius: 10px;
    background: rgba(var(--v-theme-surface), 0.4);
}

.primitive :deep(.v-input) {
    margin-bottom: 0;
}

@media (max-width: 720px) {
    .field-head {
        flex-direction: column;
        align-items: flex-start;
    }

    .property-card__headRow {
        flex-direction: column;
        align-items: flex-start;
    }

    .dictionary__row {
        grid-template-columns: 1fr;
    }
}
</style>
