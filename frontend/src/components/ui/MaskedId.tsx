interface MaskedIdProps {
  value: string | undefined | null
  testId?: string
}

export function MaskedId({ value, testId }: MaskedIdProps) {
  if (!value) return <span className="text-muted-foreground">-</span>
  return (
    <span className="font-mono text-sm text-muted-foreground" data-testid={testId}>
      {value}
    </span>
  )
}
