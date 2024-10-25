from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
import can
from can import CanError, Message
from enum import Enum
import time
from typing import Optional
from motor_commands import MotorCommands
from typing import Dict

# Configuration
CAN_CHANNEL = 'can0'
CAN_BITRATE = 1_000_000  # 1Mbps
CAN_DATA_BITRATE = 5_000_000  # 5Mbps

COMMAND_ID_BASE = 0x200
CONTROL_RESPONSE_ID_BASE = 0x500
COMMON_MESSAGE_ID = 0x000
COMMON_RESPONSE_ID = 0x100
MODULE_ID_MASK = 0xFF


def setup_can_interface() -> Optional[can.BusABC]:
    """Set up the CAN interface"""
    try:
        bus: can.BusABC = can.Bus(
            channel=CAN_CHANNEL,
            interface='socketcan',
            fd=True,
            bitrate=CAN_BITRATE,
            data_bitrate=CAN_DATA_BITRATE,
        )
        print(f"Successfully configured {CAN_CHANNEL} for CANFD")
        print(f"Bitrate: {CAN_BITRATE / 1_000_000}Mbps, Data Bitrate: {CAN_DATA_BITRATE / 1_000_000}Mbps")
        return bus
    except CanError as e:
        print(f"Error setting up CAN interface: {e}")
        return None


class MotorController:
    motor_commands: MotorCommands
    def __init__(self):
        self.bus = setup_can_interface()
        self.session = PromptSession()
        
        # Setting up command completion
        self.motor_commands = MotorCommands(self.bus)

        self.commands = WordCompleter([
            'online', 'state',
            'set', 'get', 'monitor', 'status', 'help', 'exit',
            'speed', 'position', 'acceleration'
        ])

    def handle_response(self, response: Optional[Dict]) -> None:
        """ Display the response """
        if response:
            print(self.motor_commands.format_response(response))
        else:
            print("No response received")

    def monitor(self, duration: int = 10):
        """ Monitor CAN bus traffic """
        try:
            print(f"Monitoring CAN traffic for {duration} seconds... (Ctrl+C to stop)")
            start_time = time.time()
            
            while time.time() - start_time < duration:
                msg = self.bus.recv(timeout=0.1)
                if msg:
                    print(f"ID: {msg.arbitration_id:03X} Data: {msg.data.hex()}")
                    
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except CanError as e:
            print(f"Error monitoring CAN bus: {e}")

    def show_help(self):
        """ Show available commands """
        print("\nAvailable commands:")
        print("  set <motor_id> <parameter> <value>  - Set parameter value")
        print("  get <motor_id> <parameter>         - Get parameter value")
        print("  monitor [duration]                 - Monitor CAN traffic")
        print("  status                            - Show CAN interface status")
        print("  help                              - Show this help")
        print("  exit                              - Exit the program")
        print("\nParameters:")
        print("  speed, position, acceleration")
        print("\nExample:")
        print("  set 1 speed 100")
        print("  monitor 30\n")

    def run(self):
        """ Execute the interactive interface """
        if not self.bus:
            print("Failed to initialize CAN interface")
            return

        print("\nMotor Controller CLI")
        print("Type 'help' for available commands")
        
        while True:
            try:
                # Get the command from the user
                command = self.session.prompt("motor> ", completer=self.commands).strip()
                
                if not command:
                    continue
                    
                parts = command.split()
                cmd = parts[0].lower()

                if cmd == 'exit':
                    break
                    
                elif cmd == 'help':
                    self.show_help()
                    
                elif cmd == 'status':
                    print(f"CAN interface: {CAN_CHANNEL}")
                    print(f"Bitrate: {CAN_BITRATE / 1_000_000}Mbps")
                    print(f"Data Bitrate: {CAN_DATA_BITRATE / 1_000_000}Mbps")
                    
                elif cmd == 'monitor':
                    duration = int(parts[1]) if len(parts) > 1 else 10
                    self.monitor(duration)
                    
                elif cmd == 'set':
                    if len(parts) != 4:
                        print("Usage: set <motor_id> <parameter> <value>")
                        continue
                    
                    motor_id = int(parts[1])
                    parameter = parts[2]
                    value = int(parts[3])
                    
                    response = self.motor_commands.set_parameter(motor_id, parameter, value)
                    self.handle_response(response)

                elif cmd == 'get':
                    if len(parts) != 3:
                        print("Usage: get <motor_id> <parameter>")
                        continue
                    motor_id = int(parts[1])
                    parameter = parts[2]
                    response = self.motor_commands.get_parameter(motor_id, parameter)
                    self.handle_response(response)
                elif cmd == 'online':
                    if len(parts) != 2:
                        print("Usage: online <motor_id>")
                        continue
                    # motor_id は hex で入力される
                    motor_id = int(parts[1], 16)
                    self.motor_commands.iap_update(motor_id)
                elif cmd == 'state':
                    if len(parts) != 2:
                        print("Usage: state <motor_id>")
                        continue
                    motor_id = int(parts[1], 16)
                    response = self.motor_commands.get_current_state(motor_id)
                    self.handle_response(response)
                    
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                continue
            except Exception as e:
                print(f"Error: {e}")

    def cleanup(self):
        """Clean up resources"""
        if self.bus:
            self.bus.shutdown()