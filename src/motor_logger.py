import os
import csv
from collections import defaultdict
from datetime import datetime
from typing import Dict, List
from motor_commands import ControlCommandMessage, ServoResponseMessage
import pandas as pd
from dataclasses import asdict

class MotorLogger:
    def __init__(self):
        self.start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = 'can_output'
        
        # Motor control values and servo status logs
        self.control_commands: Dict[int, List[ControlCommandMessage]] = {}
        self.servo_responses: Dict[int, List[ServoResponseMessage]] = {}
        
        # Message statistics
        self.command_counts = defaultdict(int)
        self.response_counts = defaultdict(int)
        self.accumulated_stats = defaultdict(lambda: defaultdict(lambda: {'commands_sent': 0, 'responses_received': 0}))
        
        self.current_second = 0
        self.last_stats_time = None

 
    
    def _log_control_command(self, msg: ControlCommandMessage):
        """Log a control command message"""

        if msg.module_id not in self.control_commands:
            self.control_commands[msg.module_id] = []
        self.control_commands[msg.module_id].append(msg)
        self.command_counts[msg.module_id] += 1
    
    def _log_servo_response(self, msg: ServoResponseMessage):
        """Log a servo response message"""
        
        if msg.module_id not in self.servo_responses:
            self.servo_responses[msg.module_id] = []
        self.servo_responses[msg.module_id].append(msg)
        self.response_counts[msg.module_id] += 1

    
    def log(self, msg: ControlCommandMessage | ServoResponseMessage):
        """Log a message"""
        if isinstance(msg, ControlCommandMessage):
            self._log_control_command(msg)
        elif isinstance(msg, ServoResponseMessage):
            self._log_servo_response(msg)

        self.update_stats(msg.timestamp)

    
    def update_stats(self, current_time: float):
        """Update accumulated statistics"""
        if self.last_stats_time is None:
            self.last_stats_time = current_time
            return

        if current_time - self.last_stats_time >= 1.0:
            self._save_current_stats()
            self.current_second += 1
            self.last_stats_time = current_time
    
    def _save_current_stats(self):
        """Save current statistics"""
        all_motor_ids = set(self.command_counts.keys()) | set(self.response_counts.keys())
        
        for motor_id in sorted(all_motor_ids):
            self.accumulated_stats[self.current_second][motor_id] = {
                'commands_sent': self.command_counts[motor_id],
                'responses_received': self.response_counts[motor_id]
            }
        
        # Reset counters
        self.command_counts.clear()
        self.response_counts.clear()
    
    def save_to_csv(self):
        """Save all logs to CSV files"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save control values
        for motor_id, values in self.control_commands.items():
            df = pd.DataFrame([asdict(v) for v in values])
            filename = os.path.join(self.output_dir, f'{self.start_timestamp}_control_commands_{motor_id}.csv')
            df.to_csv(filename, index=False)
            print(f"Saved control values for motor {motor_id} to {filename}")
        
        # Save servo status
        for motor_id, status_list in self.servo_responses.items():
            df = pd.DataFrame([asdict(s) for s in status_list])
            filename = os.path.join(self.output_dir, f'{self.start_timestamp}_servo_responses_{motor_id}.csv')
            df.to_csv(filename, index=False)
            print(f"Saved servo status for motor {motor_id} to {filename}")
        
        # Save statistics
        stats_file = os.path.join(self.output_dir, f'{self.start_timestamp}_stats.csv')
        with open(stats_file, 'w', newline='') as csvfile:
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

        print(f"Saved statistics to {stats_file}")
    
    def clear(self):
        """Clear all logs"""
        self.control_commands.clear()
        self.servo_responses.clear()
        self.command_counts.clear()
        self.response_counts.clear()
        self.accumulated_stats.clear()
        self.current_second = 0
        self.last_stats_time = None
        self.start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")