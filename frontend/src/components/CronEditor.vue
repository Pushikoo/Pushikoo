<template>
    <div class="cron-editor">
        <!-- Mode Tabs -->
        <v-tabs v-model="mode" density="compact" class="mb-4">
            <v-tab value="preset">
                <v-icon icon="mdi-clock-fast" class="mr-2" size="small"></v-icon>
                {{ $t('cronEditor.presetMode') }}
            </v-tab>
            <v-tab value="custom">
                <v-icon icon="mdi-code-braces" class="mr-2" size="small"></v-icon>
                {{ $t('cronEditor.customMode') }}
            </v-tab>
        </v-tabs>

        <v-window v-model="mode">
            <!-- Preset Mode -->
            <v-window-item value="preset">
                <div class="input-area">
                    <v-row>
                        <v-col cols="12" sm="6">
                            <v-select v-model="presetCategory" :items="presetCategories"
                                :label="$t('cronEditor.frequency')" prepend-inner-icon="mdi-repeat"
                                density="comfortable" variant="outlined" hide-details class="mb-3"></v-select>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'second'">
                            <v-select v-model="secondInterval" :items="secondIntervals"
                                :label="$t('cronEditor.interval')" prepend-inner-icon="mdi-timer-sand"
                                density="comfortable" variant="outlined" hide-details class="mb-3"></v-select>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'minute'">
                            <v-select v-model="minuteInterval" :items="minuteIntervals"
                                :label="$t('cronEditor.interval')" prepend-inner-icon="mdi-timer-outline"
                                density="comfortable" variant="outlined" hide-details class="mb-3"></v-select>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'hour'">
                            <v-select v-model="hourInterval" :items="hourIntervals" :label="$t('cronEditor.interval')"
                                prepend-inner-icon="mdi-timer-outline" density="comfortable" variant="outlined"
                                hide-details class="mb-3"></v-select>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'hour'">
                            <v-select v-model="atMinute" :items="minuteOptions" :label="$t('cronEditor.atMinute')"
                                prepend-inner-icon="mdi-clock-outline" density="comfortable" variant="outlined"
                                hide-details class="mb-3"></v-select>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'day'">
                            <v-text-field v-model="atTime" :label="$t('cronEditor.atTime')" type="time"
                                prepend-inner-icon="mdi-clock-outline" density="comfortable" variant="outlined"
                                hide-details class="mb-3"></v-text-field>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'week'">
                            <v-select v-model="weekDays" :items="weekDayOptions" :label="$t('cronEditor.weekDays')"
                                prepend-inner-icon="mdi-calendar-week" density="comfortable" variant="outlined"
                                hide-details multiple chips closable-chips class="mb-3"></v-select>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'week'">
                            <v-text-field v-model="atTime" :label="$t('cronEditor.atTime')" type="time"
                                prepend-inner-icon="mdi-clock-outline" density="comfortable" variant="outlined"
                                hide-details class="mb-3"></v-text-field>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'month' || presetCategory === 'year'">
                            <v-select v-model="monthDay" :items="monthDayOptions" :label="$t('cronEditor.dayOfMonth')"
                                prepend-inner-icon="mdi-calendar" density="comfortable" variant="outlined" hide-details
                                class="mb-3"></v-select>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'year'">
                            <v-select v-model="month" :items="monthOptions" :label="$t('cronEditor.month')"
                                prepend-inner-icon="mdi-calendar-month" density="comfortable" variant="outlined"
                                hide-details class="mb-3"></v-select>
                        </v-col>
                        <v-col cols="12" sm="6" v-if="presetCategory === 'month' || presetCategory === 'year'">
                            <v-text-field v-model="atTime" :label="$t('cronEditor.atTime')" type="time"
                                prepend-inner-icon="mdi-clock-outline" density="comfortable" variant="outlined"
                                hide-details class="mb-3"></v-text-field>
                        </v-col>
                    </v-row>
                </div>
            </v-window-item>

            <!-- Custom Mode -->
            <v-window-item value="custom">
                <div class="input-area">
                    <v-text-field v-model="customCron" :label="$t('cronEditor.cronExpression')"
                        :placeholder="$t('cronEditor.cronPlaceholder')" prepend-inner-icon="mdi-code-braces"
                        density="comfortable" variant="outlined" :error-messages="validationError"
                        :hint="$t('cronEditor.cronHint')" persistent-hint class="mb-2"></v-text-field>



                    <!-- Cron Fields Help -->
                    <v-expansion-panels variant="accordion" flat class="mb-3 help-panel">
                        <v-expansion-panel>
                            <v-expansion-panel-title class="text-body-2">
                                <v-icon icon="mdi-help-circle-outline" size="small" class="mr-2"></v-icon>
                                {{ $t('cronEditor.helpTitle') }}
                            </v-expansion-panel-title>
                            <v-expansion-panel-text>
                                <div class="text-caption">
                                    <div class="mb-2">
                                        <strong>{{ $t('cronEditor.supportedFormats') }}</strong>
                                    </div>
                                    <div class="cron-format-table">
                                        <div class="format-row">
                                            <span class="format-label">5 {{ $t('cronEditor.fields') }}:</span>
                                            <span class="format-value">{{ $t('cronEditor.format5') }}</span>
                                        </div>
                                        <div class="format-row">
                                            <span class="format-label">6 {{ $t('cronEditor.fields') }}:</span>
                                            <span class="format-value">{{ $t('cronEditor.format6') }}</span>
                                        </div>
                                        <div class="format-row">
                                            <span class="format-label">7 {{ $t('cronEditor.fields') }}:</span>
                                            <span class="format-value">{{ $t('cronEditor.format7') }}</span>
                                        </div>
                                    </div>
                                    <v-divider class="my-2"></v-divider>
                                    <div class="mb-2">
                                        <strong>{{ $t('cronEditor.specialChars') }}</strong>
                                    </div>
                                    <div class="special-chars">
                                        <div><code>*</code> - {{ $t('cronEditor.charAny') }}</div>
                                        <div><code>,</code> - {{ $t('cronEditor.charList') }}</div>
                                        <div><code>-</code> - {{ $t('cronEditor.charRange') }}</div>
                                        <div><code>/</code> - {{ $t('cronEditor.charStep') }}</div>
                                    </div>
                                </div>
                            </v-expansion-panel-text>
                        </v-expansion-panel>
                    </v-expansion-panels>
                </div>
            </v-window-item>
        </v-window>

        <!-- Generated Expression Preview -->
        <div class="result-box mt-3" :class="{ 'result-valid': isValid, 'result-invalid': cronExpression && !isValid }">
            <div class="d-flex align-center justify-space-between flex-wrap mb-2">
                <div>
                    <div class="text-caption text-medium-emphasis">
                        {{ $t('cronEditor.generatedExpression') }}
                    </div>
                    <code class="generated-cron">{{ cronExpression || '-' }}</code>
                </div>
                <v-chip v-if="cronExpression && isValid" size="small" color="success" variant="tonal">
                    <v-icon icon="mdi-check" size="small" class="mr-1"></v-icon>
                    {{ $t('cronEditor.valid') }}
                </v-chip>
                <v-chip v-else-if="cronExpression && !isValid" size="small" color="error" variant="tonal">
                    <v-icon icon="mdi-alert" size="small" class="mr-1"></v-icon>
                    {{ $t('cronEditor.invalid') }}
                </v-chip>
            </div>
            <!-- Human Readable Description -->
            <div v-if="cronExpression && isValid && humanReadable" class="human-readable">
                <v-icon icon="mdi-translate" size="small" class="mr-2"></v-icon>
                <span class="text-body-2">{{ humanReadable }}</span>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
    modelValue: string
}>()

