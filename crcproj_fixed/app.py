"""Zero-dependency Python backend for CRC Sentinel.

Uses Python's standard-library HTTP server so the project can be run without
installing a web framework. The frontend communicates with these JSON/file APIs.
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
import urllib.parse
from datetime import datetime
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from crc_engine import CRC_CONFIGS, bytes_to_bits, calculate_crc, config_for, crc_remainder, flip_bit, validate_bits, verify_codeword

ROOT = Path(__file__).resolve().parent
MAX_UPLOAD = 20 * 1024 * 1024
HISTORY: list[dict] = []


def record_history(operation: str, algorithm: str, source: str, result: str, filename: str = ""):
    HISTORY.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "operation": operation,
                       "algorithm": algorithm, "source": source, "result": result, "filename": filename})
    del HISTORY[20:]


def json_bytes(obj):
    return json.dumps(obj).encode("utf-8")


def parse_multipart(content_type: str, body: bytes) -> dict[str, object]:
    header = (f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n").encode() + body
    message = BytesParser(policy=policy.default).parsebytes(header)
    fields = {}
    if not message.is_multipart():
        return fields
    for part in message.iter_parts():
        disposition = part.get("Content-Disposition", "")
        match = re.search(r'name="([^"]+)"', disposition)
        if not match:
            continue
        name = match.group(1)
        filename_match = re.search(r'filename="([^"]*)"', disposition)
        payload = part.get_payload(decode=True) or b""
        if filename_match:
            fields[name] = {"filename": Path(filename_match.group(1)).name, "data": payload}
        else:
            charset = part.get_content_charset() or "utf-8"
            fields[name] = payload.decode(charset, errors="replace")
    return fields


def text_field(fields, name, default=""):
    value = fields.get(name, default)
    return value if isinstance(value, str) else default


def crc_for_binary_exact(bits, algorithm):
    config = config_for(algorithm)
    bits = validate_bits(bits)
    remainder = crc_remainder(bits, config.polynomial)
    return {"data_bits": bits, "crc": remainder, "codeword": bits + remainder,
            "data_length_bits": len(bits), "data_length_bytes": (len(bits) + 7) // 8,
            "crc_length": len(remainder)}


class Handler(BaseHTTPRequestHandler):
    server_version = "CRCSentinel/1.0"

    def log_message(self, fmt, *args):
        # Keep the demo terminal clean.
        return

    def send_data(self, data, status=HTTPStatus.OK, content_type="application/json; charset=utf-8", download_name=None):
        if isinstance(data, str):
            data = data.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if download_name:
            self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/":
            return self.serve_file(ROOT / "templates" / "index.html", "text/html; charset=utf-8")
        if path == "/static/style.css":
            return self.serve_file(ROOT / "static" / "style.css", "text/css; charset=utf-8")
        if path == "/static/app.js":
            return self.serve_file(ROOT / "static" / "app.js", "application/javascript; charset=utf-8")
        if path == "/api/algorithms":
            return self.send_data(json_bytes({k: v.polynomial for k, v in CRC_CONFIGS.items()}))
        if path == "/api/history":
            return self.send_data(json_bytes(HISTORY))
        if path == "/api/export-history":
            lines = ["CRC Sentinel laboratory verification history", ""]
            for item in HISTORY:
                lines.append(f"{item['time']} | {item['operation']} | {item['algorithm']} | {item['source']} | {item['result']}")
            return self.send_data("\n".join(lines), content_type="text/plain; charset=utf-8", download_name="crc_verification_history.txt")
        return self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def serve_file(self, path, content_type):
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            return self.send_error(404, "File not found")
        return self.send_data(data, content_type=content_type)

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_UPLOAD:
            raise ValueError("Request is too large. Maximum upload size is 20 MB.")
        return self.rfile.read(length)

    def parse_fields(self):
        body = self.read_body()
        content_type = self.headers.get("Content-Type", "")
        if content_type.startswith("multipart/form-data"):
            return parse_multipart(content_type, body)
        if content_type.startswith("application/x-www-form-urlencoded"):
            parsed = urllib.parse.parse_qs(body.decode(), keep_blank_values=True)
            return {k: v[-1] for k, v in parsed.items()}
        return json.loads(body.decode() or "{}")

    def do_POST(self):
        try:
            fields = self.parse_fields()
            if self.path == "/api/calculate":
                return self.calculate(fields)
            if self.path == "/api/verify":
                return self.verify(fields)
            return self.send_error(404, "Not found")
        except Exception as exc:
            return self.send_data(json_bytes({"success": False, "error": str(exc)}), 400)

    def calculate(self, fields):
        input_type = text_field(fields, "input_type", "text")
        algorithm = text_field(fields, "algorithm", "CRC-8")
        config = config_for(algorithm)
        if input_type == "binary":
            result = crc_for_binary_exact(text_field(fields, "data"), algorithm)
            source = "Binary input"
            filename = ""
        elif input_type == "text":
            text = text_field(fields, "data")
            if not text:
                raise ValueError("Text input cannot be empty.")
            result = calculate_crc(text.encode("utf-8"), config.polynomial)
            source = "Text input"
            filename = ""
        elif input_type == "file":
            file = fields.get("file")
            if not isinstance(file, dict) or not file.get("filename"):
                raise ValueError("Please select a file.")
            result = calculate_crc(file["data"], config.polynomial)
            source = file["filename"]
            filename = file["filename"]
        else:
            raise ValueError("Unsupported input type.")
        record_history("CRC Calculation", algorithm, source, result["crc"], filename)
        return self.send_data(json_bytes({"success": True, "algorithm": algorithm, "polynomial": config.polynomial,
                                          "input_type": input_type, "source": source, **result}))

    def verify(self, fields):
        input_type = text_field(fields, "input_type", "text")
        algorithm = text_field(fields, "algorithm", "CRC-8")
        config = config_for(algorithm)
        simulate = text_field(fields, "simulate_error", "false") == "true"

        if input_type == "file":
            original = fields.get("original_file")
            backup = fields.get("backup_file")
            if not isinstance(original, dict) or not isinstance(backup, dict) or not original.get("filename") or not backup.get("filename"):
                raise ValueError("Select both the original file and the backup file.")
            original_bytes, backup_bytes = original["data"], backup["data"]
            changed_index = None
            if simulate and backup_bytes:
                backup_bits, changed_index = flip_bit(bytes_to_bits(backup_bytes))
                backup_bytes = int(backup_bits, 2).to_bytes(len(backup_bytes), "big")
            original_crc = calculate_crc(original_bytes, config.polynomial)["crc"]
            backup_crc = calculate_crc(backup_bytes, config.polynomial)["crc"]
            byte_match, crc_match = original_bytes == backup_bytes, original_crc == backup_crc
            status = "NO ERROR DETECTED" if byte_match and crc_match else "ERROR DETECTED"
            source = f"{original['filename']} → {backup['filename']}"
            record_history("Backup Verification", algorithm, source, status)
            return self.send_data(json_bytes({"success": True, "algorithm": algorithm, "polynomial": config.polynomial,
                "original_crc": original_crc, "backup_crc": backup_crc, "original_size": len(original_bytes),
                "backup_size": len(backup_bytes), "byte_match": byte_match, "crc_match": crc_match,
                "status": status, "simulated_error": simulate, "changed_index": changed_index}))

        original = text_field(fields, "original")
        received = text_field(fields, "received")
        if not original or not received:
            raise ValueError("Enter both the original and received data.")
        if input_type == "binary":
            original = validate_bits(original); received = validate_bits(received)
            changed_index = None
            if simulate:
                received, changed_index = flip_bit(received)
            original_crc = crc_remainder(original, config.polynomial)
            received_crc = crc_remainder(received, config.polynomial)
            check_codeword = received + original_crc
            verification = verify_codeword(check_codeword, config.polynomial)
            source = "Binary original/received"
        else:
            original_bytes, received_bytes = original.encode("utf-8"), received.encode("utf-8")
            data_match = original_bytes == received_bytes
            changed_index = None
            if simulate and received_bytes:
                received_bits, changed_index = flip_bit(bytes_to_bits(received_bytes))
                received_bytes = int(received_bits, 2).to_bytes(len(received_bytes), "big")
                data_match = original_bytes == received_bytes
            original_crc = calculate_crc(original_bytes, config.polynomial)["crc"]
            received_crc = calculate_crc(received_bytes, config.polynomial)["crc"]
            check_codeword = bytes_to_bits(received_bytes) + original_crc
            verification = verify_codeword(check_codeword, config.polynomial)
            source = "Text original/received"
        status = "NO ERROR DETECTED" if verification["valid"] else "ERROR DETECTED"
        record_history("Backup Verification", algorithm, source, status)
        return self.send_data(json_bytes({"success": True, "algorithm": algorithm, "polynomial": config.polynomial,
            "original_crc": original_crc, "received_crc": received_crc,
            "verification_remainder": verification["remainder"], "status": status,
            "simulated_error": simulate, "changed_index": changed_index,
            "byte_match": (original == received) if input_type == "binary" else data_match, "crc_match": original_crc == received_crc}))


def run():
    host, port = "127.0.0.1", 5000
    print(f"CRC Sentinel running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run()
