import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Info } from 'lucide-react'
import { getLatestForecast, getModelStatus } from '@/services/api'

export function ForecastPage() {
  const { data: forecast, isLoading } = useQuery({ queryKey: ['forecast-latest'], queryFn: getLatestForecast })
  const { data: modelStatus } = useQuery({ queryKey: ['model-status'], queryFn: getModelStatus })

  if (isLoading) return <div className="text-sm text-ink-400">Loading forecast…</div>

  const insufficient = forecast?.confidence_level === 'insufficient_data'

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Expense Forecast</h1>

      <div className="rounded-xl bg-blue-50 dark:bg-blue-900/30 px-4 py-3 text-sm text-blue-700 dark:text-blue-300 flex items-start gap-2">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>{forecast?.is_estimate_disclaimer ?? 'Forecasts are statistical estimates based on your transaction history and are not financial advice.'}</span>
      </div>

      {insufficient ? (
        <div className="card p-8 text-center">
          <p className="text-ink-600 dark:text-ink-300">
            You have {forecast?.history_days_available ?? 0} day(s) of transaction history.
            ExpenseCast needs at least <strong>30 days</strong> to generate an early forecast, and
            <strong> 60 days</strong> for a fully personalized one.
          </p>
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <ForecastCard label="Next Day" value={forecast?.predicted_next_1_day} />
            <ForecastCard label="Next 7 Days" value={forecast?.predicted_next_7_days} />
            <ForecastCard label="Next 30 Days" value={forecast?.predicted_next_30_days} />
            <ForecastCard label="Next 90 Days" value={forecast?.predicted_next_90_days} />
          </div>

          {forecast?.overspending_risk === 'high' && (
            <div className="card p-5 flex items-center gap-3 border-red-200 dark:border-red-800">
              <AlertTriangle className="h-5 w-5 text-red-600 shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-300">
                Your predicted spending is trending above your set budgets for this period.
              </p>
            </div>
          )}
        </>
      )}

      {modelStatus?.model_available && (
        <div className="card p-6">
          <h2 className="font-semibold text-ink-800 dark:text-white">Model Status</h2>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div><dt className="text-ink-400">Lookback window</dt><dd className="font-medium text-ink-700 dark:text-ink-200">{modelStatus.lookback_days} days</dd></div>
            <div><dt className="text-ink-400">Test MAE</dt><dd className="font-medium text-ink-700 dark:text-ink-200">₹{modelStatus.test_mae?.toFixed(0)}</dd></div>
            <div><dt className="text-ink-400">Test RMSE</dt><dd className="font-medium text-ink-700 dark:text-ink-200">₹{modelStatus.test_rmse?.toFixed(0)}</dd></div>
            <div><dt className="text-ink-400">Test MAPE</dt><dd className="font-medium text-ink-700 dark:text-ink-200">{modelStatus.test_mape?.toFixed(1)}%</dd></div>
          </dl>
          <p className="mt-3 text-xs text-ink-400">Model last trained: {modelStatus.trained_at ? new Date(modelStatus.trained_at).toLocaleString() : 'unknown'}</p>
        </div>
      )}
    </div>
  )
}

function ForecastCard({ label, value }: { label: string; value?: number | null }) {
  return (
    <div className="card p-5">
      <p className="text-xs font-medium text-ink-400">{label}</p>
      <p className="mt-1 text-xl font-bold text-ink-800 dark:text-white">
        {value != null ? `₹${value.toLocaleString()}` : '—'}
      </p>
    </div>
  )
}
