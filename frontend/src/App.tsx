import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ResetPasswordPage } from '@/pages/ResetPasswordPage'
import { ForgotPasswordPage } from '@/pages/ForgotPasswordPage'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/features/authentication/AuthContext'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import { AppLayout } from '@/layouts/AppLayout'
import { LandingPage } from '@/pages/LandingPage'
import { SignInPage } from '@/pages/SignInPage'
import { SignUpPage } from '@/pages/SignUpPage'
import { OnboardingPage } from '@/pages/OnboardingPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { TransactionsPage } from '@/pages/TransactionsPage'
import { ImportsPage } from '@/pages/ImportsPage'
import { BudgetsPage } from '@/pages/BudgetsPage'
import { GoalsPage } from '@/pages/GoalsPage'
import { InvestmentsPage } from '@/pages/InvestmentsPage'
import { ForecastPage } from '@/pages/ForecastPage'
import { ReportsPage } from '@/pages/ReportsPage'
import { SettingsPage } from '@/pages/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/sign-in" element={<SignInPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/sign-up" element={<SignUpPage />} />
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <OnboardingPage />
                </ProtectedRoute>
              }
            />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/imports" element={<ImportsPage />} />
              <Route path="/budgets" element={<BudgetsPage />} />
              <Route path="/goals" element={<GoalsPage />} />
              <Route path="/investments" element={<InvestmentsPage />} />
              <Route path="/forecasts" element={<ForecastPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
