# 🛡️ CRC Sentinel

A web-based CRC Error Detection and Verification Dashboard.

## 📌 Overview

CRC Sentinel is a web application that demonstrates
Cyclic Redundancy Check (CRC) for detecting errors
during data transmission.

## ✨ Features

- CRC calculation
- CRC-4
- CRC-8
- CRC-32
- Binary input
- Text input
- File input
- Codeword generation
- Codeword verification
- Single-bit error simulation
- Error detection
- Verification history
- TXT export

## 🧠 How CRC Works

1. Input data is provided.
2. Generator polynomial is selected.
3. Modulo-2 division is performed.
4. CRC remainder is calculated.
5. CRC is appended to the data.
6. The receiver verifies the codeword.
7. An error is detected if the remainder is non-zero.

## 🛠️ Technologies

- HTML
- CSS
- JavaScript
- Python
- Flask

## 📂 Project Structure

```text
CRC-Sentinel/
├── app.py
├── crc_engine.py
├── templates/
├── static/
├── sample_data/
├── tests/
└── screenshots/
