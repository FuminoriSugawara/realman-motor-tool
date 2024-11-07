from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, NestedCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.application import create_app_session
import can
import time
from typing import Optional, Dict
from queue import Queue, Empty
import threading
from motor_commands import MotorCommands
import os
import csv
from datetime import datetime
from collections import defaultdict

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
        print("type 'help' for available commands")

        return bus
    except can.CanError as e:
        print(f"Error setting up CAN interface: {e}")
        return None


class MotorController:
    motor_commands: MotorCommands
    def __init__(self):
        self.bus = setup_can_interface()
        if not self.bus:
            raise Exception("Failed to initialize CAN interface")

        self.session = PromptSession()
        self.motor_commands = MotorCommands(self.bus)
        self.message_queue = Queue()
        
        # Logging related attributes
        self.start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.command_counts = defaultdict(int)
        self.response_counts = defaultdict(int)
        self.accumulated_stats = defaultdict(lambda: defaultdict(lambda: {'commands_sent': 0, 'responses_received': 0}))
        self.current_second = 0
        self.last_stats_time = time.time()
        
        self.running = False
        self.show_response = False
        self.logging_mode = False

        self.commands = WordCompleter([
            'online', 'state', 'set', 'get', 'monitor', 'status',
            'parameters', 'help', 'exit', 'startlog', 'stoplog'
        ])

    def _receive_messages(self):
        """Receive CAN messages and put them in the queue"""
        while self.running:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg:
                    self.message_queue.put(msg)
                    if self.logging_mode:
                        self._process_log_message(msg)
            except Exception as e:
                print(f"Error receiving message: {e}")

    def _process_log_message(self, message):
        """Process message for logging statistics"""
        command_id = message.arbitration_id & 0xFF00
        module_id = message.arbitration_id & MODULE_ID_MASK
        
        if command_id == COMMAND_ID_BASE:
            self.command_counts[module_id] += 1
        elif command_id == CONTROL_RESPONSE_ID_BASE:
            self.response_counts[module_id] += 1
        elif command_id == COMMON_MESSAGE_ID:
            self.command_counts[module_id] += 1
        elif command_id == COMMON_RESPONSE_ID:
            self.response_counts[module_id] += 1

        current_time = time.time()
        if current_time - self.last_stats_time >= 1:
            self._save_current_stats()
            self.last_stats_time = current_time
            self.current_second += 1

    def _save_current_stats(self):
        """Save current statistics to accumulated stats"""
        all_module_ids = set(self.command_counts.keys()) | set(self.response_counts.keys())
        
        print(f"\nSecond {self.current_second} statistics:")
        for module_id in sorted(all_module_ids):
            self.accumulated_stats[self.current_second][module_id] = {
                'commands_sent': self.command_counts[module_id],
                'responses_received': self.response_counts[module_id]
            }
            print(f"Motor ID {module_id}: Commands sent: {self.command_counts[module_id]}, "
                  f"Responses received: {self.response_counts[module_id]}")
        
        # Reset counters
        self.command_counts.clear()
        self.response_counts.clear()

    def save_stats_to_csv(self):
        """Save accumulated statistics to CSV file"""
        output_dir = 'can_output'
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f'{self.start_timestamp}_stats.csv')
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['second', 'motor_id', 'commands_sent', 'responses_received']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for second, motor_stats in self.accumulated_stats.items():
                for motor_id, data in motor_stats.items():
                    writer.writerow({
                        'second': second,
                        'motor_id': motor_id,
                        'commands_sent': data['commands_sent'],
                        'responses_received': data['responses_received']
                    })
        
        print(f"Stats saved to {filename}")

    def _process_messages(self):
        """Process messages from the queue"""
        while self.running:
            try:
                msg = self.message_queue.get(timeout=0.1)
                response = self.motor_commands.decode_response(msg)
                if self.show_response:
                    self._console_print_response(response)
            except Empty:
                continue
            except Exception as e:
                print(f"Error processing message: {e}")

    def _console_print_response(self, response: Dict) -> None:
        """Display the response"""
        if response:
            try:
                formated_response = self.motor_commands.format_response(response)
                print(f"\n{formated_response}")
            except Exception as e:
                print(f"Error formatting response: {e}")

    def _handle_command(self, command: str) -> None:
        """Handle the command"""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == 'exit':
            self.running = False
            if self.logging_mode:
                self.save_stats_to_csv()
            return

        elif cmd == 'startlog':
            self.logging_mode = True
            self.start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_second = 0
            self.last_stats_time = time.time()
            print("Started logging CAN messages")
            return

        elif cmd == 'stoplog':
            if self.logging_mode:
                self.logging_mode = False
                self.save_stats_to_csv()
                print("Stopped logging and saved statistics")
            else:
                print("Logging was not active")
            return

        elif cmd == 'help':
            self.show_help()

        elif cmd == 'status':
            print(f"CAN interface: {CAN_CHANNEL}")
            print(f"Bitrate: {CAN_BITRATE / 1_000_000}Mbps")
            print(f"Data Bitrate: {CAN_DATA_BITRATE / 1_000_000}Mbps")
            print(f"Logging: {'Active' if self.logging_mode else 'Inactive'}")

        elif cmd == 'monitor':
            duration = int(parts[1]) if len(parts) > 1 else 10
            self.monitor(duration)

        elif cmd == 'set':
            self.show_response = True
            if len(parts) != 4:
                print("Usage: set <motor_id> <parameter> <value>")
                return

            motor_id = int(parts[1])
            parameter = parts[2]
            value = int(parts[3])

            self.motor_commands.set_parameter(motor_id, parameter, value)
            self.show_response = False

        elif cmd == 'get':
            self.show_response = True
            if len(parts) != 3:
                print("Usage: get <motor_id> <parameter>")
                return
            motor_id = int(parts[1])
            parameter = parts[2]
            self.motor_commands.get_parameter(motor_id, parameter)
            time.sleep(0.1)
            self.show_response = False

        elif cmd == 'online':
            self.show_response = True
            if len(parts) != 2:
                print("Usage: online <motor_id>")
                return
            motor_id = int(parts[1], 16)
            self.motor_commands.iap_update(motor_id)
            time.sleep(0.1)
            self.show_response = False

        elif cmd == 'state':
            self.show_response = True
            if len(parts) != 2:
                print("Usage: state <motor_id>")
                return
            motor_id = int(parts[1], 16)
            self.motor_commands.get_current_state(motor_id)
            time.sleep(0.1)
            self.show_response = False

        elif cmd == 'parameters':
            self.list_parameters()

        else:
            print(f"Unknown command: {cmd}")
            print("Type 'help' for available commands")

    def _run_cli(self):
        with create_app_session() as app_session:
            with patch_stdout():
                while self.running:
                    try:
                        command = self.session.prompt("motor> ", completer=self.commands).strip()
                        if not command:
                            continue
                        self._handle_command(command)
                    except KeyboardInterrupt:
                        break
                    except EOFError:
                        break
                    except Exception as e:
                        print(f"Error: {e}")

    def monitor(self, duration: int = 10):
        """Monitor CAN bus traffic"""
        try:
            print(f"Monitoring CAN traffic for {duration} seconds... (Ctrl+C to stop)")
            start_time = time.time()
            
            while time.time() - start_time < duration:
                msg = self.bus.recv(timeout=0.1)
                if msg:
                    print(f"ID: {msg.arbitration_id:03X} Data: {msg.data.hex()}")
                    
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except can.CanError as e:
            print(f"Error monitoring CAN bus: {e}")

    def show_help(self):
        """Show available commands"""
        print("\nAvailable commands:")
        print("  online <motor_id>                   - Enter online mode")
        print("  set <motor_id> <parameter> <value>  - Set parameter value")
        print("  get <motor_id> <parameter>          - Get parameter value")
        print("  state <motor_id>                    - Get current state")
        print("  monitor [duration]                  - Monitor CAN traffic")
        print("  parameters                          - List available parameters")
        print("  status                             - Show CAN interface status")
        print("  startlog                           - Start logging CAN messages")
        print("  stoplog                            - Stop logging and save statistics")
        print("  help                               - Show this help")
        print("  exit                               - Exit the program")
    
    def list_parameters(self):
        """List available parameters"""
        print("Available parameters:")
        for param in self.motor_commands.get_available_parameters():
            print(f"  {param}")

    def run(self):
        """Execute the interactive interface"""
        self.running = True

        self.receiver_thread = threading.Thread(target=self._receive_messages)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

        self.processor_thread = threading.Thread(target=self._process_messages)
        self.processor_thread.daemon = True
        self.processor_thread.start()

        self._run_cli()

    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.logging_mode:
            self.save_stats_to_csv()
        if hasattr(self, 'receiver_thread'):
            self.receiver_thread.join()
        if hasattr(self, 'processor_thread'):
            self.processor_thread.join()
        if self.bus:
            self.bus.shutdown()