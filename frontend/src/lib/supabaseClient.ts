import { createClient } from '@supabase/supabase-js'

const rawSupabaseUrl =
  (import.meta.env.VITE_SUPABASE_URL as string | undefined)?.trim() ?? ''

const supabaseUrl = rawSupabaseUrl
  .replace(/^.*?VITE_SUPABASE_URL=/, '')
  .replace(/^.*?BASE_URL=/, '')
  .replace(/^["']|["']$/g, '')
  .trim()

const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    'VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY are not set.'
  )
}

export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder'
)