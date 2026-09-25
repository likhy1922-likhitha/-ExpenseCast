import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, TrendingUp } from 'lucide-react'
import { createInvestment, listInvestments } from '@/services/api'

const TYPES = ['fixed_deposit', 'recurring_deposit', 'mutual_fund', 'sip', 'stocks', 'gold', 'provident_fund', 'other']

export function InvestmentsPage() {
  const [showForm, setShowForm] = useState(false)
  const queryClient = useQueryClient()
  const { data: investments, isLoading } = useQuery({ queryKey: ['investments'], queryFn: listInvestments })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Investments</h1>
        <button onClick={() => setShowForm(true)} className="btn-primary"><Plus className="h-4 w-4" /> Add Investment</button>
      </div>
      <p className="text-xs text-ink-400">This is a manual tracking tool only. ExpenseCast does not provide financial advice or guarantee returns.</p>

      {isLoading ? (
        <p className="text-sm text-ink-400">Loading…</p>
      ) : !investments?.length ? (
        <div className="card p-12 text-center">
          <TrendingUp className="mx-auto h-8 w-8 text-ink-300" />
          <p className="mt-3 text-sm text-ink-500 dark:text-ink-300">No investments tracked yet.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-ink-50 dark:bg-ink-900 text-left text-xs font-semibold uppercase text-ink-400">
              <tr><th className="px-4 py-3">Name</th><th className="px-4 py-3">Type</th><th className="px-4 py-3 text-right">Invested</th><th className="px-4 py-3 text-right">Current Value</th></tr>
            </thead>
            <tbody className="divide-y divide-ink-100 dark:divide-ink-700">
              {investments.map((inv) => (
                <tr key={inv.id}>
                  <td className="px-4 py-3 font-medium text-ink-800 dark:text-white">{inv.investment_name}</td>
                  <td className="px-4 py-3 capitalize text-ink-500">{inv.investment_type.replace('_', ' ')}</td>
                  <td className="px-4 py-3 text-right">₹{Number(inv.amount_invested).toLocaleString()}</td>
                  <td className="px-4 py-3 text-right">{inv.current_value != null ? `₹${Number(inv.current_value).toLocaleString()}` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <InvestmentForm onClose={() => setShowForm(false)} onCreated={() => { setShowForm(false); queryClient.invalidateQueries({ queryKey: ['investments'] }) }} />
      )}
    </div>
  )
}

function InvestmentForm({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ investment_name: '', investment_type: 'sip', amount_invested: '', investment_date: new Date().toISOString().slice(0, 10) })
  const mutation = useMutation({
    mutationFn: () => createInvestment({ ...form, amount_invested: Number(form.amount_invested) } as never),
    onSuccess: onCreated,
  })
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" role="dialog" aria-modal="true">
      <div className="card w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-ink-800 dark:text-white">Add Investment</h2>
        <form className="mt-4 space-y-3" onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}>
          <div><label className="label">Name</label><input required className="input" value={form.investment_name} onChange={(e) => setForm({ ...form, investment_name: e.target.value })} /></div>
          <div><label className="label">Type</label>
            <select className="input" value={form.investment_type} onChange={(e) => setForm({ ...form, investment_type: e.target.value })}>
              {TYPES.map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
            </select>
          </div>
          <div><label className="label">Amount Invested (₹)</label><input type="number" required min="1" className="input" value={form.amount_invested} onChange={(e) => setForm({ ...form, amount_invested: e.target.value })} /></div>
          <div><label className="label">Investment Date</label><input type="date" required className="input" value={form.investment_date} onChange={(e) => setForm({ ...form, investment_date: e.target.value })} /></div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1">{mutation.isPending ? 'Saving…' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
