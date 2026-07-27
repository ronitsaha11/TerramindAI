import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

function App() {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>TerraMind AI</CardTitle>
          <CardDescription>Frontend Foundation Ready</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Separator />
          <Button className="w-full">Get Started</Button>
        </CardContent>
      </Card>
    </div>
  )
}

export default App
