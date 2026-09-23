import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from renamer import traiter_dossier


class Fenetre(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Billets Châtelet – Renommage")
        self.resize(520, 320)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)

        self.titre = QLabel("🎟️ Billets Châtelet")
        self.titre.setAlignment(Qt.AlignCenter)
        self.titre.setStyleSheet("font-size:22px; font-weight:bold;")

        self.zone = QLabel(
            "Glissez un dossier contenant les PDF ici\n\n"
            "ou cliquez sur « Choisir un dossier »"
        )
        self.zone.setAlignment(Qt.AlignCenter)
        self.zone.setStyleSheet("""
            QLabel {
                border: 2px dashed #888;
                border-radius: 12px;
                padding: 25px;
                background: #fafafa;
            }
        """)

        self.barre = QProgressBar()
        self.barre.setValue(0)

        self.bouton = QPushButton("Choisir un dossier")
        self.bouton.clicked.connect(self.choisir_dossier)

        layout.addWidget(self.titre)
        layout.addWidget(self.zone)
        layout.addWidget(self.barre)
        layout.addWidget(self.bouton)

    # ---------- Glisser-déposer ----------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            chemin = Path(event.mimeData().urls()[0].toLocalFile())
            if chemin.is_dir():
                event.acceptProposedAction()

    def dropEvent(self, event):
        chemin = Path(event.mimeData().urls()[0].toLocalFile())
        if chemin.is_dir():
            self.lancer(chemin)

    # ---------- Sélection du dossier ----------

    def choisir_dossier(self):
        dossier = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier des billets"
        )

        if dossier:
            self.lancer(Path(dossier))

    # ---------- Traitement ----------

    def lancer(self, dossier):
        self.bouton.setEnabled(False)
        self.barre.setValue(0)
        self.zone.setText(f"Traitement de :\n{dossier.name}")

        def progression(i, total):
            self.barre.setMaximum(total)
            self.barre.setValue(i)
            QApplication.processEvents()

        try:
            sortie, ok, erreurs = traiter_dossier(
                dossier,
                callback_progress=progression
            )

            message = f"✅ Terminé\n\n{ok} billets renommés"

            if erreurs:
                message += f"\n{erreurs} erreur(s)"

            self.zone.setText(message)

            QMessageBox.information(
                self,
                "Traitement terminé",
                f"{ok} billets renommés.\n\n"
                f"Dossier créé :\n{sortie}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                str(e)
            )

        finally:
            self.bouton.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    fenetre = Fenetre()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
