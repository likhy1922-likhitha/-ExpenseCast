import axios from 'axios'
import { supabase } from '@/lib/supabaseClient'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Session expired or invalid -- surface to the auth layer to redirect to sign-in.
      window.dispatchEvent(new CustomEvent('expensecast:unauthorized'))
    }
    return Promise.reject(error)
  }
)
