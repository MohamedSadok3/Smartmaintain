import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { deletePlant, getPlantOverview, getPlants } from '../services/authService'

function SuperAdminPlantsPage() {
  const [rows, setRows] = useState([])
  const [detailsByPlant, setDetailsByPlant] = useState({})
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState(null)

  const fetchPlants = async () => {
    setLoading(true)
    try {
      const response = await getPlants()
      const plants = response.data?.plants || []
      setRows(plants)

      const detailsEntries = await Promise.all(
        plants.map(async (plant) => {
          try {
            const detailResponse = await getPlantOverview(plant.id)
            return [plant.id, detailResponse.data]
          } catch {
            return [plant.id, null]
          }
        }),
      )
      setDetailsByPlant(Object.fromEntries(detailsEntries))
    } catch (error) {
      toast.error(error.response?.data?.error || 'Impossible de charger les usines')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPlants()
  }, [])

  const onDelete = async (row) => {
    const confirmDelete = window.confirm(
      `Supprimer l'usine "${row.name}" ? Cette action supprimera aussi ses utilisateurs, composants et alertes.`,
    )
    if (!confirmDelete) return

    setDeletingId(row.id)
    try {
      await deletePlant(row.id)
      setRows((prev) => prev.filter((item) => item.id !== row.id))
      setDetailsByPlant((prev) => {
        const next = { ...prev }
        delete next[row.id]
        return next
      })
      toast.success('Usine supprimée avec succès')
    } catch (error) {
      toast.error(error.response?.data?.error || "Echec suppression de l'usine")
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
      <h3 className="text-lg font-semibold text-slate-800">Usines (consultation + suppression)</h3>
      {loading && <p className="text-slate-500">Chargement...</p>}

      {!loading && (
        <div className="space-y-4">
          {rows.map((row) => (
            <div key={row.id} className="rounded-xl border border-slate-200 p-4 space-y-3">
              <div className="grid md:grid-cols-4 gap-3 text-sm">
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                    <p className="text-xs text-slate-500">Nom de l'usine</p>
                  <p className="font-medium text-slate-800">{row.name || '-'}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-xs text-slate-500">Code</p>
                  <p className="font-medium text-slate-800">{row.code || '-'}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-xs text-slate-500">Statut</p>
                  <p className="font-medium text-slate-800">{row.status || '-'}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-xs text-slate-500">Secteur</p>
                  <p className="font-medium text-slate-800">{row.industry || '-'}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-xs text-slate-500">Localisation</p>
                  <p className="font-medium text-slate-800">{row.location || '-'}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-xs text-slate-500">Contact</p>
                  <p className="font-medium text-slate-800">{row.contact_name || '-'}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-xs text-slate-500">Email contact</p>
                  <p className="font-medium text-slate-800">{row.contact_email || '-'}</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-xs text-slate-500">Telephone</p>
                  <p className="font-medium text-slate-800">{row.contact_phone || '-'}</p>
                </div>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                <p className="text-xs text-slate-500">Description</p>
                <p className="text-sm text-slate-800">{row.description || '-'}</p>
              </div>

              {detailsByPlant[row.id]?.kpis && (
                <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-2">
                  <div className="rounded-lg border border-slate-200 px-3 py-2">
                    <p className="text-xs text-slate-500">Utilisateurs</p>
                    <p className="font-semibold text-slate-800">{detailsByPlant[row.id].kpis.users_count}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 px-3 py-2">
                    <p className="text-xs text-slate-500">Composants</p>
                    <p className="font-semibold text-slate-800">{detailsByPlant[row.id].kpis.components_count}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 px-3 py-2">
                    <p className="text-xs text-slate-500">Alertes ouvertes</p>
                    <p className="font-semibold text-slate-800">{detailsByPlant[row.id].kpis.open_alerts}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 px-3 py-2">
                    <p className="text-xs text-slate-500">Alertes resolues</p>
                    <p className="font-semibold text-slate-800">{detailsByPlant[row.id].kpis.resolved_alerts}</p>
                  </div>
                </div>
              )}

              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-sm font-medium text-slate-800 mb-2">Utilisateurs de l'usine</p>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-500 border-b border-slate-200">
                        <th className="py-1 pr-3">Nom</th>
                        <th className="py-1 pr-3">Email</th>
                        <th className="py-1 pr-3">Role</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(detailsByPlant[row.id]?.users || []).map((user) => (
                        <tr key={user.id} className="border-b border-slate-100">
                          <td className="py-1 pr-3 text-slate-700">{user.name}</td>
                          <td className="py-1 pr-3 text-slate-700">{user.email}</td>
                          <td className="py-1 pr-3 text-slate-700">{user.role}</td>
                        </tr>
                      ))}
                      {(detailsByPlant[row.id]?.users || []).length === 0 && (
                        <tr>
                          <td colSpan={3} className="py-2 text-slate-500">
                            Aucun utilisateur trouve.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <button
                type="button"
                onClick={() => onDelete(row)}
                disabled={deletingId === row.id}
                className="rounded bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-60"
              >
                {deletingId === row.id ? 'Suppression en cours...' : "Supprimer l'usine"}
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default SuperAdminPlantsPage
