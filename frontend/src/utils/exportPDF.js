/**
 * Utilitaire pour exporter le dashboard en PDF
 * Utilise html2canvas pour capturer le DOM et jsPDF pour générer le PDF
 */

import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

/**
 * Exporte le dashboard actuel en PDF
 * @param {Object} summary - Résumé des données du dashboard
 * @param {Array} machineCards - Liste des cartes machines
 * @returns {Promise<void>}
 */
export async function exportDashboardToPDF(summary, machineCards) {
  try {
    // Créer le PDF
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const margin = 15

    // En-tête
    pdf.setFillColor(37, 99, 235) // blue-600
    pdf.rect(0, 0, pageWidth, 40, 'F')
    
    pdf.setTextColor(255, 255, 255)
    pdf.setFontSize(24)
    pdf.setFont('helvetica', 'bold')
    pdf.text('SmartMaintain', margin, 20)
    
    pdf.setFontSize(12)
    pdf.setFont('helvetica', 'normal')
    pdf.text('Rapport de Maintenance Prédictive', margin, 30)

    // Date et heure
    const now = new Date()
    const dateStr = now.toLocaleDateString('fr-FR', { 
      day: '2-digit', 
      month: 'long', 
      year: 'numeric' 
    })
    const timeStr = now.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
    pdf.setFontSize(10)
    pdf.text(`Généré le ${dateStr} à ${timeStr}`, pageWidth - margin - 60, 25)

    let yPosition = 50

    // Section KPIs
    pdf.setTextColor(0, 0, 0)
    pdf.setFontSize(16)
    pdf.setFont('helvetica', 'bold')
    pdf.text('Indicateurs Clés de Performance', margin, yPosition)
    yPosition += 10

    // KPIs en grille
    const kpiData = [
      { label: 'Machines surveillées', value: summary.active_machines ?? 4 },
      { label: 'Alertes actives', value: summary.open_alerts ?? 0 },
      { label: 'Interventions planifiées', value: summary.pending_interventions ?? 0 },
      { 
        label: 'Taux de disponibilité', 
        value: `${Math.max(65, 100 - (summary.open_alerts || 0) * 5).toFixed(0)}%` 
      },
    ]

    pdf.setFontSize(10)
    pdf.setFont('helvetica', 'normal')
    
    kpiData.forEach((kpi, index) => {
      const xPos = margin + (index % 2) * 90
      const yPos = yPosition + Math.floor(index / 2) * 20

      pdf.setDrawColor(226, 232, 240) // slate-200
      pdf.setFillColor(248, 250, 252) // slate-50
      pdf.roundedRect(xPos, yPos, 80, 15, 2, 2, 'FD')

      pdf.setTextColor(100, 116, 139) // slate-500
      pdf.setFontSize(8)
      pdf.text(kpi.label, xPos + 5, yPos + 6)

      pdf.setTextColor(15, 23, 42) // slate-900
      pdf.setFontSize(14)
      pdf.setFont('helvetica', 'bold')
      pdf.text(String(kpi.value), xPos + 5, yPos + 12)
      pdf.setFont('helvetica', 'normal')
    })

    yPosition += 50

    // Section État des Machines
    if (yPosition > pageHeight - 60) {
      pdf.addPage()
      yPosition = 20
    }

    pdf.setFontSize(16)
    pdf.setFont('helvetica', 'bold')
    pdf.setTextColor(0, 0, 0)
    pdf.text('État des Équipements', margin, yPosition)
    yPosition += 10

    machineCards.slice(0, 4).forEach((machine, index) => {
      if (yPosition > pageHeight - 40) {
        pdf.addPage()
        yPosition = 20
      }

      const score = machine.anomalyScore
      let color, status
      if (score > 70) {
        color = [220, 38, 38] // red
        status = 'Critique'
      } else if (score >= 40) {
        color = [217, 119, 6] // orange
        status = 'Attention'
      } else {
        color = [22, 163, 74] // green
        status = 'Bon état'
      }

      // Carte machine
      pdf.setDrawColor(226, 232, 240)
      pdf.setFillColor(255, 255, 255)
      pdf.roundedRect(margin, yPosition, pageWidth - 2 * margin, 25, 2, 2, 'FD')

      // Nom de la machine
      pdf.setFontSize(12)
      pdf.setFont('helvetica', 'bold')
      pdf.setTextColor(0, 0, 0)
      pdf.text(machine.label, margin + 5, yPosition + 8)

      // Badge de statut
      pdf.setFillColor(...color)
      pdf.roundedRect(pageWidth - margin - 35, yPosition + 3, 30, 6, 2, 2, 'F')
      pdf.setTextColor(255, 255, 255)
      pdf.setFontSize(8)
      pdf.text(status, pageWidth - margin - 32, yPosition + 7.5)

      // Score
      pdf.setTextColor(...color)
      pdf.setFontSize(20)
      pdf.setFont('helvetica', 'bold')
      pdf.text(`${score.toFixed(1)}%`, margin + 5, yPosition + 20)

      // Label
      pdf.setTextColor(100, 116, 139)
      pdf.setFontSize(8)
      pdf.setFont('helvetica', 'normal')
      pdf.text('Probabilité d\'anomalie', margin + 35, yPosition + 20)

      yPosition += 30
    })

    // Section Alertes Récentes
    if (yPosition > pageHeight - 60) {
      pdf.addPage()
      yPosition = 20
    }

    const recentAlerts = summary.recent_alerts || []
    if (recentAlerts.length > 0) {
      pdf.setFontSize(16)
      pdf.setFont('helvetica', 'bold')
      pdf.setTextColor(0, 0, 0)
      pdf.text('Alertes Récentes', margin, yPosition)
      yPosition += 10

      recentAlerts.slice(0, 5).forEach((alert) => {
        if (yPosition > pageHeight - 30) {
          pdf.addPage()
          yPosition = 20
        }

        pdf.setDrawColor(226, 232, 240)
        pdf.setFillColor(248, 250, 252)
        pdf.roundedRect(margin, yPosition, pageWidth - 2 * margin, 20, 2, 2, 'FD')

        pdf.setFontSize(10)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(0, 0, 0)
        pdf.text(alert.machine, margin + 5, yPosition + 7)

        pdf.setFont('helvetica', 'normal')
        pdf.setTextColor(71, 85, 105)
        pdf.setFontSize(8)
        pdf.text(`Défaut: ${alert.defect}`, margin + 5, yPosition + 12)

        const scoreText = `Score: ${(alert.anomaly_score * 100).toFixed(1)}%`
        pdf.text(scoreText, margin + 5, yPosition + 16)

        // Badge sévérité
        let severityColor
        if (alert.severity === 'Critique') severityColor = [220, 38, 38]
        else if (alert.severity === 'Majeure') severityColor = [217, 119, 6]
        else severityColor = [22, 163, 74]

        pdf.setFillColor(...severityColor)
        pdf.roundedRect(pageWidth - margin - 30, yPosition + 5, 25, 6, 2, 2, 'F')
        pdf.setTextColor(255, 255, 255)
        pdf.setFontSize(7)
        pdf.text(alert.severity, pageWidth - margin - 28, yPosition + 9)

        yPosition += 25
      })
    }

    // Pied de page
    const totalPages = pdf.internal.pages.length - 1
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i)
      pdf.setFontSize(8)
      pdf.setTextColor(148, 163, 184)
      pdf.text(
        `Page ${i} sur ${totalPages}`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      )
      pdf.text(
        'SmartMaintain - Maintenance Prédictive',
        margin,
        pageHeight - 10
      )
    }

    // Télécharger le PDF
    const fileName = `SmartMaintain_Rapport_${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}.pdf`
    pdf.save(fileName)

    return { success: true, fileName }
  } catch (error) {
    console.error('Erreur lors de l\'export PDF:', error)
    throw new Error('Impossible de générer le rapport PDF')
  }
}

/**
 * Exporte une capture d'écran du dashboard en PDF (alternative visuelle)
 * @param {string} elementId - ID de l'élément à capturer
 * @returns {Promise<void>}
 */
export async function exportDashboardScreenshot(elementId = 'dashboard-root') {
  try {
    const element = document.getElementById(elementId) || document.body
    
    // Capturer le DOM
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    })

    // Créer le PDF
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = pageWidth - 20
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    // Ajouter l'image
    pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, Math.min(imgHeight, pageHeight - 20))

    // Télécharger
    const now = new Date()
    const fileName = `SmartMaintain_Screenshot_${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}.pdf`
    pdf.save(fileName)

    return { success: true, fileName }
  } catch (error) {
    console.error('Erreur lors de la capture d\'écran:', error)
    throw new Error('Impossible de générer la capture d\'écran')
  }
}
