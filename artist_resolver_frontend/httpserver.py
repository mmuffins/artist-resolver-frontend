import asyncio
import os
from aiohttp import web


class HttpServer:
    def __init__(
        self, main_window, host: str, port: str, loop: asyncio.SelectorEventLoop
    ):
        self.main_window = main_window
        self.host = host
        self.port = port
        self.loop = loop

    def start_server(self):
        webapp = web.Application()
        webapp.add_routes([web.post("/load_files", self.handle_load_files_request)])
        runner = web.AppRunner(webapp)
        self.loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, self.host, self.port)
        self.loop.run_until_complete(site.start())

    async def handle_load_files_request(self, request):
        try:
            data = await request.json()
            files = [
                os.path.normpath(file["path"]) for file in data["files"] if os.path.exists(os.path.normpath(file["path"]))
            ]
            if files:
                self.main_window.load_files(files)
                return web.Response(status=200, text="Files loaded successfully")
            else:
                return web.Response(status=400, text="No valid files found")
        except Exception as e:
            return web.Response(status=500, text=f"An error occurred: {str(e)}")
