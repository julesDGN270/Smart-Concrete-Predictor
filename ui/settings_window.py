import customtkinter as ctk


class SettingsWindow(ctk.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Paramètres")
        self.geometry("500x400")

        title = ctk.CTkLabel(
            self,
            text="Paramètres",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=20)

        # Mode d'apparence
        ctk.CTkLabel(
            self,
            text="Mode d'apparence"
        ).pack()

        self.mode = ctk.CTkOptionMenu(
            self,
            values=["System", "Light", "Dark"],
            command=self.change_mode
        )

        self.mode.pack(pady=10)

        # Thème
        ctk.CTkLabel(
            self,
            text="Thème"
        ).pack()

        self.theme = ctk.CTkOptionMenu(
            self,
            values=["blue", "green", "dark-blue"],
            command=self.change_theme
        )

        self.theme.pack(pady=10)

        # Informations
        info = (
            "Smart Concrete Predictor\n\n"
            "Version : 1.0\n"
            "Auteur : Jules DEGNON\n\n"
            "Application de prédiction de la résistance du béton\n"
            "basée sur le Machine Learning."
        )

        ctk.CTkLabel(
            self,
            text=info,
            justify="left"
        ).pack(pady=20)

    def change_mode(self, mode):
        ctk.set_appearance_mode(mode)

    def change_theme(self, theme):
        ctk.set_default_color_theme(theme)