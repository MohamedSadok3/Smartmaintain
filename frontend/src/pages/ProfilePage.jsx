import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { getMe, updateProfile } from '../services/authService'
import { setStoredUser } from '../utils/storage'

function ProfilePage() {
  const [loading, setLoading] = useState(true)
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    role: '',
    plant_id: null,
    machines: [],
    last_login: '',
    created_at: '',
  })
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })

  const loadProfile = async () => {
    setLoading(true)
    try {
      const response = await getMe()
      const user = response.data?.user || {}
      setProfile({
        name: user.name || '',
        email: user.email || '',
        role: user.role || '',
        plant_id: user.plant_id ?? null,
        machines: user.machines || [],
        last_login: user.last_login || '',
        created_at: user.created_at || '',
      })
    } catch (error) {
      toast.error(error.response?.data?.error || 'Impossible de charger le profil')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProfile()
  }, [])

  const onSaveProfile = async () => {
    if (!profile.name.trim() || !profile.email.trim()) {
      toast.error('Nom et email sont requis')
      return
    }

    setSavingProfile(true)
    try {
      const response = await updateProfile({
        name: profile.name.trim(),
        email: profile.email.trim(),
      })
      const user = response.data?.user || {}
      setProfile((prev) => ({ ...prev, ...user }))
      setStoredUser(user)
      toast.success('Profil mis à jour')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Échec de la mise à jour du profil')
    } finally {
      setSavingProfile(false)
    }
  }

  const onChangePassword = async () => {
    if (!passwordForm.current_password || !passwordForm.new_password) {
      toast.error('Renseignez le mot de passe actuel et le nouveau')
      return
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error('Les mots de passe ne correspondent pas')
      return
    }
    if (passwordForm.new_password.length < 6) {
      toast.error('Le nouveau mot de passe doit contenir au moins 6 caractères')
      return
    }

    setSavingPassword(true)
    try {
      const response = await updateProfile({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      })
      const user = response.data?.user || {}
      setStoredUser(user)
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
      toast.success('Mot de passe modifié')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Échec du changement de mot de passe')
    } finally {
      setSavingPassword(false)
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
    <div className="space-y-5">
      <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
        <header className="space-y-1">
          <h3 className="text-lg font-semibold text-slate-800">Informations personnelles</h3>
          <p className="text-sm text-slate-500">Consultez et modifiez vos informations de compte.</p>
        </header>

        <div className="grid md:grid-cols-2 gap-3">
          <label className="space-y-1">
            <span className="text-sm text-slate-700">Nom complet</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={profile.name}
              onChange={(e) => setProfile((prev) => ({ ...prev, name: e.target.value }))}
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-700">Email</span>
            <input
              type="email"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={profile.email}
              onChange={(e) => setProfile((prev) => ({ ...prev, email: e.target.value }))}
            />
          </label>
          <input
            className="rounded-lg border border-slate-300 px-3 py-2 bg-slate-50"
            value={profile.role}
            disabled
          />
          <input
            className="rounded-lg border border-slate-300 px-3 py-2 bg-slate-50"
            value={profile.plant_id ?? 'N/A'}
            disabled
          />
        </div>

        {profile.machines?.length > 0 && (
          <p className="text-sm text-slate-600">
            Machines assignées : {profile.machines.join(', ')}
          </p>
        )}

        <div className="text-xs text-slate-500 space-y-1">
          {profile.last_login && <p>Dernière connexion : {new Date(profile.last_login).toLocaleString('fr-FR')}</p>}
          {profile.created_at && <p>Compte créé le : {new Date(profile.created_at).toLocaleString('fr-FR')}</p>}
        </div>

        <button
          type="button"
          onClick={onSaveProfile}
          disabled={savingProfile}
          className="rounded-lg bg-[#16a34a] px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-60"
        >
          {savingProfile ? 'Enregistrement...' : 'Enregistrer le profil'}
        </button>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
        <header className="space-y-1">
          <h3 className="text-lg font-semibold text-slate-800">Changer le mot de passe</h3>
          <p className="text-sm text-slate-500">Votre mot de passe actuel sera vérifié avant modification.</p>
        </header>

        <div className="grid md:grid-cols-2 gap-3">
          <label className="space-y-1 md:col-span-2">
            <span className="text-sm text-slate-700">Mot de passe actuel</span>
            <input
              type="password"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm((prev) => ({ ...prev, current_password: e.target.value }))}
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-700">Nouveau mot de passe</span>
            <input
              type="password"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm((prev) => ({ ...prev, new_password: e.target.value }))}
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-700">Confirmer le mot de passe</span>
            <input
              type="password"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm((prev) => ({ ...prev, confirm_password: e.target.value }))}
            />
          </label>
        </div>

        <button
          type="button"
          onClick={onChangePassword}
          disabled={savingPassword}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50 disabled:opacity-60"
        >
          {savingPassword ? 'Modification...' : 'Modifier le mot de passe'}
        </button>
      </section>
    </div>
  )
}

export default ProfilePage
