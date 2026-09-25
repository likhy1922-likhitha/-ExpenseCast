import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardPage } from '@/pages/DashboardPage'

vi.mock('@/services/api', () => ({
  getDashboardSummary: vi.fn().mockResolvedValue({
    date_range: { start: '2026-07-01', end: '2026-07-18' },
    current_balance: 0, total_income: 0, total_expenses: 0, total_savings: 0,
    total_investments: 0, remaining_budget: 0, savings_rate: 0,
    predicted_7_day_expense: null, predicted_30_day_expense: null,
    predicted_end_of_month_balance: null, overspending_risk: null,
    forecast_confidence: 'insufficient_data',
  }),
  getIncomeVsExpenseTrend: vi.fn().mockResolvedValue({ series: [] }),
  getCategoryBreakdown: vi.fn().mockResolvedValue({ categories: [] }),
  getInsights: vi.fn().mockResolvedValue({ highest_spending_category: null, average_daily_expense: 0, month_over_month_change_percent: null }),
}))

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('DashboardPage', () => {
  it('shows the empty state for a brand-new account', async () => {
    renderWithClient(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText(/welcome to expensecast/i)).toBeInTheDocument()
    })
  })
})
