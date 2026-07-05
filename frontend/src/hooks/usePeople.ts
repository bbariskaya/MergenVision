import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createPerson, deletePerson, getPeople, updatePerson } from '@/api/people'
import type { PeopleListParams, PersonUpdateInput } from '@/api/types'

export function usePeople(params?: PeopleListParams) {
  return useQuery({
    queryKey: ['people', params],
    queryFn: () => getPeople(params),
  })
}

export function useCreatePerson() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createPerson,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useUpdatePerson() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: PersonUpdateInput }) => updatePerson(id, patch),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['person', data.personId] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useDeletePerson() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deletePerson,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
