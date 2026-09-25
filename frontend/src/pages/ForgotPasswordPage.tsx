import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/features/authentication/AuthContext'

export function ForgotPasswordPage() {
  const { requestPasswordReset } = useAuth()

  const [email, setEmail] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setMessage(null)
    setError(null)
    setLoading(true)

    const { error } = await requestPasswordReset(email)

    setLoading(false)

    if (error) {
      setError(error)
    } else {
      setMessage(
        'If an account exists with this email, a password reset link has been sent.'
      )
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-50 dark:bg-ink-900 px-4">
      <div className="card w-full max-w-md p-8">
        <div className="mb-6 flex items-center gap-2">
          <img src="/logo.svg" alt="ExpenseCast" className="h-8 w-8" />
          <span className="text-lg font-bold text-ink-800 dark:text-white">
            ExpenseCast
          </span>
        </div>

        <h1 className="text-xl font-bold text-ink-800 dark:text-white">
          Forgot your password?
        </h1>

        <p className="mt-1 text-sm text-ink-500 dark:text-ink-300">
          Enter your email address and we'll send you a password reset link.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="label" htmlFor="email">
              Email
            </label>

            <input
              id="email"
              type="email"
              required
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          {message && (
            <p className="text-sm text-green-600" role="status">
              {message}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Sending…' : 'Send Reset Link'}
          </button>
        </form>

        <div className="mt-4 text-center text-sm">
          <Link
            to="/sign-in"
            className="text-brand-600 hover:underline"
          >
            Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  )
}