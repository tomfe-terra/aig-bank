<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAdminLogs } from '@/composables/useAdminLogs'
import { formatDate, getErrorMessage } from '@/utils/format'
import { downloadLogFile } from '@/api'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()
const { 
  logFiles, 
  isLoadingFiles, 
  logContent, 
  isLoadingContent, 
  selectedFile, 
  selectedFileInfo,
  canPreview,
  maxPreviewSize,
  refetchFiles
} = useAdminLogs()

// Search and filter
const searchQuery = ref('')
const contentSearchQuery = ref('')
const sortBy = ref<'name' | 'size' | 'date'>('date')
const sortOrder = ref<'asc' | 'desc'>('desc')

const selectFile = (filename: string) => {
  selectedFile.value = filename
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

const handleDownload = async (filename: string) => {
  try {
    const blob = await downloadLogFile(filename)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    showToast('Log file downloaded successfully!', 'success')
  } catch (e: unknown) {
    console.error('Failed to download log file:', e)
    showToast(getErrorMessage(e, 'Failed to download log file'), 'error')
  }
}

const contentLines = computed(() => {
  if (!logContent.value) return []
  return logContent.value.split('\n')
})

const matchCount = computed(() => {
  if (!contentSearchQuery.value || !logContent.value) return 0
  const query = contentSearchQuery.value.toLowerCase()
  return contentLines.value.filter(line => line.toLowerCase().includes(query)).length
})

const highlightText = (text: string): string => {
  if (!contentSearchQuery.value) return text
  
  const query = contentSearchQuery.value
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return text.replace(regex, '<mark class="search-highlight">$1</mark>')
}

// Filtered and sorted files
const filteredFiles = computed(() => {
  if (!logFiles.value) return []
  
  let files = [...logFiles.value.files]
  
  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    files = files.filter(f => f.filename.toLowerCase().includes(query))
  }
  
  // Sort files
  files.sort((a, b) => {
    let comparison = 0
    
    switch (sortBy.value) {
      case 'name':
        comparison = a.filename.localeCompare(b.filename)
        break
      case 'size':
        comparison = a.size_bytes - b.size_bytes
        break
      case 'date':
        comparison = new Date(a.modified_at).getTime() - new Date(b.modified_at).getTime()
        break
    }
    
    return sortOrder.value === 'asc' ? comparison : -comparison
  })
  
  return files
})

// File type icon
const getFileIcon = (filename: string) => {
  if (filename.includes('error')) return 'mdi-alert-circle'
  if (filename.includes('access')) return 'mdi-web'
  if (filename.includes('debug')) return 'mdi-bug'
  if (filename.includes('info')) return 'mdi-information'
  return 'mdi-file-document'
}

// File type color
const getFileColor = (filename: string) => {
  if (filename.includes('error')) return 'error'
  if (filename.includes('access')) return 'info'
  if (filename.includes('debug')) return 'warning'
  if (filename.includes('info')) return 'success'
  return undefined
}

// Check if line matches search
const lineMatchesSearch = (line: string) => {
  if (!contentSearchQuery.value) return false
  return line.toLowerCase().includes(contentSearchQuery.value.toLowerCase())
}

// Stats
const totalSize = computed(() => {
  if (!logFiles.value) return 0
  return logFiles.value.files.reduce((sum, f) => sum + f.size_bytes, 0)
})

