from queue import Queue
import threading
from typing import Optional, Dict, Callable
import time
import can
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PendingResponse:
    command_id: int
    callback: Callable
    timestamp: float
    timeout: float

class ResponseHandler:
    def __init__(self, bus: can.BusABC):
        self.bus = bus
        self.response_queue = Queue()
        self.pending_responses = defaultdict(list)
        self.running = False
        self.lock = threading.Lock()
        
    def start(self):
        """Start the response handler thread"""
        self.running = True
        self.receiver_thread = threading.Thread(target=self._receive_messages)
        self.processor_thread = threading.Thread(target=self._process_responses)
        self.receiver_thread.daemon = True
        self.processor_thread.daemon = True
        self.receiver_thread.start()
        self.processor_thread.start()
        
    def stop(self):
        """Stop the response handler thread"""
        self.running = False
        if hasattr(self, 'receiver_thread'):
            self.receiver_thread.join()
        if hasattr(self, 'processor_thread'):
            self.processor_thread.join()
            
    def register_callback(self, command_id: int, callback: Callable, timeout: float = 1.0):
        """Register a callback for a specific command ID"""
        with self.lock:
            pending = PendingResponse(
                command_id=command_id,
                callback=callback,
                timestamp=time.time(),
                timeout=timeout
            )
            self.pending_responses[command_id].append(pending)
            
    def _receive_messages(self):
        """Receive CAN messages and put them in the queue"""
        while self.running:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg:
                    self.response_queue.put(msg)
            except Exception as e:
                print(f"Error receiving message: {e}")
                
    def _process_responses(self):
        """Process received messages and call appropriate callbacks"""
        while self.running:
            try:
                # Remove expired callbacks
                current_time = time.time()
                with self.lock:
                    for command_id in list(self.pending_responses.keys()):
                        self.pending_responses[command_id] = [
                            pending for pending in self.pending_responses[command_id]
                            if current_time - pending.timestamp < pending.timeout
                        ]
                        if not self.pending_responses[command_id]:
                            del self.pending_responses[command_id]
                
                # Process new messages
                try:
                    msg = self.response_queue.get(timeout=0.1)
                except Queue.Empty:
                    continue
                
                response_id = msg.arbitration_id
                with self.lock:
                    if response_id in self.pending_responses:
                        for pending in self.pending_responses[response_id]:
                            try:
                                pending.callback(msg)
                            except Exception as e:
                                print(f"Error in callback: {e}")
                        self.pending_responses[response_id].clear()
                
            except Exception as e:
                print(f"Error processing response: {e}")