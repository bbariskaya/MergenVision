import { useState } from 'react'
import { cn } from '@/lib/utils'
import { mediaUrl, parseMediaUrl } from '@/lib/media'
import { Skeleton } from '@/components/ui/skeleton'
import { ImageOff } from 'lucide-react'

interface ImagePreviewProps {
  url: string | undefined | null
  alt: string
  className?: string
  fallbackClassName?: string
  testId?: string
}

export function ImagePreview({ url, alt, className, fallbackClassName, testId }: ImagePreviewProps) {
  const [status, setStatus] = useState<'loading' | 'loaded' | 'error'>('loading')

  const src = (() => {
    if (!url) return null
    const parsed = parseMediaUrl(url)
    if (parsed) return mediaUrl(parsed.bucket, parsed.objectKey)
    return url
  })()

  if (!src) {
    return (
      <div
        className={cn(
          'flex items-center justify-center bg-muted text-muted-foreground',
          fallbackClassName
        )}
        data-testid={testId}
      >
        <ImageOff className="h-6 w-6" />
      </div>
    )
  }

  return (
    <div className={cn('relative overflow-hidden', className)} data-testid={testId}>
      {status === 'loading' && <Skeleton className="absolute inset-0" />}
      {status === 'error' && (
        <div
          className={cn(
            'absolute inset-0 flex items-center justify-center bg-muted text-muted-foreground',
            fallbackClassName
          )}
        >
          <ImageOff className="h-6 w-6" />
        </div>
      )}
      <img
        src={src}
        alt={alt}
        className={cn('h-full w-full object-cover', status !== 'loaded' && 'opacity-0')}
        onLoad={() => setStatus('loaded')}
        onError={() => setStatus('error')}
      />
    </div>
  )
}
