import { useState } from 'react'
import { ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'

export interface MetadataTreeProps {
  metadata: Record<string, unknown>
}

export function MetadataTree({ metadata }: MetadataTreeProps) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)
  const text = JSON.stringify(metadata, null, 2)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="rounded-md bg-muted p-2" data-testid="metadata-tree">
      <div className="flex items-center justify-between gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="h-auto p-0 text-xs font-normal"
          onClick={() => setExpanded((v) => !v)}
          aria-label="Toggle metadata"
          aria-expanded={expanded}
        >
          {expanded ? <ChevronUp className="mr-1 h-3 w-3" /> : <ChevronDown className="mr-1 h-3 w-3" />}
          Metadata
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={handleCopy}
          aria-label="Metadata JSON kopyala"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
        </Button>
      </div>
      {expanded && (
        <pre className="mt-2 max-h-48 overflow-auto rounded border border-border bg-card p-2 text-xs">
          {text}
        </pre>
      )}
    </div>
  )
}
