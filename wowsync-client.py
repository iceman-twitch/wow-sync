"""
WoW Sync Client - Multi-window automation client for World of Warcraft
Handles multiple windows, server communication, and anti-AFK functionality.
Python 3.9+ compatible
"""

import asyncio
import socket
import json
import logging
import os
import time
import random
import threading
from pathlib import Path
from typing import List, Dict, Union, Optional

import mouse
from pynput import keyboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wowsync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration files in Documents/wowsync folder"""
    
    def __init__(self):
        self.config_dir = Path.home() / "Documents" / "wowsync"
        self.windows_config = self.config_dir / "windows.json"
        self.actions_config = self.config_dir / "actions.json"
        self._ensure_config_dir()
        self._create_default_configs()
    
    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Config directory: {self.config_dir}")
    
    def _create_default_configs(self):
        """Create default configuration files if they don't exist"""
        # Default windows configuration
        default_windows = {
            "window1": {"x": 100, "y": 100, "title": "World of Warcraft"},
            "window2": {"x": 200, "y": 150, "title": "World of Warcraft"},
            "window3": {"x": 300, "y": 200, "title": "World of Warcraft"},
            "window4": {"x": 400, "y": 250, "title": "World of Warcraft"},
            "window5": {"x": 500, "y": 300, "title": "World of Warcraft"}
        }
        
        # Default actions configuration
        default_actions = {
            "idle_action": {
                "keys": ["space", "q"],  # Space then Q for anti-AFK
                "delay_between_keys": [1, 2],  # 1-2 seconds between keys (human-like)
                "key_hold_time": [0.09, 0.15],  # Random hold time range
                "delay_after_focus": [1, 2]  # 1-2 seconds after focusing window
            },
            "f1_action": {
                "keys": ["f1"],
                "delay_between_keys": 0.1,
                "key_hold_time": [0.09, 0.15],
                "delay_after_focus": [1, 1.5]
            },
            "f2_action": {
                "keys": ["f2"],
                "delay_between_keys": 0.1,
                "key_hold_time": [0.09, 0.15],
                "delay_after_focus": [1, 1.5]
            },
            "f3_action": {
                "keys": ["f3"],
                "delay_between_keys": 0.1,
                "key_hold_time": [0.09, 0.15],
                "delay_after_focus": [1, 1.5]
            },
            "f4_action": {
                "keys": ["f4"],
                "delay_between_keys": 0.1,
                "key_hold_time": [0.09, 0.15],
                "delay_after_focus": [1, 1.5]
            },
            "f5_action": {
                "keys": ["f5"],
                "delay_between_keys": 0.1,
                "key_hold_time": [0.09, 0.15],
                "delay_after_focus": [1, 1.5]
            }
        }
        
        if not self.windows_config.exists():
            with open(self.windows_config, 'w') as f:
                json.dump(default_windows, f, indent=4)
            logger.info(f"Created default windows.json at {self.windows_config}")
        
        if not self.actions_config.exists():
            with open(self.actions_config, 'w') as f:
                json.dump(default_actions, f, indent=4)
            logger.info(f"Created default actions.json at {self.actions_config}")
    
    def load_windows(self) -> Dict:
        """Load windows configuration"""
        try:
            with open(self.windows_config, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load windows config: {e}")
            return {}
    
    def load_actions(self) -> Dict:
        """Load actions configuration"""
        try:
            with open(self.actions_config, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load actions config: {e}")
            return {}
    
    def save_windows(self, windows_data: Dict):
        """Save windows configuration"""
        try:
            with open(self.windows_config, 'w') as f:
                json.dump(windows_data, f, indent=4)
            logger.info("Windows configuration saved")
        except Exception as e:
            logger.error(f"Failed to save windows config: {e}")


class WindowManager:
    """Manages multiple game windows and their coordinates"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.windows_config = config_manager.load_windows()
        self.active_windows = {}
        self._setup_windows()
    
    def _setup_windows(self):
        """Setup windows from configuration"""
        # For now, we'll use the configuration as-is
        # In a real implementation, you might want to discover actual windows
        for window_key, window_config in self.windows_config.items():
            self.active_windows[window_key] = {
                'title': window_config['title'],
                'click_x': window_config['x'],
                'click_y': window_config['y']
            }
        
        logger.info(f"Configured {len(self.active_windows)} windows: {list(self.active_windows.keys())}")
    
    def focus_window(self, window_key: str) -> bool:
        """Focus a specific window by clicking on its coordinates"""
        if window_key not in self.active_windows:
            logger.warning(f"Window {window_key} not found")
            return False
        
        window_info = self.active_windows[window_key]
        try:
            # Click on the specified coordinates to focus the window
            mouse.move(window_info['click_x'], window_info['click_y'])
            
            # Add small random offset to make it more human-like (90-110% of position)
            offset_x = random.uniform(-0.1, 0.1) * 10  # ±10 pixels
            offset_y = random.uniform(-0.1, 0.1) * 10  # ±10 pixels
            
            final_x = window_info['click_x'] + offset_x
            final_y = window_info['click_y'] + offset_y
            
            mouse.move(final_x, final_y)
            mouse.click('left')
            
            logger.info(f"Focused window {window_key} at ({final_x:.1f}, {final_y:.1f})")
            return True
        except Exception as e:
            logger.error(f"Failed to focus window {window_key}: {e}")
            return False
    
    def get_window_list(self) -> List[str]:
        """Get list of available windows"""
        return list(self.active_windows.keys())


class ActionHandler:
    """Handles action execution on windows"""
    
    def __init__(self, config_manager: ConfigManager, window_manager: WindowManager):
        self.config_manager = config_manager
        self.window_manager = window_manager
        self.actions_config = config_manager.load_actions()
        self.keyboard_controller = keyboard.Controller()
    
    def execute_action(self, window_key: str, action_name: str) -> bool:
        """Execute an action on a specific window with human-like timing"""
        if not self.window_manager.focus_window(window_key):
            return False
        
        if action_name not in self.actions_config:
            logger.warning(f"Action {action_name} not found in config")
            return False
        
        action = self.actions_config[action_name]
        try:
            # Wait random time after focusing (human-like behavior)
            delay_range = action.get('delay_after_focus', [1, 1.5])
            focus_delay = random.uniform(delay_range[0], delay_range[1])
            time.sleep(focus_delay)
            logger.info(f"Waited {focus_delay:.2f}s after focusing {window_key}")
            
            # Execute each key with human-like timing
            for i, key in enumerate(action['keys']):
                if i > 0:  # Add delay between keys (except first)
                    delay_between = action.get('delay_between_keys', 0.1)
                    time.sleep(delay_between)
                
                # Random key hold time (press and release)
                hold_time_range = action.get('key_hold_time', [0.09, 0.15])
                hold_time = random.uniform(hold_time_range[0], hold_time_range[1])
                
                # Use pynput to press keys
                key_obj = self._get_key_object(key)
                if key_obj:
                    # Key down
                    self.keyboard_controller.press(key_obj)
                    time.sleep(hold_time)  # Hold the key
                    # Key up
                    self.keyboard_controller.release(key_obj)
                    
                    logger.info(f"Pressed {key} for {hold_time:.3f}s on {window_key}")
            
            logger.info(f"Executed {action_name} on {window_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute action {action_name} on {window_key}: {e}")
            return False
    
    def _get_key_object(self, key: str):
        """Convert key string to pynput key object"""
        key_map = {
            'space': keyboard.Key.space,
            'q': 'q',
            'f1': keyboard.Key.f1,
            'f2': keyboard.Key.f2,
            'f3': keyboard.Key.f3,
            'f4': keyboard.Key.f4,
            'f5': keyboard.Key.f5,
        }
        return key_map.get(key.lower(), None)


class StateManager:
    """Manages application states and cooldowns"""
    
    def __init__(self):
        self.current_state = "idle"  # idle, active_window1, active_window2, etc.
        self.last_action_time = 0
        self.action_cooldown = 2  # 2 seconds cooldown between actions
        self.idle_timeout = 10  # 10 seconds to return to idle after action
        self.active_window = None
    
    def can_execute_action(self) -> bool:
        """Check if we can execute an action (cooldown check)"""
        return time.time() - self.last_action_time >= self.action_cooldown
    
    def set_active_window(self, window_key: str):
        """Set active window state"""
        self.current_state = f"active_{window_key}"
        self.active_window = window_key
        self.last_action_time = time.time()
        logger.info(f"State: {self.current_state}")
    
    def set_idle(self):
        """Set idle state"""
        self.current_state = "idle"
        self.active_window = None
        logger.info("State: idle")
    
    def is_idle(self) -> bool:
        """Check if currently in idle state"""
        return self.current_state == "idle"
    
    def should_return_to_idle(self) -> bool:
        """Check if we should return to idle (10 second timeout)"""
        if self.is_idle():
            return False
        return time.time() - self.last_action_time >= self.idle_timeout
    
    def get_current_state(self) -> str:
        """Get current state"""
        return self.current_state


class IdleManager:
    """Manages idle mode and anti-AFK functionality"""
    
    def __init__(self, window_manager: WindowManager, action_handler: ActionHandler, state_manager: StateManager):
        self.window_manager = window_manager
        self.action_handler = action_handler
        self.state_manager = state_manager
        self.is_running = False
        self.idle_task = None
        self.current_window_index = 0
    
    async def start_idle_mode(self):
        """Start idle mode - cycle through windows and perform anti-AFK actions"""
        if self.is_running:
            return
            
        self.is_running = True
        self.state_manager.set_idle()
        logger.info("Starting idle mode")
        
        while self.is_running:
            # Check if we should return to idle from active state
            if self.state_manager.should_return_to_idle():
                self.state_manager.set_idle()
                logger.info("Returned to idle after timeout")
            
            # Only do idle actions if we're actually in idle state
            if self.state_manager.is_idle():
                windows = self.window_manager.get_window_list()
                if windows:
                    # Get current window
                    window_key = windows[self.current_window_index % len(windows)]
                    
                    # Focus window and perform anti-AFK action
                    if self.window_manager.focus_window(window_key):
                        # Random delay between 1-2 seconds after focusing (human-like)
                        idle_delay = random.uniform(1, 2)
                        await asyncio.sleep(idle_delay)
                        
                        if self.state_manager.is_idle():  # Check if still idle
                            # Execute idle action (space then Q with random timing)
                            await self._perform_idle_action(window_key)
                    
                    # Move to next window
                    self.current_window_index = (self.current_window_index + 1) % len(windows)
            
            # Wait before next cycle (human-like timing variation 90-110%)
            base_cycle_time = 8
            variation = random.uniform(0.9, 1.1)  # 90-110% variation
            cycle_delay = base_cycle_time * variation
            await asyncio.sleep(cycle_delay)
    
    async def _perform_idle_action(self, window_key: str):
        """Perform idle action with human-like random timing"""
        try:
            # Press space first
            self.action_handler.keyboard_controller.press(keyboard.Key.space)
            space_hold = random.uniform(0.09, 0.15)
            await asyncio.sleep(space_hold)
            self.action_handler.keyboard_controller.release(keyboard.Key.space)
            
            # Random delay between space and Q (1-2 seconds)
            between_delay = random.uniform(1, 2)
            await asyncio.sleep(between_delay)
            
            # Press Q
            self.action_handler.keyboard_controller.press('q')
            q_hold = random.uniform(0.09, 0.15)
            await asyncio.sleep(q_hold)
            self.action_handler.keyboard_controller.release('q')
            
            logger.info(f"Performed idle action on {window_key} (space:{space_hold:.3f}s, delay:{between_delay:.2f}s, q:{q_hold:.3f}s)")
            
        except Exception as e:
            logger.error(f"Error performing idle action: {e}")
    
    def stop_idle_mode(self):
        """Stop idle mode"""
        self.is_running = False
        logger.info("Stopping idle mode")


class AsyncClient:
    """Handles socket communication with server using asyncio"""
    
    def __init__(self, window_manager: WindowManager, action_handler: ActionHandler, idle_manager: IdleManager, state_manager: StateManager):
        self.window_manager = window_manager
        self.action_handler = action_handler
        self.idle_manager = idle_manager
        self.state_manager = state_manager
        self.socket = None
        self.reader = None
        self.writer = None
        self.server_host = "localhost"
        self.server_port = 8765
        self.connected = False
    
    async def connect_to_server(self):
        """Connect to the server using asyncio socket and listen for commands"""
        while True:
            try:
                logger.info(f"Connecting to server at {self.server_host}:{self.server_port}")
                
                # Create asyncio socket connection
                self.reader, self.writer = await asyncio.open_connection(
                    self.server_host, self.server_port
                )
                
                self.connected = True
                logger.info("Connected to server")
                
                # Listen for messages
                while self.connected:
                    try:
                        # Read message length first (4 bytes)
                        length_data = await self.reader.readexactly(4)
                        if not length_data:
                            break
                        
                        message_length = int.from_bytes(length_data, byteorder='big')
                        
                        # Read the actual message
                        message_data = await self.reader.readexactly(message_length)
                        message = message_data.decode('utf-8')
                        
                        await self.handle_server_message(message)
                        
                    except asyncio.IncompleteReadError:
                        logger.warning("Server disconnected")
                        break
                    except Exception as e:
                        logger.error(f"Error reading from server: {e}")
                        break
                
            except Exception as e:
                logger.error(f"Server connection error: {e}")
                self.connected = False
                
                # Close writer if it exists
                if self.writer:
                    self.writer.close()
                    await self.writer.wait_closed()
                
                # Wait before reconnecting
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
    
    async def send_message(self, message: str):
        """Send message to server with length prefix"""
        if not self.connected or not self.writer:
            logger.warning("Not connected to server")
            return False
        
        try:
            # Encode message
            message_bytes = message.encode('utf-8')
            message_length = len(message_bytes)
            
            # Send length first (4 bytes) then message
            length_bytes = message_length.to_bytes(4, byteorder='big')
            self.writer.write(length_bytes + message_bytes)
            await self.writer.drain()
            
            logger.debug(f"Sent message: {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.connected = False
            return False
    
    async def handle_server_message(self, message: str):
        """Handle incoming messages from server"""
        try:
            data = json.loads(message)
            command = data.get('command')
            window = data.get('window')
            action = data.get('action', 'f1_action')  # Default action
            
            if command == 'execute' and window:
                logger.info(f"Received command: {command} on {window} with action {action}")
                
                # Check cooldown
                if not self.state_manager.can_execute_action():
                    logger.warning(f"Action on cooldown, ignoring command for {window}")
                    response = {
                        'status': 'cooldown',
                        'window': window,
                        'action': action
                    }
                    await self.send_message(json.dumps(response))
                    return
                
                # Set active window state
                self.state_manager.set_active_window(window)
                
                # Execute the action
                success = self.action_handler.execute_action(window, action)
                
                # Send response to server
                response = {
                    'status': 'success' if success else 'error',
                    'window': window,
                    'action': action,
                    'state': self.state_manager.get_current_state()
                }
                await self.send_message(json.dumps(response))
                
                logger.info(f"Action completed on {window}, will return to idle after 10 seconds")
                
        except Exception as e:
            logger.error(f"Error handling server message: {e}")
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.writer:
            self.writer.close()


class WowSyncClient:
    """Main application class"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.window_manager = WindowManager(self.config_manager)
        self.action_handler = ActionHandler(self.config_manager, self.window_manager)
        self.state_manager = StateManager()
        self.idle_manager = IdleManager(self.window_manager, self.action_handler, self.state_manager)
        self.client = AsyncClient(self.window_manager, self.action_handler, self.idle_manager, self.state_manager)
        self.running = False
    
    async def start(self):
        """Start the application"""
        self.running = True
        logger.info("Starting WoW Sync Client")
        logger.info(f"Initial state: {self.state_manager.get_current_state()}")
        
        # Start idle mode initially
        idle_task = asyncio.create_task(self.idle_manager.start_idle_mode())
        
        # Start server connection
        server_task = asyncio.create_task(self.client.connect_to_server())
        
        try:
            await asyncio.gather(idle_task, server_task)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False
            self.idle_manager.stop_idle_mode()
            self.client.disconnect()


if __name__ == "__main__":
    client = WowSyncClient()
    asyncio.run(client.start())
