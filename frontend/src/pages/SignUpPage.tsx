import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/authentication/AuthContext'

export function SignUpPage() {
  const { signUp } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    const { error } = await signUp(email, password, fullName)
    setLoading(false)
    if (error) {
      setError(error)
    } else {
      setSubmitted(true)
    }
  }

  if (submitted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-ink-50 dark:bg-ink-900 px-4">
        <div className="card w-full max-w-md p-8 text-center">
          <h1 className="text-xl font-bold text-ink-800 dark:text-white">Check your email</h1>
          <p className="mt-2 text-sm text-ink-500 dark:text-ink-300">
            We sent a verification link to <strong>{email}</strong>. Confirm your email, then sign in to complete onboarding.
          </p>
          <button onClick={() => navigate('/sign-in')} className="btn-primary mt-6 w-full">Go to Sign In</button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-50 dark:bg-ink-900 px-4">
      <div className="card w-full max-w-md p-8">
        <div className="mb-6 flex items-center gap-2">
          <img src="/logo.svg" alt="ExpenseCast" className="h-8 w-8" />
          <span className="text-lg font-bold text-ink-800 dark:text-white">ExpenseCast</span>
        </div>
        <h1 className="text-xl font-bold text-ink-800 dark:text-white">Create your account</h1>
        <p className="mt-1 text-sm text-ink-500 dark:text-ink-300">Start tracking in under a minute.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="label" htmlFor="fullName">Full name</label>
            <input id="fullName" required className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="email">Email</label>
            <input id="email" type="email" required className="input" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="password">Password</label>
            <input id="password" type="password" required minLength={8} className="input" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Creating account…' : 'Sign Up'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-ink-500 dark:text-ink-300">
          Already have an account?{' '}
          <Link to="/sign-in" className="text-brand-600 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
