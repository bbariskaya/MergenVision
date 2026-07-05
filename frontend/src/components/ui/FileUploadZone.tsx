import { Upload, X } from 'lucide-react'
import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface FileUploadZoneProps {
  accept?: string
  maxSizeBytes?: number
  value: File | null
  onChange: (file: File | null) => void
  previewUrl?: string | null
  label?: string
  testId?: string
}

export function FileUploadZone({
  accept = 'image/jpeg,image/png',
  maxSizeBytes = 10 * 1024 * 1024,
  value,
  onChange,
  previewUrl,
  label = 'Görsel sürükleyin veya seçmek için tıklayın',
  testId,
}: FileUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFile = (file: File): boolean => {
    setError(null)
    if (!file.type.startsWith('image/')) {
      setError('Lütfen geçerli bir görsel dosyası seçin.')
      return false
    }
    if (file.size > maxSizeBytes) {
      setError(`Dosya boyutu ${(maxSizeBytes / 1024 / 1024).toFixed(0)} MB'ı aşamaz.`)
      return false
    }
    return true
  }

  const handleFile = (file: File) => {
    if (validateFile(file)) {
      onChange(file)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleClick = () => {
    inputRef.current?.click()
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const handleClear = () => {
    onChange(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="space-y-2" data-testid={testId}>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleInputChange}
        className="hidden"
        aria-label="Dosya yükle"
      />
      {value ? (
        <div className="relative overflow-hidden rounded-lg border border-border">
          {previewUrl && (
            <img
              src={previewUrl}
              alt="Yüklenen görsel önizlemesi"
              className="h-64 w-full object-contain"
            />
          )}
          <div className="flex items-center justify-between border-t border-border bg-card p-3">
            <span className="truncate text-sm">{value.name}</span>
            <Button variant="ghost" size="icon" onClick={handleClear} aria-label="Kaldır">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={handleClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={cn(
            'flex h-48 w-full flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-card transition-colors',
            'hover:border-primary hover:bg-muted/50',
            isDragging && 'border-primary bg-muted/50'
          )}
        >
          <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">{label}</span>
        </button>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
