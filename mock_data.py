import os
import threading
from datetime import datetime, timezone

import requests
import socketio
from tqdm import tqdm

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
SIO_URL = "http://localhost:8000"
FOLDER_PATH = "test_images/"
EXTENSIONS = {".png", ".jpg", ".jpeg"}

# Limit concurrent uploads to prevent socket buffer overflow
MAX_CONCURRENT = 50
semaphore = threading.BoundedSemaphore(MAX_CONCURRENT)

# Global counters for the progress bar description
success_count = 0
error_count = 0


def ack_callback(data=None):
    """This runs when the server returns the dictionary from handle_capture."""
    global success_count, error_count
    # Check if data exists and contains the 'ok' status
    if data and isinstance(data, dict) and data.get("status") == "ok":
        success_count += 1
    else:
        error_count += 1
    semaphore.release()  # Open a slot for the next image


def setup_test_environment():
    # Create Game entry in DB
    game_resp = requests.post(
        f"{BASE_URL}/collect/game",
        json={
            "name": "mock-data",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "game_metadata": {"source": "local_directory"},
        },
    )
    game_id = game_resp.json().get("game_id")
    print(f"inserted mock game, got game_id: {game_id}")

    # Create Session entry in DB
    session_resp = requests.post(
        f"{BASE_URL}/collect/session",
        json={
            "game_id": game_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "client_info": {"mode": "batch_importer"},
        },
    )
    session_id = session_resp.json().get("session_id")
    print(f"inserted mock session, got session_id: {session_id}")

    run_id = requests.post(
        f"{BASE_URL}/collect/run",
        json={
            "game_id": game_id,
            "session_id": session_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "client_info": {"mode": "batch_importer"},
        },
    )
    run_id = run_id.json().get("run_id")
    print(f"inserted mock run, got run_id: {run_id}")

    return game_id, session_id,run_id

def extract_serial_number(filepath):
    """
    Helper function to extract the integer serial number from a path.
    Expects format: /path/to/file/<filename>_<serial_number>.<ext>
    """
    # 1. Isolate just the filename (e.g., "game_screen_042.jpg")
    base_name = os.path.basename(filepath)

    # 2. Strip off the extension (e.g., "game_screen_042")
    name_without_ext = os.path.splitext(base_name)[0]

    try:
        # 3. Split from the right side at the first underscore it finds,
        #    grab the last piece, and convert to integer.
        serial_str = name_without_ext.rsplit("_x", 1)[-1]
        return int(serial_str)
    except (ValueError, IndexError):
        # Failsafe: If a file doesn't have an underscore or number,
        # send it to the very beginning of the list.
        return -1




sio = socketio.Client()


if __name__ == "__main__":
    if not os.path.exists(FOLDER_PATH):
        print(f"Directory {FOLDER_PATH} not found.")
        exit()

    files_to_upload = [
        f
        for f in os.listdir(FOLDER_PATH)
        if os.path.splitext(f)[1].lower() in EXTENSIONS
    ]

    if not files_to_upload:
        print("No valid images found in test_data/")
        exit(0)

    game_id, session_id,run_id = setup_test_environment()
    sio.connect(SIO_URL)

    # Iterate through all files in the folder
    with tqdm(total=len(files_to_upload), desc="Uploading", unit="img") as pbar:
        for filename in files_to_upload:
            semaphore.acquire()
            file_path = os.path.join(FOLDER_PATH, filename)

            try:
                if os.path.isfile(file_path):
                    print(f"Processing: {filename}")

                    capture_index = extract_serial_number(filename)
                    with open(file_path, "rb") as f:
                        image_bytes = f.read()

                    payload = {
                        "game_id": game_id,
                        "session_id": session_id,
                        "run_id": run_id,
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                        "capture_index": capture_index,
                        "image_data": image_bytes,
                        "screenshot_hash": f"hash_{filename}",
                    }

                    sio.emit("capture_event", payload, callback=ack_callback)
                    # Update progress bar UI
                    pbar.update(1)
                    pbar.set_postfix({"Success": success_count, "Errors": error_count})
            except Exception as e:
                error_count += 1
                pbar.write(f"Failed to read {filename}: {e}")

    for _ in range(MAX_CONCURRENT):
        semaphore.acquire()
    print(f"\nFinished. Final Stats: {success_count} Succeeded, {error_count} Failed.")
    sio.disconnect()
