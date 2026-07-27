export function FullScreenLoader() {
  return (
    <div className="flex h-screen w-screen items-center justify-center bg-zinc-950 text-zinc-50">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-800 border-t-zinc-400" />
        <p className="text-sm font-medium tracking-wide text-zinc-400 uppercase">
          TerraMind AI
        </p>
      </div>
    </div>
  )
}
