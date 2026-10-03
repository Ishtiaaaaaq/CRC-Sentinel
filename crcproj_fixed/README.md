# CRC Sentinel — USB Backup Verification Utility

A laboratory-ready CRC-based backup integrity dashboard using **HTML + CSS + JavaScript** for the frontend and **Python standard library** for the backend.

## IMPORTANT: How to start

**Do not double-click `templates/index.html`. Do not use VS Code Live Server for the dashboard.**

Use one of these methods:

### Windows easiest method
Double-click:

`run.bat`

It starts the Python backend and opens:

`http://127.0.0.1:5000`

### Manual method
Open Command Prompt in this project folder and run:

```bash
python app.py
```

Then open:

`http://127.0.0.1:5000`

The frontend and backend must be on the same origin. Otherwise `/api/calculate`, `/api/verify`, `/api/history`, etc. will not reach Python and the browser can show `Unexpected end of JSON input`.

## Features
- Binary CRC calculation
- Text-message CRC calculation
- File CRC calculation (up to 20 MB)
- CRC-3, CRC-4, CRC-8 and CRC-32 generator polynomials
- Original vs received/backup verification
- One-bit error simulation for demonstration
- CRC remainder and codeword display
- Verification history with TXT export
- Responsive presentation-ready UI

## Project flow
`User Input → Dashboard → Python Function → CRC Calculation → Result → Dashboard Output`

## If you still see the JSON error
1. Close old Python/terminal windows running the project.
2. Double-click `run.bat`.
3. Confirm the browser address is exactly `http://127.0.0.1:5000`.
4. Do not open the HTML file directly (`file:///.../index.html`).
5. Do not use a VS Code Live Server URL such as `http://127.0.0.1:5500`.
6. If port 5000 is already occupied, close the previous `app.py` process and run again.

## Suggested live demonstration
1. Calculate CRC for binary `101101` using CRC-3 or CRC-8.
2. Calculate CRC for text `HELLO`.
3. Calculate CRC for a sample file.
4. Go to **Verify Backup**, enter identical original/received data and show **NO ERROR DETECTED**.
5. Enable **Simulate a 1-bit error** and verify again to show **ERROR DETECTED**.
6. Open **History** to show the audit trail.
7. During the demo, open `crc_engine.py` and point to `crc_remainder()`, `calculate_crc()` and `verify_codeword()`.
