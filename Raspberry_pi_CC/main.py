import sys
import os

### Adjust sys.path to include project root | Only needed to launch from VS Code Run button ###
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
### End of sys.path adjustment ###


from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
