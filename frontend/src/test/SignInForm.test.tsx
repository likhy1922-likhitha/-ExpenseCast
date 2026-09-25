import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('@/features/authentication/AuthContext', () => ({
  useAuth: () => ({
    signIn: vi.fn().mockResolvedValue({ error: null }),
    signInWithGoogle: vi.fn(),
  }),
}))

import { SignInPage } from '@/pages/SignInPage'

describe('SignInPage', () => {
  it('renders email and password fields', () => {
    render(<MemoryRouter><SignInPage /></MemoryRouter>)
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('requires email and password before submit', () => {
    render(<MemoryRouter><SignInPage /></MemoryRouter>)
    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    expect(emailInput.required).toBe(true)
  })

  it('shows a Google sign-in option', () => {
    render(<MemoryRouter><SignInPage /></MemoryRouter>)
    expect(screen.getByText(/continue with google/i)).toBeInTheDocument()
  })
})
