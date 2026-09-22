import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { createUser, deleteUser, getUsers, updateUser } from '../services/userService'
import { MACHINE_OPTIONS } from '../constants/machines'

const ROLE_OPTIONS = [
  { label: 'Administrateur', value: 'admin' },
  { label: 'Superviseur', value: 'superviseur' },
  { label: 'Technicien', value: 'technicien' },
]

function roleLabel(role) {
  if (role === 'admin') return 'Administrateur'
  if (role === 'superviseur') return 'Superviseur'
  if (role === 'technicien') return 'Technicien'
  return role
}

function roleBadgeClass(role) {
  if (role === 'admin') return 'bg-purple-100 text-purple-700'
  if (role === 'superviseur') return 'bg-amber-100 text-amber-700'
  if (role === 'technicien') return 'bg-blue-100 text-blue-700'
  return 'bg-slate-100 text-slate-700'
}

function initials(name) {
  const parts = (name || '').trim().split(' ').filter(Boolean)
  if (parts.length === 0) return 'U'
  return parts
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}

function formatLastLogin(date) {
  if (!date) return '-'
  return new Date(date).toLocaleString('fr-FR', { hour12: false })
}

function SkeletonRows() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, idx) => (
        <tr key={idx} className="animate-pulse border-b border-slate-100">
          <td className="py-3">
            <div className="h-10 w-10 rounded-full bg-slate-200" />
          </td>
          <td className="py-3">
            <div className="h-4 w-24 rounded bg-slate-200" />
          </td>
          <td className="py-3">
            <div className="h-4 w-40 rounded bg-slate-200" />
          </td>
          <td className="py-3">
            <div className="h-6 w-28 rounded-full bg-slate-200" />
          </td>
          <td className="py-3">
            <div className="h-6 w-44 rounded bg-slate-200" />
          </td>
          <td className="py-3">
            <div className="h-4 w-32 rounded bg-slate-200" />
          </td>
          <td className="py-3">
            <div className="h-8 w-32 rounded bg-slate-200" />
          </td>
        </tr>
      ))}
    </>
  )
}

