import json
import os
import sys
from datetime import datetime

import openai
import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSize, QTimer, QThread
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QLabel, \
    QInputDialog, QScrollArea, QFrame, QVBoxLayout, QSizePolicy, QGridLayout, QTextEdit, QLineEdit, QDialog, QHBoxLayout
from localisation import Lang
from toast import QToaster

color_schemes = {
    "dark": {
        "buttons": "ffffff",
        "background": "303138",
        "foreground": "3C4A4A",
        "red": "E62763",
        "green": "60F029",

        "label_lower": "0D4F42",
        "label_center": "289C85",
        "label_upper": "287062"
    },
    "light": {
        "buttons": "222222",
        "background": "E8E7C9",
        "foreground": "DBDBC3",
        "red": "E62763",
        "green": "60F029",

        "label_lower": "B000E6",
        "label_center": "BB4FDB",
        "label_upper": "D342FF"
    },
}


def show_dialog(title: str, subtitle: str = '', icon=QMessageBox.Information, buttons=QMessageBox.Ok, default_button=0):
    msgBox = QMessageBox()
    msgBox.setStandardButtons(buttons)

    msgBox.setText(subtitle)
    msgBox.setWindowTitle(title)
    msgBox.setIcon(icon)
    msgBox.setDefaultButton(default_button)
    return msgBox.exec()


def translate(text, destination='en'):
    url = f"https://translate.google.com/translate_a/single?client=gtx&sl=auto&tl={destination}&dt=t&q={text}"
    response = requests.get(url)
    translated = response.json()[0][0][0].capitalize()
    language = response.json()[2]
    return translated, language


class AllowToProceed(Exception):
    def __init__(self, message: str = ''):
        self.txt = message


