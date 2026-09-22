import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { getMyPlant, updateMyPlant } from '../services/authService'

function PlantProfilePage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    name: '',
    code: '',
    status: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    location: '',
    industry: '',
    description: '',
  })

  const loadPlant = async () => {
    setLoading(true)
    try {
      const response = await getMyPlant()
      
      const plant = response.data?.plant || {}
      setForm({
        name: plant.name || '',
        code: plant.code || '',
        status: plant.status || '',
        contact_name: plant.contact_name || '',
        contact_email: plant.contact_email || '',
        contact_phone: plant.contact_phone || '',
        location: plant.location || '',
        industry: plant.industry || '',
        description: plant.description || '',
      })
    } catch (error) {
      toast.error(error.response?.data?.error || "Impossible de charger le profil d'usine")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPlant()
  }, [])

  const onSave = async () => {
    setSaving(true)
    try {
      const payload = {
        name: form.name,
        contact_name: form.contact_name,
        contact_email: form.contact_email,
        contact_phone: form.contact_phone,
        location: form.location,
        industry: form.industry,
        description: form.description,
      }
      const response = await updateMyPlant(payload)
      const plant = response.data?.plant || {}
      setForm((prev) => ({ ...prev, ...plant }))
      toast.success("Profil d'usine mis a jour")
    } catch (error) {
      toast.error(error.response?.data?.error || 'Echec mise a jour profil usine')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <p className="text-slate-500">Chargement...</p>
      </section>
    )
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
      <h3 className="text-lg font-semibold text-slate-800">Profil de mon usine</h3>

      <div className="grid md:grid-cols-2 gap-3">
        <input className="rounded-lg border border-slate-300 px-3 py-2 bg-slate-50" value={form.code} disabled />
        <input className="rounded-lg border border-slate-300 px-3 py-2 bg-slate-50" value={form.status} disabled />
        <input className="rounded-lg border border-slate-300 px-3 py-2" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} placeholder="Nom usine" />
        <input className="rounded-lg border border-slate-300 px-3 py-2" value={form.industry} onChange={(e) => setForm((p) => ({ ...p, industry: e.target.value }))} placeholder="Secteur (industrie)" />
        <input className="rounded-lg border border-slate-300 px-3 py-2" value={form.location} onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))} placeholder="Localisation" />
        <input className="rounded-lg border border-slate-300 px-3 py-2" value={form.contact_name} onChange={(e) => setForm((p) => ({ ...p, contact_name: e.target.value }))} placeholder="Nom contact" />
        <input className="rounded-lg border border-slate-300 px-3 py-2" value={form.contact_email} onChange={(e) => setForm((p) => ({ ...p, contact_email: e.target.value }))} placeholder="Email contact" />
        <input className="rounded-lg border border-slate-300 px-3 py-2" value={form.contact_phone} onChange={(e) => setForm((p) => ({ ...p, contact_phone: e.target.value }))} placeholder="Telephone contact" />
      </div>

      <textarea
        className="w-full rounded-lg border border-slate-300 px-3 py-2 min-h-28"
        value={form.description}
        onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
        placeholder="Description de l'usine"
      />

      <button
        type="button"
        onClick={onSave}
        disabled={saving}
        className="rounded-lg bg-[#16a34a] px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-60"
      >
        {saving ? 'Enregistrement...' : 'Enregistrer'}
      </button>
    </section>
  )
}

export default PlantProfilePage
