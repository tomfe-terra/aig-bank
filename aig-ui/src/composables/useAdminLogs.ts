import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getLogFiles, getLogFileContent } from '@/api'
import type { LogFileList } from '@/types'

const MAX_PREVIEW_SIZE = 10 * 1024 * 1024

export const useAdminLogs = () => {
  const selectedFile = ref<string | null>(null)

  const {
    data: logFiles,
    isLoading: isLoadingFiles,
    error: filesError,
    refetch: refetchFiles,
  } = useQuery<LogFileList>({
    queryKey: ['admin-log-files'],
    queryFn: getLogFiles,
  })

  const selectedFileInfo = computed(() => {
    if (!selectedFile.value || !logFiles.value) return null
    return logFiles.value.files.find(f => f.filename === selectedFile.value)
  })

  const canPreview = computed(() => {
    if (!selectedFileInfo.value) return false
    return selectedFileInfo.value.size_bytes <= MAX_PREVIEW_SIZE
  })

  const {
    data: logContent,
    isLoading: isLoadingContent,
    error: contentError,
    refetch: refetchContent,
  } = useQuery<string>({
    queryKey: ['admin-log-content', selectedFile],
    queryFn: () => getLogFileContent(selectedFile.value!),
    enabled: () => selectedFile.value !== null && canPreview.value,
  })

  return {
    logFiles,
    isLoadingFiles,
    filesError,
    refetchFiles,
    logContent,
    isLoadingContent,
    contentError,
    refetchContent,
    selectedFile,
    selectedFileInfo,
    canPreview,
    maxPreviewSize: MAX_PREVIEW_SIZE,
  }
}

