import { Link } from 'react-router-dom'
import { User } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatScore } from '@/lib/formatters'
import { cn } from '@/lib/utils'
import type { IdentifyCandidate, IdentifyFace } from '@/api/types'

export function DecisionBadge({ decision }: { decision: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        decision === 'matched' && 'bg-emerald-500/10 text-emerald-500',
        decision === 'possible_match' && 'bg-amber-500/10 text-amber-500',
        decision === 'no_match' && 'bg-destructive/10 text-destructive'
      )}
      data-testid="decision-badge"
    >
      {decision === 'matched' && 'Eşleşti'}
      {decision === 'possible_match' && 'Olası Eşleşme'}
      {decision === 'no_match' && 'Eşleşme Yok'}
      {!['matched', 'possible_match', 'no_match'].includes(decision) && decision}
    </span>
  )
}

export function CandidateCard({ candidate, isMain }: { candidate: IdentifyCandidate; isMain?: boolean }) {
  return (
    <Card className={cn('border-border bg-card', isMain && 'border-primary/50')}>
      <CardContent className="flex items-center gap-4 p-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-full bg-muted">
          {candidate.cropImageUrl ? (
            <img
              src={candidate.cropImageUrl}
              alt={candidate.name || 'Aday yüz'}
              className="h-full w-full object-cover"
            />
          ) : (
            <User className="h-6 w-6 text-muted-foreground" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">
            {candidate.personId ? (
              <Link to={`/people/${candidate.personId}`} className="hover:underline">
                {candidate.name}
              </Link>
            ) : (
              <span>{candidate.name}</span>
            )}
          </p>
          <p className="text-xs text-muted-foreground">
            Skor: {formatScore(candidate.score)} • Sıra: {candidate.rank}
          </p>
        </div>
        <DecisionBadge decision={candidate.decision} />
      </CardContent>
    </Card>
  )
}

export interface FaceResultProps {
  face: IdentifyFace
  title?: string
  showCandidatesLabel?: boolean
}

export function FaceResult({ face, title, showCandidatesLabel = true }: FaceResultProps) {
  const best = face.candidates[0]
  const hasOthers = face.candidates.length > 1

  return (
    <Card className="border-border bg-card" data-testid="face-result">
      <CardHeader>
        <CardTitle className="text-base">{title ?? 'Yüz Sonucu'}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm text-muted-foreground">Kalite Skoru</p>
            <p className="font-medium">{formatScore(face.qualityScore)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Karar</p>
            <DecisionBadge decision={face.result.status} />
          </div>
        </div>
        {best ? (
          <div className="space-y-3">
            <p className="text-sm font-medium">
              {showCandidatesLabel ? 'En İyi Aday' : 'Adaylar'}
            </p>
            <CandidateCard candidate={best} isMain />
            {showCandidatesLabel && hasOthers && (
              <p className="text-sm font-medium">Diğer Adaylar</p>
            )}
            {(!showCandidatesLabel || hasOthers) &&
              face.candidates.slice(1).map((candidate) => (
                <CandidateCard key={candidate.rank} candidate={candidate} />
              ))}
          </div>
        ) : (
          <Card className="border-border bg-card">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-muted">
                <User className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">Bilinmeyen kişi</p>
                <p className="text-xs text-muted-foreground">Veritabanında eşleşen kayıt bulunamadı.</p>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  )
}
