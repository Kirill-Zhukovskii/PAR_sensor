"""
Scan a Modbus-RTU bus for a responding slave address.

Sends a "read holding register 0, count 1" query (function code 0x03)
to every address from 1 to 247 and reports which one(s) reply with a
valid, checksum-correct response.

Usage:
    python3 scan_modbus_address.py [port] [baudrate]

Examples:
    python3 scan_modbus_address.py
    python3 scan_modbus_address.py /dev/ttyUSB0 9600
"""

import sys
import time

import minimalmodbus
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUDRATE = int(sys.argv[2]) if len(sys.argv) > 2 else 9600

REGISTER_ADDRESS = 0
FUNCTION_CODE = 3
TIMEOUT = 0.3  # seconds, short since we're scanning many addresses


def try_address(addr: int) -> tuple[bool, str]:
    instrument = minimalmodbus.Instrument(PORT, addr, mode=minimalmodbus.MODE_RTU)
    instrument.serial.baudrate = BAUDRATE
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = TIMEOUT
    instrument.clear_buffers_before_each_transaction = True
    instrument.close_port_after_each_call = True

    try:
        value = instrument.read_register(
            registeraddress=REGISTER_ADDRESS,
            number_of_decimals=0,
            functioncode=FUNCTION_CODE,
            signed=False,
        )
        return True, f"raw register value = {value}"
    except minimalmodbus.NoResponseError:
        return False, "no response"
    except minimalmodbus.InvalidResponseError as exc:
        return False, f"invalid/garbled response: {exc}"
    except Exception as exc:  # noqa: BLE001 - we want to keep scanning regardless
        return False, f"error: {exc}"


def main() -> None:
    print(f"Scanning {PORT} at {BAUDRATE} baud, addresses 1-247 ...")
    print("(this can take a couple of minutes with a 0.3s timeout per address)\n")

    found = []

    for addr in range(1, 248):
        ok, detail = try_address(addr)
        marker = "✅" if ok else "  "
        # Only print non-silent results plus every 20th address as a progress heartbeat
        if ok:
            print(f"{marker} address {addr:3d}: {detail}")
            found.append(addr)
        elif "no response" not in detail:
            # garbled/invalid responses are still interesting - a real device may be there
            print(f"⚠️  address {addr:3d}: {detail}")
        elif addr % 20 == 0:
            print(f"   ... still scanning (up to address {addr})")

        time.sleep(0.02)

    print("\n--- Scan complete ---")
    if found:
        print(f"Responding address(es): {found}")
    else:
        print("No address responded cleanly.")
        print("If you saw ⚠️  lines above, a device may be present but garbling")
        print("its reply (check wiring/grounding). If you saw nothing at all,")
        print("the issue is likely wiring, power, or baud rate rather than address.")


if __name__ == "__main__":
    main()