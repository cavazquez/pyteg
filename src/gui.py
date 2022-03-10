from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow
from PySide6.QtCore import QSize

# Only needed for access to command line arguments
import sys

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

# Create a Qt widget, which will be our window.
#window = QWidget()
window = QMainWindow()
window.setWindowTitle("PyTeg")
button = QPushButton("Push me")
window.setCentralWidget(button)

#window.setFixedSize(QSize(800, 600))
window.setFixedSize(QSize(1024, 768))

window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()

# Your application won't reach here until you exit and the event
# loop has stopped.
