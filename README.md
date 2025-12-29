# BLE Tracker for MikroTik

Tools for tracking Bluetooth Low Energy (BLE) devices using a MikroTik router as a scanner and a small Python backend.

The project listens for BLE scan data sent from a MikroTik RouterOS device, processes the received advertisements and stores them in a local SQLite database (`ble_tracker.db`) for logging, analysis or integration with other systems.

> Developed by **Amir Mobasheraghdam**

---

## Features

- 📡 Use a **MikroTik router** as a BLE scanner  
- 🔎 Receive and parse **BLE advertisements** (beacons / tags / devices)  
- 💾 Store data in a local **SQLite database** (`ble_tracker.db`)  
- 🐍 Simple **Python server** (`ble_server_fixed.py`, `start_server.py`) to handle incoming data  
- 🔧 Small, hackable codebase for experiments, home automation or asset tracking

---

## Repository structure

The most relevant files are:

- `main.py` – entry point / helper for running and testing the project
- `start_server.py` – starts the BLE tracking server
- `ble_server_fixed.py` – main server logic for receiving and handling BLE data
- `ble_tracker.db` – SQLite database file used to store tracking data
- `tags.py`, `test_server.py`, `run_test.py` – utilities and test scripts
- `requirements.txt` – Python dependencies

(Some helper folders like `app`, `dir`, `echo`, `pip`, `python`, `venvScriptsactivate` are used during development or testing.)

---

## Requirements

- Python 3.9+ (recommended)
- A MikroTik router with:
  - Bluetooth / BLE support
  - Ability to send data (e.g. via HTTP requests / scripts) to the Python server
- `pip` to install Python packages

Install the Python dependencies with:

```bash
pip install -r requirements.txt
````

(If you use a virtual environment, activate it before installing.)

---

## How to run

1. **Clone the repository**

```bash
git clone https://github.com/Amirmobash/ble_tracker_mikrotik.git
cd ble_tracker_mikrotik
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Start the server**

Most setups will use something like:

```bash
python start_server.py
```

or:

```bash
python ble_server_fixed.py
```

Check/adjust the host and port inside these files according to your network.

4. **Configure the MikroTik router**

On your MikroTik device:

* Enable BLE scanning.
* Configure a script or tool that sends BLE scan results to the IP and port of this Python server (for example via HTTP or TCP, depending on how you adapt the code).

> The exact MikroTik configuration depends on your RouterOS version and setup. You can adjust the Python code and MikroTik scripts to match your use case.

---

## Database

The project uses a local SQLite database file: **`ble_tracker.db`**

You can inspect it using tools like:

```bash
sqlite3 ble_tracker.db
```

or a GUI such as DB Browser for SQLite.

Typical data stored may include:

* MAC / identifier of BLE device
* RSSI (signal strength)
* Timestamp of detection
* Tag / type information (depending on your parsing logic in `ble_server_fixed.py` / `tags.py`)

---

## Use cases

This project can be used as a base for:

* Home automation and presence detection
* Tracking BLE beacons in a room / building
* Logging nearby devices for analysis
* Integrating BLE signals into other systems (MQTT, dashboards, etc.) by extending the Python code

---

## Roadmap / Ideas

Some possible future improvements:

* Add a simple REST API to query data from `ble_tracker.db`
* Add Docker support for easier deployment
* Provide ready-to-use MikroTik RouterOS scripts
* Add configuration via `.env` or config file (host, port, DB path, etc.)
* Create dashboards / visualizations of detected devices

---

## Author

**Amir Mobasheraghdam**