const toggleSort = (field: 'name' | 'size' | 'date') => {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = field
    sortOrder.value = 'desc'
  }
}
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4 mb-1">Logs Explorer</h1>
        <div v-if="logFiles" class="text-body-2 text-medium-emphasis">
          {{ logFiles.files.length }} files • {{ formatFileSize(totalSize) }} total
        </div>
      </div>
      <v-btn
        prepend-icon="mdi-refresh"
        variant="outlined"
        @click="refetchFiles"
        :loading="isLoadingFiles"
      >
        Refresh
      </v-btn>
    </div>

    <v-row>
      <!-- Log Files List -->
      <v-col cols="12" md="4" lg="3">
        <v-card variant="outlined" class="log-files-card">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-folder-open" class="mr-2" />
            Log Files
          </v-card-title>
          <v-divider />

          <!-- Search and Sort -->
          <div class="pa-3">
            <v-text-field
              v-model="searchQuery"
              density="compact"
              variant="outlined"
              placeholder="Search files..."
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            />
            
            <div class="d-flex gap-1 mt-2">
              <v-btn
                size="small"
                variant="text"
                density="compact"
                @click="toggleSort('name')"
                :class="{ 'text-primary': sortBy === 'name' }"
              >
                Name
                <v-icon v-if="sortBy === 'name'" :icon="sortOrder === 'asc' ? 'mdi-arrow-up' : 'mdi-arrow-down'" size="small" />
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                density="compact"
                @click="toggleSort('size')"
                :class="{ 'text-primary': sortBy === 'size' }"
              >
                Size
                <v-icon v-if="sortBy === 'size'" :icon="sortOrder === 'asc' ? 'mdi-arrow-up' : 'mdi-arrow-down'" size="small" />
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                density="compact"
                @click="toggleSort('date')"
                :class="{ 'text-primary': sortBy === 'date' }"
              >
                Date
                <v-icon v-if="sortBy === 'date'" :icon="sortOrder === 'asc' ? 'mdi-arrow-up' : 'mdi-arrow-down'" size="small" />
              </v-btn>
            </div>
          </div>

          <v-divider />

          <v-skeleton-loader v-if="isLoadingFiles" type="list-item@5" />

          <v-list v-else-if="filteredFiles.length > 0" density="compact" class="log-files-list">
            <v-list-item
              v-for="file in filteredFiles"
              :key="file.filename"
              :active="selectedFile === file.filename"
              @click="selectFile(file.filename)"
              class="log-file-item"
            >
              <template #prepend>
                <v-icon 
                  :icon="getFileIcon(file.filename)" 
                  :color="getFileColor(file.filename)"
                />
              </template>

              <v-list-item-title class="text-body-2">
                {{ file.filename }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption">
                {{ formatFileSize(file.size_bytes) }} • {{ formatDate(file.modified_at) }}
              </v-list-item-subtitle>

              <template #append>
                <v-btn
                  icon="mdi-download"
                  variant="text"
                  size="x-small"
                  @click.stop="handleDownload(file.filename)"
                  title="Download"
                />
              </template>
            </v-list-item>
          </v-list>

          <div v-else class="pa-8 text-center">
            <v-icon icon="mdi-file-document-off" size="48" color="grey" class="mb-2" />
            <div class="text-body-2 text-medium-emphasis">
              {{ searchQuery ? 'No matching files' : 'No log files found' }}
            </div>
          </div>
        </v-card>
      </v-col>

      <!-- Log Content -->
      <v-col cols="12" md="8" lg="9">
        <v-card variant="outlined" class="log-content-card">
          <v-card-title class="d-flex justify-space-between align-center flex-wrap">
            <div class="d-flex align-center">
              <v-icon 
                v-if="selectedFile"
                :icon="getFileIcon(selectedFile)" 
                :color="getFileColor(selectedFile)"
                class="mr-2"
              />
              <div>
                <div>{{ selectedFile || 'Log Content' }}</div>
                <div v-if="selectedFileInfo" class="text-caption text-medium-emphasis font-weight-regular">
                  {{ formatFileSize(selectedFileInfo.size_bytes) }} • {{ formatDate(selectedFileInfo.modified_at) }}
                </div>
              </div>
            </div>
            <v-btn
              v-if="selectedFile"
              prepend-icon="mdi-download"
              variant="outlined"
              size="small"
              @click="handleDownload(selectedFile)"
            >
              Download
            </v-btn>
          </v-card-title>
          
          <!-- Content Search Bar -->
          <div v-if="selectedFile && canPreview" class="px-4 pb-3">
            <v-text-field
              v-model="contentSearchQuery"
              density="compact"
              variant="outlined"
              placeholder="Search in log content..."
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            >
              <template #append-inner>
                <v-chip v-if="contentSearchQuery && matchCount > 0" size="small" variant="tonal" color="success">
                  {{ matchCount }} matches
                </v-chip>
                <v-chip v-else-if="contentSearchQuery && matchCount === 0" size="small" variant="tonal" color="error">
                  No matches
                </v-chip>
              </template>
            </v-text-field>
          </div>
          <v-divider />

          <v-card-text v-if="!selectedFile" class="pa-12 text-center">
            <v-icon icon="mdi-file-document-outline" size="64" color="grey" class="mb-4" />
            <div class="text-h6 mb-2">No File Selected</div>
            <div class="text-body-2 text-medium-emphasis">
              Select a log file from the list to view its contents
            </div>
          </v-card-text>

          <v-card-text v-else-if="!canPreview" class="pa-12 text-center">
            <v-icon icon="mdi-alert-outline" size="64" color="warning" class="mb-4" />
            <div class="text-h6 mb-2">File Too Large for Preview</div>
            <div class="text-body-2 text-medium-emphasis mb-2">
              <strong>{{ selectedFile }}</strong> ({{ formatFileSize(selectedFileInfo?.size_bytes || 0) }})
            </div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              Files larger than {{ formatFileSize(maxPreviewSize) }} cannot be previewed in the browser.
              Please download the file to view its contents.
            </div>
            <v-btn
              color="primary"
              variant="flat"
              prepend-icon="mdi-download"
              @click="handleDownload(selectedFile)"
            >
              Download File
            </v-btn>
          </v-card-text>

          <v-skeleton-loader v-else-if="isLoadingContent" type="paragraph@10" />

          <v-card-text v-else-if="logContent" class="pa-0">
            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="ma-4 mb-0 rounded"
            >
              <div class="d-flex align-center justify-space-between">
                <div>
                  <v-icon icon="mdi-text-box-outline" size="small" class="mr-2" />
                  {{ contentLines.length.toLocaleString() }} lines
                  <span v-if="contentSearchQuery && matchCount > 0" class="ml-2">
                    • {{ matchCount.toLocaleString() }} matches
                  </span>
                </div>
                <v-chip size="small" variant="tonal">
                  {{ formatFileSize(selectedFileInfo?.size_bytes || 0) }}
                </v-chip>
              </div>
            </v-alert>
            <div class="log-viewer">
              <pre class="log-content"><code v-for="(line, index) in contentLines" :key="index" class="log-line" :class="{ 'has-match': lineMatchesSearch(line) }"><span class="line-number">{{ index + 1 }}</span><span v-html="highlightText(line)"></span></code></pre>
            </div>
          </v-card-text>

          <v-card-text v-else class="pa-12 text-center">
            <v-icon icon="mdi-alert-circle" size="64" color="error" class="mb-4" />
            <div class="text-h6 mb-2">Failed to Load Log</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              Unable to load the selected log file
            </div>
            <v-btn
              variant="outlined"
              prepend-icon="mdi-refresh"
              @click="selectFile(selectedFile!)"
            >
              Retry
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.log-files-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.log-files-list {
  flex: 1;
  overflow-y: auto;
}

.log-file-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.log-file-item:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
}