const emit = defineEmits<{
    (e: 'update:modelValue', value: string): void
    (e: 'valid', value: boolean): void
}>()

const { t, locale } = useI18n()

// Mode: preset or custom
const mode = ref<'preset' | 'custom'>('preset')

// Preset mode state
const presetCategory = ref('minute')
const secondInterval = ref(5)
const minuteInterval = ref(5)
const hourInterval = ref(1)
const atMinute = ref(0)
const atTime = ref('00:00')
const weekDays = ref<number[]>([1, 2, 3, 4, 5]) // Mon-Fri
const monthDay = ref(1)
const month = ref(1)

// Custom mode state
const customCron = ref('')

// Preset categories for frequency selection
const presetCategories = computed(() => [
    { title: t('cronEditor.everyXSeconds'), value: 'second' },
    { title: t('cronEditor.everyXMinutes'), value: 'minute' },
    { title: t('cronEditor.everyXHours'), value: 'hour' },
    { title: t('cronEditor.daily'), value: 'day' },
    { title: t('cronEditor.weekly'), value: 'week' },
    { title: t('cronEditor.monthly'), value: 'month' },
    { title: t('cronEditor.yearly'), value: 'year' },
])

// Second interval options
const secondIntervals = computed(() => [1, 2, 5, 10, 15, 30].map(n => ({
    title: t('cronEditor.everyNSeconds', { n }),
    value: n
})))

