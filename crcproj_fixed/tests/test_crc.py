import unittest
from crc_engine import CRC_CONFIGS, crc_remainder, verify_codeword, flip_bit, bytes_to_bits, calculate_crc

class TestCRC(unittest.TestCase):
    def test_crc_configs(self):
        self.assertEqual(CRC_CONFIGS['CRC-4'].polynomial, '10011')
        self.assertEqual(CRC_CONFIGS['CRC-8'].polynomial, '100000111')

    def test_valid_codeword_crc4(self):
        bits='101101'
        rem=crc_remainder(bits, CRC_CONFIGS['CRC-4'].polynomial)
        self.assertEqual(len(rem), 4)
        self.assertTrue(verify_codeword(bits+rem, CRC_CONFIGS['CRC-4'].polynomial)['valid'])

    def test_corrupted_codeword_crc4(self):
        bits='101101'
        rem=crc_remainder(bits, CRC_CONFIGS['CRC-4'].polynomial)
        corrupted,_=flip_bit(bits+rem, 2)
        self.assertFalse(verify_codeword(corrupted, CRC_CONFIGS['CRC-4'].polynomial)['valid'])

    def test_text(self):
        result=calculate_crc(b'HELLO', CRC_CONFIGS['CRC-8'].polynomial)
        self.assertEqual(result['data_length_bytes'], 5)
        self.assertEqual(len(result['crc']), 8)

    def test_binary(self):
        bits=bytes_to_bits(b'AB')
        result=calculate_crc(b'AB', CRC_CONFIGS['CRC-8'].polynomial)
        self.assertEqual(result['data_bits'], bits)

if __name__ == '__main__': unittest.main()