function UserModal({ open, mode, user, onClose, onSaved }) {
  const [showPassword, setShowPassword] = useState(false)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    defaultValues: {
      name: '',
      email: '',
      password: '',
      role: 'technicien',
      machines: [],
    },
  })

  useEffect(() => {
    if (!open) return
    reset({
      name: user?.name || '',
      email: user?.email || '',
      password: '',
      role: user?.role || 'technicien',
      machines: user?.machines || [],
    })
  }, [open, user, reset])

  const onSubmit = async (values) => {
    const normalizedMachines = Array.isArray(values.machines)
      ? values.machines
      : values.machines
        ? [values.machines]
        : []

    const payload = {
      name: values.name,
      email: values.email,
      role: values.role,
      machines: normalizedMachines,
    }

    if (values.password) {
      payload.password = values.password
    }

    try {
      if (mode === 'create') {
        await createUser(payload)
        toast.success('Utilisateur cree')
      } else {
        await updateUser(user.id, payload)
        toast.success('Utilisateur mis a jour')
      }
      onSaved()
      onClose()
    } catch (error) {
      toast.error(error.response?.data?.error || 'Operation impossible')
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4">
      <div className="max-h-[92dvh] w-full overflow-y-auto rounded-t-xl bg-white shadow-xl sm:max-w-xl sm:rounded-xl">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800">
            {mode === 'create' ? 'Ajouter un utilisateur' : "Modifier l'utilisateur"}
          </h3>
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-800">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          <div>
            <label className="mb-1 block text-sm text-slate-700">Nom</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              {...register('name', { required: 'Nom requis' })}
            />
            {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
          </div>

          <div>
            <label className="mb-1 block text-sm text-slate-700">Email</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              {...register('email', {
                required: 'Email requis',
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: 'Format email invalide',
                },
              })}
            />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>

          <div>
            <label className="mb-1 block text-sm text-slate-700">Mot de passe</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder={mode === 'edit' ? 'Laisser vide pour conserver' : 'Mot de passe'}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 pr-20"
                {...register('password', {
                  required: mode === 'create' ? 'Mot de passe requis' : false,
                  minLength: {
                    value: 8,
                    message: 'Minimum 8 caracteres',
                  },
                })}
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-slate-600"
              >
                {showPassword ? 'Masquer' : 'Afficher'}
              </button>
            </div>
            {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
          </div>

          <div>
            <label className="mb-1 block text-sm text-slate-700">Role</label>
            <select className="w-full rounded-lg border border-slate-300 px-3 py-2" {...register('role')}>
              {ROLE_OPTIONS.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <p className="mb-2 text-sm text-slate-700">Machines</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {MACHINE_OPTIONS.map((machine) => (
                <label key={machine.value} className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" value={machine.value} {...register('machines')} />
                  {machine.label}
                </label>
              ))}
            </div>
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-lg bg-[#16a34a] px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-70"
            >
              {isSubmitting ? 'Enregistrement...' : mode === 'create' ? 'Ajouter' : 'Enregistrer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function UtilisateursPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState('create')
  const [selectedUser, setSelectedUser] = useState(null)

  const sortedUsers = useMemo(() => [...users].sort((a, b) => a.id - b.id), [users])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const response = await getUsers()
      setUsers(response.data.users || [])
    } catch (error) {
      toast.error(error.response?.data?.error || 'Impossible de charger les utilisateurs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const openCreate = () => {
    setModalMode('create')
    setSelectedUser(null)
    setModalOpen(true)
  }

  const openEdit = (user) => {
    setModalMode('edit')
    setSelectedUser(user)
    setModalOpen(true)
  }

  const onDelete = async (user) => {
    const confirmed = window.confirm(`Supprimer ${user.name} ?`)
    if (!confirmed) return

    try {
      await deleteUser(user.id)
      setUsers((prev) => prev.filter((item) => item.id !== user.id))
      toast.success('Utilisateur supprime')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Suppression impossible')
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="text-lg font-semibold text-slate-800">Utilisateurs</h3>
        <button
          type="button"
          onClick={openCreate}
          className="w-full rounded-lg bg-[#16a34a] px-4 py-2 text-sm text-white hover:bg-green-700 sm:w-auto"
        >
          Ajouter
        </button>
      </div>

      <div className="overflow-auto">
        <table className="w-full min-w-[980px] text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b border-slate-200">
              <th className="py-2">Avatar</th>
              <th className="py-2">Nom</th>
              <th className="py-2">Email</th>
              <th className="py-2">Rôle</th>
              <th className="py-2">Machines</th>
              <th className="py-2">Dernière connexion</th>
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && <SkeletonRows />}
            {!loading &&
              sortedUsers.map((user) => (
                <tr key={user.id} className="border-b border-slate-100">
                  <td className="py-3">
                    <div className="h-10 w-10 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-semibold">
                      {initials(user.name)}
                    </div>
                  </td>
                  <td className="py-3 text-slate-800 font-medium">{user.name}</td>
                  <td className="py-3 text-slate-700">{user.email}</td>
                  <td className="py-3">
                    <span className={`rounded-full px-2 py-1 text-xs ${roleBadgeClass(user.role)}`}>
                      {roleLabel(user.role)}
                    </span>
                  </td>
                  <td className="py-3">
                    <div className="flex flex-wrap gap-1">
                      {(user.machines || []).length === 0 && (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">Aucune machine</span>
                      )}
                      {(user.machines || []).map((machine) => (
                        <span
                          key={`${user.id}-${machine}`}
                          className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700"
                        >
                          {MACHINE_OPTIONS.find((item) => item.value === machine)?.label || machine}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3 text-slate-600">{formatLastLogin(user.last_login)}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => openEdit(user)}
                        className="rounded border border-slate-300 px-3 py-1 text-xs hover:bg-slate-50"
                      >
                        Modifier
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(user)}
                        className="rounded border border-red-200 px-3 py-1 text-xs text-red-600 hover:bg-red-50"
                      >
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <UserModal
        open={modalOpen}
        mode={modalMode}
        user={selectedUser}
        onClose={() => setModalOpen(false)}
        onSaved={fetchUsers}
      />
    </section>
  )
}

export default UtilisateursPage
