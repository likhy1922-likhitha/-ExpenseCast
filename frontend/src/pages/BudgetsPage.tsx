import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Wallet } from 'lucide-react'
import { createBudget, listBudgets, listCategories } from '@/services/api'

export function BudgetsPage() {
  const today = new Date()
  const [showForm, setShowForm] = useState(false)
  const queryClient = useQueryClient()
  const { data: budgets, isLoading } = useQuery({
    queryKey: ['budgets', today.getMonth() + 1, today.getFullYear()],
    queryFn: () => listBudgets(today.getMonth() + 1, today.getFullYear()),
  })
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: listCategories })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Budgets</h1>
        <button onClick={() => setShowForm(true)} className="btn-primary"><Plus className="h-4 w-4" /> New Budget</button>
      </div>

      {isLoading ? (
        <p className="text-sm text-ink-400">Loading…</p>
      ) : !budgets?.length ? (
        <div className="card p-12 text-center">
          <Wallet className="mx-auto h-8 w-8 text-ink-300" />
          <p className="mt-3 text-sm text-ink-500 dark:text-ink-300">No budgets set for this month yet.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {budgets.map((b) => (
            <div key={b.id} className="card p-5">
              <p className="font-semibold text-ink-800 dark:text-white">{b.name}</p>
              <p className="mt-1 text-sm text-ink-500">Limit: ₹{Number(b.limit_amount).toLocaleString()}</p>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <BudgetForm
          categories={categories ?? []}
          onClose={() => setShowForm(false)}
          onCreated={() => { setShowForm(false); queryClient.invalidateQueries({ queryKey: ['budgets'] }) }}
        />
      )}
    </div>
  )
}

function BudgetForm({ categories, onClose, onCreated }: { categories: { id: string; name: string }[]; onClose: () => void; onCreated: () => void }) {
  const today = new Date()
  const [form, setForm] = useState({ name: '', limit_amount: '', category_id: '' })
  const mutation = useMutation({
    mutationFn: () => createBudget({
      name: form.name, limit_amount: Number(form.limit_amount),
      category_id: form.category_id || undefined,
      period_month: today.getMonth() + 1, period_year: today.getFullYear(),
    }),
    onSuccess: onCreated,
  })
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" role="dialog" aria-modal="true">
      <div className="card w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-ink-800 dark:text-white">New Budget</h2>
        <form className="mt-4 space-y-3" onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}>
          <div><label className="label">Name</label><input required className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
          <div><label className="label">Category</label>
            <select className="input" value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
              <option value="">Overall budget</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div><label className="label">Limit Amount (₹)</label><input type="number" required min="1" className="input" value={form.limit_amount} onChange={(e) => setForm({ ...form, limit_amount: e.target.value })} /></div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1">{mutation.isPending ? 'Saving…' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
