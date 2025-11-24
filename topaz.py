import sys
from re import split as rsplit

from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6 import QtWidgets

from models import ManageDb


NOTES_JSON_FILE = 'notes.json'
HEIGHT_OF_WINDOW = 600
WIDTH_OF_WINDOW = 400


class NoteButton(QtWidgets.QPushButton):
    requestDelete = QtCore.pyqtSignal(int, str)

    def __init__(self, note_id, title, preview_text, tags, parent=None):
        super().__init__(parent)

        self.note_id = note_id
        self.title = title
        self.preview_text = preview_text
        self.tags = tags

        self.setFixedWidth(100)
        self.setFixedHeight(100)
        self.setText(f"{title}\n\n{preview_text}")

        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #4CAF50;
                border-radius: 12px;
                text-align: left;
                padding: 4px 8px;
            }
        """)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec(event.globalPos())

        if action == delete_action:
            self.requestDelete.emit(self.note_id, self.title)


class MainWindow(QtWidgets.QMainWindow):
    '''Main window.'''
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
        'Move the window to the center.'
        screen = QtGui.QGuiApplication.primaryScreen()
        center_point = screen.availableGeometry().center()

        frame = self.frameGeometry()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def adding_data_into_widget(self, note):
        '''Add data into VBox Layout. Then it'll add to a grid.'''
        box = QtWidgets.QWidget()

        notes_box = QtWidgets.QVBoxLayout(box)
        note_id = note[0]
        title = note[1][0]
        text = note[1][1]
        tags = note[1][2]
        note_button = NoteButton(note_id, title, text, tags)

        # Adding propertis for editing note
        note_button.note_id = note[0]
        note_button.title = note[1][0]
        note_button.text = note[1][1]
        note_button.tags = note[1][2]

        note_button.clicked.connect(self.show_single_note)
        note_button.requestDelete.connect(self.confirm_delete_note)
        notes_box.addWidget(note_button)
        return box

    def show_single_note(self):
        '''Show note to user; user can update note.'''
        sender = self.sender()
        self.editing_button = sender
        self.create_note(
            sender.title, sender.text, sender.tags, is_update=True
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

            r, c = self.coord[note_id]

            wd = self.notes_grid.itemAtPosition(r, c).widget()
            self.notes_grid.removeWidget(wd)
            wd.deleteLater()

            self.notes.pop(note_id)
            self.coord.pop(note_id)
            self.refresh_notes()

    def show_main_window(self):
        'Display main window with all notes.'
        self.notes = self.load_notes()
        self.coord = {}

        self.scroll_main_window = QtWidgets.QScrollArea()
        self.window = QtWidgets.QWidget()
        self.stack.addWidget(self.scroll_main_window)

        self.main_box = QtWidgets.QVBoxLayout()
        self.notes_grid = QtWidgets.QGridLayout()

        self.create_button = QtWidgets.QPushButton('Create note')
        self.create_button.setFixedWidth(200)
        self.main_box.addWidget(
            self.create_button,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        # Adding data into grid
        self.cols = 2
        self.add_item_to_grid()

        self.main_box.addLayout(self.notes_grid)
        self.window.setLayout(self.main_box)
        self.main_box.addStretch()

        self.create_button.clicked.connect(self.create_note)

        self.scroll_main_window.setWidgetResizable(True)
        self.scroll_main_window.setWidget(self.window)

        self.stack.setCurrentWidget(self.scroll_main_window)

    def add_item_to_grid(self):
        notes_box, r, c = None, None, None
        for i, note in enumerate(self.notes.items()):
            r, c = divmod(i, self.cols)
            notes_box = self.adding_data_into_widget(note)
            self.coord[note[0]] = (r, c)

            self.notes_grid.addWidget(
                notes_box, r, c, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
            )
        return notes_box, r, c

    def refresh_notes(self, data=None):
        for i in reversed(range(self.notes_grid.count())):
            widget = self.notes_grid.itemAt(i).widget()
            if widget:
                self.notes_grid.removeWidget(widget)
                widget.deleteLater()

        if data:
            self.notes[data['note_id']] = (
                data['title'], data['text'], data['tags']
            )

        notes_box, r, c = self.add_item_to_grid()

        self.notes_grid.addWidget(
            notes_box, r, c, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

    def create_note(self, title=None, text=None, tags=None, is_update=False):
        self.create_window = QtWidgets.QWidget()
        self.stack.addWidget(self.create_window)

        layout = QtWidgets.QVBoxLayout()
        layout_for_buttons = QtWidgets.QHBoxLayout()

        # Accept_button
        self.accept_button = QtWidgets.QPushButton()
        self.accept_button.setFixedWidth(50)
        self.accept_button.setIcon(QtGui.QIcon('check-mark2.png'))
        self.accept_button.setIconSize(QtCore.QSize(24, 24))
        self.accept_button.setFixedHeight(40)
        self.accept_button.setStyleSheet('border: 0px;')

        # Title field
        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText('Enter title')
        self.old_title = title
        if title:
            self.title.setText(title)

        # Text field
        self.text = QtWidgets.QTextEdit()
        self.text.setPlaceholderText('Enter note text here')
        if text:
            self.text.setText(text)

        # Tags field
        self.tags = QtWidgets.QLineEdit()
        self.tags.setPlaceholderText('Enter note tags here')
        if tags:
            self.tags.setText(', '.join(tag if tag else '' for tag in tags))

        # Back button
        self.back_button = QtWidgets.QPushButton('← Back')
        self.back_button.setFixedHeight(40)
        self.back_button.setStyleSheet('border: 0px;')

        # Managing layout
        layout_for_buttons.addStretch()
        layout_for_buttons.addWidget(self.back_button)
        layout_for_buttons.addWidget(self.accept_button)
        layout.addLayout(layout_for_buttons)
        layout.addWidget(self.title)
        layout.addWidget(self.tags)
        layout.addWidget(self.text)
        layout.addStretch()
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

    def click_accept_and_save_button(self):
        title = self.title.text()
        text = self.text.toPlainText()
        if not title and not text:
            return
        note = {
                'title': title,
                'text': text,
                'tags': rsplit(r'[,|\s|,\s]', self.tags.text())
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
                'tags': rsplit(r'[, |,|\s|,\s]', self.tags.text())
        }
        self.db.update_data(
            button.note_id, note['title'], note['text'], note['tags']
        )

        # ADD GETTING DATA FROM DB for consistency?
        button.title = note['title']
        button.text = note['text']
        button.tags = note['tags']
        button.setText(f"{button.title}\n\n{button.text}")

        self.stack.setCurrentWidget(self.scroll_main_window)

    def click_back_button(self):
        self.stack.setCurrentWidget(self.scroll_main_window)

    def load_notes(self) -> dict:
        data = self.db.get_all_data_from_db()
        return data


if __name__ == '__main__':
    db = ManageDb()
    db.create_tables() # Late hide this in some script
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(db)
    app.exec()
