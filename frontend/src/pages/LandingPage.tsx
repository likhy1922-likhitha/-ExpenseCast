import { Link } from 'react-router-dom'
import {
  TrendingUp, ShieldCheck, Upload, BrainCircuit, PiggyBank, Users, ArrowRight,
} from 'lucide-react'
import { useAuth } from '@/features/authentication/AuthContext'

const DEMO_MODE_ENABLED = import.meta.env.VITE_ENABLE_DEMO_MODE === 'true'

export function LandingPage() {
  const { activateDemoMode } = useAuth()

  return (
    <div className="min-h-screen bg-white dark:bg-ink-900">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <img src="/logo.svg" alt="ExpenseCast" className="h-9 w-9" />
          <span className="text-xl font-bold text-ink-800 dark:text-white">ExpenseCast</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/sign-in" className="btn-secondary">Sign In</Link>
          <Link to="/sign-up" className="btn-primary">Sign Up</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-4xl px-6 py-20 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-ink-900 dark:text-white sm:text-5xl">
          Know where your money is going —{' '}
          <span className="text-brand-600">before it's gone.</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-ink-500 dark:text-ink-300">
          ExpenseCast tracks your income, expenses, budgets and savings goals, then uses a
          deep-learning LSTM model to forecast your future spending — so you can plan ahead,
          not just look back.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/sign-up" className="btn-primary text-base px-6 py-3">
            Get Started Free <ArrowRight className="h-4 w-4" />
          </Link>
          {DEMO_MODE_ENABLED && (
            <button
              onClick={() => activateDemoMode()}
              className="btn-secondary text-base px-6 py-3"
            >
              Try Demo
            </button>
          )}
        </div>
      </section>

      {/* Feature grid */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <FeatureCard icon={ArrowRight} title="Effortless Tracking" desc="Log income, expenses, savings and investments in seconds, with smart auto-categorization." />
          <FeatureCard icon={Upload} title="Flexible Imports" desc="Upload any bank CSV or PDF statement — ExpenseCast auto-detects columns and formats." />
          <FeatureCard icon={BrainCircuit} title="LSTM Forecasting" desc="A trained deep-learning model predicts your 7, 30 and 90-day expenses from your own history." />
          <FeatureCard icon={PiggyBank} title="Budgets & Goals" desc="Set category budgets with 50/75/90/100% warnings and track savings goals to completion." />
          <FeatureCard icon={TrendingUp} title="Investment Tracking" desc="Track SIPs, mutual funds, FDs and stocks alongside your everyday spending." />
          <FeatureCard icon={ShieldCheck} title="Private by Design" desc="Row-level security means only you can ever see your financial data." />
        </div>
      </section>

      {/* How LSTM works */}
      <section className="bg-ink-50 dark:bg-ink-800/40 py-16">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-2xl font-bold text-ink-900 dark:text-white">How the forecasting works</h2>
          <p className="mx-auto mt-3 max-w-2xl text-ink-500 dark:text-ink-300">
            ExpenseCast trains a Long Short-Term Memory (LSTM) neural network on daily spending
            patterns — day of week, rolling averages, recurring bills and more — to learn how
            your spending evolves over time. Once you have at least 30 days of transaction
            history, it starts forecasting; after 60 days, forecasts become fully personalized.
            Every prediction is clearly labelled as an estimate, never a guarantee.
          </p>
        </div>
      </section>

      {/* Target users */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-center text-2xl font-bold text-ink-900 dark:text-white">Built for real budgets</h2>
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {['Students', 'Salaried Employees', 'Freelancers', 'Teenagers'].map((t) => (
            <div key={t} className="card p-6 text-center">
              <Users className="mx-auto h-6 w-6 text-brand-600" />
              <p className="mt-3 font-semibold text-ink-800 dark:text-white">{t}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-ink-100 dark:border-ink-800 py-8 text-center text-sm text-ink-400">
        ExpenseCast — Intelligent Expense Tracking and Financial Forecasting Using Deep Learning-Based LSTM.
        <br />Forecasts are statistical estimates, not financial advice.
      </footer>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, desc }: { icon: typeof ArrowRight; title: string; desc: string }) {
  return (
    <div className="card p-6">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-900/40">
        <Icon className="h-5 w-5 text-brand-600" />
      </div>
      <h3 className="mt-4 font-semibold text-ink-800 dark:text-white">{title}</h3>
      <p className="mt-1.5 text-sm text-ink-500 dark:text-ink-300">{desc}</p>
    </div>
  )
}
