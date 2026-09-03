import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useLocation, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { login } from '../services/authService'

function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  const getRoleHome = (role) => {
    if (role === 'superadmin') return '/superadmin/inscriptions'
    if (role === 'admin') return '/dashboard'
    if (role === 'superviseur') return '/dashboard'
    if (role === 'technicien') return '/dashboard'
    return '/dashboard'
  }

  const onSubmit = async (values) => {
    try {
      const response = await login(values.email, values.password)
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
      toast.success('Connexion reussie')
      navigate(from === '/dashboard' ? getRoleHome(response.data.user?.role) : from, { replace: true })
    } catch (error) {
      toast.error(error.response?.data?.error || 'Echec de connexion')
    }
  }

  return (
    <div className="min-h-screen bg-[#0f172a] flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_20%_20%,#2563eb_0%,transparent_35%),radial-gradient(circle_at_80%_30%,#16a34a_0%,transparent_30%),linear-gradient(120deg,transparent_0%,rgba(255,255,255,0.08)_45%,transparent_100%)]" />
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="relative z-10 w-full max-w-[400px] rounded-xl bg-white p-8 shadow-xl space-y-4"
      >
        <h1 className="text-2xl font-bold text-[#16a34a] text-center">SmartMaintain</h1>

        <input
          className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:ring-2 focus:ring-[#16a34a]"
          type="email"
          placeholder="Email"
          {...register('email', {
            required: 'Email requis',
            pattern: {
              value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
              message: 'Format email invalide',
            },
          })}
        />
        {errors.email && <p className="text-sm text-red-600">{errors.email.message}</p>}

        <div className="relative">
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 pr-20 outline-none focus:ring-2 focus:ring-[#16a34a]"
            type={showPassword ? 'text' : 'password'}
            placeholder="Mot de passe"
            {...register('password', {
              required: 'Mot de passe requis',
              minLength: { value: 6, message: 'Minimum 6 caracteres' },
            })}
          />
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-sm text-slate-600 hover:text-slate-900"
          >
            {showPassword ? 'Masquer' : 'Afficher'}
          </button>
        </div>
        {errors.password && <p className="text-sm text-red-600">{errors.password.message}</p>}

        <input
          type="submit"
          value={isSubmitting ? 'Connexion...' : 'Se connecter'}
          className="w-full rounded-lg bg-[#16a34a] py-2.5 text-white font-medium hover:bg-green-700 transition cursor-pointer disabled:opacity-80 disabled:cursor-not-allowed"
          disabled={isSubmitting}
        />
        <div className="text-center">
          <a href="/inscription-usine" className="text-sm text-[#16a34a] hover:underline">
            Nouvelle usine ? Demander une inscription
          </a>
        </div>
        {isSubmitting && (
          <div className="flex justify-center">
            <span className="h-5 w-5 rounded-full border-2 border-[#16a34a] border-t-transparent animate-spin" />
          </div>
        )}
      </form>
    </div>
  )
}

export default LoginPage
