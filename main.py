import sys
import time
import requests
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit,
    QMessageBox, QProgressBar, QCheckBox, QTextEdit,
    QSplitter, QSizePolicy, QAbstractItemView, QScrollArea
)
from PyQt5.QtGui import QColor, QPalette, QFont

DISCORD_API_BASE = "https://discord.com/api/v9"

class MessageDeleteWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, token, channel_id=None, guild_id=None, user_id=None, delete_all_channels=False):
        super().__init__()
        self.token = token
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.user_id = user_id
        self.delete_all_channels = delete_all_channels
        self.headers = {
            "Authorization": self.token,
        }
        self._is_running = True

    def run(self):
        total_deleted = 0
        try:
            if self.delete_all_channels:
                r_channels = requests.get(f"{DISCORD_API_BASE}/guilds/{self.guild_id}/channels", headers=self.headers)
                if r_channels.status_code != 200:
                    self.status.emit(f"Failed to fetch guild channels: {r_channels.status_code}")
                    self.finished.emit(total_deleted)
                    return
                channels = r_channels.json()
                text_channels = [ch for ch in channels if ch['type'] == 0]

                for ch_idx, channel in enumerate(text_channels, start=1):
                    if not self._is_running:
                        break
                    channel_id = channel['id']
                    self.status.emit(f"Deleting messages in channel: {channel['name']} ({ch_idx}/{len(text_channels)})")

                    while self._is_running:
                        before_message_id = None
                        found_my_messages = False

                        while self._is_running:
                            params = {"limit": 100}
                            if before_message_id:
                                params["before"] = before_message_id

                            r = requests.get(f"{DISCORD_API_BASE}/channels/{channel_id}/messages", headers=self.headers, params=params)
                            if r.status_code == 403:
                                self.status.emit(f"Skipping channel {channel['name']}: No access (403)")
                                break
                            if r.status_code != 200:
                                self.status.emit(f"Failed to fetch messages in channel {channel['name']}: {r.status_code}")
                                break

                            messages = r.json()
                            if not messages:
                                break

                            for msg in messages:
                                before_message_id = msg['id']

                                if msg['author']['id'] != self.user_id:
                                    continue

                                found_my_messages = True

                                del_r = requests.delete(f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{msg['id']}", headers=self.headers)
                                if del_r.status_code == 204:
                                    total_deleted += 1
                                    self.status.emit(f"Deleted message {msg['id']} in {channel['name']}")
                                    self.progress.emit(total_deleted)
                                elif del_r.status_code == 429:
                                    retry_after = del_r.json().get('retry_after', 1)
                                    self.status.emit(f"Rate limited, sleeping {retry_after}s...")
                                    time.sleep(retry_after)
                                else:
                                    self.status.emit(f"Failed to delete {msg['id']} ({del_r.status_code})")
                                time.sleep(0.25)

                            if len(messages) < 100:
                                break

                        if not found_my_messages:
                            break

            else:
                if not self.channel_id:
                    self.status.emit("No channel selected")
                    self.finished.emit(total_deleted)
                    return

                while self._is_running:
                    before_message_id = None
                    found_my_messages = False

                    while self._is_running:
                        params = {"limit": 100}
                        if before_message_id:
                            params["before"] = before_message_id

                        r = requests.get(f"{DISCORD_API_BASE}/channels/{self.channel_id}/messages", headers=self.headers, params=params)
                        if r.status_code == 403:
                            self.status.emit(f"Skipping channel: No access (403)")
                            break
                        if r.status_code != 200:
                            self.status.emit(f"Failed to fetch messages: {r.status_code}")
                            break

                        messages = r.json()
                        if not messages:
                            break

                        for msg in messages:
                            before_message_id = msg['id']

                            if msg['author']['id'] != self.user_id:
                                continue

                            found_my_messages = True

                            del_r = requests.delete(f"{DISCORD_API_BASE}/channels/{self.channel_id}/messages/{msg['id']}", headers=self.headers)
                            if del_r.status_code == 204:
                                total_deleted += 1
                                self.status.emit(f"Deleted message {msg['id']}")
                                self.progress.emit(total_deleted)
                            elif del_r.status_code == 429:
                                retry_after = del_r.json().get('retry_after', 1)
                                self.status.emit(f"Rate limited, sleeping {retry_after}s...")
                                time.sleep(retry_after)
                            else:
                                self.status.emit(f"Failed to delete {msg['id']} ({del_r.status_code})")
                            time.sleep(0.25)

                        if len(messages) < 100:
                            break

                    if not found_my_messages:
                        break

        except Exception as e:
            self.status.emit(f"Exception: {str(e)}")

        self.finished.emit(total_deleted)

    def stop(self):
        self._is_running = False


class DiscordMessageDeleter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Message Deleter")
        self.resize(850, 650)
        self.token = None
        self.user_id = None
        self.guild_id = None
        self.channel_id = None
        self.headers = None
        self.worker = None
        self.keep_my_messages_filter = True  # default ON cause y not

        self.setup_ui()
        self.apply_dark_theme()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Left panel: Guilds and Channels stacked vertically
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(0, 0, 0, 0)

        # Token input & login button
        token_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Enter your Discord token here")
        token_layout.addWidget(QLabel("Token:"))
        token_layout.addWidget(self.token_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        token_layout.addWidget(self.login_btn)
        left_panel.addLayout(token_layout)

        # Guild list
        left_panel.addWidget(QLabel("Guilds"))
        self.guild_list = QListWidget()
        self.guild_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.guild_list.itemClicked.connect(self.on_guild_selected)
        self.guild_list.setMinimumWidth(250)
        left_panel.addWidget(self.guild_list)

        # Channel list
        left_panel.addWidget(QLabel("Channels"))
        self.channel_list = QListWidget()
        self.channel_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.channel_list.itemClicked.connect(self.on_channel_selected)
        self.channel_list.setMinimumWidth(250)
        left_panel.addWidget(self.channel_list)

        main_layout.addLayout(left_panel, 1)

        # Right panel: Messages and controls
        right_panel = QVBoxLayout()

        # Checkbox to filter "Only My Messages"
        self.filter_my_messages_checkbox = QCheckBox("Show Only My Messages")
        self.filter_my_messages_checkbox.setChecked(True)
        self.filter_my_messages_checkbox.stateChanged.connect(self.on_filter_toggle)
        right_panel.addWidget(self.filter_my_messages_checkbox)

        # Messages list
        self.messages_list = QListWidget()
        self.messages_list.setSelectionMode(QAbstractItemView.NoSelection)
        right_panel.addWidget(self.messages_list, 4)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.load_messages_btn = QPushButton("Load Messages")
        self.load_messages_btn.clicked.connect(self.load_messages_btn_clicked)
        buttons_layout.addWidget(self.load_messages_btn)

        self.delete_messages_btn = QPushButton("Delete My Messages in Channel")
        self.delete_messages_btn.clicked.connect(self.delete_messages_in_channel)
        buttons_layout.addWidget(self.delete_messages_btn)

        self.delete_all_guild_btn = QPushButton("Delete My Messages in Guild")
        self.delete_all_guild_btn.clicked.connect(self.delete_messages_in_guild)
        buttons_layout.addWidget(self.delete_all_guild_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_deletion)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)

        right_panel.addLayout(buttons_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_panel.addWidget(self.progress_bar)

        # Status log box
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setFixedHeight(140)
        self.status_text.setStyleSheet("background-color: #222; color: #ccc; font-family: Consolas, monospace;")
        right_panel.addWidget(self.status_text, 2)

        main_layout.addLayout(right_panel, 3)

        # Style buttons now
        self.apply_button_styles()

    def apply_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(20, 20, 20))
        dark_palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(50, 50, 50))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)
        self.setAutoFillBackground(True)

        font = QFont("Segoe UI", 10)
        self.setFont(font)

    def apply_button_styles(self):
        button_style = """
            QPushButton {
                background-color: #2a82da;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1c5bbf;
            }
            QPushButton:pressed {
                background-color: #154c8f;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """
        for btn in [self.login_btn, self.load_messages_btn, self.delete_messages_btn,
                    self.delete_all_guild_btn, self.stop_btn]:
            btn.setStyleSheet(button_style)

    def log(self, message):
        self.status_text.append(message)
        self.status_text.ensureCursorVisible()

    def login(self):
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Error", "Please enter a token.")
            return

        self.headers = {
            "Authorization": token,
            "User-Agent": "DiscordBot (https://github.com/yourbot, v0.1)",
            "Content-Type": "application/json"
        }

        r = requests.get(f"{DISCORD_API_BASE}/users/@me", headers=self.headers)
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Failed to login: {r.status_code} {r.text}")
            return

        user_data = r.json()
        self.user_id = user_data['id']
        self.token = token
        self.log(f"Logged in as {user_data['username']}#{user_data['discriminator']} (ID: {self.user_id})")

        r_guilds = requests.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=self.headers)
        if r_guilds.status_code != 200:
            QMessageBox.warning(self, "Error", f"Failed to fetch guilds: {r_guilds.status_code}")
            return
        self.guild_list.clear()
        self.guilds = r_guilds.json()
        for g in self.guilds:
            item_text = f"{g['name']}"
            self.guild_list.addItem(item_text)

        self.channel_list.clear()
        self.messages_list.clear()

    def on_guild_selected(self, item):
        guild_name = item.text()
        guild = next((g for g in self.guilds if g['name'] == guild_name), None)
        if guild:
            self.guild_id = guild['id']
            self.load_channels(guild['id'])
            self.channel_list.setCurrentRow(-1)
            self.messages_list.clear()

    def load_channels(self, guild_id):
        r = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}/channels", headers=self.headers)
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Failed to fetch channels: {r.status_code}")
            return
        self.channel_list.clear()
        self.channels = [ch for ch in r.json() if ch['type'] == 0]
        for ch in self.channels:
            self.channel_list.addItem(ch['name'])

    def on_channel_selected(self, item):
        channel_name = item.text()
        channel = next((ch for ch in self.channels if ch['name'] == channel_name), None)
        if channel:
            self.channel_id = channel['id']
            self.load_messages(channel['id'])

    def on_filter_toggle(self, state):
        self.keep_my_messages_filter = (state == Qt.Checked)
        if hasattr(self, 'channel_id') and self.channel_id:
            self.load_messages(self.channel_id)

    def load_messages_btn_clicked(self):
        if not self.channel_id:
            QMessageBox.warning(self, "Error", "No channel selected.")
            return
        self.load_messages(self.channel_id)

    def load_messages(self, channel_id):
        self.messages_list.clear()

        before_message_id = None
        all_messages = []
        max_fetch = 500
        fetched = 0

        while True:
            params = {"limit": 100}
            if before_message_id:
                params["before"] = before_message_id

            r = requests.get(f"{DISCORD_API_BASE}/channels/{channel_id}/messages", headers=self.headers, params=params)
            if r.status_code == 403:
                self.log(f"Failed to fetch messages for channel {channel_id}: 403 (No access)")
                break
            if r.status_code != 200:
                self.log(f"Failed to fetch messages: {r.status_code}")
                break

            messages = r.json()
            if not messages:
                break

            all_messages.extend(messages)
            fetched += len(messages)
            before_message_id = messages[-1]['id']

            if fetched >= max_fetch:
                break

            if len(messages) < 100:
                break

        if self.keep_my_messages_filter:
            all_messages = [m for m in all_messages if m['author']['id'] == self.user_id]

        for msg in all_messages:
            content_preview = msg['content'][:70].replace("\n", " ")
            display_text = f"{msg['author']['username']}#{msg['author']['discriminator']}: {content_preview}"
            self.messages_list.addItem(display_text)

        self.log(f"Loaded {len(all_messages)} messages from channel.")

    def delete_messages_in_channel(self):
        if not self.token or not self.channel_id or not self.user_id:
            QMessageBox.warning(self, "Error", "Login and select a channel first.")
            return
        self.start_deletion(delete_all_channels=False)

    def delete_messages_in_guild(self):
        if not self.token or not self.guild_id or not self.user_id:
            QMessageBox.warning(self, "Error", "Login and select a guild first.")
            return
        self.start_deletion(delete_all_channels=True)

    def start_deletion(self, delete_all_channels):
        self.disable_controls(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(0)
        self.log("Starting deletion process...")

        self.worker = MessageDeleteWorker(
            token=self.token,
            channel_id=self.channel_id,
            guild_id=self.guild_id,
            user_id=self.user_id,
            delete_all_channels=delete_all_channels
        )
        self.worker.progress.connect(self.on_progress_update)
        self.worker.status.connect(self.log)
        self.worker.finished.connect(self.on_deletion_finished)
        self.worker.start()

    def stop_deletion(self):
        if self.worker:
            self.worker.stop()
            self.log("Stop requested, waiting for current operation to finish...")
            self.stop_btn.setEnabled(False)

    def on_progress_update(self, count):
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setMaximum(1000)
        self.progress_bar.setValue(min(count, 1000))

    def on_deletion_finished(self, total_deleted):
        self.log(f"Deletion finished. Total messages deleted: {total_deleted}")
        self.disable_controls(False)
        self.progress_bar.setVisible(False)
        self.worker = None

    def disable_controls(self, disable):
        self.login_btn.setEnabled(not disable)
        self.guild_list.setEnabled(not disable)
        self.channel_list.setEnabled(not disable)
        self.load_messages_btn.setEnabled(not disable)
        self.delete_messages_btn.setEnabled(not disable)
        self.delete_all_guild_btn.setEnabled(not disable)
        self.stop_btn.setEnabled(disable)
        self.filter_my_messages_checkbox.setEnabled(not disable)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiscordMessageDeleter()
    window.show()
    sys.exit(app.exec_())
