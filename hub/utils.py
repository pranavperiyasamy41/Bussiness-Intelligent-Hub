import pandas as pd
import fitz  # This is the PyMuPDF library
import os

def read_file_content(file_path):
    """
    Reads the content of a .pdf, .csv, or .xlsx file
    and returns it as a single text string.
    """
    # Get the file extension
    file_name, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    text_content = ""

    try:
        if file_extension == '.pdf':
            # Open the PDF file
            with fitz.open(file_path) as doc:
                for page in doc:
                    text_content += page.get_text()

        elif file_extension == '.csv':
            # Read CSV, convert all columns to string, and then to a single text block
            df = pd.read_csv(file_path, dtype=str)
            text_content = df.to_string()

        elif file_extension == '.xlsx':
            # Read Excel, convert all columns to string, and then to a single text block
            # We'll read the first sheet by default
            df = pd.read_excel(file_path, sheet_name=0, dtype=str)
            text_content = df.to_string()

        else:
            return f"Unsupported file type: {file_extension}"

        return text_content

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return f"Error reading file. It may be corrupted. Error: {e}"