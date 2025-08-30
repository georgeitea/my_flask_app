import socket
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle


# Ρύθμιση του χρώματος φόντου του παραθύρου
Window.clearcolor = (0.95, 0.95, 0.95, 1)  # Πολύ απαλό γκρι

# -------- Πρώτη Οθόνη (Σύνδεση) --------
class ConnectScreen(BoxLayout):
    def __init__(self, manager, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 20
        self.padding = 40
        self.manager = manager

        # Δημιουργία Gradient Φόντου
        with self.canvas.before:
            # Αρχικό χρώμα (πιο σκούρο μπλε-μοβ)
            Color(0.2, 0.4, 0.6, 1)
            self.rect1 = Rectangle(size=self.size, pos=self.pos)
            # Δεύτερο χρώμα (πιο ανοιχτό γαλάζιο)
            Color(0.4, 0.6, 0.8, 1)
            self.rect2 = Rectangle(size=self.size, pos=(self.pos[0], self.pos[1] + self.height/2))
        
        self.bind(pos=self.update_rects, size=self.update_rects)

        self.label = Label(
            text="Enter the server IP:",
            font_size=50,
            color=(1, 1, 1, 1),  # Λευκό κείμενο για να φαίνεται στο σκούρο φόντο
            bold=True
        )
        self.add_widget(self.label)

        self.ip_input = TextInput(
            hint_text="e.g. 192.168.1.10",
            multiline=False,
            font_size=50,
            size_hint_y=None,
            height=100,
            background_normal='',
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0.1, 0.1, 0.1, 1),
            padding=(10, 10, 10, 10)
        )
        self.add_widget(self.ip_input)

        self.connect_btn = Button(
            text="Login",
            font_size=50,
            size_hint=(1, 0.4),
            background_normal='',
            background_color=(0.2, 0.8, 0.2, 1),  # Πιο έντονο πράσινο
            color=(1, 1, 1, 1),
            bold=True
        )
        self.connect_btn.bind(on_press=self.try_connect)
        self.add_widget(self.connect_btn)

    def update_rects(self, instance, value):
        self.rect1.size = instance.size
        self.rect1.pos = instance.pos
        self.rect2.size = instance.size
        self.rect2.pos = (instance.pos[0], instance.pos[1] + instance.size[1]/2)

    def try_connect(self, instance):
        ip = self.ip_input.text.strip()
        port = 5000
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((ip, port))
            self.manager.client_socket = s
            self.manager.current = "control"
        except Exception:
            popup = Popup(
                title="Connection Error",
                content=Label(
                    text="Server not found! Check the IP.",
                    font_size=20,
                    color=(1, 0.3, 0.3, 1)
                ),
                size_hint=(0.8, 0.4)
            )
            popup.open()


# -------- Δεύτερη Οθόνη (Χειριστήριο) --------
class ControlScreen(BoxLayout):
    def __init__(self, manager, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 15
        self.padding = 30
        self.manager = manager

        # Λίστα κουμπιών με εντολές και χρώματα
        buttons = [
            ("Play", "play_pause", (0.2, 0.7, 0.2, 1)),      # Πράσινο
            ("Pause", "play_pause", (0.8, 0.5, 0.1, 1)),     # Πορτοκαλί
            ("Volume Up", "volume_up", (0.1, 0.6, 0.8, 1)),   # Μπλε
            ("Volume Down", "volume_down", (0.1, 0.6, 0.8, 1)), # Μπλε
            ("Repeat", "repeat", (0.5, 0.5, 0.5, 1))           # Γκρι
        ]

        for text, cmd, color in buttons:
            btn = Button(
                text=text,
                font_size=60,
                size_hint=(1, 0.3),
                background_normal='',
                background_color=color,
                color=(1, 1, 1, 1)
            )
            btn.bind(on_press=lambda instance, c=cmd: self.send_command(c))
            self.add_widget(btn)

    def send_command(self, command):
        try:
            self.manager.client_socket.sendall(command.encode())
        except Exception:
            popup = Popup(
                title="Disconnection Error",
                content=Label(
                    text="The server has been disconnected! Back...",
                    font_size=20,
                    color=(1, 0.3, 0.3, 1)
                ),
                size_hint=(0.8, 0.4)
            )
            popup.open()
            self.manager.current = "connect"


# -------- Διαχείριση Οθονών --------
class MyScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_socket = None

        # Οθόνη σύνδεσης
        connect_screen = Screen(name="connect")
        connect_screen.add_widget(ConnectScreen(self))
        self.add_widget(connect_screen)

        # Οθόνη ελέγχου
        control_screen = Screen(name="control")
        control_screen.add_widget(ControlScreen(self))
        self.add_widget(control_screen)


# -------- Εφαρμογή --------
class RemoteControlApp(App):
    def build(self):
        self.title = "GDREMOTEHUB"
        return MyScreenManager()


if __name__ == "__main__":

    RemoteControlApp().run()

