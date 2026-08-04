"""Page Formulation IA : assistant de formulation (formulaire classique,
materiaux locaux, ou texte libre) integre au tableau de bord."""

import customtkinter as ctk
from tkinter import messagebox

from core.formulation_assistant import FormulationAssistant
from core.local_formulation import LocalMaterialsFormulationAssistant
from core.text_to_formulation import generer_rapport
from core.local_materials import CIMENTS_LOCAUX, SABLES_LOCAUX, GRANULATS_LOCAUX, ADDITIONS_LOCALES
from core.database import Database

MODES = ["Formulaire classique", "Materiaux locaux", "Texte libre"]


class FormulationIAPage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.db = Database()
        self.classic_assistant = FormulationAssistant()
        self.local_assistant = LocalMaterialsFormulationAssistant()
        self.last_values_for_db = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(scroll, text="Formulation IA", font=("Arial", 24, "bold")).pack(pady=15)

        self.mode_selector = ctk.CTkSegmentedButton(scroll, values=MODES, command=self.on_mode_change)
        self.mode_selector.set(MODES[0])
        self.mode_selector.pack(pady=10)

        self.form_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.form_frame.pack(fill="x", padx=20, pady=10)

        self.result_box = ctk.CTkTextbox(scroll, height=260)
        self.result_box.pack(fill="both", expand=True, padx=20, pady=10)

        actions = ctk.CTkFrame(scroll, fg_color="transparent")
        actions.pack(pady=5)
        ctk.CTkButton(actions, text="Enregistrer dans l'historique", command=self.save_to_history).pack(side="left", padx=5)

        self.build_form(MODES[0])

    # -----------------------------------------------------------------
    def on_mode_change(self, value):
        self.build_form(value)

    def build_form(self, mode):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        if mode == "Formulaire classique":
            self._build_classic_form()
        elif mode == "Materiaux locaux":
            self._build_local_form()
        else:
            self._build_text_form()

    def _field(self, parent, label, default=""):
        ctk.CTkLabel(parent, text=label).pack(anchor="w")
        entry = ctk.CTkEntry(parent, width=200)
        entry.insert(0, default)
        entry.pack(anchor="w", pady=(0, 8))
        return entry

    def _build_classic_form(self):
        row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row.pack(fill="x")

        col1 = ctk.CTkFrame(row, fg_color="transparent")
        col1.pack(side="left", padx=10)
        col2 = ctk.CTkFrame(row, fg_color="transparent")
        col2.pack(side="left", padx=10)

        self.c_target = self._field(col1, "Resistance cible (MPa)", "30")
        self.c_dmax = self._field(col1, "Dmax (mm)", "20")
        self.c_affaissement = self._field(col1, "Affaissement (cm)", "7")
        self.c_exposure = self._field(col1, "Classe d'exposition (optionnel)", "")

        self.c_sigma = self._field(col2, "Classe vraie ciment (MPa, optionnel)", "")
        self.c_mf = self._field(col2, "Module de finesse sable", "2.5")
        self.c_quality = ctk.CTkOptionMenu(col2, values=["excellente", "bonne", "passable"])
        ctk.CTkLabel(col2, text="Qualite des granulats").pack(anchor="w")
        self.c_quality.pack(anchor="w", pady=(0, 8))

        ctk.CTkButton(self.form_frame, text="Generer la formulation", command=self.run_classic).pack(pady=10)

    def _build_local_form(self):
        row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row.pack(fill="x")
        col1 = ctk.CTkFrame(row, fg_color="transparent")
        col1.pack(side="left", padx=10)
        col2 = ctk.CTkFrame(row, fg_color="transparent")
        col2.pack(side="left", padx=10)

        self.l_target = self._field(col1, "Resistance cible (MPa)", "30")
        self.l_dmax = self._field(col1, "Dmax (mm)", "20")
        self.l_affaissement = self._field(col1, "Affaissement (cm)", "7")

        def _menu(parent, label, options_dict):
            ctk.CTkLabel(parent, text=label).pack(anchor="w")
            values = [f"{k} - {v.label}" for k, v in options_dict.items()]
            menu = ctk.CTkOptionMenu(parent, values=values)
            menu.pack(anchor="w", pady=(0, 8))
            return menu

        self.l_cement = _menu(col2, "Ciment local", CIMENTS_LOCAUX)
        self.l_sable = _menu(col2, "Sable local", SABLES_LOCAUX)
        self.l_granulat = _menu(col2, "Granulat local", GRANULATS_LOCAUX)
        addition_options = {"aucune": type("_", (), {"label": "Aucune addition"})()}
        addition_options.update(ADDITIONS_LOCALES)
        self.l_addition = _menu(col2, "Addition locale (optionnel)", addition_options)

        ctk.CTkButton(self.form_frame, text="Generer la formulation", command=self.run_local).pack(pady=10)

    def _build_text_form(self):
        ctk.CTkLabel(self.form_frame, text="Decris ton besoin en francais :").pack(anchor="w")
        self.t_text = ctk.CTkTextbox(self.form_frame, height=100)
        self.t_text.pack(fill="x", pady=5)
        self.t_text.insert(
            "1.0",
            "Ex: beton de 30 MPa, Dmax 20mm, XC3, affaissement de 7cm, "
            "sable de riviere, granite concasse, cendre de balle de riz."
        )
        ctk.CTkButton(self.form_frame, text="Analyser et generer", command=self.run_text).pack(pady=10)

    # -----------------------------------------------------------------
    def _show_result(self, text):
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", text)

    def run_classic(self):
        try:
            sigma = self.c_sigma.get().strip()
            verif = self.classic_assistant.propose_and_verify(
                target_strength=float(self.c_target.get()),
                dmax=float(self.c_dmax.get()),
                affaissement_cm=float(self.c_affaissement.get()) if self.c_affaissement.get().strip() else None,
                cement_true_class=float(sigma) if sigma else None,
                sand_fineness_modulus=float(self.c_mf.get()),
                exposure_class=self.c_exposure.get().strip() or None,
                granulat_quality=self.c_quality.get(),
            )
            m = verif.mix
            texte = (
                verif.summary() + "\n\n"
                f"Mix : Ciment={m.cement:.0f}  Eau={m.water:.0f}  Sable={m.sand:.0f}  "
                f"Gravier={m.gravel:.0f}  E/C={m.ec_ratio:.3f}\n\n"
                + "\n".join(f"! {w}" for w in m.warnings)
            )
            self.last_values_for_db = m.as_predictor_values()
            self._show_result(texte)
            self.app.set_status(f"Formulation generee : {verif.predicted_strength:.1f} MPa predits")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def run_local(self):
        try:
            cement_key = self.l_cement.get().split(" - ")[0]
            sable_key = self.l_sable.get().split(" - ")[0]
            granulat_key = self.l_granulat.get().split(" - ")[0]
            addition_raw = self.l_addition.get().split(" - ")[0]
            addition_key = None if addition_raw == "aucune" else addition_raw

            result = self.local_assistant.propose(
                target_strength=float(self.l_target.get()),
                dmax=float(self.l_dmax.get()),
                cement_key=cement_key,
                sable_key=sable_key,
                granulat_key=granulat_key,
                addition_key=addition_key,
                affaissement_cm=float(self.l_affaissement.get()) if self.l_affaissement.get().strip() else None,
            )
            self.last_values_for_db = [
                result.cement_final, 0.0, result.addition_mass, result.water_final,
                0.0, result.verification.mix.gravel, result.verification.mix.sand,
                result.verification.mix.age,
            ]
            self._show_result(result.summary())
            self.app.set_status(f"Formulation locale generee : {result.predicted_strength_final:.1f} MPa predits")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def run_text(self):
        try:
            texte_utilisateur = self.t_text.get("1.0", "end").strip()
            rapport = generer_rapport(texte_utilisateur)
            self._show_result(rapport)
            self.last_values_for_db = None
            self.app.set_status("Rapport genere depuis le texte libre")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def save_to_history(self):
        if not self.last_values_for_db:
            messagebox.showwarning("Historique", "Genere d'abord une formulation (formulaire ou materiaux locaux).")
            return
        try:
            predicted = float(self.classic_assistant.predictor.predict(self.last_values_for_db))
            self.db.insert(self.last_values_for_db, predicted, source="formulation_ia")
            messagebox.showinfo("Historique", "Formulation enregistree dans l'historique.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
