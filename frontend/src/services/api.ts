import { api } from '@/lib/apiClient'
import type {
  Budget, BudgetProgress, Category, DashboardSummary, ForecastResult,
  Investment, PaginatedTransactions, SavingsGoal, Transaction, UserProfile,
} from '@/types'

// --- Profile ---
export const getProfile = () => api.get<UserProfile>('/api/profile').then((r) => r.data)
export const createProfile = (payload: Partial<UserProfile> & { full_name: string; user_type: string }) =>
  api.post<UserProfile>('/api/profile', payload).then((r) => r.data)

// --- Dashboard ---
export const getDashboardSummary = (dateRange: string) =>
  api.get<DashboardSummary>('/api/dashboard/summary', { params: { date_range: dateRange } }).then((r) => r.data)
export const getIncomeVsExpenseTrend = (dateRange: string) =>
  api.get('/api/dashboard/charts/income-vs-expense', { params: { date_range: dateRange } }).then((r) => r.data)
export const getCategoryBreakdown = (dateRange: string) =>
  api.get('/api/dashboard/charts/category-breakdown', { params: { date_range: dateRange } }).then((r) => r.data)
export const getUpcomingRecurring = () => api.get('/api/dashboard/upcoming-recurring').then((r) => r.data)
export const getInsights = () => api.get('/api/dashboard/insights').then((r) => r.data)

// --- Transactions ---
export const listTransactions = (params: Record<string, unknown>) =>
  api.get<PaginatedTransactions>('/api/transactions', { params }).then((r) => r.data)
export const createTransaction = (payload: Partial<Transaction>) =>
  api.post<Transaction>('/api/transactions', payload).then((r) => r.data)
export const updateTransaction = (id: string, payload: Partial<Transaction>) =>
  api.put<Transaction>(`/api/transactions/${id}`, payload).then((r) => r.data)
export const deleteTransaction = (id: string) => api.delete(`/api/transactions/${id}`)

// --- Categories ---
export const listCategories = () => api.get<Category[]>('/api/categories').then((r) => r.data)

// --- Budgets ---
export const listBudgets = (month: number, year: number) =>
  api.get<Budget[]>('/api/budgets', { params: { period_month: month, period_year: year } }).then((r) => r.data)
export const createBudget = (payload: Partial<Budget>) => api.post<Budget>('/api/budgets', payload).then((r) => r.data)
export const getBudgetProgress = (id: string) => api.get<BudgetProgress>(`/api/budgets/${id}/progress`).then((r) => r.data)

// --- Goals ---
export const listGoals = () => api.get<SavingsGoal[]>('/api/goals').then((r) => r.data)
export const createGoal = (payload: Partial<SavingsGoal>) => api.post<SavingsGoal>('/api/goals', payload).then((r) => r.data)
export const addGoalContribution = (goalId: string, amount: number, date: string) =>
  api.post(`/api/goals/${goalId}/contributions`, { amount, contribution_date: date })

// --- Investments ---
export const listInvestments = () => api.get<Investment[]>('/api/investments').then((r) => r.data)
export const createInvestment = (payload: Partial<Investment>) =>
  api.post<Investment>('/api/investments', payload).then((r) => r.data)

// --- Forecasts ---
export const generateForecast = () => api.post<ForecastResult>('/api/forecasts/generate').then((r) => r.data)
export const getLatestForecast = () => api.get<ForecastResult>('/api/forecasts/latest').then((r) => r.data)
export const getModelStatus = () => api.get('/api/forecasts/model-status').then((r) => r.data)

// --- Imports ---
export const uploadCsv = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/api/imports/csv/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then((r) => r.data)
}
export const confirmCsvImport = (payload: unknown) => api.post('/api/imports/csv/confirm', payload).then((r) => r.data)
