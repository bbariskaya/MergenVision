import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuthStore } from '@/stores/authStore'

const loginSchema = z.object({
  token: z.string().min(1, 'Token is required'),
})

type LoginFormValues = z.infer<typeof loginSchema>

const LOGO_URL =
  'https://interprobe.com.tr/themes/interprobe/assets/img/logo.png'

export function LoginPage() {
  const login = useAuthStore((state) => state.login)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  })

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const onSubmit = (values: LoginFormValues) => {
    login(values.token)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-sm border-border bg-card">
        <CardHeader className="text-center">
          <div className="mb-4 flex justify-center">
            <img
              src={LOGO_URL}
              alt="INTERPROBE"
              className="h-12 w-auto object-contain"
            />
          </div>
          <CardTitle className="text-xl">INTERPROBE MergenVision</CardTitle>
          <CardDescription>Protect Beyond The Endpoint</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="token">API Token</Label>
              <Input
                id="token"
                type="password"
                placeholder="admin-token"
                data-testid="login-token-input"
                {...register('token')}
              />
              {errors.token && (
                <p className="text-sm text-destructive">
                  {errors.token.message}
                </p>
              )}
            </div>
            <Button type="submit" className="w-full" data-testid="login-submit-button">
              Sign In
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
