import { useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import { registerPlant } from '../services/authService'

const MAX_PDF_BYTES = 5 * 1024 * 1024

const readFileAsBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })

function PdfUploadField({ label, required, file, onChange }) {
  return (
    <div className="space-y-1">
      <span className="text-sm font-medium text-slate-700">
        {label} {required && <span className="text-red-500">*</span>}
      </span>
      <label
        className={`flex items-center gap-3 rounded-lg border-2 border-dashed px-4 py-3 cursor-pointer transition ${
          file
            ? 'border-[#16a34a] bg-green-50'
            : 'border-slate-300 hover:border-[#16a34a] bg-slate-50'
        }`}
      >
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => onChange(e.target.files?.[0] || null)}
        />
        <span className="text-lg">{file ? '✅' : '📄'}</span>
        <div className="min-w-0">
          {file ? (
            <>
              <p className="text-sm font-medium text-green-700 truncate">{file.name}</p>
              <p className="text-xs text-green-600">{(file.size / 1024).toFixed(0)} Ko</p>
            </>
          ) : (
            <p className="text-sm text-slate-500">Cliquer pour sélectionner un fichier PDF</p>
          )}
        </div>
      </label>
    </div>
  )
}

function PlantRegistrationPage() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm()

  const [patenteFile, setPatenteFile] = useState(null)
  const [rneFile, setRneFile] = useState(null)

  const onSubmit = async (values) => {
    if (!patenteFile) {
      toast.error('Le document Patente (PDF) est obligatoire.')
      return
    }
    if (!rneFile) {
      toast.error('Le document RNE (PDF) est obligatoire.')
      return
    }
    if ([patenteFile, rneFile].some((file) => file.size > MAX_PDF_BYTES)) {
      toast.error('Chaque document PDF doit faire au maximum 5 Mo.')
      return
    }

    try {
      const [patenteBase64, rneBase64] = await Promise.all([
        readFileAsBase64(patenteFile),
        readFileAsBase64(rneFile),
      ])

      const payload = {
        plant: {
          name: values.plant_name,
          contact_name: values.contact_name,
          contact_email: values.contact_email.toLowerCase(),
        },
        users: {
          admin: {
            name: values.admin_name,
            email: values.admin_email.toLowerCase(),
            password: values.admin_password,
          },
        },
        documents: {
          patente: { data: patenteBase64, name: patenteFile.name },
          rne: { data: rneBase64, name: rneFile.name },
        },
      }

      await registerPlant(payload)
      toast.success("Inscription envoyée. En attente de validation du superadmin.")
      reset()
      setPatenteFile(null)
      setRneFile(null)
    } catch (error) {
      toast.error(error.response?.data?.error || "Impossible d'envoyer l'inscription")
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 py-10 px-4">
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-slate-800">Inscription d'une usine</h1>
          <Link to="/login" className="rounded-lg bg-white px-3 py-2 text-sm text-slate-700 border border-slate-200">
            Retour connexion
          </Link>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200 space-y-6">

          {/* Informations usine */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
              Informations usine
            </h2>
            <div className="grid md:grid-cols-2 gap-3">
              <input
                className="rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Nom de l'usine"
                {...register('plant_name', { required: true })}
              />
              <input
                className="rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Nom du contact"
                {...register('contact_name', { required: true })}
              />
              <input
                className="rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Email du contact"
                type="email"
                {...register('contact_email', { required: true })}
              />
            </div>
          </section>

          {/* Documents légaux */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
              Documents légaux
            </h2>
            <p className="text-xs text-slate-500">
              Veuillez fournir les deux documents officiels de votre entreprise au format PDF.
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <PdfUploadField
                label="Patente"
                required
                file={patenteFile}
                onChange={setPatenteFile}
              />
              <PdfUploadField
                label="RNE (Registre National des Entreprises)"
                required
                file={rneFile}
                onChange={setRneFile}
              />
            </div>
          </section>

          {/* Compte administrateur */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
              Compte administrateur
            </h2>
            <div className="grid md:grid-cols-3 gap-3">
              <input
                className="rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Nom de l'administrateur"
                {...register('admin_name', { required: true })}
              />
              <input
                className="rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Email admin"
                type="email"
                {...register('admin_email', { required: true })}
              />
              <input
                className="rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Mot de passe admin"
                type="password"
                {...register('admin_password', { required: true, minLength: 8 })}
              />
            </div>
          </section>

          {Object.keys(errors).length > 0 && (
            <p className="text-sm text-red-600">
              Champs obligatoires manquants : usine, contact, compte admin (mot de passe min. 8 caractères).
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg bg-[#16a34a] px-5 py-2.5 text-white font-medium hover:bg-green-700 disabled:opacity-70 transition"
          >
            {isSubmitting ? "Envoi en cours..." : "Envoyer l'inscription"}
          </button>
        </form>
      </div>
    </div>
  )
}

export default PlantRegistrationPage