class TaskLabel(QWidget):
    def __init__(self, title, description=None, column=0, deadline=None, reward=None, timestamp=None):
        super().__init__()

        self.reward = None if reward == '' else reward
        self.column = column
        self.deadline = deadline
        self.description = lang["gui.tasks.labels.no_desc"] if description is None else description
        self.title = title
        self.upload_timestamp = datetime.now().strftime("[%H:%M:%S] [%d.%m.%y]") if timestamp is None else timestamp

        self.background_rect = QFrame()
        self.lower_frame = QFrame()
        self.upper_frame = QFrame()
        self.title_label = QLabel(self.title)
        self.desc_label = QLabel(self.description)
        self.timestamp_label = QLabel(self.upload_timestamp)

        self.prev_button = QPushButton()
        self.next_button = QPushButton()
        self.del_button = QPushButton()

        self.setup_widgets()
        # self.setup_layouts()

    def setup_widgets(self):
        # Create a black rect widget
        self.background_rect.setAutoFillBackground(False)
        self.background_rect.setStyleSheet("background-color: #805CFF; padding: 10px 20px; border-radius: 5px;")
        self.background_rect.setMaximumWidth(600)
        self.background_rect.setMinimumSize(200, 100)

        main_layout = QVBoxLayout()
        upper_layout = QHBoxLayout()
        lower_layout = QGridLayout()

        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        self.desc_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.desc_label.setMinimumWidth(200)
        self.desc_label.setWordWrap(True)

        self.timestamp_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.timestamp_label.setStyleSheet('color: white')
        self.timestamp_label.setMinimumSize(150, 50)

        self.del_button.setIcon(QIcon("icons/tile_buttons/trash.svg"))
        self.next_button.setIcon(QIcon("icons/tile_buttons/arrows/next.svg"))
        self.prev_button.setIcon(QIcon("icons/tile_buttons/arrows/prev.svg"))

        ico_size = 40
        self.next_button.setIconSize(QSize(ico_size, ico_size))
        self.prev_button.setIconSize(QSize(ico_size, ico_size))
        self.del_button.setIconSize(QSize(ico_size * 2, ico_size * 2))

        self.next_button.setStyleSheet("background: transparent;")
        self.prev_button.setStyleSheet("background: transparent;")
        self.del_button.setStyleSheet("background: transparent;")

        self.del_button.setFixedWidth(80)

        lower_layout.addWidget(self.prev_button, 0, 0, alignment=Qt.AlignLeft)
        lower_layout.addWidget(self.timestamp_label, 0, 1, alignment=Qt.AlignCenter)
        lower_layout.addWidget(self.next_button, 0, 2, alignment=Qt.AlignRight)

        upper_layout.addWidget(self.title_label)
        upper_layout.addWidget(self.del_button)

        self.upper_frame.setMinimumHeight(70)
        self.upper_frame.setMaximumHeight(200)
        self.upper_frame.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.upper_frame.setStyleSheet("background-color: #6940F7; border-radius: 3px;")
        self.upper_frame.setLayout(upper_layout)

        self.lower_frame.setFixedHeight(50)
        self.lower_frame.setStyleSheet("background-color: #3B1BAB; border-radius: 3px;")
        lower_layout.setContentsMargins(0, 0, 0, 0)
        self.lower_frame.setContentsMargins(0, 0, 0, 0)
        self.lower_frame.setLayout(lower_layout)

        main_layout.addWidget(self.upper_frame)
        main_layout.addWidget(self.desc_label, alignment=Qt.AlignLeft | Qt.AlignTop)
        main_layout.addWidget(self.lower_frame)

        parent_layout = QVBoxLayout()

        # Add the grid layout to the rect widget
        self.background_rect.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.background_rect.setLayout(main_layout)

        # Add the rect widget to the parent layout
        parent_layout.addWidget(self.background_rect)
        self.background_rect.setContentsMargins(0, 0, 0, 0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.background_rect.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        # Assign the parent layout to the parent widget
        self.setLayout(parent_layout)

    def get_dict_form(self):
        return {
            "title": self.title,
            "desc": self.description,
            "reward": self.reward,
            "deadline": self.deadline,
            "timestamp": self.upload_timestamp
        }


class OpenAIFetcher(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.data = {}
        self.topic = ''
        self.result = 'OK'
        self.prev = []

    def get_previous_responses(self):
        result = ''
        prefixes = ['AI', 'Answer']
        for i, response in enumerate(self.prev):
            prefix = prefixes[i % 2]
            result += f'\n{prefix}: {response}'
        if len(result): result += '\nAI:'
        return result

    def run(self):
        try:
            topic_en, original_lang = translate(self.topic)
            prompt = ("Create a title, description and reward for provided topic, if there is too few information "
                      "provided, you can ask for more using one of this methods: "
                      
                      "chooseOption \"Message\" | option that splitted with `|` (you will get number of option "
                      "in answer), getText \"What text you want to get\", "
                      "getTrue \"Binary question with yes or no answers\" and "
                      "endDialog \"message\" if you want to end it, can be used if got unclear commands multiple times."
                      
                      "Format answer like: "
                      "\"title, description, reward\".\n\n"
                      "EXAMPLE #1:\n"
                      "Topic: \"Finish my project\"\n"
                      "AI: getText \"What is your project about?\"\n"
                      "Answer: About creating TODO list using python\n"
                      "AI: \"Project finishing, Finish my TODO list project in Python and publish it to github, +1 project in the portfolio\"\n\n"
                      "EXAMPLE #2:\n"
                      "Topic: \"Doing my homework\"\n"
                      "AI: \"Homework, Finish my homework until 22:00, Good mark tomorrow\"\n\n"
                      "Topic: \"{}\"{}".format(topic_en, self.get_previous_responses()))
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=1,
                max_tokens=100,
                top_p=1,
                frequency_penalty=0.5,
                presence_penalty=0,
                stop=["."]
            )
            answer_en = response["choices"][0]["text"]
            answer_en = answer_en.strip('.').strip()
        except Exception as exception:
            self.result = str(exception)
        else:
            try:
                while x.busy: pass
                print('Proceeding...\t\t', answer_en)
                if answer_en == '':
                    self.result = 'REJECT'
                    raise AllowToProceed
                self.data = {}
                lines = answer_en.split('\n')
                first_line = lines[0].replace("AI:", "").replace('"', "").strip()
                self.prev.append(first_line[4:])
                for get_method in ["enddialog", "gettext", "gettrue", "chooseoption"]:
                    if first_line.lower().startswith(get_method):  # AI: getText "..."
                        end_index = len(get_method)
                        self.data['method'] = get_method
                        if get_method == 'chooseoption':
                            split_index = first_line.find("|")
                            self.data['message'] = first_line[end_index:split_index].strip()
                            self.data['options'] = first_line[split_index+1:].strip().split('|')
                        else:
                            self.data['message'] = first_line[end_index:]
                        self.result = 'REPLY'
                        raise AllowToProceed
                else:
                    try:
                        clear_line = first_line.strip().strip('"')
                        title, desc, reward = clear_line.split(',')
                        self.data['title'] = title
                        self.data['desc'] = desc
                        self.data['reward'] = reward
                        self.result = 'OK'
                    except Exception:
                        pass
            except AllowToProceed:
                pass


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.busy = False
        self.fetch = OpenAIFetcher()
        self.autosaver = QTimer()
        self.autosaver.timeout.connect(self.autosave)
        self.autosaver.start(30000)

        self.toaster = QToaster()
        self.dark_mode = app_data["is_light_theme"]
        QToolTip.setFont(QFont("Aubrey Pro", 20))

        self.setWindowTitle(lang["gui.titles.main_window"])
        self.setWindowIcon(QIcon("icons/title_ico.png"))
        self.setGeometry(500, 200, 1000, 500)

        self.grid_layout = QGridLayout()

        buttons_layout = QGridLayout()
        button_icons = ["add_task", "change_language", "auto_generate"]
        button_functions = [self.show_form_for_add_task, self.change_lang, self.on_auto_generate_click]
        button_icon_sizes = [75, 75, 75]
        self.right_buttons = []
        for i, icon_name in enumerate(button_icons):
            ico_size = button_icon_sizes[i]
            icon = QIcon(f"icons/tile_buttons/{icon_name}.svg")
            # icon.actualSize(QSize(100, 100))

            self.right_buttons.append(QPushButton(self))
            self.right_buttons[i].setIconSize(QSize(ico_size, ico_size))
            self.right_buttons[i].setStyleSheet("background-color: rgba(0, 0, 0, 5);border: none;")
            self.right_buttons[i].setToolTip(lang[f"tooltips.{icon_name}"])
            self.right_buttons[i].setIcon(icon)
            self.right_buttons[i].clicked.connect(button_functions[i])
            buttons_layout.addWidget(self.right_buttons[i], 0, i, 1, 1)

        self.generate_list_of_tasks()

        self.dark_mode_button = QPushButton(self)
        self.dark_mode_button.setIconSize(QtCore.QSize(100, 100))
        self.dark_mode_button.resize(50, 90)
        self.dark_mode_button.setStyleSheet("background-color: rgba(255, 255, 255, 0);border: none;")

        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(10, 0, 10, 7)
        last_row = self.grid_layout.rowCount()
        self.grid_layout.addLayout(buttons_layout, last_row, 2,
                                   alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.grid_layout.addWidget(self.dark_mode_button, last_row, 0,
                                   alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)

        self.dark_mode_button.clicked.connect(self.on_theme_switch)
        self.on_theme_switch()
        self.setLayout(self.grid_layout)

        self.show()

    def on_auto_generate_click(self):
        topic, okay = QInputDialog.getText(self, "Input", "Input topic for auto-generate")
        if okay:
            openai.api_key = app_data["api_key"]
            self.toaster.showMessage(self, f'Generating task for you on topic "{topic}"', timeout=3000, closable=False)

            self.fetch = OpenAIFetcher()
            self.fetch.finished.connect(self.show_auto_generated_form)
            self.fetch.topic = topic
            self.fetch.start()

    def show_auto_generated_form(self):
        self.busy = True
        data = self.fetch.data
        if self.fetch.result == 'OK':
            self.toaster.showMessage(self, 'Created task for you.')
            self.show_form_for_add_task(data['title'], data['desc'], data['reward'])
        elif self.fetch.result == 'REPLY':
            method = data['method']
            okay, reply = False, ''
            if method == 'gettext':
                reply, okay = QInputDialog.getText(self, "Providing some text to AI", data['message'])
            elif method == 'gettrue':
                yes_or_no = show_dialog("Providing some text to AI", data['message'], QMessageBox.Question,
                                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                reply = ['Yes', 'No'][yes_or_no == QMessageBox.No]
                okay = reply != QMessageBox.Cancel
            elif method == 'chooseoption':
                item, okay = QInputDialog.getItem(self, "Providing some text to AI", data['message'], data['options'])
                reply = '№' + str(data['options'].index(item) + 1)

            elif method == 'enddialog':
                self.toaster.showMessage(self, 'OpenAI\'s tool ended dialog with message "{}"'.format(data['message']),
                                         icon=QtWidgets.QStyle.SP_MessageBoxWarning)

            if okay:
                self.fetch.prev.append(reply)
                self.fetch.start()
        else:
            self.toaster.showMessage(self, 'Something went wrong...\n' + self.fetch.result,
                                     icon=QtWidgets.QStyle.SP_MessageBoxCritical, timeout=10000, margin=30)
        try:
            del self.form
        except AttributeError:
            pass
        self.busy = False

    def generate_list_of_tasks(self):
        column_names = [
            lang["gui.tasks.columns.awaits"],
            lang["gui.tasks.columns.in_process"],
            lang["gui.tasks.columns.finished"]]
        for x, label_name in enumerate(column_names):
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.NoFrame)
            list_widget = QWidget()

            scroll_layout = QVBoxLayout()
            scroll_layout.addWidget(scroll_area)

            list_layout = QVBoxLayout(list_widget)

            str_x = str(x)

            if str_x in app_data["tasks"].keys():
                for dictionary in app_data["tasks"][str_x]:
                    label = self.create_task_from_dict(dictionary)

                    list_layout.addWidget(label)

            spaces = 100
            label = QLabel(' ' * spaces + label_name + ' ' * spaces)
            label.setAutoFillBackground(True)
            label.setMinimumSize(300, 60)
            label.setFixedHeight(60)
            label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)

            scroll_area.setWidget(list_widget)

            self.grid_layout.addWidget(label, 1, x, alignment=QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
            self.grid_layout.addLayout(scroll_layout, 2, x, alignment=QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)

    def change_lang(self):
        primary_ids_count = len(primary_lang.dictionary.keys())
        languages_names = []
        languages_short = []
        languages_full = []
        for path in os.listdir("langs"):
            if path.endswith(".txt"):
                clear_lang = path[:5]
                new_lang = Lang(clear_lang)
                lang_name = new_lang["language"]
                ids_count = len(new_lang.dictionary.keys())
                languages_names.append(lang_name)
                languages_short.append(clear_lang)
                languages_full.append(f"({clear_lang}) {lang_name.capitalize()} "
                                      f"{round(ids_count / primary_ids_count * 100, 2)}%")

        del_index = languages_names.index(lang["language"])
        languages_full.pop(del_index)

        languages_full.sort(key=lambda x: ord(x[1]))
        selected, okay = QInputDialog.getItem(self, lang["gui.titles.data_prompt"],
                                              "Select language:" if lang.language == 'en_US' else
                                              f"Select Language/" + lang["gui.titles.language_selection"],
                                              languages_full, 0, False)
        if okay:
            selected_language_index = languages_full.index(selected)
            if selected_language_index >= del_index: selected_language_index += 1
            app_data["lang"] = languages_short[selected_language_index]

            self.closeEvent(QtGui.QCloseEvent())
            app.exit(101)

    def on_delete_task(self):
        row, column, task = self.get_task_by_sender()
        if column == 2:
            if task.reward is not None:
                reward_content = lang["gui.tasks.labels.reward.desc"] + ' ' + task.reward
                show_dialog(lang["gui.tasks.labels.reward.name"], reward_content)
                self.toaster.showMessage(self, lang["gui.tasks.labels.completed_with_reward"].
                                         format(task.title, task.reward))
            else:
                self.toaster.showMessage(self, lang["gui.tasks.labels.completed"].format(task.title),
                                         corner=QtCore.Qt.BottomRightCorner)
            reply = QMessageBox.Yes
        else:

            reply = show_dialog(lang["gui.tasks.management.delete.name"],
                                lang["gui.tasks.management.delete.desc"].format(task.title), QMessageBox.Question,
                                QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            task.deleteLater()
            self.autosave(False)

    def find_task_in_scroll_area(self, target: TaskLabel):
        for column in range(3):
            scroll_area = self.grid_layout.itemAtPosition(2, column).itemAt(0).widget()
            scroll_area: QScrollArea
            tasks = scroll_area.findChildren(TaskLabel)
            if target in tasks:
                return tasks.index(target), column
        return -1, -1

    def get_task_by_coordinates(self, row: int, column: int) -> TaskLabel:
        created_tasks = self.grid_layout.itemAtPosition(2, column).itemAt(0).widget().findChildren(TaskLabel)
        return created_tasks[row]

    def show_form_for_add_task(self, title='', desc='', reward=''):
        self.form = Form()
        self.form.title_edit.setText(str(title))
        self.form.description_edit.setText(str(desc))
        self.form.reward_edit.setText(str(reward))
        self.form.create_button.clicked.connect(self.add_new_task)
        self.form.exec_()

    def add_new_task(self):
        if self.form.title_edit.text() == '':
            show_dialog(lang["warnings.no_title_for_task.name"], lang["warnings.no_title_for_task.desc"],
                        QMessageBox.Warning)
            return
        vals = [self.form.title_edit.text(), self.form.description_edit.toPlainText(),
                self.form.reward_edit.toPlainText()]
        keys = ["title", "desc", "reward"]
        new_dict = {}
        for index, key in enumerate(keys):
            new_dict[key] = vals[index]

        new_task = self.create_task_from_dict(new_dict)
        scroll = self.grid_layout.itemAtPosition(2, 0).layout().itemAt(0).widget()
        scroll.widget().layout().insertWidget(0, new_task)
        self.redraw_()
        self.autosave(False)

        del self.form
        self.form = Form()

    def on_theme_switch(self):
        self.dark_mode = not self.dark_mode
        color_scheme = color_schemes[("light", "dark")[self.dark_mode]]
        background = '#' + color_scheme["background"]
        foreground = '#' + color_scheme["foreground"]
        buttons_col = '#' + color_scheme["buttons"]
        icon = QtGui.QIcon()

        if self.dark_mode:
            self.dark_mode_button.setToolTip(lang["tooltips.swap_to_light_theme"])
            icon.addPixmap(QtGui.QPixmap("icons/tile_buttons/dark_theme.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        else:
            self.dark_mode_button.setToolTip(lang["tooltips.swap_to_dark_theme"])
            icon.addPixmap(QtGui.QPixmap("icons/tile_buttons/light_theme.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)

        self.set_object_color(self, background)
        self.set_object_color(QToolTip, foreground)
        self.dark_mode_button.setIcon(icon)

        buttons = [self.dark_mode_button]
        buttons.extend(self.right_buttons)
        for button in buttons:
            button.setStyleSheet("background-color: rgba(255, 255, 255, 0);border: none;")
            effect = QtWidgets.QGraphicsColorizeEffect()
            effect.setColor(QtGui.QColor(buttons_col))
            button.setGraphicsEffect(effect)

        self.redraw_()

    def create_task_from_dict(self, dictionary):
        keys = dictionary.keys()
        title = dictionary["title"]
        desc = dictionary["desc"] if "desc" in keys else lang["gui.tasks.labels.no_desc"]
        column = dictionary["column"] if "column" in keys else 0
        deadline = dictionary["deadline"] if "deadline" in keys else None
        reward = dictionary["reward"] if "reward" in keys else None
        upload_timestamp = dictionary["timestamp"] if "timestamp" in keys else None

        task = TaskLabel(title, desc, column, deadline, reward, upload_timestamp)
        task.next_button.clicked.connect(self.move_task_right)
        task.prev_button.clicked.connect(self.move_task_left)
        task.del_button.clicked.connect(self.on_delete_task)

        return task

    def redraw_(self):
        color_scheme = color_schemes[("light", "dark")[self.dark_mode]]
        background = '#' + color_scheme["background"]
        foreground = '#' + color_scheme["foreground"]
        buttons_col = '#' + color_scheme["buttons"]
        label_lower = '#' + color_scheme["label_lower"]
        label_center = '#' + color_scheme["label_center"]
        label_upper = '#' + color_scheme["label_upper"]
        for index in range(3):
            widget_headers = self.grid_layout.itemAtPosition(1, index).widget()
            widget_headers.setStyleSheet(f"background-color: {foreground};"
                                         f"color: {buttons_col};"
                                         "font-size: 20px;"
                                         f"border: {background};")
            created_tasks = self.grid_layout.itemAtPosition(2, index).itemAt(0).widget().findChildren(TaskLabel)
            for created_task in created_tasks:
                created_task: TaskLabel

                created_task.upper_frame.setStyleSheet(f"background-color: {label_upper}; border-radius: 3px;")
                created_task.lower_frame.setStyleSheet(f"background-color: {label_lower}; border-radius: 3px;")
                created_task.background_rect.setStyleSheet(f"background-color: {label_center};"
                                                           "padding: 10px 20px; border-radius: 5px;")

                for text_label in [created_task.title_label, created_task.desc_label]:
                    text_label.setStyleSheet(f"color: {buttons_col};")

                for button in [created_task.next_button, created_task.prev_button, created_task.del_button]:
                    effect = QtWidgets.QGraphicsColorizeEffect()
                    effect.setColor(QtGui.QColor(buttons_col))
                    button.setGraphicsEffect(effect)

    def get_task_by_sender(self):
        sender = self.sender()
        task = sender.parent().parent().parent()
        task: TaskLabel
        row, column = self.find_task_in_scroll_area(task)
        return row, column, task

    @staticmethod
    def set_object_color(subject, color):
        palette = subject.palette()
        palette.setColor(QtGui.QPalette.Normal, QtGui.QPalette.Window, QtGui.QColor(color))
        palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Window, QtGui.QColor(color))
        subject.setPalette(palette)

    def closeEvent(self, event):
        self.save_tasks_to_file()
        event.accept()

    def save_tasks_to_file(self):
        app_data["is_light_theme"] = not self.dark_mode
        app_data["tasks"] = {"0": [], "1": [], "2": []}
        for column in range(3):
            created_tasks = self.grid_layout.itemAtPosition(2, column).itemAt(0).widget().findChildren(TaskLabel)
            for created_task in created_tasks:
                created_task: TaskLabel
                app_data["tasks"][str(column)].append(created_task.get_dict_form())
                # print(created_task.get_dict_form(), created_task.column)

    def move_task_left(self):
        self.move_task_to_n_tiles(n=-1)

    def move_task_right(self):
        self.move_task_to_n_tiles(n=1)

    def move_task_to_n_tiles(self, n):
        row, column, task = self.get_task_by_sender()
        clone = self.create_task_from_dict(task.get_dict_form())

        task.deleteLater()
        new_column = column + n + 3 if column + n % 3 < 0 else (column + n) % 3
        scroll = self.grid_layout.itemAtPosition(2, new_column).layout().itemAt(0).widget()
        scroll: QScrollArea
        scroll.widget().layout().insertWidget(0, clone)

        clone.column = new_column
        if clone.column == 2:
            clone.del_button.setIcon(QIcon("icons/tile_buttons/checkmark.svg"))
        else:
            clone.del_button.setIcon(QIcon("icons/tile_buttons/trash.svg"))
        self.redraw_()

    def autosave(self, is_auto=True):
        now = datetime.now()
        if is_auto:
            self.toaster.showMessage(self, lang["sys.autosave"] + now.strftime(" [%H:%M] [%d/%m]"),
                                     corner=QtCore.Qt.TopEdge, timeout=800, closable=False)
        else:
            self.toaster.showMessage(self, lang["sys.save"] + now.strftime(" [%H:%M] [%d/%m]"),
                                     corner=QtCore.Qt.TopEdge, timeout=3000, closable=False)
        self.save_tasks_to_file()
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(app_data, f)


class Form(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(lang["gui.titles.data_prompt"])
        self.setWindowIcon(QIcon("icons/gui/gear.svg"))

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.title_label = QLabel(lang["form.title"] + ':')
        self.title_edit = QLineEdit()

        self.description_label = QLabel(lang["form.description"] + ':')
        self.description_edit = QTextEdit()

        self.reward_label = QLabel(lang["form.reward"] + ':')
        self.reward_edit = QTextEdit()
        self.reward_edit.setMinimumHeight(20)

        self.create_button = QPushButton(lang["form.create"], self)
        self.create_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton(lang["form.cancel"], self)
        self.cancel_button.clicked.connect(self.reject)

    def create_layout(self):
        form_layout = QGridLayout(self)
        form_layout.addWidget(self.title_label, 0, 0)
        form_layout.addWidget(self.title_edit, 0, 1)

        form_layout.addWidget(self.description_label, 1, 0)
        form_layout.addWidget(self.description_edit, 1, 1)

        form_layout.addWidget(self.reward_label, 3, 0)
        form_layout.addWidget(self.reward_edit, 3, 1)

        form_layout.addWidget(self.create_button, 4, 0)
        form_layout.addWidget(self.cancel_button, 4, 1)


while __name__ == "__main__":
    files = os.listdir()
    app = QApplication(sys.argv)
    primary_lang = Lang("ru_RU")

    if "data.json" not in files:
        key, okay = QInputDialog.getText(None, "Proved api key for open ai",
                                         "It can be found: https://beta.openai.com/account/api-keys, for free")
        if not okay: break
        file = open("data.json", "w")
        file.write(
            '{"lang": "en_US", "api_key": "APIKEY", "is_light_theme": false, "tasks": {"0": [{"title": "Example"}]}}'.
            replace("APIKEY", key))
        file.close()

    with open("data.json", "r", encoding="utf-8") as f:
        try:
            app_data = json.load(f)
            lang = Lang(app_data["lang"])
        except ValueError as exception:
            lang = Lang('en_US')
            reply = show_dialog('File corruption',
                                f"File with app's data got corrupted!\nWant to regenerate it??\n\n - {exception} error",
                                QMessageBox.Critical, QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                f.close()
                os.remove("data.json")
                del app
                continue
            break

    x = Window()
    exit_code = app.exec_()

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(app_data, f)

    if exit_code == 101:  # reloading code
        del app, x
        continue
    sys.exit(exit_code)
