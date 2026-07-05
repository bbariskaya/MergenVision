import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'

export interface DataTableColumn<T> {
  key: string
  header: ReactNode
  cell: (row: T) => ReactNode
  className?: string
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  data: T[]
  keyExtractor: (row: T) => string
  loading?: boolean
  emptyState?: ReactNode
  onRowClick?: (row: T) => void
  footer?: ReactNode
  className?: string
  testId?: string
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  loading,
  emptyState,
  onRowClick,
  footer,
  className,
  testId,
}: DataTableProps<T>) {
  return (
    <div className={cn('rounded-md border border-border', className)} data-testid={testId}>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {columns.map((column) => (
              <TableHead key={column.key} className={column.className}>
                {column.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                Yükleniyor...
              </TableCell>
            </TableRow>
          ) : data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                {emptyState ?? 'Veri bulunamadı.'}
              </TableCell>
            </TableRow>
          ) : (
            data.map((row) => (
              <TableRow
                key={keyExtractor(row)}
                className={cn(onRowClick && 'cursor-pointer')}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((column) => (
                  <TableCell key={`${keyExtractor(row)}-${column.key}`} className={column.className}>
                    {column.cell(row)}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      {footer && <div className="border-t border-border px-4 py-3">{footer}</div>}
    </div>
  )
}
