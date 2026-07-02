import sys
import asyncio
from crawl import crawl_site_async
from json_report import write_json_report


async def main_async():
    if len(sys.argv) < 2:
        print("no website provided")
        exit(1)
    elif len(sys.argv) > 4:
        print("too many arguments provided")
        exit(1)
    else:
        print(f"starting crawl of: {sys.argv[1]}")
        page_data = await crawl_site_async(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
        write_json_report(page_data)


if __name__ == "__main__":
    asyncio.run(main_async())
