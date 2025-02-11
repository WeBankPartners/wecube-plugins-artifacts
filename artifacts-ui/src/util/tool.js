export const formatFileSize = bytes => {
  if (bytes === 0) return '0 Bytes'
  const units = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  const unitIndex = Math.floor(Math.log(bytes) / Math.log(1024))
  const size = (bytes / Math.pow(1024, unitIndex)).toFixed(2)
  return `${size} ${units[unitIndex]}`
}
