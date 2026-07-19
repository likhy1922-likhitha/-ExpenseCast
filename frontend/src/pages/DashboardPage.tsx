import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { Wallet, TrendingDown, TrendingUp, PiggyBank, AlertTriangle, Sparkles } from 'lucide-react'
import { getCategoryBreakdown, getDashboardSummary, getIncomeVsExpenseTrend, getInsights } from '@/services/api'

const DATE_RANGES = [
  { key: 'this_week', label: 'This Week' },
  { key: 'this_month', label: 'This Month' },
  { key: 'last_3_months', label: 'Last 3 Months' },
  { key: 'last_6_months', label: 'Last 6 Months' },
  { key: 'this_year', label: 'This Year' },
]

const PIE_COLORS = ['#22b072', '#42c98a', '#78dfad', '#adeecd', '#12724b', '#158f5c', '#104a34']

export function DashboardPage() {
  const [dateRange, setDateRange] = useState('this_month')

  const { data: summary, isLoading } = useQuery({
    queryKey: ['dashboard-summary', dateRange],
    queryFn: () => getDashboardSummary(dateRange),
  })
  const { data: trend } = useQuery({
    queryKey: ['income-vs-expense', dateRange],
    queryFn: () => getIncomeVsExpenseTrend(dateRange),
  })
  const { data: categoryBreakdown } = useQuery({
    queryKey: ['category-breakdown', dateRange],
    queryFn: () => getCategoryBreakdown(dateRange),
  })
  const { data: insights } = useQuery({ queryKey: ['insights'], queryFn: getInsights })

  const isEmpty = summary && summary.total_income === 0 && summary.total_expenses === 0

  if (isLoading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Dashboard</h1>
        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          className="input w-auto"
        >
          {DATE_RANGES.map((r) => (
            <option key={r.key} value={r.key}>{r.label}</option>
          ))}
        </select>
      </div>

      {isEmpty && (
        <div className="card p-8 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-brand-500" />
          <h2 className="mt-3 text-lg font-semibold text-ink-800 dark:text-white">Welcome to ExpenseCast</h2>
          <p className="mt-1 text-sm text-ink-500 dark:text-ink-300 max-w-md mx-auto">
            You haven't logged any transactions yet. Add your first transaction or import a bank
            statement to see your dashboard come to life.
          </p>
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <SummaryCard icon={Wallet} label="Current Balance" value={summary?.current_balance ?? 0} tone="brand" />
        <SummaryCard icon={TrendingUp} label="Total Income" value={summary?.total_income ?? 0} tone="green" />
        <SummaryCard icon={TrendingDown} label="Total Expenses" value={summary?.total_expenses ?? 0} tone="red" />
        <SummaryCard icon={PiggyBank} label="Total Savings" value={summary?.total_savings ?? 0} tone="blue" />
      </div>

      {/* Forecast card */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ink-800 dark:text-white">Forecast</h2>
          <ConfidenceBadge level={summary?.forecast_confidence} />
        </div>
        {summary?.forecast_confidence === 'insufficient_data' ? (
          <p className="mt-3 text-sm text-ink-500 dark:text-ink-300">
            Add at least 30 days of transaction history to unlock expense forecasting.
          </p>
        ) : (
          <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
            <ForecastStat label="Next 7 Days" value={summary?.predicted_7_day_expense} />
            <ForecastStat label="Next 30 Days" value={summary?.predicted_30_day_expense} />
            <ForecastStat label="Predicted EOM Balance" value={summary?.predicted_end_of_month_balance} />
          </div>
        )}
        {summary?.overspending_risk === 'high' && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-red-50 dark:bg-red-900/30 px-4 py-3 text-sm text-red-700 dark:text-red-300">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            Your predicted spending may exceed your budget this period.
          </div>
        )}
        <p className="mt-3 text-xs text-ink-400">Forecasts are statistical estimates, not financial advice.</p>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h2 className="mb-4 font-semibold text-ink-800 dark:text-white">Income vs Expense</h2>
          {trend?.series?.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trend.series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eceef2" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="income" stroke="#22b072" strokeWidth={2} />
                <Line type="monotone" dataKey="expense" stroke="#e05252" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState />
          )}
        </div>

        <div className="card p-6">
          <h2 className="mb-4 font-semibold text-ink-800 dark:text-white">Spending by Category</h2>
          {categoryBreakdown?.categories?.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={categoryBreakdown.categories} dataKey="amount" nameKey="category_id" innerRadius={60} outerRadius={90}>
                  {categoryBreakdown.categories.map((_: unknown, i: number) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState />
          )}
        </div>
      </div>

      {/* Insights */}
      {insights && (insights.highest_spending_category || insights.average_daily_expense > 0) && (
        <div className="card p-6">
          <h2 className="mb-4 font-semibold text-ink-800 dark:text-white">Financial Insights</h2>
          <ul className="space-y-2 text-sm text-ink-600 dark:text-ink-300">
            {insights.highest_spending_category && (
              <li>Your highest spending category this month is <strong>{insights.highest_spending_category}</strong>, at ₹{insights.highest_spending_category_amount?.toLocaleString()}.</li>
            )}
            <li>Your average daily expense this month is ₹{insights.average_daily_expense?.toLocaleString()}.</li>
            {insights.month_over_month_change_percent !== null && (
              <li>Spending is {insights.month_over_month_change_percent >= 0 ? 'up' : 'down'} {Math.abs(insights.month_over_month_change_percent).toFixed(1)}% compared to last month.</li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}

function SummaryCard({ icon: Icon, label, value, tone }: { icon: typeof Wallet; label: string; value: number; tone: string }) {
  const toneClasses: Record<string, string> = {
    brand: 'bg-brand-50 text-brand-600 dark:bg-brand-900/40',
    green: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/40',
    red: 'bg-red-50 text-red-600 dark:bg-red-900/40',
    blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/40',
  }
  return (
    <div className="card p-5">
      <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${toneClasses[tone]}`}>
        <Icon className="h-4.5 w-4.5" />
      </div>
      <p className="mt-3 text-xs font-medium text-ink-400">{label}</p>
      <p className="mt-1 text-xl font-bold text-ink-800 dark:text-white">₹{value.toLocaleString()}</p>
    </div>
  )
}

function ForecastStat({ label, value }: { label: string; value: number | null | undefined }) {
  return (
    <div>
      <p className="text-xs text-ink-400">{label}</p>
      <p className="mt-1 text-lg font-semibold text-ink-800 dark:text-white">
        {value != null ? `₹${value.toLocaleString()}` : '—'}
      </p>
    </div>
  )
}

function ConfidenceBadge({ level }: { level?: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    insufficient_data: { label: 'Not enough data', cls: 'bg-ink-100 text-ink-500' },
    low_confidence: { label: 'Low confidence', cls: 'bg-amber-100 text-amber-700' },
    personalized: { label: 'Personalized', cls: 'bg-brand-100 text-brand-700' },
  }
  const info = map[level ?? 'insufficient_data']
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${info.cls}`}>{info.label}</span>
}

function EmptyChartState() {
  return (
    <div className="flex h-64 items-center justify-center text-sm text-ink-400">
      No data yet for this period.
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-40 rounded bg-ink-100 dark:bg-ink-800" />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-28 rounded-2xl bg-ink-100 dark:bg-ink-800" />)}
      </div>
      <div className="h-48 rounded-2xl bg-ink-100 dark:bg-ink-800" />
    </div>
  )
}
