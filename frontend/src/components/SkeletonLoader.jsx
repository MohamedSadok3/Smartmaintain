/**
 * Composant Skeleton pour les états de chargement
 */
function SkeletonLoader({ variant = 'text', className = '' }) {
  const baseClasses = 'animate-pulse bg-slate-200 rounded'
  
  const variants = {
    text: 'h-4 w-full',
    title: 'h-6 w-3/4',
    circle: 'rounded-full w-12 h-12',
    card: 'h-32 w-full',
    button: 'h-10 w-24',
  }

  return (
    <div className={`${baseClasses} ${variants[variant]} ${className}`} />
  )
}

/**
 * Skeleton pour une carte de KPI
 */
export function KPISkeleton() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
      <SkeletonLoader variant="text" className="w-1/2" />
      <SkeletonLoader variant="title" />
      <SkeletonLoader variant="text" className="w-1/3" />
    </div>
  )
}

/**
 * Skeleton pour une carte de machine
 */
export function MachineCardSkeleton() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
      <div className="flex justify-between">
        <SkeletonLoader variant="title" className="w-1/3" />
        <SkeletonLoader variant="button" className="w-20" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <SkeletonLoader variant="circle" />
        <div className="space-y-2">
          <SkeletonLoader variant="text" />
          <SkeletonLoader variant="title" className="w-20" />
        </div>
      </div>
      <SkeletonLoader variant="card" className="h-16" />
    </div>
  )
}

/**
 * Skeleton pour une liste d'alertes
 */
export function AlertListSkeleton({ count = 3 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-lg border border-slate-100 p-3 space-y-2">
          <SkeletonLoader variant="title" className="w-1/2" />
          <SkeletonLoader variant="text" />
          <SkeletonLoader variant="text" className="w-2/3" />
        </div>
      ))}
    </div>
  )
}

export default SkeletonLoader
