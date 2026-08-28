import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Folder, Plus, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useProjectStore } from '@/stores/useProjectStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

type Project = {
  id: string
  name: string
  description?: string
  created_at: string
}

export function ProjectsPanel() {
  const queryClient = useQueryClient()
  const { activeProjectId, setActiveProject } = useProjectStore()
  const [isCreating, setIsCreating] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Fetch projects
  const { data: projects, isLoading, isError, error } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/projects`)
      if (!res.ok) throw new Error('Failed to fetch projects')
      const json = await res.json()
      return json.data
    }
  })

  // Create project mutation
  const createMutation = useMutation({
    mutationFn: async (newProject: { name: string; description?: string }) => {
      const res = await fetch(`${API_BASE_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProject)
      })
      if (!res.ok) {
        if (res.status === 409) {
          throw new Error('A project with this name already exists.')
        }
        throw new Error('An error occurred while creating the project.')
      }
      const json = await res.json()
      return json.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setIsCreating(false)
      setName('')
      setDescription('')
      setErrorMsg(null)
    },
    onError: (err: Error) => {
      setErrorMsg(err.message)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    setErrorMsg(null)
    createMutation.mutate({ name, description })
  }

  return (
    <div className="flex flex-col bg-zinc-950 border border-zinc-800 rounded-md shadow-xl w-80 h-96 text-zinc-50 overflow-hidden shrink-0 pointer-events-auto">
      <div className="p-4 border-b border-zinc-800 flex justify-between items-center shrink-0">
        <h2 className="font-semibold flex items-center gap-2">
          <Folder className="w-4 h-4 text-zinc-400" />
          Projects
        </h2>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => setIsCreating(!isCreating)}
          className="h-8 w-8 hover:bg-zinc-800"
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isCreating && (
          <form onSubmit={handleSubmit} className="bg-zinc-950 p-4 rounded-md border border-zinc-800 space-y-3">
            <h3 className="text-sm font-medium">New Project</h3>
            {errorMsg && (
              <div className="text-red-400 text-xs bg-red-950/50 p-2 rounded flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <p>{errorMsg}</p>
              </div>
            )}
            <input 
              type="text"
              placeholder="Project Name" 
              className="w-full bg-zinc-900 border border-zinc-700 rounded p-2 text-sm focus:outline-none focus:border-zinc-500"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={createMutation.isPending}
              autoFocus
            />
            <textarea 
              placeholder="Description (optional)" 
              className="w-full bg-zinc-900 border border-zinc-700 rounded p-2 text-sm focus:outline-none focus:border-zinc-500 resize-none h-20"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={createMutation.isPending}
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button 
                type="button" 
                variant="ghost" 
                size="sm"
                onClick={() => setIsCreating(false)}
                disabled={createMutation.isPending}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                size="sm"
                disabled={!name.trim() || createMutation.isPending}
                className="bg-zinc-100 text-zinc-900 hover:bg-zinc-300"
              >
                {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create'}
              </Button>
            </div>
          </form>
        )}

        {isError && (
          <div className="text-red-400 text-sm bg-red-950/50 p-3 rounded flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Connection Error</p>
              <p className="text-xs opacity-80">{error?.message || 'Could not connect to backend.'}</p>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center p-8 text-zinc-500">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : (
          <div className="space-y-2">
            {projects?.length === 0 ? (
              <p className="text-zinc-500 text-sm text-center py-8">No projects found. Create one to get started.</p>
            ) : (
              projects?.map((proj) => (
                <div 
                  key={proj.id} 
                  className={`bg-zinc-950 p-3 rounded-md border cursor-pointer group transition-colors ${activeProjectId === proj.id ? 'border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.1)]' : 'border-zinc-800 hover:border-zinc-700'}`}
                  onClick={() => setActiveProject(proj.id)}
                >
                  <div className="flex justify-between items-start">
                    <h4 className={`font-medium text-sm transition-colors ${activeProjectId === proj.id ? 'text-blue-400' : 'group-hover:text-blue-400'}`}>{proj.name}</h4>
                    {activeProjectId === proj.id && (
                      <span className="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded border border-blue-500/30">Active</span>
                    )}
                  </div>
                  {proj.description && (
                    <p className="text-xs text-zinc-500 mt-1 line-clamp-2">{proj.description}</p>
                  )}
                  <p className="text-[10px] text-zinc-600 mt-2">
                    {new Date(proj.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
