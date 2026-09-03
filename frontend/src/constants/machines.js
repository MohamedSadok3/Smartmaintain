export const MACHINE_LABELS = Object.freeze({
  moteur: 'Moteur',
  pompe: 'Pompe',
  compresseur: 'Compresseur',
  echangeur: 'Échangeur thermique',
})

export const MACHINE_KEYS = Object.freeze(Object.keys(MACHINE_LABELS))

export const MACHINE_OPTIONS = Object.freeze(
  MACHINE_KEYS.map((value) => ({ value, label: MACHINE_LABELS[value] })),
)
