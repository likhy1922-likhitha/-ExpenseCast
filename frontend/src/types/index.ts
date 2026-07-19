export type TransactionType = 'income' | 'expense' | 'savings' | 'investment'

export interface Transaction {
  transaction_id: string
  user_id: string
  account_id: string | null
  date: string
  time: string | null
  transaction_type: TransactionType
  amount: number
  currency: string
  category_id: string | null
  description: string | null
  merchant: string | null
  payment_method: string | null
  tags: string | null
  is_recurring: boolean
  source: string
  created_at: string
  updated_at: string
}

export interface PaginatedTransactions {
  items: Transaction[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Category {
  id: string
  user_id: string | null
  name: string
  category_type: 'income' | 'expense' | 'transfer'
  icon: string | null
  color: string | null
  is_default: boolean
}

export interface Budget {
  id: string
  user_id: string
  category_id: string | null
  name: string
  period_month: number
  period_year: number
  limit_amount: number
}

export interface BudgetProgress {
  budget: Budget
  spent_amount: number
  remaining_amount: number
  percent_used: number
  warning_level: '50' | '75' | '90' | '100' | null
}

export interface SavingsGoal {
  goal_id: string
  user_id: string
  goal_name: string
  target_amount: number
  current_amount: number
  target_date: string | null
  monthly_required_amount: number | null
  status: 'active' | 'completed' | 'abandoned'
}

export interface Investment {
  id: string
  user_id: string
  investment_name: string
  investment_type: string
  amount_invested: number
  investment_date: string
  current_value: number | null
  expected_return_percent: number | null
  notes: string | null
}

export interface DashboardSummary {
  date_range: { start: string; end: string }
  current_balance: number
  total_income: number
  total_expenses: number
  total_savings: number
  total_investments: number
  remaining_budget: number
  savings_rate: number
  predicted_7_day_expense: number | null
  predicted_30_day_expense: number | null
  predicted_end_of_month_balance: number | null
  overspending_risk: 'low' | 'medium' | 'high' | null
  forecast_confidence: 'insufficient_data' | 'low_confidence' | 'personalized'
}

export interface ForecastResult {
  confidence_level: 'insufficient_data' | 'low_confidence' | 'personalized'
  history_days_available: number
  predicted_next_1_day: number | null
  predicted_next_7_days: number | null
  predicted_next_30_days: number | null
  predicted_next_90_days: number | null
  predicted_end_of_month_expense: number | null
  predicted_end_of_month_balance: number | null
  overspending_risk: 'low' | 'medium' | 'high' | null
  generated_at: string
  is_estimate_disclaimer: string
}

export interface UserProfile {
  user_id: string
  user_type: 'student' | 'teenager' | 'salaried' | 'freelancer' | 'other'
  preferred_currency: string
  approx_monthly_income: number | null
  budget_start_day: number
  savings_target: number | null
  preferred_categories: string | null
  onboarding_completed: boolean
  theme: 'light' | 'dark'
}
