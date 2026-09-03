import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import {
  createComponent,
  deleteComponent,
  getComponents,
  updateComponent,
} from '../services/componentService'
import { MACHINE_OPTIONS } from '../constants/machines'

function emptyForm() {
  return { name: '', type: 'moteur', enabled: true }
}

function ComposantsPage() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)

  const sortedRows = useMemo(() => [...rows].sort((a, b) => a.id - b.id), [rows])

  const fetchComponents = async () => {
    setLoading(true)
    try {
      const response = await getComponents()
      setRows(response.data.components || [])
    } catch (error) {
      toast.error(error.response?.data?.error || 'Impossible de charger les composants')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchComponents()
  }, [])

  const resetForm = () => {
    setEditingId(null)
    setForm(emptyForm())
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    if (!form.name.trim() || !form.type) {
      toast.error('Nom et type sont requis')
      return
    }

    const payload = {
      name: form.name.trim(),
      type: form.type,
      enabled: Boolean(form.enabled),
    }

    try {
      if (editingId) {
        const response = await updateComponent(editingId, payload)
        setRows((prev) => prev.map((item) => (item.id === editingId ? response.data.component : item)))
        toast.success('Composant mis a jour')
      } else {
        const response = await createComponent(payload)
        setRows((prev) => [...prev, response.data.component])
        toast.success('Composant ajoute')
      }
      resetForm()
    } catch (error) {
      toast.error(error.response?.data?.error || 'Operation impossible')
    }
  }

  const startEdit = (row) => {
    setEditingId(row.id)
    setForm({ name: row.name, type: row.type || 'moteur', enabled: row.enabled })
  }

  const onDelete = async (row) => {
    const confirmed = window.confirm(`Supprimer le composant ${row.name} ?`)
    if (!confirmed) return

    try {
      await deleteComponent(row.id)
      setRows((prev) => prev.filter((item) => item.id !== row.id))
      if (editingId === row.id) {
        resetForm()
      }
      toast.success('Composant supprime')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Suppression impossible')
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-5 sm:p-5">
      <header className="space-y-1">
        <h3 className="text-lg font-semibold text-slate-800">Gestion des composants</h3>
        <p className="text-sm text-slate-500">
          Ajouter, modifier, activer ou supprimer les composants machine du systeme.
        </p>
      </header>

      <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
        <label className="space-y-1 md:col-span-2">
          <span className="text-sm text-slate-700">Nom affichage</span>
          <input
            value={form.name}
            onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            placeholder="ex: Moteur principal A"
          />
        </label>
        <label className="space-y-1">
          <span className="text-sm text-slate-700">Type de composant</span>
          <select
            value={form.type}
            onChange={(event) => setForm((prev) => ({ ...prev, type: event.target.value }))}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          >
            {MACHINE_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="inline-flex items-center gap-2 text-sm text-slate-700 pb-2">
          <input
            type="checkbox"
            checked={form.enabled}
            onChange={(event) => setForm((prev) => ({ ...prev, enabled: event.target.checked }))}
          />
          Actif
        </label>

        <div className="md:col-span-4 flex items-center gap-2">
          <button
            type="submit"
            className="rounded-lg bg-[#16a34a] px-4 py-2 text-sm text-white hover:bg-green-700"
          >
            {editingId ? 'Enregistrer' : 'Ajouter'}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
            >
              Annuler
            </button>
          )}
        </div>
      </form>

      <div className="overflow-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b border-slate-200">
              <th className="py-2">ID</th>
              <th className="py-2">Key</th>
              <th className="py-2">Nom</th>
              <th className="py-2">Type</th>
              <th className="py-2">Etat</th>
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="py-4 text-slate-500">
                  Chargement...
                </td>
              </tr>
            )}
            {!loading &&
              sortedRows.map((row) => (
                <tr key={row.id} className="border-b border-slate-100">
                  <td className="py-2">{row.id}</td>
                  <td className="py-2 font-mono text-xs">{row.key}</td>
                  <td className="py-2">{row.name}</td>
                  <td className="py-2 capitalize">{row.type || '-'}</td>
                  <td className="py-2">
                    <span
                      className={`rounded-full px-2 py-1 text-xs ${
                        row.enabled ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {row.enabled ? 'Actif' : 'Desactive'}
                    </span>
                  </td>
                  <td className="py-2 space-x-2">
                    <button
                      type="button"
                      onClick={() => startEdit(row)}
                      className="rounded border border-slate-300 px-3 py-1 text-xs hover:bg-slate-50"
                    >
                      Modifier
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(row)}
                      className="rounded border border-red-200 px-3 py-1 text-xs text-red-600 hover:bg-red-50"
                    >
                      Supprimer
                    </button>
                  </td>
                </tr>
              ))}
            {!loading && sortedRows.length === 0 && (
              <tr>
                <td colSpan={6} className="py-4 text-slate-500">
                  Aucun composant disponible.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default ComposantsPage
