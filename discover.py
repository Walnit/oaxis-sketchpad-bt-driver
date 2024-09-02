import asyncio
from bleak import BleakScanner


async def main():
    async with BleakScanner() as scanner:
        print("Scanning...")
        found = False
        data = scanner.advertisement_data()
        if data is not None:
            async for bd, ad in data:
                if bd is not None and bd.name is not None:
                    if "SKETCHBOOK#" in bd.name:
                        print(f"Found {bd.name}! The MAC Address is:")
                        print(bd.address)
                        found = True
                        break

        if not found:
            print("Unable to find device! Make sure the name starts with 'SKETCHBOOK#' and is not currently connected to your device.")


if __name__ == "__main__":
    asyncio.run(main())
