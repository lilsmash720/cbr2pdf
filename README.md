# CBR and CBZ to PDF Converter

This script converts CBR and CBZ files in specified folders to single PDF files. It handles both `.cbr` and `.cbz` archive formats and extracts the images within, combining them into a PDF document.

## Features

- Supports `.cbz` (ZIP) and `.cbr` (RAR) file formats.
- Extracts images from the archives and combines them into single PDFs.
- Maintains the order of images based on filenames.
- Displays progress bars for both extraction and PDF conversion processes.
- Supports processing multiple folders at once.

## Requirements

- Python 3.x
- Required Python packages:
  - `Pillow`
  - `patool`
  - `tqdm`

## Installation

1. Ensure you have Python 3 installed on your system.
2. Install the required packages using pip:

    ```sh
    pip install Pillow patool tqdm
    ```

## Usage

1. Place your CBR and CBZ files in folders.
2. Run the script with the folder paths as arguments:

    ```sh
    python cbr2pdf.py "path/to/your/folder1" "path/to/your/folder2"
    ```

3. The script will create PDF files in the parent directories of the input folders, named after the input folders.

## Example

If your folder structure is:

Comics1/
├── issue1.cbr
├── issue2.cbz
└── issue3.cbr

Comics2/
├── issue1.cbz
└── issue2.cbr

Troubleshooting

    Ensure all required packages are installed.
    Verify the paths to your input folders are correct.
    If you encounter issues with specific archives, check if they are corrupted or try extracting them manually using an archive tool.

License

This project is licensed under the MIT License.