<template>
    <div class="d-flex flex-column align-center justify-center py-12 h-100 w-100 text-center" style="width: 100%;">
        <v-progress-circular :size="size" :width="width" color="primary" indeterminate
            class="mb-4"></v-progress-circular>
        <div v-if="text" class="text-body-1 text-medium-emphasis animate-pulse">
            {{ text }}
        </div>
    </div>
</template>

<script lang="ts" setup>
withDefaults(defineProps<{
    text?: string
    size?: number | string
    width?: number | string
}>(), {
    text: 'Loading...',
    size: 64,
    width: 6
})
</script>

<style scoped>
.animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {

    0%,
    100% {
        opacity: 1;
    }

    50% {
        opacity: .5;
    }
}
</style>
