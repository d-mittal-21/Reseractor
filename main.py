import tkinter as tk
from tkinter import filedialog, Text, Scrollbar
import urllib.request
from src.whitespaceAlgo import text_extraction
from src.relevancyScore import relevancy_table
import socket


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.select_button = tk.Button(self)
        self.select_button["text"] = "Select PDF Files"
        self.select_button["command"] = self.select_files
        self.select_button.pack(side="top", pady=10)

        self.run_button = tk.Button(self)
        self.run_button["text"] = "Run Function"
        self.run_button["command"] = self.run_function
        self.run_button.pack(side="top", pady=10)

        self.scrollbar = Scrollbar(self)
        self.scrollbar.pack(side="right", fill="y")

        self.output = Text(self, height=10, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.output.yview)
        self.output.pack(side="bottom", fill="both", expand=True)

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.pack(side="bottom", pady=10)
        
        self.option1_value = tk.IntVar()
        self.option2_value = tk.IntVar()
        self.option3_value = tk.IntVar()
        
        #relevancy shift
        self.options_frame = tk.Frame(self)
        self.options_heading = tk.Label(self.options_frame, text="Select Relevancy Parameters")
        self.options_heading.pack(side="top")
        self.option1 = tk.Checkbutton(self.options_frame, text="Title Score", variable=self.option1_value)
        self.option1.pack(side="top")
        self.option2 = tk.Checkbutton(self.options_frame, text="Abstract Score", variable=self.option2_value)
        self.option2.pack(side="top")
        self.option3 = tk.Checkbutton(self.options_frame, text="Similiarity Score", variable=self.option3_value)
        self.option3.pack(side="top")
        self.next_button = tk.Button(self.options_frame, text="Next", command=self.next_frame)
        self.next_button.pack(side="top")

    def next_frame(self):
        # Get the values of the options and store them in instance variables
        # print(self.option1_value.get(), self.option2_value.get(), self.option3_value.get())

        # Remove the options frame
        self.options_frame.pack_forget()
        self.relevancy_params = [self.option1_value.get(), self.option2_value.get(), self.option3_value.get()]
        ids, res2 = relevancy_table(self.relevancy_params)
        
        if res2 == 0:
            self.output.insert('1.0', "Error in Relevancy Scoring\n")
        else:
            self.output.insert('1.0', "Relevacy Scoring Successful\n")
    
    def select_files(self):
        self.filepaths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])

    def run_function(self):
        if self.check_internet():
            if hasattr(self, 'filepaths'):
                for filepath in self.filepaths:
                    self.output.insert('1.0', f"Running function on {filepath}\n")
                data_table = self.process()
            else:
                self.output.insert('1.0', "No files selected\n")
        else:
            self.output.insert('1.0', "No internet connection\n")
            
    def process(self):
        res1 = text_extraction(self.filepaths)
        if res1 == 0:
            self.output.insert('1.0', "Error in Text Extraction\n")
        else:
            self.output.insert('1.0', "Text Extraction Successful\n")
            self.options_frame.pack(side="top", pady=10)
        return self.filepaths

    def check_internet(self):
        try:
            # urllib.request.urlopen('http://google.com', timeout=1)
            socket.create_connection(("1.1.1.1", 53))
            return True
        except urllib.request.URLError:
            return False

root = tk.Tk()
root.geometry("500x500")  # Set the window size to 500x500
app = Application(master=root)
app.mainloop()