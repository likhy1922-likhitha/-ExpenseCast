import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createProfile } from '@/services/api'

const USER_TYPES = ['student', 'teenager', 'salaried', 'freelancer', 'other'] as const

export function OnboardingPage() {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [userType, setUserType] = useState<typeof USER_TYPES[number]>('student')
  const [income, setIncome] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await createProfile({
        full_name: fullName,
        user_type: userType,
        preferred_currency: 'INR',
        approx_monthly_income: income ? Number(income) : undefined,
      })
      navigate('/dashboard')
    } catch {
      setError('Could not save your profile. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-50 dark:bg-ink-900 px-4">
      <div className="card w-full max-w-lg p-8">
        <h1 className="text-xl font-bold text-ink-800 dark:text-white">Let's set up your account</h1>
        <p className="mt-1 text-sm text-ink-500 dark:text-ink-300">A few details help us personalise your dashboard. All optional fields can be skipped.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="label">Full name</label>
            <input required className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <label className="label">I am a...</label>
            <select className="input" value={userType} onChange={(e) => setUserType(e.target.value as typeof USER_TYPES[number])}>
              {USER_TYPES.map((t) => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Approximate monthly income (optional)</label>
            <input type="number" className="input" value={income} onChange={(e) => setIncome(e.target.value)} placeholder="e.g. 50000" />
          </div>
          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Saving…' : 'Continue to Dashboard'}
          </button>
        </form>
      </div>
    </div>
  )
}
