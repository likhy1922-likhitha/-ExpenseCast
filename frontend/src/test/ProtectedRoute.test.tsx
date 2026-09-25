import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

vi.mock('@/features/authentication/AuthContext', () => ({
  useAuth: () => ({ session: null, isLoading: false }),
}))

import { ProtectedRoute } from '@/routes/ProtectedRoute'

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users away from protected content', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/sign-in" element={<div>Sign In Page</div>} />
          <Route path="/dashboard" element={<ProtectedRoute><div>Secret Dashboard</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.getByText('Sign In Page')).toBeInTheDocument()
    expect(screen.queryByText('Secret Dashboard')).not.toBeInTheDocument()
  })
})
