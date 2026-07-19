import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { SignInPage } from '@/pages/SignInPage'

const signInMock = vi.fn().mockResolvedValue({ error: null })

vi.mock('@/features/authentication/AuthContext', () => ({
  useAuth: () => ({
    signIn: signInMock,
    signInWithGoogle: vi.fn(),
  }),
}))

describe('SignInPage', () => {
  it('renders email and password fields', () => {
    render(<MemoryRouter><SignInPage /></MemoryRouter>)
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('calls signIn with entered credentials on submit', async () => {
    render(<MemoryRouter><SignInPage /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    expect(signInMock).toHaveBeenCalledWith('user@test.com', 'password123')
  })
})
