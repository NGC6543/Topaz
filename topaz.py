import sys
from datetime import datetime
from pathlib import Path
from re import split as rsplit

from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6 import QtWidgets

from models import ManageDb


NOTES_JSON_FILE = 'notes.json'
HEIGHT_OF_WINDOW = 600
WIDTH_OF_WINDOW = 400


class NoteButton(QtWidgets.QPushButton):
    request_delete = QtCore.pyqtSignal(int, str)

    def __init__(self, note_id, title, preview_text, tags, created_at, parent=None):
        super().__init__(parent)

        self.note_id = note_id
        self.title = title
        self.preview_text = preview_text
        self.tags = tags
        self.created_at = created_at

        self.setFixedWidth(100)
        self.setFixedHeight(100)
        self.setText(f"{title}\n\n{preview_text}")

        # Set name for using in style.qss
        self.setObjectName('note_button')

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec(event.globalPos())

        if action == delete_action:
            self.request_delete.emit(self.note_id, self.title)


class MainWindow(QtWidgets.QMainWindow):
    "Main window."
    def __init__(self, db):
        super().__init__()
        self.db = db

        self.initializeUI()

    def initializeUI(self):
        self.setWindowTitle("Topaz")
        # self.setGeometry(300, 300, 400, 300)
        # Set fixed size of the window
        self.setFixedWidth(WIDTH_OF_WINDOW)
        self.setFixedHeight(HEIGHT_OF_WINDOW)

        self.stack = QtWidgets.QStackedWidget()

        self.setCentralWidget(self.stack)

        self.show_main_window()

        self.show()
        self.center_window()

    def center_window(self):
        "Move the window to the center."
        screen = QtGui.QGuiApplication.primaryScreen()
        center_point = screen.availableGeometry().center()

        frame = self.frameGeometry()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def show_main_window(self):
        "Display main window with all notes."
        self.notes = self.load_notes_from_db()
        self.note_widgets = {}

        self.scroll_main_window = QtWidgets.QScrollArea()
        self.window = QtWidgets.QWidget()

        # Search bar
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setObjectName('search_bar') # NEED ADD STYLE IN style.qss

        self.main_box = QtWidgets.QVBoxLayout()
        self.notes_grid = QtWidgets.QGridLayout()

        # Create button
        self.create_button = QtWidgets.QPushButton('Create note')
        self.create_button.setFixedWidth(200)
        self.create_button.setObjectName('create_button')

        # Adding data into grid
        self.cols = 2
        self.fill_note_widgets()

        self.main_box.addWidget(
            self.create_button,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        self.main_box.addWidget(self.search_bar)
        self.main_box.addLayout(self.notes_grid)
        self.window.setLayout(self.main_box)
        self.main_box.addStretch()

        self.create_button.clicked.connect(self.create_note)
        self.search_bar.textChanged.connect(self.update_display)

        self.scroll_main_window.setWidgetResizable(True)
        self.scroll_main_window.setWidget(self.window)

        self.stack.addWidget(self.scroll_main_window)
        self.stack.setCurrentWidget(self.scroll_main_window)

    def adding_data_into_widget(self, note_id: int, *note: tuple):
        "Add data into VBox Layout. Then it'll add to a grid."
        box = QtWidgets.QWidget()

        notes_box = QtWidgets.QVBoxLayout(box)
        note_id = note_id
        title = note[0]
        text = note[1]
        tags = note[2]
        created_at = note[3]
        note_button = NoteButton(note_id, title, text, tags, created_at)

        # Add data for sender. For editing.
        note_button.note_id = note_id
        note_button.title = title
        note_button.text = text
        note_button.tags = tags
        note_button.created_at = created_at

        # Set properties to widget. For searching.
        box.setProperty("noteId", note_id)
        box.setProperty("noteTitle", title)
        box.setProperty("noteText", text)
        box.setProperty("noteTags", tags)

        note_button.clicked.connect(self.show_single_note)
        note_button.request_delete.connect(self.confirm_delete_note)
        notes_box.addWidget(note_button)
        return box

    def show_single_note(self):
        "Show note to user; user can update note."
        sender = self.sender()
        self.editing_button = sender
        self.create_note(
            sender.title, sender.text, sender.tags,
            sender.created_at, is_update=True
        )

    def confirm_delete_note(self, note_id, title):
        reply = QtWidgets.QMessageBox.question(
            self,
            'Delete note',
            f'Are you sure you want to delete note "{title}"?',
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.db.delete_note(note_id)

            widget = self.note_widgets.pop(note_id)
            self.notes_grid.removeWidget(widget)
            widget.deleteLater()
            self.notes.pop(note_id, None)
            self.rebuild_grid(list(self.note_widgets.values()))

    def fill_note_widgets(self):
        "Fill note_widgets dict with widgets forming from notes."
        notes_box, r, c = None, None, None
        for i, note in enumerate(self.notes.items()):
            note_id, (title, text, tags, created_at) = note
            r, c = divmod(i, self.cols)
            notes_box = self.adding_data_into_widget(note_id, title, text, tags, created_at)
            self.note_widgets[note_id] = notes_box

        self.rebuild_grid(list(self.note_widgets.values()))
        return notes_box, r, c

    def clean_grid_layout(self):
        "Clear grid layout from all widgets."
        for i in reversed(range(self.notes_grid.count())):
            widget = self.notes_grid.itemAt(i).widget()
            if widget:
                self.notes_grid.removeWidget(widget)

    def rebuild_grid(self, widgets):
        "Reform grid layout after changing in notes_grid dict."
        self.clean_grid_layout()

        for i, w in enumerate(widgets):
            r, c = divmod(i, self.cols)
            self.notes_grid.addWidget(
                w, r, c, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
            )

    def refresh_notes(self, data):
        "Reform grid layout after adding new data."
        self.clean_grid_layout()

        self.notes[data['note_id']] = (
            data['title'], data['text'], data['tags'], data['created_at']
        )

        self.fill_note_widgets()

    def update_display(self, search_input):
        "Form widgets which satisfy user's input."
        query = search_input.lower().strip()
        if not query:
            for w in self.note_widgets.values():
                w.setVisible(True)
            self.rebuild_grid(list(self.note_widgets.values()))
            return

        visible_widgets = []
        for widget in self.note_widgets.values():
            title = widget.property('noteTitle').lower()
            text = widget.property('noteText').lower()
            preview = widget.property('noteText').lower()
            tags = widget.property('noteTags') or []

            is_match = (
                query in title
                or query in text
                or query in preview
                or any(query in t.lower() for t in tags)
            )

            widget.setVisible(is_match)
            if is_match:
                visible_widgets.append(widget)

        self.rebuild_grid(visible_widgets)

    def create_note(
            self, title=None, text=None, tags=None, date=None, is_update=False
    ):
        self.create_window = QtWidgets.QWidget()
        self.stack.addWidget(self.create_window)

        layout = QtWidgets.QVBoxLayout()
        layout_for_buttons = QtWidgets.QHBoxLayout()

        # Accept_button
        self.accept_button = QtWidgets.QPushButton()
        self.accept_button.setObjectName('accept_button')
        self.accept_button.setIcon(QtGui.QIcon('check-mark2.png'))
        self.accept_button.setIconSize(QtCore.QSize(24, 24))

        # Title field
        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText('Enter title')
        self.old_title = title
        if title:
            self.title.setText(title)
        self.title.setObjectName('title_edit')
        self.title.textChanged.connect(self.on_title_changed)

        # Time Label
        if date:
            cur_time = date
        else:
            cur_time = datetime.today().strftime('%d-%B-%Y %H:%M')
        self.time_label = QtWidgets.QLabel(cur_time)
        self.time_label.setObjectName('time_label')

        # Tags field
        self.tags = QtWidgets.QLineEdit()
        self.tags.setPlaceholderText('Enter note tags here')
        if tags:
            self.tags.setText(', '.join(tag if tag else '' for tag in tags))
        self.tags.setObjectName('tags_edit')

        # Text field
        self.text = QtWidgets.QTextEdit()
        self.text.setPlaceholderText('Enter note text here')
        if text:
            self.text.setText(text)
        self.text.setObjectName('text_edit')

        # Back button
        self.back_button = QtWidgets.QPushButton('← Back')
        self.back_button.setObjectName('back_button')

        # Managing layout
        layout_for_buttons.addStretch()
        layout_for_buttons.addWidget(self.back_button)
        layout_for_buttons.addWidget(self.accept_button)
        layout.addLayout(layout_for_buttons)
        layout.addWidget(self.title)
        layout.addWidget(self.time_label)
        layout.addWidget(self.tags)
        layout.addWidget(self.text)
        # layout.addStretch()
        self.create_window.setLayout(layout)

        # Connecting buttons
        if is_update:
            self.accept_button.clicked.connect(
                self.click_accept_and_update_button
            )
        else:
            self.accept_button.clicked.connect(
                self.click_accept_and_save_button
            )
        self.back_button.clicked.connect(self.click_back_button)

        self.stack.setCurrentWidget(self.create_window)

    def on_title_changed(self, text):
        if text:
            self.title.setStyleSheet("font-size: 14px; font-weight: bold;")
        else:
            self.title.setStyleSheet("font-size: 18px; font-weight: normal;")

    def click_accept_and_save_button(self):
        title = self.title.text()
        text = self.text.toPlainText()
        if not title and not text:
            return
        note = {
                'title': title,
                'text': text,
                'tags': rsplit(r'[,|\s|,\s]', self.tags.text()),
                'created_at': None
        }
        adding_data_and_get_id = self.db.insert_data_in_tables(
            note['title'], note['text'], note['tags']
        )
        note['note_id'] = adding_data_and_get_id
        self.refresh_notes(note)
        self.stack.setCurrentWidget(self.scroll_main_window)

    def click_accept_and_update_button(self):
        button = self.editing_button
        note = {
                'title': self.title.text(),
                'text': self.text.toPlainText(),
                'tags': rsplit(r'[, |,|\s|,\s]', self.tags.text()),
                'created_at': self.time_label.text()
        }
        self.db.update_data(
            button.note_id, note['title'], note['text'], note['tags']
        )

        # ADD GETTING DATA FROM DB for consistency?
        button.title = note['title']
        button.text = note['text']
        button.tags = note['tags']
        button.created_at = note['created_at']
        button.setText(f"{button.title}\n\n{button.text}")

        self.stack.setCurrentWidget(self.scroll_main_window)

    def click_back_button(self):
        self.stack.setCurrentWidget(self.scroll_main_window)

    def load_notes_from_db(self) -> dict:
        data = self.db.get_all_data_from_db()
        return data


if __name__ == '__main__':
    db = ManageDb()
    db.create_tables() # Later hide this in some script
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(Path('style.qss').read_text())
    window = MainWindow(db)
    app.exec()
