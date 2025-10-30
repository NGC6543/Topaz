import sys

from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6 import QtWidgets

"""
https://habr.com/ru/companies/skillfactory/articles/599599/

"""


class MainMenu(QtWidgets.QWidget):
    def __init__(self, open_create_menu_callback):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()

        # Button for create a note
        self.create_button = QtWidgets.QPushButton('Create a note')
        self.layout.addWidget(self.create_button)

        # Container where notes will appear
        self.notes_container = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.notes_container)
        self.layout.addStretch()

        self.setLayout(self.layout)

        self.create_button.clicked.connect(open_create_menu_callback)

    def add_note(self, title, text):
        """Add a new note label dynamically."""
        note_widget = QtWidgets.QWidget()
        note_layout = QtWidgets.QVBoxLayout()
        note_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QtWidgets.QLabel(f"Title: <b>{title}</b>")
        text_label = QtWidgets.QLabel(f'Text: {text}')
        text_label.setWordWrap(True)

        note_layout.addWidget(title_label)
        note_layout.addWidget(text_label)
        note_widget.setLayout(note_layout)

        # Add to container
        self.notes_container.addWidget(note_widget)


class CreateMenu(QtWidgets.QWidget):
    def __init__(self, save_callback, back_callback):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()

        # DATA
        self.accept_button = QtWidgets.QPushButton()
        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText("Enter title...")
        self.text = QtWidgets.QTextEdit()
        self.text.setPlaceholderText("Enter note text here...")

        layout.addWidget(self.accept_button)
        layout.addStretch()
        layout.addWidget(self.title)
        layout.addWidget(self.text)
        self.setLayout(layout)

        self.accept_button.setIcon(QtGui.QIcon('check-mark.jpg'))
        self.accept_button.setIconSize(QtCore.QSize(24, 24))
        self.accept_button.setFixedHeight(40)
        self.accept_button.setStyleSheet("text-align: right;")

        # Back button
        self.back_button = QtWidgets.QPushButton("← Back")

        layout.addWidget(self.back_button)
        layout.addWidget(self.accept_button)
        layout.addWidget(self.title)
        layout.addWidget(self.text)
        layout.addStretch()

        self.accept_button.clicked.connect(
            lambda: save_callback(self.title.text(), self.text.toPlainText())
        )
        self.back_button.clicked.connect(back_callback)

    def clear_fields(self):
        """Clear text boxes after saving."""
        self.title.clear()
        self.text.clear()


class MainWindow(QtWidgets.QMainWindow):
    '''Main window.'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Topaz")

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_menu = MainMenu(self.show_create_menu)
        self.create_menu = CreateMenu(self.save_data, self.show_main_menu)

        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.create_menu)

        self.stack.setCurrentWidget(self.main_menu)

    def show_create_menu(self):
        self.stack.setCurrentWidget(self.create_menu)

    def show_main_menu(self):
        self.stack.setCurrentWidget(self.main_menu)

    def save_data(self, title, text):
        if title.strip() or text.strip():
            self.main_menu.add_note(title.strip() or "Untitled", text[:10].strip())
            print(f"Saved note: {title} -> {text[:10]}")
        self.create_menu.clear_fields()
        self.show_main_menu()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
