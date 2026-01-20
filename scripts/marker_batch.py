"""
Marker batch processing script
Process 1260 pages in 100-page chunks
"""
import subprocess
import os
import time
import shutil

PDF_PATH = "source/2024 Building Code Compendium/301880.pdf"
OUTPUT_DIR = "output_marker"
MARKER_EXE = r"C:\Users\A\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\marker_single.exe"

TOTAL_PAGES = 1260
CHUNK_SIZE = 100

def run_chunk(start, end, chunk_num):
    """Process a chunk of pages"""
    chunk_dir = os.path.join(OUTPUT_DIR, f"chunk_{chunk_num:02d}")
    os.makedirs(chunk_dir, exist_ok=True)

    page_range = f"{start}-{end}"
    print(f"\n{'='*50}")
    print(f"Processing chunk {chunk_num}: pages {start}-{end}")
    print(f"Output: {chunk_dir}")
    print(f"{'='*50}")

    cmd = [
        MARKER_EXE,
        PDF_PATH,
        "--output_dir", chunk_dir,
        "--page_range", page_range,
        "--layout_batch_size", "1"
    ]

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - start_time

    if result.returncode == 0:
        print(f"Chunk {chunk_num} completed in {elapsed:.1f}s")
        return True
    else:
        print(f"Chunk {chunk_num} FAILED")
        return False

def main():
    # Skip first chunk (already done)
    # chunks = [(0, 99, 1)]  # Already completed

    chunks = []
    chunk_num = 1
    for start in range(0, TOTAL_PAGES, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE - 1, TOTAL_PAGES - 1)
        chunks.append((start, end, chunk_num))
        chunk_num += 1

    print(f"Total chunks: {len(chunks)}")
    print(f"Pages per chunk: {CHUNK_SIZE}")

    # Process each chunk
    completed = 0
    failed = 0

    for start, end, num in chunks:
        # Skip chunk 1 if already done
        chunk_dir = os.path.join(OUTPUT_DIR, f"chunk_{num:02d}")
        if os.path.exists(os.path.join(chunk_dir, "301880", "301880.md")):
            print(f"Chunk {num} already exists, skipping...")
            completed += 1
            continue

        if run_chunk(start, end, num):
            completed += 1
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"DONE! Completed: {completed}, Failed: {failed}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
