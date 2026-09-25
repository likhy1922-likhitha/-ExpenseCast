import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabaseClient'

export function ResetPasswordPage() {
  const navigate = useNavigate()

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setError(null)
    setMessage(null)

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    const { error } = await supabase.auth.updateUser({
      password,
    })

    setLoading(false)

    if (error) {
      setError(error.message)
      return
    }

    setMessage('Your password has been updated successfully.')

    setTimeout(() => {
      navigate('/sign-in')
    }, 2000)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-50 dark:bg-ink-900 px-4">
      <div className="card w-full max-w-md p-8">

        <div className="mb-6 flex items-center gap-2">
          <img
            src="/logo.svg"
            alt="ExpenseCast"
            className="h-8 w-8"
          />

          <span className="text-lg font-bold text-ink-800 dark:text-white">
            ExpenseCast
          </span>
        </div>

        <h1 className="text-xl font-bold text-ink-800 dark:text-white">
          Reset your password
        </h1>

        <p className="mt-1 text-sm text-ink-500 dark:text-ink-300">
          Enter your new password below.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">

          <div>
            <label className="label" htmlFor="password">
              New Password
            </label>

            <input
              id="password"
              type="password"
              required
              minLength={8}
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter new password"
            />
          </div>

          <div>
            <label className="label" htmlFor="confirmPassword">
              Confirm Password
            </label>

            <input
              id="confirmPassword"
              type="password"
              required
              minLength={8}
              className="input"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
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
            {loading ? 'Updating…' : 'Update Password'}
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