import json
import os
import sys

from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6 import QtWidgets

"""
https://habr.com/ru/companies/skillfactory/articles/599599/

"""


class ShowMenu(QtWidgets.QWidget):
    def __init__(self, load_data):
        super().__init__()
        self.load_data = load_data()

        self.setup_menu()

    def setup_menu(self):
        self.layout = QtWidgets.QVBoxLayout()
        note_widget = QtWidgets.QWidget()
        if self.load_data is None:
            return
        for data in self.load_data:
            title_widget = QtWidgets.QLabel(data['title'])
            text_widget = QtWidgets.QLabel(data['text'])
            self.layout.addWidget(title_widget)
            self.layout.addWidget(text_widget)
        note_widget.setLayout(self.layout)


class MainMenu(QtWidgets.QWidget):
    def __init__(self, open_create_menu_callback, load_data):
        super().__init__()

        ShowMenu(load_data)

        self.layout = QtWidgets.QVBoxLayout()

        # Button for create a note
        self.create_button = QtWidgets.QPushButton('Create a note')
        self.create_button.setFixedWidth(200)
        self.layout.addWidget(self.create_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Container where notes will appear
        self.notes_container = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.notes_container)
        self.layout.addStretch()

        self.setLayout(self.layout)

        self.create_button.clicked.connect(open_create_menu_callback)

    def add_note(self, title, text):
        """Add a new note label dynamically."""
        # new_but = QtWidgets.QPushButton()

        note_widget = QtWidgets.QWidget()
        note_layout = QtWidgets.QVBoxLayout()
        note_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QtWidgets.QLabel(f"Title: <b>{title}</b>")
        # title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        text_label = QtWidgets.QLabel(f'Text: {text}')
        text_label.setWordWrap(True)

        note_layout.addWidget(title_label)
        note_layout.addWidget(text_label)
        note_widget.setLayout(note_layout)

        # Add to container
        self.notes_container.addWidget(note_widget)


class CreateMenu(QtWidgets.QWidget):
    '''
    Create menu.
    '''
    def __init__(self, save_callback, back_callback):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        layout_for_buttons = QtWidgets.QHBoxLayout()

        # DATA
        self.accept_button = QtWidgets.QPushButton()
        self.accept_button.setFixedWidth(50)
        self.accept_button.setIcon(QtGui.QIcon('check-mark2.png'))
        self.accept_button.setIconSize(QtCore.QSize(24, 24))
        self.accept_button.setFixedHeight(40)
        self.accept_button.setStyleSheet('border: 0px;')

        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText('Enter title')

        self.text = QtWidgets.QTextEdit()
        self.text.setPlaceholderText('Enter note text here')

        # Back button
        self.back_button = QtWidgets.QPushButton('← Back')
        self.back_button.setFixedHeight(40)
        self.back_button.setStyleSheet('border: 0px;')

        layout_for_buttons.addStretch()
        layout_for_buttons.addWidget(self.back_button)
        layout_for_buttons.addWidget(self.accept_button)
        layout.addLayout(layout_for_buttons)
        layout.addWidget(self.title)
        layout.addWidget(self.text)
        layout.addStretch()

        self.accept_button.clicked.connect(
            lambda: save_callback(self.title.text(), self.text.toPlainText())
        )
        self.back_button.clicked.connect(back_callback)
        self.setLayout(layout)

    def clear_fields(self):
        """Clear text boxes after saving."""
        self.title.clear()
        self.text.clear()


class MainWindow(QtWidgets.QMainWindow):
    '''Main window.'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Topaz")
        self.setGeometry(300, 300, 400, 300)

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_menu = MainMenu(self.show_create_menu, self.load_data)
        self.create_menu = CreateMenu(self.save_data, self.show_main_menu)

        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.create_menu)

        self.stack.setCurrentWidget(self.main_menu)

    def show_create_menu(self):
        self.stack.setCurrentWidget(self.create_menu)

    def show_main_menu(self):
        self.stack.setCurrentWidget(self.main_menu)

    def save_data(self, title, text):
        # notes = []
        note = {'title': title, 'text': text}
        # notes.append(note)
        with open('notes.json', 'a', encoding='utf-8') as f:
            # for note in notes
            json.dump(note, f, indent=2, ensure_ascii=False)
        self.show_main_menu()

        # if title.strip() or text.strip():
        #     self.main_menu.add_note(title.strip() or "Untitled", text[:10].strip())
        #     print(f"Saved note: {title} -> {text[:10]}")
        # self.create_menu.clear_fields()
        # self.show_main_menu()

    def load_data(self):
        # data = json.load('notes.json')
        data = None
        if os.path.exists('notes.json'):
            with open('notes.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(data)
        return data


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
