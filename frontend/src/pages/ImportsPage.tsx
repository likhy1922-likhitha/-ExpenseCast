import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, CheckCircle2, AlertCircle } from 'lucide-react'
import { confirmCsvImport, uploadCsv } from '@/services/api'

export function ImportsPage() {
  const [preview, setPreview] = useState<any>(null)
  const [summary, setSummary] = useState<any>(null)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: uploadCsv,
    onSuccess: (data) => setPreview(data),
  })

  const confirmMutation = useMutation({
    mutationFn: () => confirmCsvImport({
      imported_file_id: preview.imported_file_id,
      mapping: preview.suggested_mapping,
      row_numbers_to_import: preview.preview_rows.filter((r: any) => r.is_valid && !r.is_duplicate).map((r: any) => r.row_number),
    }),
    onSuccess: (data) => {
      setSummary(data)
      setPreview(null)
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
    },
  })

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSummary(null)
      uploadMutation.mutate(file)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-ink-900 dark:text-white">Import Centre</h1>
      <p className="text-sm text-ink-500 dark:text-ink-300">
        Upload a bank statement CSV in any format — ExpenseCast will detect the columns automatically.
      </p>

      {!preview && !summary && (
        <label className="card flex cursor-pointer flex-col items-center justify-center gap-3 p-12 text-center hover:bg-ink-50 dark:hover:bg-ink-900/40">
          <Upload className="h-8 w-8 text-ink-300" />
          <span className="text-sm font-medium text-ink-600 dark:text-ink-300">
            {uploadMutation.isPending ? 'Uploading…' : 'Click to select a CSV file'}
          </span>
          <input type="file" accept=".csv" className="hidden" onChange={handleFile} />
        </label>
      )}

      {uploadMutation.isError && (
        <p className="text-sm text-red-600 flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Could not process this file. Please check the format and try again.</p>
      )}

      {preview && (
        <div className="card p-6 space-y-4">
          <div className="flex flex-wrap gap-4 text-sm">
            <span>Total rows: <strong>{preview.total_rows}</strong></span>
            <span className="text-emerald-600">Valid: <strong>{preview.valid_rows}</strong></span>
            <span className="text-red-600">Invalid: <strong>{preview.invalid_rows}</strong></span>
            <span className="text-amber-600">Duplicates: <strong>{preview.duplicate_rows}</strong></span>
          </div>
          <div className="max-h-80 overflow-auto rounded-xl border border-ink-100 dark:border-ink-700">
            <table className="w-full text-xs">
              <thead className="bg-ink-50 dark:bg-ink-900 sticky top-0">
                <tr><th className="px-3 py-2 text-left">Date</th><th className="px-3 py-2 text-left">Amount</th><th className="px-3 py-2 text-left">Type</th><th className="px-3 py-2 text-left">Category</th><th className="px-3 py-2 text-left">Status</th></tr>
              </thead>
              <tbody className="divide-y divide-ink-100 dark:divide-ink-700">
                {preview.preview_rows.map((r: any) => (
                  <tr key={r.row_number} className={!r.is_valid ? 'bg-red-50 dark:bg-red-900/20' : r.is_duplicate ? 'bg-amber-50 dark:bg-amber-900/20' : ''}>
                    <td className="px-3 py-2">{r.parsed_date ?? '—'}</td>
                    <td className="px-3 py-2">{r.parsed_amount ?? '—'}</td>
                    <td className="px-3 py-2 capitalize">{r.parsed_type ?? '—'}</td>
                    <td className="px-3 py-2">{r.suggested_category ?? 'Uncategorized'}</td>
                    <td className="px-3 py-2">{!r.is_valid ? 'Invalid' : r.is_duplicate ? 'Duplicate' : 'Ready'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setPreview(null)} className="btn-secondary flex-1">Cancel</button>
            <button onClick={() => confirmMutation.mutate()} disabled={confirmMutation.isPending} className="btn-primary flex-1">
              {confirmMutation.isPending ? 'Importing…' : `Import ${preview.valid_rows - preview.duplicate_rows} Transactions`}
            </button>
          </div>
        </div>
      )}

      {summary && (
        <div className="card p-6 flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-ink-800 dark:text-white">Import complete</p>
            <p className="text-sm text-ink-500 mt-1">
              Imported {summary.imported_rows} transactions. Skipped {summary.skipped_duplicate_rows} duplicates and {summary.invalid_rows} invalid rows.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
