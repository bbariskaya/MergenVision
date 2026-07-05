import { useMutation, useQueryClient } from '@tanstack/react-query'
import { identify } from '@/api/identify'
import type { IdentifyRequestQuery } from '@/api/types'

export function useIdentify() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, options }: { file: File; options?: IdentifyRequestQuery }) =>
      identify(file, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['identification-requests'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
