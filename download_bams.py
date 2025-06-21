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
def download_with_aspera(sample_id, aspera_url, download_dir):
    """
    Downloads a single file using Aspera Connect.
    """
    ensure_dir(download_dir)
    destination_path = get_download_path(aspera_url, download_dir)

    print(f"\nProcessing sample: {sample_id}")
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
            print(f"  Successfully downloaded (or resumed/verified) {os.path.basename(destination_path)} for sample {sample_id}.")
            # Check for common Aspera success messages in stdout/stderr if needed
            if stdout:
                print(f"    Aspera stdout: {stdout.decode().strip()}")
            if stderr: # Aspera often prints status to stderr even on success
                print(f"    Aspera stderr: {stderr.decode().strip()}")
            return True
        else:
            print(f"  Error downloading {sample_id}. Return code: {process.returncode}")
            if stdout:
                print(f"    Stdout: {stdout.decode()}")
            if stderr:
                print(f"    Stderr: {stderr.decode()}")
            return False
    except FileNotFoundError:
        print(f"  Error: Aspera Connect executable ('{ASPERA_CONNECT_PATH}') not found.")
        print(f"  Please ensure Aspera Connect CLI is installed and in your PATH, or update ASPERA_CONNECT_PATH.")
        return False
    except Exception as e:
        print(f"  An unexpected error occurred during download for {sample_id}: {e}")
        return False

def main():
    """
    Main function to read TSV and initiate downloads.
    """
    if not os.path.exists(TSV_FILE):
        print(f"Error: TSV file '{TSV_FILE}' not found.")
        return

    print(f"Starting BAM file downloads. Files will be saved to: {os.path.abspath(DOWNLOAD_DIR)}")

    successful_downloads = 0
    failed_downloads = 0

    with open(TSV_FILE, 'r', newline='') as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter='\t')
        if 'sample_id' not in reader.fieldnames or 'bam_url' not in reader.fieldnames:
            print(f"Error: TSV file must contain 'sample_id' and 'bam_url' columns.")
            return

        for row in reader:
            sample_id = row['sample_id']
            bam_url = row['bam_url']

            if not bam_url or not sample_id:
                print(f"Skipping row due to missing sample_id or bam_url: {row}")
                continue

            if download_with_aspera(sample_id, bam_url, DOWNLOAD_DIR):
                successful_downloads += 1
            else:
                failed_downloads += 1

    print("\n--- Download Summary ---")
    print(f"Successfully downloaded/verified: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    if failed_downloads > 0:
        print("Please check the error messages above for details on failed downloads.")
    print("------------------------")

if __name__ == "__main__":
    main()
