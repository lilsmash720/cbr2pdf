import os
import zipfile
import tempfile
from PIL import Image
import argparse
import shutil
import patoolib
from patoolib.util import PatoolError
from tqdm import tqdm

# Suppress patoolib INFO messages
import logging
logging.getLogger('patool').setLevel(logging.ERROR)

def extract_files(input_folder):
    extracted_images = []
    temp_dir = tempfile.mkdtemp()
    folder_index = 1

    # Collect and sort all archive files in the input folder
    archive_files = sorted(
        [os.path.join(input_folder, file) for file in os.listdir(input_folder) if file.endswith(('.cbz', '.cbr'))],
        key=lambda x: os.path.basename(x).lower()
    )

    for archive_path in tqdm(archive_files, desc="Extracting archives"):
        archive_folder = os.path.join(temp_dir, str(folder_index))

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

    return extracted_images, temp_dir

def convert_to_pdf(images, output_pdf_path):
    image_objs = [Image.open(image).convert('RGB') for image in tqdm(images, desc="Opening images")]

    if image_objs:
        first_image = image_objs[0]
        remaining_images = image_objs[1:]

        with tqdm(total=len(remaining_images), desc="Saving PDF") as pbar:
            first_image.save(output_pdf_path, save_all=True, append_images=remaining_images)
            pbar.update(len(remaining_images))

def process_folder(input_folder):
    output_pdf_name = os.path.basename(input_folder.rstrip('/\\')) + '.pdf'
    output_pdf_path = os.path.join(os.path.dirname(input_folder), output_pdf_name)
    images, temp_dir = extract_files(input_folder)
    convert_to_pdf(images, output_pdf_path)
    shutil.rmtree(temp_dir)  # Clean up the temporary directory
    print(f'PDF saved to {output_pdf_path}')

def main(input_folders):
    for folder in input_folders:
        if os.path.isdir(folder):
            print(f'Processing folder: {folder}')
            process_folder(folder)
        else:
            print(f'Skipping invalid folder: {folder}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CBR and CBZ files in folders to single PDFs.')
    parser.add_argument('input_folders', nargs='+', help='The paths to the folders containing the CBR and CBZ files.')
    args = parser.parse_args()
    main(args.input_folders)
