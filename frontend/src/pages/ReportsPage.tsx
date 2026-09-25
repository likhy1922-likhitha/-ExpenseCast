import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { api } from '@/lib/apiClient'

async function getReport(period: string) {
  const { data } = await api.get(`/api/reports/${period}`)
  return data
}

function downloadExport(period: string, format: 'csv' | 'pdf') {
  api.get(`/api/reports/export/${format}`, { params: { period }, responseType: 'blob' }).then((res) => {
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `expensecast_${period}_report.${format}`
    link.click()
  })
}

export function ReportsPage() {
  const { data: monthly } = useQuery({ queryKey: ['report-monthly'], queryFn: () => getReport('monthly') })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Reports</h1>

      <div className="card p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ink-800 dark:text-white">Monthly Report</h2>
          <div className="flex gap-2">
            <button onClick={() => downloadExport('monthly', 'csv')} className="btn-secondary !px-3 !py-1.5 text-xs"><Download className="h-3.5 w-3.5" /> CSV</button>
            <button onClick={() => downloadExport('monthly', 'pdf')} className="btn-secondary !px-3 !py-1.5 text-xs"><Download className="h-3.5 w-3.5" /> PDF</button>
          </div>
        </div>
        {monthly && (
          <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
            <div><dt className="text-ink-400">Income</dt><dd className="font-semibold text-ink-800 dark:text-white">₹{monthly.total_income.toLocaleString()}</dd></div>
            <div><dt className="text-ink-400">Expense</dt><dd className="font-semibold text-ink-800 dark:text-white">₹{monthly.total_expense.toLocaleString()}</dd></div>
            <div><dt className="text-ink-400">Savings</dt><dd className="font-semibold text-ink-800 dark:text-white">₹{monthly.total_savings.toLocaleString()}</dd></div>
            <div><dt className="text-ink-400">Net Change</dt><dd className="font-semibold text-ink-800 dark:text-white">₹{monthly.net_change.toLocaleString()}</dd></div>
          </dl>
        )}
      </div>
    </div>
  )
}
