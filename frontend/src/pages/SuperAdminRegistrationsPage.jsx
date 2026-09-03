import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { getRegistrations, reviewRegistration } from '../services/authService'

function getPayloadObject(row) {
  if (row?.payload_data && typeof row.payload_data === 'object') {
    return row.payload_data
  }
  if (row?.payload && typeof row.payload === 'object') {
    return row.payload
  }
  if (typeof row?.payload === 'string') {
    try {
      return JSON.parse(row.payload)
    } catch {
      return {}
    }
  }
  return {}
}

function downloadPdf(base64Data, fileName) {
  try {
    const byteChars = atob(base64Data)
    const byteNumbers = new Uint8Array(byteChars.length)
    for (let i = 0; i < byteChars.length; i++) {
      byteNumbers[i] = byteChars.charCodeAt(i)
    }
    const blob = new Blob([byteNumbers], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName || 'document.pdf'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.error('Impossible de télécharger le document.')
  }
}

function PdfButton({ doc, label }) {
  if (!doc?.data) {
    return <span className="text-xs text-slate-400 italic">Non fourni</span>
  }
  return (
    <button
      type="button"
      onClick={() => downloadPdf(doc.data, doc.name || `${label}.pdf`)}
      className="inline-flex items-center gap-1 rounded border border-slate-300 bg-slate-50 px-2 py-1 text-xs text-slate-700 hover:bg-slate-100 transition"
    >
      📄 {label}
    </button>
  )
}

function SuperAdminRegistrationsPage() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [reviewingId, setReviewingId] = useState(null)

  const fetchRows = async () => {
    setLoading(true)
    try {
      const response = await getRegistrations({ status: 'pending' })
      setRows(response.data?.registrations || [])
    } catch (error) {
      toast.error(error.response?.data?.error || 'Impossible de charger les inscriptions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRows()
  }, [])

  const onReview = async (id, action) => {
    setReviewingId(id)
    try {
      await reviewRegistration(id, { action })
      toast.success(action === 'approve' ? 'Inscription approuvée' : 'Inscription rejetée')
      setRows((prev) => prev.filter((item) => item.id !== id))
    } catch (error) {
      toast.error(error.response?.data?.error || 'Échec traitement inscription')
    } finally {
      setReviewingId(null)
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
      <h3 className="text-lg font-semibold text-slate-800">Validation inscriptions usines</h3>

      {loading && <p className="text-slate-500">Chargement...</p>}
      {!loading && rows.length === 0 && <p className="text-slate-500">Aucune inscription en attente.</p>}

      {!loading && rows.length > 0 && (
        <div className="overflow-auto">
          <table className="w-full min-w-[860px] text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="py-2 pr-3">Usine</th>
                <th className="py-2 pr-3">Contact</th>
                <th className="py-2 pr-3">Administrateur</th>
                <th className="py-2 pr-3">Documents</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 align-top">
                  {(() => {
                    const payload = getPayloadObject(row)
                    return (
                      <>
                  <td className="py-3 pr-3 font-medium text-slate-800">{row.plant_name}</td>
                  <td className="py-3 pr-3 text-slate-700">
                    <p>{row.contact_name}</p>
                    <span className="text-xs text-slate-500">{row.contact_email}</span>
                  </td>
                  <td className="py-3 pr-3 text-slate-700">
                    <p>{payload?.users?.admin?.name || '-'}</p>
                    <span className="text-xs text-slate-500">{payload?.users?.admin?.email || ''}</span>
                  </td>
                  <td className="py-3 pr-3">
                    <div className="flex flex-col gap-1.5">
                      <PdfButton doc={payload?.documents?.patente} label="Patente" />
                      <PdfButton doc={payload?.documents?.rne} label="RNE" />
                    </div>
                  </td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onReview(row.id, 'approve')}
                        disabled={reviewingId === row.id}
                        className="rounded bg-[#16a34a] px-3 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-60"
                      >
                        Approuver
                      </button>
                      <button
                        type="button"
                        onClick={() => onReview(row.id, 'reject')}
                        disabled={reviewingId === row.id}
                        className="rounded bg-red-600 px-3 py-1 text-xs text-white hover:bg-red-700 disabled:opacity-60"
                      >
                        Rejeter
                      </button>
                    </div>
                  </td>
                      </>
                    )
                  })()}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default SuperAdminRegistrationsPage
