import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Target } from 'lucide-react'
import { createGoal, listGoals } from '@/services/api'

export function GoalsPage() {
  const [showForm, setShowForm] = useState(false)
  const queryClient = useQueryClient()
  const { data: goals, isLoading } = useQuery({ queryKey: ['goals'], queryFn: listGoals })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Savings Goals</h1>
        <button onClick={() => setShowForm(true)} className="btn-primary"><Plus className="h-4 w-4" /> New Goal</button>
      </div>

      {isLoading ? (
        <p className="text-sm text-ink-400">Loading…</p>
      ) : !goals?.length ? (
        <div className="card p-12 text-center">
          <Target className="mx-auto h-8 w-8 text-ink-300" />
          <p className="mt-3 text-sm text-ink-500 dark:text-ink-300">No savings goals yet. Create one to start tracking progress.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {goals.map((g) => {
            const percent = Math.min(100, (g.current_amount / g.target_amount) * 100)
            return (
              <div key={g.goal_id} className="card p-5">
                <p className="font-semibold text-ink-800 dark:text-white">{g.goal_name}</p>
                <p className="mt-1 text-sm text-ink-500">₹{g.current_amount.toLocaleString()} of ₹{g.target_amount.toLocaleString()}</p>
                <div className="mt-3 h-2 rounded-full bg-ink-100 dark:bg-ink-700">
                  <div className="h-2 rounded-full bg-brand-500" style={{ width: `${percent}%` }} />
                </div>
                {g.monthly_required_amount != null && (
                  <p className="mt-2 text-xs text-ink-400">Needs ₹{g.monthly_required_amount.toLocaleString()}/month to reach on time</p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {showForm && (
        <GoalForm onClose={() => setShowForm(false)} onCreated={() => { setShowForm(false); queryClient.invalidateQueries({ queryKey: ['goals'] }) }} />
      )}
    </div>
  )
}

function GoalForm({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ goal_name: '', target_amount: '', target_date: '' })
  const mutation = useMutation({
    mutationFn: () => createGoal({ goal_name: form.goal_name, target_amount: Number(form.target_amount), target_date: form.target_date || undefined }),
    onSuccess: onCreated,
  })
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" role="dialog" aria-modal="true">
      <div className="card w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-ink-800 dark:text-white">New Savings Goal</h2>
        <form className="mt-4 space-y-3" onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}>
          <div><label className="label">Goal name</label><input required className="input" value={form.goal_name} onChange={(e) => setForm({ ...form, goal_name: e.target.value })} /></div>
          <div><label className="label">Target amount (₹)</label><input type="number" required min="1" className="input" value={form.target_amount} onChange={(e) => setForm({ ...form, target_amount: e.target.value })} /></div>
          <div><label className="label">Target date (optional)</label><input type="date" className="input" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} /></div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1">{mutation.isPending ? 'Saving…' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
