import webbrowser 
import sys
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QMenu, QSystemTrayIcon, QInputDialog
)
import time
import math
import json
import sqlite3

from database import (
    init_db,
    count_distractions as db_count_distractions,
    add_study_session,
    get_study_sessions
)


class Pet(QWidget):
    def open_dashboard(self):
        webbrowser.open( 
            "http://127.0.0.1:8501"
        )

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        # Smiski picture
        self.picture = QLabel(self)
        self.picture.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # Timer caption
        self.caption = QLabel(self)
        self.caption.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.caption.setStyleSheet(
            'background:#e5f2d2;'
            'color:#34482b;'
            'border-radius:12px;'
            'font-size:13px;'
        )

        self.caption.hide()

        # Distraction counter
        self.counter = QLabel(self)

        self.counter.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.counter.setStyleSheet(
            'background:#34482b;'
            'color:#e5f2d2;'
            'border-radius:10px;'
            'font-size:12px;'
            'padding:3px;'
        )

        # Default settings
        self.mode = 'work'
        self.size_scale = 1.5
        self.focus_minutes = 25
        self.break_minutes = 5

        self.deadline = None
        self.phase = None
        self.drag = None

        self.loading = True

        # File locations
        self.base_dir = Path(__file__).parent

        self.settings_file = (
            self.base_dir / 'settings.json'
        )

        # Initialize SQLite
        init_db()

        # Focus session tracking
        self.session_start = None
        self.session_start_monotonic = None
        self.session_start_count = 0
        self.pending_sessions = []

        # Distraction tracking
        self.distraction_count = self.count_distractions()
        self.previous_mode = None
        self.reaction_deadline = None
        self.counter_visible = True

        # Load Smiski images
        self.images = {
            name: QPixmap(
                str(self.base_dir / (name + '.png'))
            )
            for name in ('work', 'sleep', 'push', 'peek')
        }

        # Load saved settings
        settings = self.load_settings()

        self.resize_pet(self.size_scale)

        # Starting position
        screen = QApplication.primaryScreen().availableGeometry()

        default_x = (
            screen.right() - self.width() - 15
        )

        default_y = (
            screen.bottom() - self.height() - 10
        )

        self.move(
            settings.get('x', default_x),
            settings.get('y', default_y)
        )

        self.keep_on_screen()

        self.loading = False

        self.update_counter()

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(80)

        # System tray
        self.tray = QSystemTrayIcon(
            QIcon(self.images['work']), self
        )

        self.tray.setToolTip('Smiski Desktop')

        # Right-click menu
        self.menu = QMenu()

        for name, label in [
            ('work', 'Working'),
            ('sleep', 'Sleeping'),
            ('push', 'Pushing'),
            ('peek', 'Peeking')
        ]:

            self.menu.addAction(
                label,
                lambda checked=False, n=name: self.manual(n)
            )

        self.menu.addSeparator()

        # Size options
        size_menu = self.menu.addMenu('Size')

        size_menu.addAction(
            'Small', lambda: self.resize_pet(0.75)
        )

        size_menu.addAction(
            'Medium', lambda: self.resize_pet(1.0)
        )

        size_menu.addAction(
            'Large', lambda: self.resize_pet(1.5)
        )

        size_menu.addAction(
            'Extra Large', lambda: self.resize_pet(2.0)
        )

        size_menu.addAction(
            'Giant', self.giant_mode
        )

        size_menu.addAction(
            'Mega Giant', self.mega_giant_mode
        )

        self.menu.addSeparator()

        # Timer options
        self.menu.addAction(
            'Customize Timer', self.customize_timer
        )

        self.menu.addAction(
            'Start Focus', self.start_focus
        )

        self.menu.addAction(
            'Start Break', self.start_break
        )

        self.menu.addAction(
            'Stop Timer', self.stop
        )

        self.menu.addSeparator()

        # Statistics options
        self.menu.addAction(
            'Distraction Statistics',
            self.show_statistics
        )

        self.menu.addAction(
            "Today's Study Statistics",
            self.show_today_statistics
        )
        self.menu.addAction(
            'Open Analytics Dashboard',
            self.open_dashboard
        )

        self.menu.addAction(
            'Toggle Counter',
            self.toggle_counter
        )

        self.menu.addSeparator()

        # Settings options
        self.menu.addAction(
            'Save Settings', self.save_settings
        )

        self.menu.addAction(
            'Reset Settings', self.reset_settings
        )

        self.menu.addSeparator()

        self.menu.addAction(
            'Show Smiski', self.show
        )

        self.menu.addAction(
            'Hide Smiski', self.hide
        )

        self.menu.addAction(
            'Quit', self.quit_pet
        )

        self.tray.setContextMenu(self.menu)
        self.tray.show()

        # Check database every second
        self.distraction_timer = QTimer(self)

        self.distraction_timer.timeout.connect(
            self.check_distractions
        )

        self.distraction_timer.start(1000)

        # Save session and settings on normal exit
        QApplication.instance().aboutToQuit.connect(
            self.on_exit
        )

    # Count Instagram blocks using SQLite
    def count_distractions(self):

        try:

            return db_count_distractions()

        except sqlite3.Error as error:

            print('Database error:', error)

            return getattr(
                self, 'distraction_count', 0
            )

    # Update live counter
    def update_counter(self):

        self.counter.setText(
            f'Blocked: {self.distraction_count}'
        )

        self.counter.setVisible(
            self.counter_visible
        )

    # Show or hide counter
    def toggle_counter(self):

        self.counter_visible = not self.counter_visible

        self.update_counter()
        self.save_settings()

    # Detect new Instagram blocks
    def check_distractions(self):

        new_count = self.count_distractions()

        if new_count > self.distraction_count:

            if self.reaction_deadline is None:
                self.previous_mode = self.mode

            self.distraction_count = new_count

            self.set_mode('push')

            self.reaction_deadline = (
                time.monotonic() + 3
            )

            self.update_counter()

            self.tray.showMessage(
                'Smiski Focus',
                f'Instagram blocked! Total: {new_count}'
            )

        elif new_count < self.distraction_count:

            self.distraction_count = new_count

            self.update_counter()

        # Retry saving any pending sessions
        if self.pending_sessions:
            self.flush_sessions()

    # Lifetime distraction statistics
    def show_statistics(self):

        self.tray.showMessage(
            'Smiski Statistics',
            f'Total Instagram blocks: '
            f'{self.count_distractions()}'
        )

    # Today's study statistics
    def show_today_statistics(self):

        today = datetime.now().date().isoformat()

        try:

            sessions = [
                row for row in get_study_sessions()
                if row[1].startswith(today)
            ]

            total_minutes = sum(
                row[3] for row in sessions
            )

            completed = sum(
                row[4] for row in sessions
            )

            unfinished = len(sessions) - completed

            distractions = sum(
                row[5] for row in sessions
            )

            self.tray.showMessage(
                "Today's Study Statistics",
                f'Focus time: {total_minutes:.1f} min\n'
                f'Completed sessions: {completed}\n'
                f'Unfinished sessions: {unfinished}\n'
                f'Distractions: {distractions}'
            )

        except sqlite3.Error as error:

            print('Database error:', error)

            self.tray.showMessage(
                'Database Error',
                'Could not load study statistics.'
            )

    # Finish and record a focus session
    def finish_session(self, completed=False):

        if self.session_start is None:
            return

        end_time = datetime.now().isoformat(
            timespec='seconds'
        )

        duration = (
            time.monotonic()
            - self.session_start_monotonic
        ) / 60

        distractions = max(
            0,
            self.count_distractions()
            - self.session_start_count
        )

        session = (
            self.session_start,
            end_time,
            round(duration, 2),
            completed,
            distractions
        )

        self.pending_sessions.append(session)

        self.session_start = None
        self.session_start_monotonic = None
        self.session_start_count = 0

        self.flush_sessions()

    # Save sessions waiting to be recorded
    def flush_sessions(self):

        while self.pending_sessions:

            session = self.pending_sessions[0]

            try:

                add_study_session(*session)

            except sqlite3.Error as error:

                print('Could not save session:', error)
                return

            self.pending_sessions.pop(0)

            print(
                f'Session saved: {session[2]:.2f} minutes, '
                f'{session[4]} distractions, '
                f'completed: {session[3]}'
            )

    # Cancel temporary pushing reaction
    def cancel_reaction(self):

        self.reaction_deadline = None
        self.previous_mode = None

    # Save settings
    def save_settings(self):

        if self.loading:
            return

        saved_mode = self.mode

        if self.reaction_deadline is not None:

            saved_mode = self.previous_mode or 'work'

        settings = {
            'focus_minutes': self.focus_minutes,
            'break_minutes': self.break_minutes,
            'size_scale': self.size_scale,
            'mode': saved_mode,
            'counter_visible': self.counter_visible,
            'x': self.x(),
            'y': self.y()
        }

        try:

            with open(
                self.settings_file,
                'w',
                encoding='utf-8'
            ) as file:

                json.dump(settings, file, indent=4)

        except OSError as error:

            print('Could not save settings:', error)

    # Load saved settings
    def load_settings(self):

        if not self.settings_file.exists():
            return {}

        try:

            with open(
                self.settings_file,
                'r',
                encoding='utf-8'
            ) as file:

                settings = json.load(file)

            if not isinstance(settings, dict):
                return {}

            focus = settings.get(
                'focus_minutes', 25
            )

            rest = settings.get(
                'break_minutes', 5
            )

            scale = settings.get(
                'size_scale', 1.5
            )

            mode = settings.get(
                'mode', 'work'
            )

            if type(focus) is int and 1 <= focus <= 180:

                self.focus_minutes = focus

            if type(rest) is int and 1 <= rest <= 60:

                self.break_minutes = rest

            if (
                type(scale) in (int, float)
                and math.isfinite(scale)
                and scale >= 0.5
            ):

                self.size_scale = scale

            if isinstance(mode, str) and mode in self.images:

                self.mode = mode

            self.counter_visible = (
                settings.get('counter_visible', True) is True
            )

            position = {}

            for key in ('x', 'y'):

                value = settings.get(key)

                if type(value) is int and abs(value) < 100000:

                    position[key] = value

            return position

        except (OSError, ValueError) as error:

            print('Could not load settings:', error)

            return {}

    # Reset settings
    def reset_settings(self):

        self.stop()
        self.cancel_reaction()

        self.focus_minutes = 25
        self.break_minutes = 5
        self.mode = 'work'
        self.counter_visible = True

        self.resize_pet(1.5)

        self.update_counter()

        screen = QApplication.primaryScreen().availableGeometry()

        self.move(
            screen.right() - self.width() - 15,
            screen.bottom() - self.height() - 10
        )

        self.keep_on_screen()

        self.save_settings()

        self.tray.showMessage(
            'Settings Reset',
            'Smiski is back to its default settings!'
        )

    # Change Smiski pose
    def set_mode(self, mode):

        self.mode = mode

        self.picture.setPixmap(
            self.images[mode].scaled(
                int(180 * self.size_scale),
                int(170 * self.size_scale),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    # Keep Smiski inside the screen
    def keep_on_screen(self):

        screen = self.screen().availableGeometry()

        x = max(
            screen.left(),
            min(
                self.x(),
                screen.right() - self.width() + 1
            )
        )

        y = max(
            screen.top(),
            min(
                self.y(),
                screen.bottom() - self.height() + 1
            )
        )

        self.move(x, y)

    # Change Smiski size
    def resize_pet(self, scale):

        screen = self.screen().availableGeometry()

        scale = min(
            scale,
            screen.width() / 220,
            screen.height() / 260
        )

        self.size_scale = scale

        self.setFixedSize(
            int(220 * scale),
            int(260 * scale)
        )

        self.picture.setGeometry(
            int(10 * scale),
            int(30 * scale),
            int(200 * scale),
            int(178 * scale)
        )

        self.caption.setGeometry(
            0,
            0,
            int(220 * scale),
            28
        )

        self.counter.setGeometry(
            int(20 * scale),
            int(260 * scale) - 31,
            int(180 * scale),
            25
        )

        self.counter.raise_()
        self.caption.raise_()

        self.set_mode(self.mode)

        self.keep_on_screen()

        self.save_settings()

    # Giant mode
    def giant_mode(self):

        screen = self.screen().availableGeometry()

        target_width = screen.width() * 0.5
        target_height = screen.height() * 0.5

        scale = min(
            target_width / 220,
            target_height / 260
        )

        self.resize_pet(scale)

        self.move(
            screen.right() - self.width() + 1,
            screen.bottom() - self.height() + 1
        )

        self.save_settings()

    # Mega Giant mode
    def mega_giant_mode(self):

        screen = self.screen().availableGeometry()

        target_width = screen.width() * 0.95
        target_height = screen.height() * 0.95

        scale = min(
            target_width / 220,
            target_height / 260
        )

        self.resize_pet(scale)

        self.move(
            screen.left()
            + (screen.width() - self.width()) // 2,

            screen.top()
            + (screen.height() - self.height()) // 2
        )

        self.save_settings()

    # Manually change pose
    def manual(self, mode):

        self.stop()

        self.cancel_reaction()

        self.set_mode(mode)

        self.save_settings()

    # Customize timer
    def customize_timer(self):

        was_visible = self.isVisible()

        self.hide()

        try:

            focus, ok = QInputDialog.getInt(
                None,
                'Focus Settings',
                'Enter focus duration in minutes:',
                self.focus_minutes,
                1,
                180
            )

            if not ok:
                return

            rest, ok = QInputDialog.getInt(
                None,
                'Break Settings',
                'Enter break duration in minutes:',
                self.break_minutes,
                1,
                60
            )

            if not ok:
                return

            self.focus_minutes = focus
            self.break_minutes = rest

            self.save_settings()

            self.tray.showMessage(
                'Timer Updated',
                f'Focus: {focus} minutes\n'
                f'Break: {rest} minutes'
            )

        finally:

            if was_visible:

                self.show()
                self.raise_()

    # Start a focus session
    def start_focus(self):

        # Save any previous unfinished session
        self.finish_session(False)

        # Record starting information
        self.session_start = datetime.now().isoformat(
            timespec='seconds'
        )

        self.session_start_monotonic = time.monotonic()

        self.session_start_count = self.count_distractions()

        self.phase = 'Focus'

        self.deadline = (
            self.session_start_monotonic
            + self.focus_minutes * 60
        )

        if self.reaction_deadline is None:

            self.set_mode('work')

        else:

            self.previous_mode = 'work'

        self.caption.setText(
            f'Focus  {self.focus_minutes:02}:00'
        )

        self.caption.show()

    # Start break
    def start_break(self):

        # Save unfinished focus session if necessary
        self.finish_session(False)

        self.phase = 'Break'

        self.deadline = (
            time.monotonic()
            + self.break_minutes * 60
        )

        if self.reaction_deadline is None:

            self.set_mode('sleep')

        else:

            self.previous_mode = 'sleep'

        self.caption.setText(
            f'Break  {self.break_minutes:02}:00'
        )

        self.caption.show()

    # Stop timer
    def stop(self):

        self.finish_session(False)

        self.phase = None
        self.deadline = None

        self.caption.hide()

    # Animation and timer countdown
    def tick(self):

        t = time.monotonic()

        # Finish Instagram reaction
        if self.reaction_deadline is not None:

            if t >= self.reaction_deadline:

                if self.phase == 'Focus':

                    mode = 'work'

                elif self.phase == 'Break':

                    mode = 'sleep'

                else:

                    mode = self.previous_mode or 'work'

                self.set_mode(mode)

                self.cancel_reaction()

        # Breathing animation
        self.picture.move(
            int(10 * self.size_scale),
            int(30 * self.size_scale)
            + round(3 * math.sin(t * 2))
        )

        # Timer countdown
        if self.deadline is not None:

            remaining = max(
                0,
                math.ceil(self.deadline - t)
            )

            if remaining == 0:

                if self.phase == 'Focus':

                    # Save completed focus session
                    self.finish_session(True)

                    self.tray.showMessage(
                        'Focus Complete!',
                        'Study session saved. Time for a break!'
                    )

                    self.start_break()

                    remaining = self.break_minutes * 60

                else:

                    self.tray.showMessage(
                        'Break Complete!',
                        'Ready for another study session?'
                    )

                    self.stop()

                    if self.reaction_deadline is None:

                        self.set_mode('work')

                    else:

                        self.previous_mode = 'work'

                    return

            self.caption.setText(
                f'{self.phase}  '
                f'{remaining // 60:02}:'
                f'{remaining % 60:02}'
            )

    # Right-click menu
    def contextMenuEvent(self, event):

        self.menu.exec(event.globalPos())

    # Start dragging
    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self.drag = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

    # Drag Smiski
    def mouseMoveEvent(self, event):

        if (
            self.drag is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):

            self.move(
                event.globalPosition().toPoint()
                - self.drag
            )

    # Stop dragging
    def mouseReleaseEvent(self, event):

        if self.drag is not None:

            self.drag = None

            self.keep_on_screen()

            self.save_settings()

    # Save data before exiting
    def on_exit(self):

        self.finish_session(False)

        self.flush_sessions()

        self.save_settings()

        if self.pending_sessions:

            print(
                'Warning: Some sessions could not be saved.'
            )

    # Quit application
    def quit_pet(self):

        QApplication.instance().quit()


if __name__ == '__main__':

    app = QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)

    pet = Pet()

    pet.show()

    sys.exit(app.exec())
