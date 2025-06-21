import subprocess
import os
import csv

# --- Configuration ---
TSV_FILE = "sample_bam_urls.tsv"
DOWNLOAD_DIR = "bam_downloads"  # Directory to save downloaded BAM files
ASPERA_CONNECT_PATH = "ascp"  # Path to ascp executable (assumes it's in PATH)
# Aspera options:
# -k1: Enable resume of failed transfers
# -Q: Adaptive flow control / for disk throttling
# -T: Disable encryption (often not needed for public FTPs, can speed up)
# -l: Set target transfer rate (e.g., 200M for 200 Mbps). Adjust as needed.
#     It's good practice to not saturate the connection, hence a reasonable limit.
ASPERA_OPTS = "-k1 -Q -T -l200M"
# Aspera private key if needed for this source (usually for ENA/EBI it's not required for public data)
# Example: ASPERA_SSH_KEY = "/path/to/asperaweb_id_dsa.openssh"
ASPERA_SSH_KEY = None # For ENA public downloads, key is often embedded or not needed.

# --- Helper Functions ---
def ensure_dir(directory_path):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")

def get_download_path(aspera_url, download_dir):
    """Determines the local path for the downloaded file."""
    filename = os.path.basename(aspera_url.split(':')[1]) # Get path part and then filename
    return os.path.join(download_dir, filename)

# --- Main Download Logic ---
def download_with_aspera(sample_id, aspera_url, download_dir, file_type="file"):
    """
    Downloads a single file using Aspera Connect.
    """
    if not aspera_url:
        print(f"  Skipping {file_type} for {sample_id} as URL is not provided.")
        return True # Not a failure, just nothing to do

    ensure_dir(download_dir)
    destination_path = get_download_path(aspera_url, download_dir)

    print(f"\nProcessing {file_type} for sample: {sample_id}")
    print(f"  Aspera URL: {aspera_url}")
    print(f"  Destination: {destination_path}")

    if os.path.exists(destination_path):
        # Basic check for existing file, ascp's -k1 handles resume more robustly
        print(f"  File {destination_path} already exists. Aspera will attempt to resume/verify.")

    # Construct the ascp command
    # Example: ascp -k1 -Q -T -l200M era-fasp@fasp.sra.ebi.ac.uk:/path/to/file.bam ./local_dir/
    cmd = [ASPERA_CONNECT_PATH]
    cmd.extend(ASPERA_OPTS.split())

    if ASPERA_SSH_KEY and os.path.exists(ASPERA_SSH_KEY):
        cmd.extend(["-i", ASPERA_SSH_KEY])
    elif ASPERA_SSH_KEY:
        print(f"  Warning: Aspera SSH key specified but not found at {ASPERA_SSH_KEY}. Proceeding without it.")

    cmd.append(aspera_url)
    cmd.append(download_dir + "/") # Ensure downloading into the directory

    print(f"  Executing command: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            print(f"  Successfully downloaded (or resumed/verified) {os.path.basename(destination_path)} ({file_type}) for sample {sample_id}.")
            if stdout:
                print(f"    Aspera stdout: {stdout.decode().strip()}")
            if stderr: # Aspera often prints status to stderr even on success
                print(f"    Aspera stderr: {stderr.decode().strip()}")
            return True
        else:
            print(f"  Error downloading {file_type} for {sample_id}. Return code: {process.returncode}")
            if stdout:
                print(f"    Stdout: {stdout.decode()}")
            if stderr:
                print(f"    Stderr: {stderr.decode()}")
            return False
    except FileNotFoundError:
        print(f"  Error: Aspera Connect executable ('{ASPERA_CONNECT_PATH}') not found for downloading {file_type} for {sample_id}.")
        print(f"  Please ensure Aspera Connect CLI is installed and in your PATH, or update ASPERA_CONNECT_PATH.")
        return False
    except Exception as e:
        print(f"  An unexpected error occurred during download of {file_type} for {sample_id}: {e}")
        return False

def main():
    """
    Main function to read TSV and initiate downloads for BAM and BAI files.
    """
    if not os.path.exists(TSV_FILE):
        print(f"Error: TSV file '{TSV_FILE}' not found.")
        return

    print(f"Starting BAM and BAI file downloads. Files will be saved to: {os.path.abspath(DOWNLOAD_DIR)}")

    successful_bam_downloads = 0
    failed_bam_downloads = 0
    successful_bai_downloads = 0
    failed_bai_downloads = 0

    with open(TSV_FILE, 'r', newline='') as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter='\t')
        expected_columns = ['sample_id', 'bam_url', 'bai_url']
        if not all(col in reader.fieldnames for col in expected_columns):
            print(f"Error: TSV file must contain {expected_columns} columns. Found: {reader.fieldnames}")
            return

        for row in reader:
            sample_id = row['sample_id']
            bam_url = row['bam_url']
            bai_url = row.get('bai_url') # Use .get() for graceful handling if column is missing for a row

            if not sample_id:
                print(f"Skipping row due to missing sample_id: {row}")
                continue

            # Download BAM file
            if bam_url:
                print(f"\n--- Attempting BAM download for {sample_id} ---")
                if download_with_aspera(sample_id, bam_url, DOWNLOAD_DIR, file_type="BAM"):
                    successful_bam_downloads += 1
                else:
                    failed_bam_downloads += 1
            else:
                print(f"Skipping BAM download for {sample_id} as bam_url is missing.")
                failed_bam_downloads +=1


            # Download BAI file
            if bai_url:
                print(f"\n--- Attempting BAI download for {sample_id} ---")
                if download_with_aspera(sample_id, bai_url, DOWNLOAD_DIR, file_type="BAI"):
                    successful_bai_downloads += 1
                else:
                    failed_bai_downloads += 1
            else:
                print(f"Skipping BAI download for {sample_id} as bai_url is missing or not provided.")
                # Not necessarily a failure if BAI is optional and not listed

    print("\n--- Download Summary ---")
    print(f"BAM Files: {successful_bam_downloads} successful, {failed_bam_downloads} failed.")
    print(f"BAI Files: {successful_bai_downloads} successful, {failed_bai_downloads} failed.")
    if failed_bam_downloads > 0 or failed_bai_downloads > 0:
        print("Please check the error messages above for details on any failed downloads.")
    print("------------------------")

if __name__ == "__main__":
    main()
