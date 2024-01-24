
from enum import Enum
from dataclasses import dataclass
import smaz


class MessageType(Enum):
    MSG = 0
    ACK = 1

    def to_bits(self):
        return bin(self.value)[2:].zfill(2)

class CompressionType(Enum):
    NONE = 0
    SMAZ = 1

    def to_bits(self):
        return bin(self.value)[2:].zfill(2)

@dataclass
class MsgId:
    id: int

    def __post_init__(self):
        if self.id > 65535:
            raise ValueError("id must be less than 65535")

    def to_bytes(self):
        return self.id.to_bytes(2)
    
    @classmethod
    def from_bytes(self, bytes):
        return MsgId(int.from_bytes(bytes))

@dataclass
class InfoByte:
    message_type: MessageType
    compression_type: CompressionType

    def to_byte(self):
        bits = ""
        bits += str(self.message_type.to_bits())
        bits += str(self.compression_type.to_bits())
        bits = bits.ljust(8, '0')
        return bytes([int(bits, 2)])
    
    @classmethod
    def from_int(self, integer):
        byte_value = integer.to_bytes(1)
        bits = "".join([bit for byte in byte_value for bit in f'{byte:08b}'])
        message_type = MessageType(int(bits[0:2]))
        compression_type = CompressionType(int(bits[2:4]))
        return InfoByte(message_type, compression_type)

@dataclass
class Message:
    string: str
    compress: CompressionType = CompressionType.NONE

    def to_bytes(self):
        if self.compress == CompressionType.NONE:
            return self.string.encode()
        elif self.compress == CompressionType.SMAZ:
            return smaz.compress(self.string)
        else:
            raise ValueError("Compression type not supported")
    
    @classmethod
    def from_bytes(self, byte_array: bytearray, compression_type: CompressionType):
        if compression_type == CompressionType.NONE:
            return Message(bytes.decode())
        elif compression_type == CompressionType.SMAZ:
            return Message(smaz.decompress(bytes(byte_array)))
        else:
            raise ValueError("Compression type not supported")