// Minute interval options
const minuteIntervals = computed(() => [1, 2, 5, 10, 15, 30].map(n => ({
    title: t('cronEditor.everyNMinutes', { n }),
    value: n
})))

// Hour interval options
const hourIntervals = computed(() => [1, 2, 3, 4, 6, 12].map(n => ({
    title: t('cronEditor.everyNHours', { n }),
    value: n
})))

// Minute options (0-59)
const minuteOptions = computed(() =>
    Array.from({ length: 60 }, (_, i) => ({
        title: i.toString().padStart(2, '0'),
        value: i
    }))
)

// Week day options
const weekDayOptions = computed(() => [
    { title: t('cronEditor.sunday'), value: 0 },
    { title: t('cronEditor.monday'), value: 1 },
    { title: t('cronEditor.tuesday'), value: 2 },
    { title: t('cronEditor.wednesday'), value: 3 },
    { title: t('cronEditor.thursday'), value: 4 },
    { title: t('cronEditor.friday'), value: 5 },
    { title: t('cronEditor.saturday'), value: 6 },
])

// Month day options (1-31)
const monthDayOptions = computed(() =>
    Array.from({ length: 31 }, (_, i) => ({
        title: (i + 1).toString(),
        value: i + 1
    }))
)

// Month options (1-12)
const monthOptions = computed(() =>
    Array.from({ length: 12 }, (_, i) => ({
        title: (i + 1).toString(),
        value: i + 1
    }))
)



// Generate cron expression from preset settings
const presetCron = computed(() => {
    const [hours, minutes] = atTime.value.split(':').map(Number)

    switch (presetCategory.value) {
        case 'second':
            if (secondInterval.value === 1) return '* * * * * *'
            return `*/${secondInterval.value} * * * * *`

        case 'minute':
            if (minuteInterval.value === 1) return '* * * * *'
            return `*/${minuteInterval.value} * * * *`

        case 'hour':
            if (hourInterval.value === 1) return `${atMinute.value} * * * *`
            return `${atMinute.value} */${hourInterval.value} * * *`

        case 'day':
            return `${minutes} ${hours} * * *`

        case 'week':
            if (weekDays.value.length === 0) return `${minutes} ${hours} * * *`
            const sortedDays = [...weekDays.value].sort((a, b) => a - b)
            return `${minutes} ${hours} * * ${sortedDays.join(',')}`

        case 'month':
            return `${minutes} ${hours} ${monthDay.value} * *`

        case 'year':
            return `0 ${minutes} ${hours} ${monthDay.value} ${month.value} ? *`

        default:
            return '* * * * *'
    }
})

// Final cron expression
const cronExpression = computed(() => {
    return mode.value === 'preset' ? presetCron.value : customCron.value
})

// Validation error message
const validationError = computed(() => {
    if (!customCron.value) return ''
    if (!isValid.value) return t('cronEditor.invalidExpression')
    return ''
})

