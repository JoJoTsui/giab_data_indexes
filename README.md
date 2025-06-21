# BAM and BAI File Downloader using Aspera Connect

This project provides a Python script (`download_bams.py`) to download BAM files and their corresponding BAI index files listed in a TSV file (`sample_bam_urls.tsv`) using Aspera Connect.

## Prerequisites

1.  **Python 3**: Ensure you have Python 3 installed on your system.
2.  **Aspera Connect CLI (`ascp`)**: The script relies on the Aspera Connect command-line interface.
    *   **Installation**:
        *   Download Aspera Connect from the IBM Aspera website: [https://www.ibm.com/aspera/connect/](https://www.ibm.com/aspera/connect/)
        *   Follow the installation instructions for your operating system.
        *   After installation, the `ascp` command-line tool should be available. You might need to add its installation directory to your system's PATH environment variable if it's not found automatically.
            *   On Linux/macOS, `ascp` is often installed in `~/.aspera/connect/bin` or `/opt/aspera/bin` or similar user/system-wide locations.
            *   On Windows, it's typically in `C:\Program Files\Aspera\Aspera Connect\bin` or `C:\Users\<YourUser>\AppData\Local\Programs\Aspera\Aspera Connect\bin`.
    *   **Verification**: Open a terminal or command prompt and type `ascp -A`. If it displays help information, `ascp` is correctly installed and in your PATH. If not, you'll need to update the `ASPERA_CONNECT_PATH` variable at the top of the `download_bams.py` script to point to the full path of the `ascp` executable.

## Files

*   `sample_bam_urls.tsv`: A tab-separated values file containing the list of samples and their Aspera download URLs for both BAM and BAI files.
    *   **Format**: Must contain three columns: `sample_id`, `bam_url`, and `bai_url`.
*   `download_bams.py`: The Python script to perform the downloads.
*   `README.md`: This file.

## Configuration (inside `download_bams.py`)

You can configure the following settings at the top of `download_bams.py`:

*   `TSV_FILE`: Path to the TSV file containing BAM URLs (default: "sample_bam_urls.tsv").
*   `DOWNLOAD_DIR`: Directory where BAM files will be saved (default: "bam_downloads"). This directory will be created if it doesn't exist.
*   `ASPERA_CONNECT_PATH`: Path to the `ascp` executable. If `ascp` is in your system PATH, "ascp" is usually sufficient. Otherwise, provide the full path.
*   `ASPERA_OPTS`: Aspera command-line options (default: "-k1 -Q -T -l200M").
    *   `-k1`: Enables resume for interrupted transfers.
    *   `-Q`: Enables adaptive flow control (useful for disk throttling).
    *   `-T`: Disables encryption (can speed up transfers for public data; remove if encryption is required).
    *   `-l200M`: Sets a target transfer rate of 200 Mbps. Adjust this value based on your internet connection and server limits.
*   `ASPERA_SSH_KEY`: Path to an Aspera SSH private key file, if required by the server (default: `None`). For public ENA/EBI downloads, this is typically not needed.

## How to Run

1.  **Prepare the TSV file**: Ensure `sample_bam_urls.tsv` is present in the same directory as the script and contains the correct sample IDs and Aspera URLs.
2.  **Open a terminal or command prompt**.
3.  **Navigate to the directory** containing `download_bams.py` and `sample_bam_urls.tsv`.
4.  **Run the script**:
    ```bash
    python3 download_bams.py
    ```
    (Use `python` or `python3` depending on your system's Python installation).

The script will:
*   Read each entry from the TSV file.
*   Create the download directory if it doesn't exist.
*   Attempt to download each BAM file and its corresponding BAI file using Aspera Connect.
*   If a file already exists, Aspera Connect (with `-k1`) will attempt to resume the download or verify the existing file.
*   Print progress and error messages to the console.
*   Provide a summary of successful and failed downloads for both BAM and BAI files at the end.

## Troubleshooting

*   **`ascp: command not found` or `FileNotFoundError`**:
    *   Ensure Aspera Connect CLI is installed.
    *   Verify that the `ascp` executable is in your system's PATH or update the `ASPERA_CONNECT_PATH` variable in the script with the full path to `ascp`.
*   **Permission Denied (Aspera)**:
    *   This could be due to incorrect Aspera URLs or the server requiring specific credentials/SSH keys not provided. The current URLs are for public EBI data and usually don't require special keys.
    *   Ensure the `DOWNLOAD_DIR` is writable by your user.
*   **Slow Downloads**:
    *   Adjust the `-l` option in `ASPERA_OPTS` (e.g., `-l500M` for 500 Mbps). Be mindful of fair usage policies on public servers.
    *   Network congestion can also affect speed.
*   **Firewall Issues**: Aspera uses TCP port 33001 and UDP port 33001 by default. Ensure these are not blocked by your firewall if you encounter connection issues.
*   **Python script issues**: Ensure you are using Python 3. Some older systems might default `python` to Python 2.

This `README.md` provides instructions on prerequisites, configuration, and how to run the script.
