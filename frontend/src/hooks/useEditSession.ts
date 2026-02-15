import { useCallback, useEffect, useRef, useState } from 'react'

import { editorApi } from '../services/editorApi'
import type {
  EditActionInput,
  EditActionResponse,
  EditSessionResponse,
} from '../types'

const MAX_HISTORY = 20

const toInputs = (actions: EditActionResponse[]): EditActionInput[] =>
  actions.map(({ id, risk_item_id, type, start_time, end_time, options }) => ({
    id,
    risk_item_id,
    type,
    start_time,
    end_time,
    options,
  }))

export const useEditSession = (jobId: string | null) => {
  const [session, setSession] = useState<EditSessionResponse | null>(null)
  const [actions, setActions] = useState<EditActionResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [canUndo, setCanUndo] = useState(false)
  const historyRef = useRef<EditActionInput[][]>([])

  const pushHistory = useCallback((snapshot: EditActionInput[]) => {
    historyRef.current.push(snapshot)
    if (historyRef.current.length > MAX_HISTORY) {
      historyRef.current.shift()
    }
    setCanUndo(historyRef.current.length > 0)
  }, [])

  useEffect(() => {
    historyRef.current = []
    setCanUndo(false)
  }, [jobId])

  const loadSession = useCallback(async () => {
    if (!jobId) {
      setSession(null)
      setActions([])
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await editorApi.getEditSession(jobId)
      setSession(response)
      setActions(response.actions)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load edit session')
    } finally {
      setLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    const load = async () => {
      await loadSession()
    }

    load()
  }, [loadSession])

  const saveActions = useCallback(
    async (nextActions: EditActionInput[]) => {
      if (!jobId) {
        return null
      }
      setSaving(true)
      setError(null)
      try {
        const response = await editorApi.updateEditSession(jobId, {
          actions: nextActions,
        })
        setSession(response)
        setActions(response.actions)
        return response
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to save edit session')
        throw err
      } finally {
        setSaving(false)
      }
    },
    [jobId]
  )

  const addAction = useCallback(
    async (action: EditActionInput) => {
      const snapshot = toInputs(actions)
      const next = [...snapshot, action]
      const response = await saveActions(next)
      pushHistory(snapshot)
      return response
    },
    [actions, pushHistory, saveActions]
  )

  const updateAction = useCallback(
    async (action: EditActionInput) => {
      if (!action.id) {
        throw new Error('Action id is required for update')
      }
      const snapshot = toInputs(actions)
      const index = snapshot.findIndex((item) => item.id === action.id)
      if (index === -1) {
        throw new Error('Action not found')
      }
      const next = [...snapshot]
      next[index] = action
      const response = await saveActions(next)
      pushHistory(snapshot)
      return response
    },
    [actions, pushHistory, saveActions]
  )

  const removeAction = useCallback(
    async (actionId: string) => {
      const snapshot = toInputs(actions)
      const next = snapshot.filter((item) => item.id !== actionId)
      if (next.length === snapshot.length) {
        return null
      }
      const response = await saveActions(next)
      pushHistory(snapshot)
      return response
    },
    [actions, pushHistory, saveActions]
  )

  const replaceActions = useCallback(
    async (nextActions: EditActionInput[]) => {
      const snapshot = toInputs(actions)
      const response = await saveActions(nextActions)
      pushHistory(snapshot)
      return response
    },
    [actions, pushHistory, saveActions]
  )

  const undo = useCallback(async () => {
    const previous = historyRef.current.pop()
    setCanUndo(historyRef.current.length > 0)
    if (!previous) {
      return null
    }
    try {
      return await saveActions(previous)
    } catch (err) {
      historyRef.current.push(previous)
      setCanUndo(true)
      throw err
    }
  }, [saveActions])

  return {
    session,
    actions,
    loading,
    saving,
    error,
    canUndo,
    reload: loadSession,
    addAction,
    updateAction,
    removeAction,
    replaceActions,
    undo,
  }
}