.log-content-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.log-viewer {
  flex: 1;
  overflow: auto;
  background-color: #f8f9fa;
  border-radius: 0;
  max-height: calc(100vh - 380px);
}

.log-content {
  margin: 0;
  padding: 16px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #1f2937;
}

.log-line {
  display: block;
  padding: 2px 8px;
  margin: 0;
  transition: background-color 0.15s;
}

.log-line:hover {
  background-color: rgba(59, 130, 246, 0.08);
}

.line-number {
  display: inline-block;
  width: 60px;
  margin-right: 16px;
  color: #9ca3af;
  text-align: right;
  user-select: none;
  font-size: 11px;
}

/* Search highlighting */
.log-line.has-match {
  background-color: rgba(251, 191, 36, 0.15);
}

:deep(.search-highlight) {
  background-color: #fbbf24;
  color: #000;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 600;
}

/* Dark Theme */
.v-theme--dark .log-viewer {
  background-color: #0d1117;
}

.v-theme--dark .log-content {
  color: #c9d1d9;
}

.v-theme--dark .line-number {
  color: #6e7681;
}

.v-theme--dark .log-line:hover {
  background-color: rgba(56, 139, 253, 0.1);
}

.v-theme--dark .log-line.has-match {
  background-color: rgba(187, 128, 9, 0.2);
}

.v-theme--dark :deep(.search-highlight) {
  background-color: #bb8009;
  color: #fff;
}
</style>
