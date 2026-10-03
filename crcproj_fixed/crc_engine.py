"""CRC engine for the USB Backup Verification Utility.

The implementation intentionally uses the generator-polynomial bit strings so
that the modulo-2/XOR process is easy to explain during the laboratory demo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CRCConfig:
    name: str
    polynomial: str


CRC_CONFIGS = {
    # Polynomial representations follow the lab's bit-string style.
    "CRC-3": CRCConfig("CRC-3", "1011"),
    "CRC-4": CRCConfig("CRC-4", "10011"),
    "CRC-8": CRCConfig("CRC-8", "100000111"),
    "CRC-32": CRCConfig("CRC-32", "100000100110000010001110110110111"),
}


def validate_bits(bits: str) -> str:
    """Return a cleaned binary string or raise ValueError for invalid input."""
    cleaned = "".join(bits.split())
    if not cleaned:
        raise ValueError("Binary input cannot be empty.")
    if any(ch not in "01" for ch in cleaned):
        raise ValueError("Binary input may contain only 0 and 1.")
    return cleaned


def bytes_to_bits(data: bytes) -> str:
    """Convert bytes to an 8-bit binary representation."""
    return "".join(f"{byte:08b}" for byte in data)


def text_to_bytes(text: str) -> bytes:
    """Encode text as UTF-8 bytes for CRC processing."""
    return text.encode("utf-8")


def crc_remainder(data_bits: str, polynomial: str) -> str:
    """Calculate the CRC remainder using modulo-2 division and XOR."""
    data_bits = validate_bits(data_bits)
    polynomial = validate_bits(polynomial)
    if len(polynomial) < 2 or polynomial[0] != "1":
        raise ValueError("Generator polynomial must be a valid binary polynomial.")

    degree = len(polynomial) - 1
    working = list(data_bits + "0" * degree)
    poly = list(polynomial)

    for i in range(len(data_bits)):
        if working[i] == "1":
            for j in range(len(poly)):
                working[i + j] = "0" if working[i + j] == poly[j] else "1"

    return "".join(working[-degree:]) if degree else ""


def calculate_crc(data: bytes, polynomial: str) -> dict:
    """Calculate CRC, codeword and useful intermediate values for a byte payload."""
    bits = bytes_to_bits(data)
    remainder = crc_remainder(bits, polynomial)
    codeword = bits + remainder
    return {
        "data_bits": bits,
        "crc": remainder,
        "codeword": codeword,
        "data_length_bytes": len(data),
        "data_length_bits": len(bits),
        "crc_length": len(remainder),
    }


def verify_codeword(codeword_bits: str, polynomial: str) -> dict:
    """Verify a received codeword. Zero remainder means no detected error."""
    codeword_bits = validate_bits(codeword_bits)
    polynomial = validate_bits(polynomial)
    degree = len(polynomial) - 1

    working = list(codeword_bits)
    poly = list(polynomial)
    for i in range(len(codeword_bits) - degree):
        if working[i] == "1":
            for j in range(len(poly)):
                working[i + j] = "0" if working[i + j] == poly[j] else "1"

    remainder = "".join(working[-degree:]) if degree else ""
    valid = set(remainder) <= {"0"}
    return {"remainder": remainder, "valid": valid}


def flip_bit(bits: str, index: int | None = None) -> tuple[str, int]:
    """Flip one bit for a controlled error-injection demonstration."""
    bits = validate_bits(bits)
    if index is None:
        index = len(bits) // 2
    if not 0 <= index < len(bits):
        raise ValueError("Bit index is outside the data range.")
    changed = "1" if bits[index] == "0" else "0"
    result = bits[:index] + changed + bits[index + 1 :]
    return result, index


def config_for(name: str) -> CRCConfig:
    if name not in CRC_CONFIGS:
        raise ValueError(f"Unsupported CRC algorithm: {name}")
    return CRC_CONFIGS[name]