// Validate cron expression
const isValid = computed(() => {
    const expr = cronExpression.value
    if (!expr) return false

    const parts = expr.trim().split(/\s+/)

    // Must have 5, 6, or 7 parts
    if (parts.length < 5 || parts.length > 7) return false

    // Validate each part
    const patterns = {
        minute: /^(\*|[0-5]?\d)(\/\d+)?$|^(\*|[0-5]?\d)(-[0-5]?\d)?(,(\*|[0-5]?\d)(-[0-5]?\d)?)*$/,
        hour: /^(\*|[01]?\d|2[0-3])(\/\d+)?$|^(\*|[01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(,(\*|[01]?\d|2[0-3])(-([01]?\d|2[0-3]))?)*$/,
        dayOfMonth: /^(\*|[1-9]|[12]\d|3[01])(\/\d+)?$|^(\*|[1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(,(\*|[1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?)*$/,
        month: /^(\*|[1-9]|1[0-2])(\/\d+)?$|^(\*|[1-9]|1[0-2])(-([1-9]|1[0-2]))?(,(\*|[1-9]|1[0-2])(-([1-9]|1[0-2]))?)*$/,
        dayOfWeek: /^(\*|[0-7])(\/\d+)?$|^(\*|[0-7])(-[0-7])?(,(\*|[0-7])(-[0-7])?)*$/,
        second: /^(\*|[0-5]?\d)(\/\d+)?$|^(\*|[0-5]?\d)(-[0-5]?\d)?(,(\*|[0-5]?\d)(-[0-5]?\d)?)*$/,
        year: /^(\*|\d{4})(\/\d+)?$|^(\*|\d{4})(-\d{4})?(,(\*|\d{4})(-\d{4})?)*$/,
    }

    let partIndex = 0

    // 6 or 7 fields: first is seconds
    if (parts.length >= 6) {
        const part = parts[partIndex]
        if (!part || !patterns.second.test(part)) return false
        partIndex++
    }

    // Minute
    const minPart = parts[partIndex]
    if (!minPart || !patterns.minute.test(minPart)) return false
    partIndex++

    // Hour
    const hourPart = parts[partIndex]
    if (!hourPart || !patterns.hour.test(hourPart)) return false
    partIndex++

    // Day of month
    const domPart = parts[partIndex]
    if (!domPart || !patterns.dayOfMonth.test(domPart)) return false
    partIndex++

    // Month
    const monthPart = parts[partIndex]
    if (!monthPart || !patterns.month.test(monthPart)) return false
    partIndex++

    // Day of week
    const dowPart = parts[partIndex]
    if (!dowPart || !patterns.dayOfWeek.test(dowPart)) return false
    partIndex++

    // 7 fields: last is year
    if (parts.length === 7) {
        const yearPart = parts[partIndex]
        if (!yearPart || !patterns.year.test(yearPart)) return false
    }

    return true
})

import cronstrue from 'cronstrue/i18n';

// ... (keep existing imports)

// Human readable description
const humanReadable = computed(() => {
    if (!isValid.value) return ''

    try {
        const currentLocale = locale.value
        let cronLocale = 'en'

        // Map vue-i18n locale to cronstrue locale
        if (currentLocale === 'zh' || currentLocale.startsWith('zh-')) {
            cronLocale = 'zh_CN'
        } else if (currentLocale === 'ja') {
            cronLocale = 'ja'
        }

        return cronstrue.toString(cronExpression.value, {
            locale: cronLocale,
            use24HourTimeFormat: true,
            verbose: true
        })
    } catch (e) {
        return ''
    }
})

// Sync with v-model
watch(cronExpression, (newVal) => {
    emit('update:modelValue', newVal)
    emit('valid', isValid.value)
})

// Initialize from modelValue
onMounted(() => {
    if (props.modelValue) {
        // Try to parse the initial value and set appropriate mode
        const expr = props.modelValue.trim()
        customCron.value = expr

        // Check if it matches a simple preset
        if (tryParsePreset(expr)) {
            mode.value = 'preset'
        } else {
            mode.value = 'custom'
        }
    }
    emit('valid', isValid.value)
})

// Watch for external modelValue changes
watch(() => props.modelValue, (newVal) => {
    if (newVal && newVal !== cronExpression.value) {
        customCron.value = newVal
        if (tryParsePreset(newVal)) {
            mode.value = 'preset'
        } else {
            mode.value = 'custom'
        }
    }
})

// Try to parse a cron expression into preset settings
function tryParsePreset(expr: string): boolean {
    const parts = expr.trim().split(/\s+/)

    // Parse standard 5/6/7 part cron
    const sec = parts.length >= 6 ? (parts[0] ?? '') : ''
    const min = parts.length >= 6 ? (parts[1] ?? '') : (parts[0] ?? '')
    const hour = parts.length >= 6 ? (parts[2] ?? '') : (parts[1] ?? '')
    const dom = parts.length >= 6 ? (parts[3] ?? '') : (parts[2] ?? '')
    const monthVal = parts.length >= 6 ? (parts[4] ?? '') : (parts[3] ?? '')
    const dow = parts.length >= 6 ? (parts[5] ?? '') : (parts[4] ?? '')
    const year = parts.length === 7 ? (parts[6] ?? '') : ''

    // Every X seconds: */5 * * * * *
    if (parts.length === 6 && sec.startsWith('*/') && min === '*' && hour === '*' && dom === '*' && monthVal === '*' && dow === '*') {
        const interval = parseInt(sec.slice(2))
        if ([1, 2, 5, 10, 15, 30].includes(interval)) {
            presetCategory.value = 'second'
            secondInterval.value = interval
            return true
        }
    }

    // Every second: * * * * * *
    if (parts.length === 6 && sec === '*' && min === '*' && hour === '*' && dom === '*' && monthVal === '*' && dow === '*') {
        presetCategory.value = 'second'
        secondInterval.value = 1
        return true
    }

    // Every X minutes
    if (parts.length === 5 && min.startsWith('*/') && hour === '*' && dom === '*' && monthVal === '*' && dow === '*') {
        const interval = parseInt(min.slice(2))
        if ([1, 2, 5, 10, 15, 30].includes(interval)) {
            presetCategory.value = 'minute'
            minuteInterval.value = interval
            return true
        }
    }

    // Every minute
    if (parts.length === 5 && min === '*' && hour === '*' && dom === '*' && monthVal === '*' && dow === '*') {
        presetCategory.value = 'minute'
        minuteInterval.value = 1
        return true
    }

    // Other presets... Reuse logic where possible but adjust index checks carefully for 5/6 fields
    // Logic below assumes 5 fields for simplicity unless 6 fields detected above
    // To keep simple, we can prioritize strict matching

    if (parts.length === 5) {
        // Every X hours at specific minute
        if (!min.includes('*') && hour.startsWith('*/') && dom === '*' && monthVal === '*' && dow === '*') {
            const hourInt = parseInt(hour.slice(2))
            const minVal = parseInt(min)
            if ([1, 2, 3, 4, 6, 12].includes(hourInt) && !isNaN(minVal)) {
                presetCategory.value = 'hour'
                hourInterval.value = hourInt
                atMinute.value = minVal
                return true
            }
        }

        // Every hour at specific minute
        if (!min.includes('*') && hour === '*' && dom === '*' && monthVal === '*' && dow === '*') {
            const minVal = parseInt(min)
            if (!isNaN(minVal)) {
                presetCategory.value = 'hour'
                hourInterval.value = 1
                atMinute.value = minVal
                return true
            }
        }

        // Daily at specific time
        if (!min.includes('*') && !hour.includes('*') && dom === '*' && monthVal === '*' && dow === '*') {
            const minVal = parseInt(min)
            const hourVal = parseInt(hour)
            if (!isNaN(minVal) && !isNaN(hourVal)) {
                presetCategory.value = 'day'
                atTime.value = `${hourVal.toString().padStart(2, '0')}:${minVal.toString().padStart(2, '0')}`
                return true
            }
        }

        // Weekly
        if (!min.includes('*') && !hour.includes('*') && dom === '*' && monthVal === '*' && dow !== '*') {
            const minVal = parseInt(min)
            const hourVal = parseInt(hour)
            const days = dow.split(',').map(d => parseInt(d)).filter(d => !isNaN(d))
            if (!isNaN(minVal) && !isNaN(hourVal) && days.length > 0) {
                presetCategory.value = 'week'
                atTime.value = `${hourVal.toString().padStart(2, '0')}:${minVal.toString().padStart(2, '0')}`
                weekDays.value = days
                return true
            }
        }

        // Monthly
        if (!min.includes('*') && !hour.includes('*') && !dom.includes('*') && monthVal === '*' && dow === '*') {
            const minVal = parseInt(min)
            const hourVal = parseInt(hour)
            const dayVal = parseInt(dom)
            if (!isNaN(minVal) && !isNaN(hourVal) && !isNaN(dayVal)) {
                presetCategory.value = 'month'
                atTime.value = `${hourVal.toString().padStart(2, '0')}:${minVal.toString().padStart(2, '0')}`
                monthDay.value = dayVal
                return true
            }
        }

        // Yearly (implied by 0 0 1 1 *)
        if (!min.includes('*') && !hour.includes('*') && !dom.includes('*') && !monthVal.includes('*') && dow === '*') {
            const minVal = parseInt(min)
            const hourVal = parseInt(hour)
            const dayVal = parseInt(dom)
            const monVal = parseInt(monthVal)
            if (!isNaN(minVal) && !isNaN(hourVal) && !isNaN(dayVal) && !isNaN(monVal)) {
                presetCategory.value = 'year'
                atTime.value = `${hourVal.toString().padStart(2, '0')}:${minVal.toString().padStart(2, '0')}`
                monthDay.value = dayVal
                month.value = monVal
                return true
            }
        }
    }

    // 7 fields for yearly with year wildcard
    // 0 0 12 1 1 ? *
    if (parts.length === 7 && year === '*') {
        if (sec === '0' && !min.includes('*') && !hour.includes('*') && !dom.includes('*') && !monthVal.includes('*')) {
            const minV = parseInt(min)
            const hourV = parseInt(hour)
            const domV = parseInt(dom)
            const monV = parseInt(monthVal)
            if (!isNaN(minV) && !isNaN(hourV) && !isNaN(domV) && !isNaN(monV)) {
                presetCategory.value = 'year'
                atTime.value = `${hourV.toString().padStart(2, '0')}:${minV.toString().padStart(2, '0')}`
                monthDay.value = domV
                month.value = monV
                return true
            }
        }
    }

    return false
}

// Expose validation state
defineExpose({
    isValid,
    cronExpression
})
</script>

<style scoped>
.cron-editor {
    width: 100%;
}

/* Input area needs padding-top for floating labels */
.input-area {
    padding-top: 8px;
}

/* Fix for v-window cutting off floating labels */
.cron-editor :deep(.v-window) {
    overflow: visible;
}

.cron-editor :deep(.v-window__container) {
    overflow: visible;
}

.cron-editor :deep(.v-window-item) {
    overflow: visible;
}

/* Fix for label text being cut off in Vuetify input fields */
.cron-editor :deep(.v-field__field) {
    overflow: visible;
}

.cron-editor :deep(.v-label) {
    max-width: none;
    overflow: visible;
    text-overflow: unset;
    white-space: nowrap;
}

.cron-editor :deep(.v-field--focused .v-label),
.cron-editor :deep(.v-field--dirty .v-label) {
    max-width: none;
}

.cron-editor :deep(.v-field__outline) {
    overflow: visible;
}

/* Result box styling */
.result-box {
    border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
    border-radius: 8px;
    padding: 12px 16px;
    background: rgba(var(--v-theme-on-surface), 0.02);
}

.result-box.result-valid {
    border-color: rgb(var(--v-theme-success));
    background: rgba(var(--v-theme-success), 0.05);
}

.result-box.result-invalid {
    border-color: rgb(var(--v-theme-error));
    background: rgba(var(--v-theme-error), 0.05);
}

.human-readable {
    display: flex;
    align-items: center;
    padding-top: 8px;
    border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
    color: rgba(var(--v-theme-on-surface), 0.7);
}

.generated-cron {
    font-size: 1rem;
    font-weight: 600;
    color: inherit;
}

.quick-presets {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
}

.quick-chip {
    cursor: pointer;
    transition: all 0.15s ease;
}



.cron-format-table {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.format-row {
    display: flex;
    gap: 8px;
}

.format-label {
    min-width: 70px;
    color: rgba(var(--v-theme-on-surface), 0.7);
}

.format-value {
    font-weight: 500;
    color: rgba(var(--v-theme-on-surface), 0.87);
}

.special-chars {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 4px;
}

.special-chars code {
    background: rgba(var(--v-theme-on-surface), 0.08);
    padding: 1px 4px;
    border-radius: 4px;
}

/* Outlined style for help panel */
.help-panel {
    border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
    border-radius: 8px;
}

.help-panel :deep(.v-expansion-panel) {
    background: transparent;
}

.help-panel :deep(.v-expansion-panel-title) {
    min-height: 44px;
    padding: 8px 16px;
}
</style>
