
import sys
import subprocess
import time
import socket
import ctypes
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PYTHON = Path(sys.executable).with_name("python.exe")

if not PYTHON.exists():
    PYTHON = Path(sys.executable)

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW

processes = []

# Launcher log file
log_file = BASE_DIR / "launcher.log"


def log(message):

    with open(log_file, "a", encoding="utf-8") as file:

        file.write(str(message) + "\n")

    print(message)


# Check if service is ready
def port_is_open(port):

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    ) as sock:

        sock.settimeout(0.5)

        return sock.connect_ex(
            ("127.0.0.1", port)
        ) == 0


# Start background process
def launch_process(name, arguments):

    log(f"Starting {name}...")

    with open(
        BASE_DIR / f"{name}.log",
        "w",
        encoding="utf-8"
    ) as file:

        process = subprocess.Popen(
            [str(PYTHON), "-u"] + arguments,
            cwd=str(BASE_DIR),
            creationflags=CREATE_NO_WINDOW,
            stdout=file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL
        )

    processes.append(process)

    return process


def wait_for_port(port, process):

    deadline = time.monotonic() + 45

    while time.monotonic() < deadline:

        if process.poll() is not None:
            return False

        if port_is_open(port):
            return True

        time.sleep(0.5)

    return False


try:

    log("Launching Smiski Focus...")
    log(f"Python: {PYTHON}")

    # Start Flask server
    if port_is_open(5000):

        raise RuntimeError(
            "Port 5000 is already in use. "
            "Close your previous server first."
        )

    server = launch_process(
        "server",
        ["server.py"]
    )

    if not wait_for_port(5000, server):

        raise RuntimeError(
            "Server failed. Check server.log."
        )

    log("Server ready!")

    # Start Streamlit dashboard
    if port_is_open(8501):

        raise RuntimeError(
            "Port 8501 is already in use. "
            "Close your previous dashboard first."
        )

    dashboard = launch_process(
        "dashboard",
        [
            "-m",
            "streamlit",
            "run",
            "dashboard.py",
            "--server.headless=true",
            "--server.address=127.0.0.1",
            "--server.port=8501",
            "--browser.gatherUsageStats=false"
        ]
    )

    if not wait_for_port(8501, dashboard):

        raise RuntimeError(
            "Dashboard failed. Check dashboard.log."
        )

    log("Dashboard ready!")

    # Start desktop Smiski
    pet = launch_process(
        "smiski",
        ["smiski.py"]
    )

    log("Smiski launched!")

    pet.wait()

    if pet.returncode != 0:

        raise RuntimeError(
            "Smiski closed unexpectedly. "
            "Check smiski.log."
        )

except Exception as error:

    log(traceback.format_exc())

    ctypes.windll.user32.MessageBoxW(
        None,
        str(error),
        "Smiski Focus Error",
        0x10
    )

finally:

    log("Shutting down Smiski Focus...")

    for process in reversed(processes):

        if process.poll() is None:

            process.terminate()

            try:

                process.wait(timeout=5)

            except subprocess.TimeoutExpired:

                process.kill()
                process.wait()

    log("Smiski Focus closed.")
