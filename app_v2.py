<<<<<<< HEAD
from ui.login_window import LoginWindow
from ui.dashboard_window import DashboardApp


def launch_dashboard(user):
    app = DashboardApp(current_user=user)
    app.mainloop()


if __name__ == "__main__":
    login = LoginWindow(on_success=launch_dashboard)
    login.mainloop()
=======
from ui.dashboard_window import DashboardApp

if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()
>>>>>>> 1280d27de547dbc305e9f55dee04900c72692f4d
