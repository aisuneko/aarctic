import threading
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QUrl, QSettings, QCoreApplication
#from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebEngineWidgets import QWebEngineView
import aarctic.utils as utils
import aarctic.server as server

port = 7036 if utils.debug else utils.find_free_port()
address = f"http://{utils.INTERFACE}:{port}"


class WordListEntry(QWidget):
    __slots__ = ['entry', 'd']

    def __init__(self, entry, d):
        QWidget.__init__(self)
        uic.loadUi(utils.uifile("wordlistentry.ui"), self)
        self.entryName.setText(f"<b>{entry}</b>")
        self.dictName.setText(d)


class About(QWidget):
    def get_dict_info(self):
        settings = QSettings()
        settings_dir = settings.value("directory")
        code, data = utils.server_parser(f"{address}/slob", settings_dir)
        if code:
            self.dictInfoView.setText(data)
        else:
            self.dictInfoView.setText(utils.build_dicts_info(data))

    def __init__(self):
        QWidget.__init__(self)
        uic.loadUi(utils.uifile("about.ui"), self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.buttonBox.button(QDialogButtonBox.Close).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Close).setFocus()
        self.buttonBox.rejected.connect(self.close)
        self.get_dict_info()


class Settings(QWidget):
    aboutWindow = None

    def on_browsebutton_clicked(self):
        path = QFileDialog.getExistingDirectory(self, "Open")
        self.dirEdit.setText(path)

    def on_aboutbutton_clicked(self):
        self.aboutWindow = About()
        self.aboutWindow.show()

    def save(self):
        self.settings.setValue("limit", self.limitEdit.value())
        self.settings.setValue("directory", self.dirEdit.text())

    def load(self):
        self.limitEdit.setValue(self.set_limit)
        self.dirEdit.setText(self.set_dir)

    def save_and_exit(self):
        if (int(self.limitEdit.value()) != self.set_limit) or (self.dirEdit.text() != self.set_dir):
            self.save()
            QMessageBox.information(
                self, "Info", "Settings saved. Restart to take effect")
        self.close()

    def __init__(self):
        QWidget.__init__(self)
        uic.loadUi(utils.uifile("settings.ui"), self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.limitEdit.setMaximum(200)
        self.settings = QSettings()
        self.set_limit = int(self.settings.value("limit", 100))
        self.set_dir = self.settings.value("directory", "")
        self.load()
        self.buttonBox.rejected.connect(self.close)
        self.buttonBox.accepted.connect(self.save_and_exit)
        self.browseButton.clicked.connect(self.on_browsebutton_clicked)
        self.aboutButton.clicked.connect(self.on_aboutbutton_clicked)


class MainWindow(QWidget):
    wordLinks = []
    current_index = 0
    settingsWindow = None

    def on_button_clicked(self):
        self.current_index = 0
        query = self.queryEdit.text()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter something")
            return
        code, data = utils.server_parser(
            f"{address}/lookup?word={query}", self.settings_dir)
        if code == 1:
            QMessageBox.critical(self, "Error", data)
        elif code == 2:
            QMessageBox.warning(self, "Warning", data)
        else:
            self.webView.load(QUrl(f"{address}{data[0]['link']}"))
            self.wordList.clear()
            self.wordLinks.clear()
            for i in data:
                item = QListWidgetItem(self.wordList)
                self.wordList.addItem(item)
                row = WordListEntry(i['key'], i['source'])
                item.setSizeHint(row.minimumSizeHint())
                item.setToolTip(f"\"{i['key']}\" from {i['source']}")
                self.wordList.setItemWidget(item, row)
                self.wordLinks.append(i['link'])

    def on_entry_selection(self):
        item = self.wordList.currentRow()
        if item != self.current_index:
            self.webView.load(QUrl(f"{address}{self.wordLinks[item]}"))
            self.current_index = item
            # self.webView.page().mainFrame().findFirstElement("body").setAttribute("onunload", "func()")
            # self.webView.history().clear()
            # QWebSettings.clearMemoryCaches()

    def on_settingsbutton_clicked(self):
        self.settingsWindow = Settings()
        self.settingsWindow.show()

    def init_server(self):
        self.thread = threading.Thread(target=server.main, args=(
            self.settings_dir, self.settings_limit, port))
        self.thread.daemon = True
        self.thread.start()

    def __init__(self):
        QWidget.__init__(self)
        uic.loadUi(utils.uifile("main.ui"), self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.searchButton.clicked.connect(self.on_button_clicked)
        self.settingsButton.clicked.connect(self.on_settingsbutton_clicked)
        self.wordList.itemPressed.connect(self.on_entry_selection)
        self.queryEdit.setFocus()
        self.settings = QSettings()
        self.settings_dir = self.settings.value("directory")
        self.settings_limit = int(self.settings.value("limit", 100))


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(True)
    QCoreApplication.setOrganizationName("aisuneko")
    QCoreApplication.setApplicationName("aarctic")
    mainwindow = MainWindow()
    mainwindow.show()
    mainwindow.init_server()
    app.exec()


if __name__ == '__main__':
    main()
