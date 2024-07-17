import os
import zipfile
import tempfile
from PIL import Image, ImageFile
import argparse
import shutil
import patoolib
from patoolib.util import PatoolError
from tqdm import tqdm
from PyPDF2 import PdfMerger
import logging
import warnings
import time  # Added for delay

# Suppress patoolib INFO messages
logging.getLogger('patool').setLevel(logging.ERROR)

# Suppress all decompression bomb warnings
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)

def extract_files(input_folder):
    extracted_images = []
    parent_temp_dir = tempfile.mkdtemp(dir=os.path.dirname(input_folder))
    folder_index = 1

    # Collect and sort all archive files in the input folder
    archive_files = sorted(
        [os.path.join(input_folder, file) for file in os.listdir(input_folder) if file.endswith(('.cbz', '.cbr'))],
        key=lambda x: os.path.basename(x).lower()
    )

    for archive_path in tqdm(archive_files, desc="Extracting archives", ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'):
        archive_folder = os.path.join(parent_temp_dir, str(folder_index))

        if archive_path.endswith('.cbz'):
            with zipfile.ZipFile(archive_path, 'r') as archive:
                archive.extractall(archive_folder)
        elif archive_path.endswith('.cbr'):
            try:
                patoolib.extract_archive(archive_path, outdir=archive_folder)
            except PatoolError:
                print(f"Failed to extract {archive_path} using patoolib. Trying as a zip file.")
                try:
                    with zipfile.ZipFile(archive_path, 'r') as archive:
                        archive.extractall(archive_folder)
                except zipfile.BadZipFile:
                    print(f"Failed to extract {archive_path} as a zip file.")
                    continue

        # Collect images from the extracted folder
        folder_images = []
        for dirpath, _, filenames in os.walk(archive_folder):
            for image_file in sorted(filenames, key=lambda x: x.lower()):
                if image_file.lower().endswith(('png', 'jpg', 'jpeg')):
                    folder_images.append(os.path.join(dirpath, image_file))
        
        extracted_images.extend(folder_images)
        folder_index += 1

    return extracted_images, parent_temp_dir

def convert_to_pdf(images, output_pdf_path, batch_size=100):
    """
    Convert a list of images to a single PDF file.

    Parameters:
    images (list of str): List of image file paths.
    output_pdf_path (str): The output PDF file path.
    batch_size (int): Number of images to process at a time to avoid memory errors.
    """
    if not images:
        print("No images to convert.")
        return

    temp_dir = tempfile.mkdtemp()
    temp_pdfs = []

    for i in tqdm(range(0, len(images), batch_size), desc="Processing image batches", ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'):
        batch_images = images[i:i + batch_size]
        image_objs = []

        for image in tqdm(batch_images, desc=f"Processing batch {i // batch_size + 1:02d}", leave=False, ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'):
            try:
                img = Image.open(image).convert('RGB')
                
                # Check for decompression bomb warning
                img.verify()
                
                # Append image to list if it doesn't raise a warning
                image_objs.append(img)
            except Image.DecompressionBombWarning as e:
                print(f"Skipping decompression bomb image {image}: {e}")
            except Exception as e:
                print(f"Failed to open image {image}: {e}")

        if image_objs:
            batch_pdf_path = os.path.join(temp_dir, f"batch_{i // batch_size + 1}.pdf")
            image_objs[0].save(batch_pdf_path, save_all=True, append_images=image_objs[1:], resolution=100.0)
            temp_pdfs.append(batch_pdf_path)

    # Combine all batch PDFs into a single PDF
    merger = PdfMerger()
    for pdf in temp_pdfs:
        merger.append(pdf)

    merger.write(output_pdf_path)
    merger.close()

    # Remove temporary batch PDFs and directory
    try:
        shutil.rmtree(temp_dir, onerror=force_remove_readonly)
    except OSError as e:
        print(f"Failed to delete temporary directory {temp_dir}: {e}")
    except Exception as e:
        print(f"Unexpected error when deleting temporary directory {temp_dir}: {e}")

    print(f"PDF saved to {output_pdf_path}")

def process_folder(input_folder):
    parent_dir = os.path.dirname(input_folder.rstrip('/\\'))
    folder_name = os.path.basename(input_folder.rstrip('/\\'))
    output_pdf_path = os.path.join(parent_dir, f"{folder_name}.pdf")
    images, temp_dir = extract_files(input_folder)
    convert_to_pdf(images, output_pdf_path)
    try:
        shutil.rmtree(temp_dir)  # Clean up the temporary directory
    except OSError as e:
        print(f"Failed to delete temporary directory {temp_dir}: {e}")
    except Exception as e:
        print(f"Unexpected error when deleting temporary directory {temp_dir}: {e}")
    print(f'PDF saved to {output_pdf_path}')

def main(input_folders):
    for folder in input_folders:
        if os.path.isdir(folder):
            print(f'Processing folder: {folder}')
            process_folder(folder)
        else:
            print(f'Skipping invalid folder: {folder}')
    
    print("Worst comic book converting script, ever. Thank you.")

def force_remove_readonly(func, path, exc_info):
    import stat
    exc_type, _, _ = exc_info
    if issubclass(exc_type, OSError):
        # Try to change the file permissions and retry
        os.chmod(path, stat.S_IWRITE)
        func(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CBR and CBZ files in folders to single PDFs.')
    parser.add_argument('input_folders', nargs='+', help='The paths to the folders containing the CBR and CBZ files.')
    args = parser.parse_args()
    main(args.input_folders)
