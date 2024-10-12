import sys
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from scrapping import *
from config import *

modern_style = """
QWidget {
    font-family: Arial, sans-serif;
    font-size: 14px;
    background-color: #f0f0f0;
}
QMainWindow {
    background-color: #ffffff;
}
QLabel {
    color: #333333;
}
QLineEdit {
    border: 2px solid #ccc;
    border-radius: 8px;
    padding: 10px;
    font-size: 14px;
    color: #495057;
}
QLineEdit:focus {
    border-color: #007bff;
}
QPushButton {
    border-radius: 8px;
    color: white;
    padding: 10px 20px;
    font-size: 14px;
    margin: 5px;
}
QPushButton#scrapeButton {
    background-color: #28a745;  /* Green */
}
QPushButton#scrapeButton:hover {
    background-color: #218838;  /* Darker green on hover */
}
QPushButton#closeButton {
    background-color: #dc3545;  /* Red */
}
QPushButton#closeButton:hover {
    background-color: #c82333;  /* Darker red on hover */
}
QTextEdit {
    border: 2px solid #ccc;
    border-radius: 8px;
    padding: 10px;
    font-size: 14px;
    color: #495057;
    background-color: white;
}
QTextEdit:focus {
    border-color: #007bff;
}
"""

class ScraperThread(QThread):
    progress_signal = pyqtSignal(str)

    def __init__(self, file_path, output_text):
        super().__init__()
        self.file_path = file_path
        self.output_text = output_text  # Store the QTextEdit reference
        # self.output_text = ''

    def run(self):
        print_the_output_statement(
            self.output_text, "Scrapping started, please wait for few minutes."
        )
        driver = None  # Initialize driver variable
        SEARCH_COUNT = 0
        DRIVER_QUIT = 50  # Number of entries to process before quitting the 
        init_csv()
        
        try:
            df = read_excel_data(self.file_path, start_row=0, row_limit=5)  # Modify start_row as needed
            all_data = df.fillna('')
            list_of_main_data = all_data.values.tolist()
            driver = create_driver()

            if driver:
                for single_data_list in list_of_main_data:
                    search_terms = single_data_list[3]  # Adjust based on your Excel structure
                    location = f"{single_data_list[4]}, {single_data_list[6]}, {single_data_list[7]}"
                    print_the_output_statement(self.output_text, f"Scrapping Inprogress for  the {search_terms} {location}.")

                    if str(search_terms):
                        print(f"{SEARCH_COUNT} SEARCH_COUNT================================================") 
                        SEARCH_COUNT += 1

                        # Scrape Yelp data
                        restaurant_data = scrape_yelp_data(driver, search_terms, location)
                        
                        # Process scraped data
                        if restaurant_data['restaurant_data']:
                            single_data_list[9] = restaurant_data['yelplink']
                            single_data_list[10] = restaurant_data['restaurant_name']
                            single_data_list[11] = restaurant_data['phone']
                            single_data_list[12] = restaurant_data['site_url']
                            single_data_list[13] = restaurant_data['rating']
                            append_data_in_csv(single_data_list)  # Append processed data to CSV
                        else:
                            append_data_in_csv(single_data_list)  # Append original data if no restaurant found
                    else:
                        append_data_in_csv(single_data_list)
                        SEARCH_COUNT += 1
                        print(f"Missing data for 'DBA Name' in row {SEARCH_COUNT}, skipping...")

                    if SEARCH_COUNT >= DRIVER_QUIT:
                        print(f"Closing driver after processing {DRIVER_QUIT} entries...")
                        driver.quit()  
                        driver = create_driver()
                        SEARCH_COUNT = 0

                driver.quit() 
            else:
                print("Failed to initialize the web driver.")

        except Exception as e:
            self.progress_signal.emit(f"An error occurred: {str(e)}")
        finally:
            if driver:
                driver.quit()  
        print_the_output_statement(self.output_text, f"Scraping completed.")
        # After all scraping is done, convert CSV to Excel
        if convert_csv_to_excel():
            # self.progress_signal.emit("CSV successfully converted to Excel.")
            print_the_output_statement(self.output_text, f"Ready To Downlaod")
            prompt_file_download(self.output_text)
            
        else:
            self.progress_signal.emit("Failed to convert CSV to Excel.")

class ScraperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(500, 600, 800, 500)
        self.selected_file = ""
        # self.center_window()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Create the title 
        title_label = QLabel(f"<h1>{APP_NAME}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Create a Upload File 
        form_layout = QVBoxLayout()
        form_layout.addSpacing(20)
        layout.addLayout(form_layout)
        self.upload_csv_button = QPushButton("Choose Excel File")
        self.upload_csv_button.setStyleSheet("color: black;")
        self.upload_csv_button.clicked.connect(self.select_file)
        form_layout.addWidget(self.upload_csv_button)

        button_layout = QHBoxLayout()
        form_layout.addLayout(button_layout)
        self.scrape_data_button = QPushButton("Scrape Data", objectName="scrapeButton")
        self.scrape_data_button.setEnabled(False)
        self.scrape_data_button.clicked.connect(self.scrap_data)
        button_layout.addWidget(self.scrape_data_button)

        self.close_button = QPushButton("Close Window", objectName="closeButton")
        self.close_button.clicked.connect(self.close_application)
        button_layout.addWidget(self.close_button)
        self.create_output_area(layout)

    def create_output_area(self, layout):
        layout.addWidget(QLabel("<b>Output:</b>"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Arial", 12))
        layout.addWidget(self.output_text)

    def select_file(self):
        print_the_output_statement(self.output_text, "Uploading Excel...")
        options = QFileDialog.Options()
        self.selected_file, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "All Files (*);;CSV Files (*.csv)", options=options)
        if self.selected_file:
            print_the_output_statement(self.output_text, f"Excel file selected: {self.selected_file}")
            self.scrape_data_button.setEnabled(True)
        else:
            self.output_text.append("No file selected.")
            self.scrape_data_button.setEnabled(False)
            print_the_output_statement(self.output_text, f"Please choose a valid Excel file.")

    def scrap_data(self):
        if self.selected_file:
            self.thread = ScraperThread(self.selected_file, self.output_text)
            self.thread.progress_signal.connect(self.update_output)
            
            self.thread.start()
        else:
            QMessageBox.warning(self, "No Input", "Please select a file before scraping.")

    def update_output(self, message):
        self.output_text.append(message)

    def close_application(self):
        print("Closing the application...")
        self.close()

# Run the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(modern_style)
    scraper_app = ScraperApp()
    scraper_app.show()
    sys.exit(app.exec_())
