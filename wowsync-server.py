"""
Simple Socket Server for WoW Sync Client
Demonstrates how to send commands to the client using raw sockets
Uses hostname instead of localhost for network accessibility
"""

import asyncio
import socket
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WowSyncServer:
    """Simple server to send commands to WoW Sync clients"""
    
    def __init__(self, host=None, port=8765):
        # Use hostname if not specified
        self.host = host if host else socket.gethostname()
        self.port = port
        self.clients = []
        self.server = None
        self.keybinds = self._load_server_config()
    
    def _load_server_config(self):
        """Load server configuration from Documents/wowsync/server.json"""
        config_dir = Path.home() / "Documents" / "wowsync"
        server_config_path = config_dir / "server.json"
        
        # Create default config if it doesn't exist
        if not server_config_path.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            default_config = {
                "host": socket.gethostname(),
                "port": 8765,
                "keybinds": {
                    "F1": "window1",
                    "F2": "window2",
                    "F3": "window3", 
                    "F4": "window4",
                    "F5": "window5"
                }
            }
            with open(server_config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            logger.info(f"Created default server.json at {server_config_path}")
        
        # Load configuration
        try:
            with open(server_config_path, 'r') as f:
                config = json.load(f)
                self.host = config.get("host", self.host)
                self.port = config.get("port", self.port)
                return config.get("keybinds", {})
        except Exception as e:
            logger.error(f"Failed to load server config: {e}")
            return {
                "F1": "window1",
                "F2": "window2", 
                "F3": "window3",
                "F4": "window4",
                "F5": "window5"
            }
    
    async def handle_client(self, reader, writer):
        """Handle individual client connections"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"Client connected: {client_addr}")
        self.clients.append((reader, writer))
        
        try:
            while True:
                # Read message length first (4 bytes)
                length_data = await reader.readexactly(4)
                if not length_data:
                    break
                
                message_length = int.from_bytes(length_data, byteorder='big')
                
                # Read the actual message
                message_data = await reader.readexactly(message_length)
                message = message_data.decode('utf-8')
                
                logger.info(f"Received from {client_addr}: {message}")
                
        except asyncio.IncompleteReadError:
            logger.info(f"Client {client_addr} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            if (reader, writer) in self.clients:
                self.clients.remove((reader, writer))
            writer.close()
            await writer.wait_closed()
    
    async def send_to_all_clients(self, message: str):
        """Send message to all connected clients"""
        if not self.clients:
            logger.warning("No clients connected")
            return
        
        message_bytes = message.encode('utf-8')
        message_length = len(message_bytes)
        length_bytes = message_length.to_bytes(4, byteorder='big')
        
        disconnected_clients = []
        
        for reader, writer in self.clients:
            try:
                writer.write(length_bytes + message_bytes)
                await writer.drain()
                logger.info(f"Sent to client: {message}")
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected_clients.append((reader, writer))
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in self.clients:
                self.clients.remove(client)
    
    async def start_server(self):
        """Start the server"""
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        
        logger.info(f"Server started on {self.host}:{self.port}")
        logger.info(f"Machine IP: {socket.gethostbyname(socket.gethostname())}")
        logger.info("Keybind mappings:")
        for key, window in self.keybinds.items():
            logger.info(f"  {key} -> {window}")
        logger.info("\nCommands you can send:")
        logger.info("- F1-F5 keys will map to corresponding windows")
        logger.info("- Type 'quit' to stop server")
        
        # Start command input handler
        asyncio.create_task(self.command_handler())
        
        async with self.server:
            await self.server.serve_forever()
    
    async def send_key_command(self, key: str):
        """Send a key command using the keybind mapping"""
        key_upper = key.upper()
        if key_upper not in self.keybinds:
            logger.warning(f"Key {key_upper} not found in keybinds")
            return
        
        window = self.keybinds[key_upper]
        action = f"{key.lower()}_action"
        
        command = {
            "command": "execute",
            "window": window,
            "action": action
        }
        
        await self.send_to_all_clients(json.dumps(command))
        logger.info(f"Sent {key_upper} command to {window}")
    
    async def command_handler(self):
        """Handle user input for sending commands"""
        while True:
            try:
                # Example: automatically send some test commands
                await asyncio.sleep(10)  # Wait 10 seconds
                
                # Send F1 to mapped window
                await self.send_key_command("F1")
                
                await asyncio.sleep(15)  # Wait 15 seconds
                
                # Send F2 to mapped window
                await self.send_key_command("F2")
                
                await asyncio.sleep(15)  # Wait 15 seconds
                
                # Send F3 to mapped window
                await self.send_key_command("F3")
                
            except Exception as e:
                logger.error(f"Error in command handler: {e}")
                break


async def main():
    """Main server function"""
    server = WowSyncServer()
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")


if __name__ == "__main__":
    asyncio.run(main())