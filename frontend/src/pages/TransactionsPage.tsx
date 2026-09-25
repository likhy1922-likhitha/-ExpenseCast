import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Trash2, Pencil, Inbox } from 'lucide-react'
import { createTransaction, deleteTransaction, listCategories, listTransactions } from '@/services/api'
import type { TransactionType } from '@/types'

export function TransactionsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<TransactionType | ''>('')
  const [showForm, setShowForm] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['transactions', page, search, typeFilter],
    queryFn: () => listTransactions({
      page, page_size: 20,
      ...(search ? { search } : {}),
      ...(typeFilter ? { transaction_type: typeFilter } : {}),
    }),
  })

  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: listCategories })

  const deleteMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Transactions</h1>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          <Plus className="h-4 w-4" /> Add Transaction
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
          <input
            className="input pl-9"
            placeholder="Search by merchant or description..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <select className="input w-auto" value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value as TransactionType | ''); setPage(1) }}>
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
          <option value="savings">Savings</option>
          <option value="investment">Investment</option>
        </select>
      </div>

      {showForm && (
        <AddTransactionForm
          categories={categories ?? []}
          onClose={() => setShowForm(false)}
          onCreated={() => {
            setShowForm(false)
            queryClient.invalidateQueries({ queryKey: ['transactions'] })
            queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
          }}
        />
      )}

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-ink-400">Loading…</div>
        ) : !data?.items.length ? (
          <div className="p-12 text-center">
            <Inbox className="mx-auto h-8 w-8 text-ink-300" />
            <p className="mt-3 text-sm text-ink-500 dark:text-ink-300">No transactions found. Add one to get started.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-ink-50 dark:bg-ink-900 text-left text-xs font-semibold uppercase text-ink-400">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Merchant</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3 text-right">Amount</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100 dark:divide-ink-700">
              {data.items.map((t) => (
                <tr key={t.transaction_id} className="hover:bg-ink-50 dark:hover:bg-ink-900/40">
                  <td className="px-4 py-3 text-ink-600 dark:text-ink-300">{t.date}</td>
                  <td className="px-4 py-3 font-medium text-ink-800 dark:text-white">{t.merchant || '—'}</td>
                  <td className="px-4 py-3">
                    <TypeBadge type={t.transaction_type} />
                  </td>
                  <td className={`px-4 py-3 text-right font-semibold ${t.transaction_type === 'income' ? 'text-emerald-600' : 'text-ink-800 dark:text-white'}`}>
                    ₹{Number(t.amount).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => deleteMutation.mutate(t.transaction_id)} className="text-ink-400 hover:text-red-600" aria-label="Delete">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex justify-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="btn-secondary disabled:opacity-40">Previous</button>
          <span className="flex items-center px-2 text-sm text-ink-500">Page {page} of {data.total_pages}</span>
          <button disabled={page >= data.total_pages} onClick={() => setPage((p) => p + 1)} className="btn-secondary disabled:opacity-40">Next</button>
        </div>
      )}
    </div>
  )
}

function TypeBadge({ type }: { type: TransactionType }) {
  const colors: Record<TransactionType, string> = {
    income: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    expense: 'bg-red-50 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    savings: 'bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    investment: 'bg-purple-50 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  }
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${colors[type]}`}>{type}</span>
}

function AddTransactionForm({
  categories, onClose, onCreated,
}: {
  categories: { id: string; name: string }[]
  onClose: () => void
  onCreated: () => void
}) {
  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    transaction_type: 'expense' as TransactionType,
    amount: '',
    merchant: '',
    description: '',
    category_id: '',
  })
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => createTransaction({
      date: form.date,
      transaction_type: form.transaction_type,
      amount: Number(form.amount),
      merchant: form.merchant || undefined,
      description: form.description || undefined,
      category_id: form.category_id || undefined,
    }),
    onSuccess: onCreated,
    onError: () => setError('Could not save this transaction. Check the amount and try again.'),
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" role="dialog" aria-modal="true">
      <div className="card w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-ink-800 dark:text-white">Add Transaction</h2>
        <form
          className="mt-4 space-y-3"
          onSubmit={(e) => { e.preventDefault(); setError(null); mutation.mutate() }}
        >
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Date</label>
              <input type="date" required className="input" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            </div>
            <div>
              <label className="label">Type</label>
              <select className="input" value={form.transaction_type} onChange={(e) => setForm({ ...form, transaction_type: e.target.value as TransactionType })}>
                <option value="expense">Expense</option>
                <option value="income">Income</option>
                <option value="savings">Savings</option>
                <option value="investment">Investment</option>
              </select>
            </div>
          </div>
          <div>
            <label className="label">Amount (₹)</label>
            <input type="number" min="0.01" step="0.01" required className="input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
          </div>
          <div>
            <label className="label">Merchant</label>
            <input className="input" value={form.merchant} onChange={(e) => setForm({ ...form, merchant: e.target.value })} />
          </div>
          <div>
            <label className="label">Category</label>
            <select className="input" value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
              <option value="">Auto-detect</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Notes</label>
            <input className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1">
              {mutation.isPending ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
