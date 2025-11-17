import sys
from re import split as rsplit

from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6 import QtWidgets

from models import ManageDb


NOTES_JSON_FILE = 'notes.json'


class MainWindow(QtWidgets.QMainWindow):
    '''Main window.'''
    def __init__(self, db):
        super().__init__()
        self.db = db

        self.initializeUI()

    def initializeUI(self):
        self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle("Topaz")

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.show_main_window()

        self.show()

    def adding_data_into_widget(self, note):
        '''Add data into VBox Layout. Then it'll add to a grid.'''
        notes_box = QtWidgets.QVBoxLayout()
        test_button = QtWidgets.QPushButton()
        test_button.setFixedWidth(100)
        test_button.setFixedHeight(100)
        test_button.title = note[0]
        test_button.text = note[1][0]
        test_button.tags = note[1][1]
        test_button.setText(f'{note[0]}\n\n {note[1][0]}')
        test_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #4CAF50;
                border-radius: 12px;
                text-align: left;
                padding: 4px 8px;
            }
        """)

        notes_box.addWidget(test_button)
        test_button.clicked.connect(self.show_single_note)
        return notes_box

    def show_single_note(self):
        '''Function must update db not insert new data'''
        sender = self.sender()
        self.create_note(
            sender.title, sender.text, sender.tags, is_update=True
        )

    def show_main_window(self):
        self.notes = self.load_notes()

        self.window = QtWidgets.QWidget()
        self.stack.addWidget(self.window)

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

        self.stack.setCurrentWidget(self.window)

    def add_item_to_grid(self):
        notes_box, r, c = None, None, None
        for i, note in enumerate(self.notes.items()):
            r, c = divmod(i, self.cols)
            notes_box = self.adding_data_into_widget(note)
            self.notes_grid.addItem(notes_box, r, c)
        return notes_box, r, c

    def refresh_notes(self, data):
        # for i in reversed(range(self.notes_grid.count())): # Reversed?
        for i in range(self.notes_grid.count()):
            widget = self.notes_grid.itemAt(i).widget()
            if widget:
                self.notes_grid.removeWidget(widget)
                widget.deleteLater()

        self.notes[data['title']] = (data['text'], data['tags'])

        notes_box, r, c = self.add_item_to_grid()

        self.notes_grid.addLayout(notes_box, r, c)

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
        if title:
            self.old_title = title
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
        note = {
                'title': self.title.text(),
                'text': self.text.toPlainText(),
                'tags': rsplit(r'[,|\s|,\s]', self.tags.text())
        }
        self.db.insert_data_in_tables(
            note['title'], note['text'], note['tags']
        )
        self.refresh_notes(note)
        self.stack.setCurrentWidget(self.window)

    def click_accept_and_update_button(self):
        note = {
                'title': self.title.text(),
                'text': self.text.toPlainText(),
                'tags': rsplit(r'[,|\s|,\s]', self.tags.text())
        }
        self.db.update_data(
            self.old_title, note['title'], note['text'], note['tags']
        )
        self.notes.pop(note['title'], None)
        self.refresh_notes(note)
        self.stack.setCurrentWidget(self.window)

    def click_back_button(self):
        self.stack.setCurrentWidget(self.window)

    def load_notes(self) -> dict:
        data = self.db.get_all_data_from_db()
        return data

if __name__ == '__main__':
    db = ManageDb()
    db.create_tables() # Late hide this in some script
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(db)
    app.exec()
