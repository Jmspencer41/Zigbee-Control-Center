import sys
import os

### Adjust sys.path to include project root | Only needed to launch from VS Code Run button ###
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
### End of sys.path adjustment ###


from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
# TODO: from gui.Functionality.dht22.py import TempHumidSensor Not sure if needed here.

def main():

    app = QApplication(sys.argv)
    #temp_humid_monitor = tempHumidMonitor()
    window = MainWindow(None)
    window.show()

    try:
        sys.exit(app.exec())
    finally:
        #temp_humid_monitor.stop() 
        pass # Stop the temp/humid monitor thread on exit

if __name__ == '__main__':
    main()
