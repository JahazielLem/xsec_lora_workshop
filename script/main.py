import zmq
import pmt
import time
import cmd
import struct
import threading
from spacepackets.ccsds.spacepacket import SpHeader, PacketType, CCSDS_HEADER_LEN

def hexdump(data: bytes, width: int = 16):
  lines = []
  for offset in range(0, len(data), width):
    chunk = data[offset:offset + width]
    hex_bytes = " ".join(f"{b:02x}" for b in chunk)
    ascii_repr = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    lines.append(f"{offset:08x}  {hex_bytes:<{width*3}}  |{ascii_repr}|")
  return "\n".join(lines)

def spp_print_packet_details(packet: bytes):
  if len(packet) < 6:
    print("Error: paquete demasiado corto SPP.")
    return

  (packet_id, sequence, length) = struct.unpack_from(">HHH", packet)

  version = (packet_id >> 13) & 0x7
  pkt_type = (packet_id >> 11) & 0x1
  sec_header = (packet_id >> 10) & 0x1
  apid = packet_id & 0x7FF

  seq_flags = (sequence >> 14) & 0x3
  seq_count = sequence & 0x3FFF

  seq_flag_str = {
      0b00: "Continuation",
      0b01: "Start",
      0b10: "End",
      0b11: "Unsegmented",
  }.get(seq_flags, "Unknown")

  print("=== Space Packet Header ===")
  print(f" Version:             {version}")
  print(f" Type:                {pkt_type:02X}")
  print(f" Secondary Header:    {sec_header}")
  print(f" APID:                0x{apid:04X}")
  print(f" Sequence Flags:      0x{seq_flags:X} ({seq_flag_str})")
  print(f" Sequence Count:      {seq_count}")
  print(f" Data Length:         {length}")

  payload = packet[6:6 + length + 1]  # CCSDS length = (N - 1)
  print("=== Payload Dump (Hex) ===")


class SPP:
  def __init__(self):
    self.sequence_tc = 0
    self.sequence_tm = 0

  def build_packet(self, payload=b"Hello X-Sec", apid=0x01, seq_count=0, packet_type=PacketType.TM):
    if packet_type == PacketType.TM:
      spp_header = SpHeader.tm(apid=apid, seq_count=seq_count, data_len=len(payload))
    else:
      spp_header = SpHeader.tc(apid=apid, seq_count=seq_count, data_len=len(payload))

    packet = spp_header.pack() + payload
    return bytes(packet)

  def build_tm(self, payload=b"Hello X-Sec", apid=0x02, packet_type=PacketType.TM):
    self.sequence_tm += 1
    return self.build_packet(payload, apid, self.sequence_tm, packet_type)
  def build_tc(self, payload=b"Hello X-Sec", apid=0x01, packet_type=PacketType.TC):
    self.sequence_tc += 1
    return self.build_packet(payload, apid, self.sequence_tc, packet_type)
  def show_packet_details(self, packet):
    spp_print_packet_details(packet)
    print(hexdump(packet))


class ZMQRecv:
  def __init__(self):
    self.context = zmq.Context()
    self.socket = self.context.socket(zmq.PULL)

    self.socket.bind("tcp://*:5008")
    self.running = False
    self.th_worker = threading.Thread()

  def recv_worker(self):
    while self.running:
      data = self.socket.recv()
      print(f"Recv:\n")
      SPP().show_packet_details(data)
      time.sleep(0.1)

  def run(self):
    self.running = True
    self.th_worker = threading.Thread(target=self.recv_worker, daemon=True)
    self.th_worker.start()

class ZMQConnector:
  def __init__(self):
    self.context = zmq.Context()
    self.socket = self.context.socket(zmq.PUSH)
  
  def connect(self):
    self.socket.connect("tcp://127.0.0.1:5009")

  def send_message(self, message):
    msg = pmt.to_pmt(message)
    serialized = pmt.serialize_str(msg)
    self.socket.send(serialized)


class CLIMain(cmd.Cmd):
  prompt = "> "
  intro = "Welcome to the SDR message sender."
  file = None

  def __init__(self, completekey = "tab", stdin = None, stdout = None):
    super().__init__(completekey, stdin, stdout)
    self.user_message = "Hello world!\n"
    self.zm_client = ZMQConnector()
    self.zm_client.connect()
    self.zm_server = ZMQRecv()
    self.zm_server.run()
    self.spp_builder = SPP()

  def do_send(self, args):
    message_list = args.split(" ")
    if len(message_list) == 1 and message_list[0] == '':
      print(f"Sending: {self.user_message}")
      self.user_message = self.user_message + '\n'
      self.zm_client.send_message(self.user_message.encode().hex())
      return
    else:
      print(f"Sending: {"".join(message_list)}")
      msg = "".join(message_list) + '\n'
      self.zm_client.send_message(msg.encode().hex())
  
  def do_loop(self, args):
    message_list = args.split(" ")
    if len(message_list) == 1 and message_list[0] == '':
      print("Please provide a number")
      return
    for _ in range(0, int(message_list[0])):
      print(f"Sending: {self.user_message}")
      self.user_message = self.user_message + '\n'
      self.zm_client.send_message(self.user_message.encode().hex())
      time.sleep(1)
  
  def do_set_message(self, args):
    message_list = args.split(" ")
    if len(message_list) == 1 and message_list[0] == '':
      print("Please provide a message")
      return
    self.user_message = "".join(message_list)
    print(f"Message changed to: {self.user_message}")

  def do_tm(self, args):
    message_list = args.split(" ")
    if len(message_list) == 1 and message_list[0] == '':
      print(f"Sending TM: {self.user_message}")
      frame = self.spp_builder.build_tm() + b'\n'
      self.zm_client.send_message(frame.hex())
      return
    else:
      print(f"Sending TM: {"".join(message_list)}")
      frame = self.spp_builder.build_tm(payload="".join(message_list).encode()) + b'\n'
      self.zm_client.send_message(frame.hex())

  def do_tc(self, args):
    message_list = args.split(" ")
    if len(message_list) == 1 and message_list[0] == '':
      print(f"Sending TC: {self.user_message}")
      frame = self.spp_builder.build_tc() + b'\n'
      self.zm_client.send_message(frame.hex())
      return
    else:
      print(f"Sending TC: {"".join(message_list)}")
      frame = self.spp_builder.build_tc(payload="".join(message_list).encode()) + b'\n'
      self.zm_client.send_message(frame.hex())

  def do_exit(self, _):
    return True


if __name__ == "__main__":
  CLIMain().cmdloop()


