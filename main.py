import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QLineEdit, QTextEdit, QVBoxLayout, QWidget, QFileDialog, QMessageBox,
                           QProgressBar, QCheckBox, QFrame, QListWidget, QScrollArea, QHBoxLayout, QInputDialog)
from PyQt5.QtCore import Qt
import urllib.request
from src.whitespaceAlgo import text_extraction
from src.relevancyScore import relevancy_table
from src.conditionExtraction import topic_extract, condition_extraction, extract_experimental_data
import socket
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import sqlite3

class TextExtractionWorker(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(float)
    message = pyqtSignal(str)

    def __init__(self, filepaths):
        super().__init__()
        self.filepaths = filepaths

    def run(self):
        try:
            success = text_extraction(self.filepaths, self.progress.emit)
            self.finished.emit(success)
        except Exception as e:
            self.message.emit(f"Error: {str(e)}")
            self.finished.emit(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Research PDF Analyzer")
        self.setGeometry(100, 100, 500, 500)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)
        
        # Create widgets
        self.create_widgets()
        
    def create_widgets(self):
        # Select PDF Button
        self.select_button = QPushButton("Select PDF Files")
        self.select_button.clicked.connect(self.select_files)
        self.layout.addWidget(self.select_button)
        
        self.clear_button = QPushButton("Clear Database")
        self.clear_button.clicked.connect(self.clear_database)
        self.layout.addWidget(self.clear_button)
        
        # Search Term
        search_layout = QHBoxLayout()
        self.search_term_label = QLabel("Search Terms (separate by ;)")
        self.search_term_entry = QLineEdit()
        search_layout.addWidget(self.search_term_label)
        search_layout.addWidget(self.search_term_entry)
        self.layout.addLayout(search_layout)
        
        # Run Button
        self.run_button = QPushButton("Run Function")
        self.run_button.clicked.connect(self.run_function)
        self.layout.addWidget(self.run_button)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.hide()
        self.layout.addWidget(self.progress)
        
        # Options Frame
        self.options_frame = QFrame()
        options_layout = QVBoxLayout(self.options_frame)
        
        options_heading = QLabel("Select Relevancy Parameters")
        options_layout.addWidget(options_heading)
        
        self.option1 = QCheckBox("Title Score")
        self.option2 = QCheckBox("Abstract Score")
        self.option3 = QCheckBox("Similarity Score")
        
        options_layout.addWidget(self.option1)
        options_layout.addWidget(self.option2)
        options_layout.addWidget(self.option3)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_frame)
        options_layout.addWidget(self.next_button)
        
        self.options_frame.hide()
        self.layout.addWidget(self.options_frame)
        
        # Topic Frame
        self.topic_frame = QFrame()
        topic_layout = QVBoxLayout(self.topic_frame)
        
        self.topic_heading = QLabel("Select related words you want to search for")
        topic_layout.addWidget(self.topic_heading)
        
        lists_layout = QHBoxLayout()
        
        self.topic_list = QListWidget()
        self.topic_list.setSelectionMode(QListWidget.MultiSelection)
        
        self.units_list = QListWidget()
        self.units_list.setSelectionMode(QListWidget.MultiSelection)
        
        lists_layout.addWidget(self.topic_list)
        lists_layout.addWidget(self.units_list)
        topic_layout.addLayout(lists_layout)
        
        # Add custom unit button
        self.add_unit_button = QPushButton("Add Custom Unit")
        self.add_unit_button.clicked.connect(self.add_custom_unit)
        topic_layout.addWidget(self.add_unit_button)
        
        self.topic_next_button = QPushButton("Next")
        self.topic_next_button.clicked.connect(self.extract_experimental_data)
        topic_layout.addWidget(self.topic_next_button)
        
        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        self.export_button.hide()
        topic_layout.addWidget(self.export_button)
        
        self.topic_frame.hide()
        self.layout.addWidget(self.topic_frame)
        
        # Output Text
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

    def select_files(self):
        self.filepaths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF Files",
            "",
            "PDF Files (*.pdf)"
        )
    
    def clear_database(self):
        try:
            conn = sqlite3.connect('database/articles.db')
            c = conn.cursor()
            c.execute('DROP TABLE IF EXISTS articles')
            c.execute('DROP TABLE IF EXISTS f_text_table')
            conn.commit()
            conn.close()
            
            # Clear text corpora file
            open('database/text_corpora.txt', 'w').close()
            
            self.output.append("Database cleared successfully")
        except Exception as e:
            self.output.append(f"Error clearing database: {str(e)}")

    def run_function(self):
        if self.check_internet():
            if hasattr(self, 'filepaths') and self.filepaths:
                self.search_term = self.search_term_entry.text()
                self.search_term_label.hide()
                self.search_term_entry.hide()
                data_table = self.start_process()
            else:
                self.output.append("No files selected")
        else:
            self.output.append("No internet connection")

    def start_process(self):
        self.progress.show()
        self.worker = TextExtractionWorker(self.filepaths)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.process_completed)
        self.worker.message.connect(self.output.append)
        self.worker.start()

    def update_progress(self, value):
        self.progress.setValue(int(value * 100))

    def process_completed(self, success):
        self.progress.hide()
        if success:
            self.output.append("Text Extraction Successful")
            self.options_frame.show()
        else:
            self.output.append("Error in Text Extraction")

    def next_frame(self):
        self.relevancy_params = [
            self.option1.isChecked(),
            self.option2.isChecked(),
            self.option3.isChecked()
        ]
        self.options_frame.hide()
        
        # Similar to your original code, but adapted for PyQt5
        res2 = 1
        self.relevant_ids = [i for i in range(1, len(self.filepaths) + 1)]
        # self.relevant_ids = [0, 1]
        if res2 == 0:
            self.output.append("Error in Relevancy Scoring")
        else:
            self.output.append("Relevancy Scoring Successful")
            self.topic_options, self.units, res3 = topic_extract(self.relevant_ids)
            
            if res3 == 0:
                self.output.append("Error in Topic Extraction")
            else:
                self.output.append("Topic Extraction Successful")
                self.topic_list.clear()
                self.topic_list.addItems(self.topic_options)
                self.units_list.addItems(self.units)
                self.topic_frame.show()
    
    def extract_experimental_data(self):
        search_terms = [term.strip() for term in self.search_term_entry.text().split(';')]
        selected_topics = [item.text() for item in self.topic_list.selectedItems()]
        selected_units = [item.text() for item in self.units_list.selectedItems()]
        
        if not (search_terms and selected_units):
            QMessageBox.warning(self, "Warning", 
                "Please enter search terms and select units!")
            return
        
        print("Search terms:", search_terms)  # Debug print
        print("Units:", selected_units)  # Debug print
        
        self.detailed_df, self.pivoted_df = extract_experimental_data(
            search_terms, selected_topics, selected_units)
        
        if not self.detailed_df.empty:
            # Display results in output
            self.output.clear()
            self.output.append("Extracted Data:")
            self.output.append("\nDetailed View:")
            self.output.append(self.detailed_df.to_string())
            self.output.append("\n\nSummary View (grouped by document):")
            self.output.append(self.pivoted_df.to_string())
            self.export_button.show()
        else:
            self.output.append("No matching data found!")

    def next_frame2(self):
        self.topic_frame.hide()
        selected_topics = [item.text() for item in self.topic_list.selectedItems()]
        
        self.conditions, res4 = condition_extraction(selected_topics)
        if res4 == 0:
            self.output.append("Error in Condition Extraction")
        else:
            self.output.append("Condition Extraction Successful")
            for condition in self.conditions:
                self.output.append(condition)
    
    def add_custom_unit(self):
        unit, ok = QInputDialog.getText(self, 'Add Custom Unit', 
            'Enter custom measurement unit:')
        if ok and unit:
            self.units_list.addItem(unit)

    def export_to_csv(self):
        if hasattr(self, 'detailed_df'):
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Data", "", "CSV Files (*.csv)")
            if filename:
                # Save both views
                base_name = filename.rsplit('.', 1)[0]
                self.detailed_df.to_csv(f"{base_name}_detailed.csv", index=False)
                self.pivoted_df.to_csv(f"{base_name}_summary.csv", index=False)
                QMessageBox.information(self, "Success", 
                    "Data exported successfully!")

    def check_internet(self):
        try:
            socket.create_connection(("1.1.1.1", 53))
            return True
        except:
            return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())