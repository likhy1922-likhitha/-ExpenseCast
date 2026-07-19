import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/apiClient'
import { useAuth } from '@/features/authentication/AuthContext'

export function SettingsPage() {
  const { user, signOut } = useAuth()
  const { data: settings } = useQuery({
    queryKey: ['user-settings'],
    queryFn: () => api.get('/api/settings').then((r) => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.delete('/api/profile/account'),
    onSuccess: () => signOut(),
  })

  const exportMutation = useMutation({
    mutationFn: () => api.get('/api/settings/export-data'),
    onSuccess: (res) => {
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'expensecast_data_export.json'
      link.click()
    },
  })

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Settings</h1>

      <div className="card p-6">
        <h2 className="font-semibold text-ink-800 dark:text-white">Account</h2>
        <p className="mt-2 text-sm text-ink-500">{user?.email}</p>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-ink-800 dark:text-white">Notifications</h2>
        <div className="mt-3 space-y-2 text-sm text-ink-600 dark:text-ink-300">
          <label className="flex items-center gap-2"><input type="checkbox" defaultChecked={settings?.notify_budget_warnings} /> Budget warnings</label>
          <label className="flex items-center gap-2"><input type="checkbox" defaultChecked={settings?.notify_recurring_upcoming} /> Upcoming recurring payments</label>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-ink-800 dark:text-white">Your Data</h2>
        <button onClick={() => exportMutation.mutate()} className="btn-secondary mt-3">Export my data (JSON)</button>
      </div>

      <div className="card p-6 border-red-200 dark:border-red-800">
        <h2 className="font-semibold text-red-700 dark:text-red-400">Danger Zone</h2>
        <p className="mt-1 text-sm text-ink-500">Permanently delete your account and all associated data.</p>
        <button
          onClick={() => { if (confirm('This will permanently delete your account. Continue?')) deleteMutation.mutate() }}
          className="mt-3 rounded-xl border border-red-300 px-4 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
        >
          Delete Account
        </button>
      </div>
    </div>
  )
}
