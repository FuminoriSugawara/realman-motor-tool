from enum import IntEnum, Enum
from typing import Dict, Optional
import time
import can

class CommandMessageType(IntEnum):
    COMMON = 0x0000   # 共通コマンド
    SERVO_POS = 0x0200      # 位置サーボコマンド
    SERVO_VEL = 0x0300      # 速度サーボコマンド
    SERVO_CUR = 0x0400      # 電流サーボコマンド
    JSTATE = 0x0600   # ジョイントステータス要求

class ResponseMessageType(IntEnum):
    COMMON = 0x0100   # 共通コマンド応答
    SERVO = 0x0500    # サーボコマンド応答
    JSTATE = 0x0700   # ジョイントステータス応答
    DEBUG = 0x0900    # デバッグ情報応答

class ServoMode(IntEnum):
    OPN = 0x00  # オープンループ
    CUR = 0x01  # 電流制御
    VEL = 0x02  # 速度制御
    POS = 0x03  # 位置制御

class CommandType(IntEnum):
    CMD_RD = 0x01  # 読み込み
    CMD_WR = 0x02  # 書き込み

class CommandIndex(IntEnum):
    # Common commands
    SYS_ID = 0x01
    SYS_FW_VERSION = 0x03
    SYS_ERROR = 0x04
    SYS_VOLTAGE = 0x05
    SYS_TEMP = 0x06
    SYS_REDU_RATIO = 0x07
    # System flag commands
    SYS_ENABLE_DRIVER = 0x0A
    SYS_ENABLE_ON_POWER = 0x0B
    SYS_SAVE_TO_FLASH = 0x0C
    SYS_ABSOLUTE_POS_AUTO_CALIB = 0x0D
    SYS_SET_ZERO_POS = 0x0E
    SYS_CLEAR_ERROR = 0x0F
    # Query commands
    CUR_CURRENT_L = 0x10
    CUR_CURRENT_H = 0x11
    CUR_SPEED_L = 0x12
    CUR_SPEED_H = 0x13
    CUR_POSITION_L = 0x14
    CUR_POSITION_H = 0x15
    # Motor model commands
    MOT_MODEL_ID0 = 0x2A
    MOT_MODEL_ID1 = 0x2B
    MOT_MODEL_ID2 = 0x2C
    MOT_MODEL_ID3 = 0x2D
    MOT_MODEL_ID4 = 0x2E
    MOT_MODEL_ID5 = 0x2F
    # Target commands
    TAG_WORK_MODE = 0x30
    TAG_CURRENT_L = 0x32
    TAG_CURRENT_H = 0x33
    TAG_SPEED_L = 0x34
    TAG_SPEED_H = 0x35
    TAG_POSITION_L = 0x36
    TAG_POSITION_H = 0x37
    SPEED_FEED_FORWARD_SWITCH = 0x39
    # Limit commands
    LIT_MAX_CURRENT = 0x40
    LIT_MAX_SPEED = 0x41
    LIT_MAX_ACC = 0x42
    LIT_MAX_DEC = 0x43
    LIT_MIN_POSITION_L = 0x44
    LIT_MIN_POSITION_H = 0x45
    LIT_MAX_POSITION_L = 0x46
    LIT_MAX_POSITION_H = 0x47
    # IAP commands
    IAP_FLAG = 0x49
    # PID commands
    SEV_CURRENT_P = 0x51
    SEV_CURRENT_I = 0x52
    SEV_CURRENT_D = 0x53
    SEV_SPEED_P = 0x54
    SEV_SPEED_I = 0x55
    SEV_SPEED_D = 0x56
    SEV_SPEED_DS = 0x57
    SEV_POSITION_P = 0x58
    SEV_POSITION_I = 0x59
    SEV_POSITION_D = 0x5A
    SEV_POSITION_DS = 0x5B
    # Error commands
    ERROR = 0x78

class ErrorCode(IntEnum):
    FOC_RATE_TOO_HIGH = 0x0001
    OVER_VOLTAGE = 0x0002
    UNDER_VOLTAGE = 0x0004
    OVER_TEMPERATURE = 0x0008
    STARTUP_FAILED = 0x0010
    ENCODER_ERROR = 0x0020
    OVER_CURRENT = 0x0040
    SOFTWARE_ERROR = 0x0080
    THERMAL_SENSOR_ERROR = 0x0100
    POSITION_LIMIT_ERROR = 0x0200
    JOINT_ID_INVALID = 0x0400
    POSITION_HORMING_LIMIT_OVER = 0x0800
    CURRENT_DETECTION_ERROR = 0x1000
    BLAKE_FAILED = 0x2000
    POSITION_COMMAND_STEP_ERROR = 0x4000
    MULTI_TURN_COUNT_ERROR = 0x8000

class UnitScaleFactor(float, Enum):
    VOLTAGE = 0.01 # V
    TEMPERATURE = 0.1 # Degrees Celsius
    POSITION = 0.0001 # Degrees
    TARGET_SPEED = 0.002 # RPM
    ACTUAL_SPEED = 0.02 # RPM
    CURRENT_MODEL10 = 1.0 # mA
    CURRENT_MODEL30 = 1.0 # mA
    CURRENT_MODEL60 = 2.0 # mA
    CURRENT_FEEDFORWARD = 2.0 # mA


# 書き込み可能なパラメータのリスト
WRITABLE_PARAMETERS = [
    CommandIndex.SYS_ID,
    CommandIndex.SYS_ENABLE_DRIVER,
    CommandIndex.SYS_ENABLE_ON_POWER,
    CommandIndex.SYS_SAVE_TO_FLASH,
    CommandIndex.SYS_ABSOLUTE_POS_AUTO_CALIB,
    CommandIndex.SYS_SET_ZERO_POS,
    CommandIndex.SYS_CLEAR_ERROR,
    CommandIndex.TAG_WORK_MODE,
    CommandIndex.TAG_CURRENT_L,
    CommandIndex.TAG_CURRENT_H,
    CommandIndex.TAG_SPEED_L,
    CommandIndex.TAG_SPEED_H,
]









class MotorCommands:
    bus: can.BusABC
    # can.BusABC をコンストラクタで受け取る
    def __init__(self, bus: can.BusABC):
        self.bus = bus
    
    def send_message(self, command_id: int, data: list[int]) -> None:
        data = bytes(data)
        """Send a message"""
        msg = can.Message(
            arbitration_id=command_id,
            is_fd=True,
            is_extended_id=False,
            data=data
        )
        self.bus.send(msg)
    
    def send_and_receive(self, command_id: int, data: list[int], timeout: float = 1.0) -> Optional[Dict]:
        """Send a message and wait for response
        
        Args:
            command_id: Command identifier
            data: Message data bytes
            timeout: Response timeout in seconds
            
        Returns:
            Decoded response message or None if no response received
        """
        try:
            self.send_message(command_id, data)
            # wait 1ms for response

            time.sleep(0.0001)
            response = self.bus.recv(timeout=timeout)
            if response:
                return self.decode_response(response)
            return None
        except Exception as e:
            print(f"Error in send_and_receive: {e}")
            return None
    
    def decode_response(self, msg: can.Message) -> Dict:
        """Decode response message
        
        Args:
            msg: CAN message to decode
            
        Returns:
            Dictionary containing decoded message data
        """
        try:
            response_type = msg.arbitration_id & 0x0F00
            module_id = msg.arbitration_id & 0xFF
            response_data = {}

            if response_type == ResponseMessageType.COMMON:
                response_data = self._decode_common_response(msg.data)
            elif response_type == ResponseMessageType.SERVO:
                response_data = self._decode_servo_response(msg.data)
            elif response_type == ResponseMessageType.JSTATE:
                response_data = self._decode_joint_state_response(msg.data)
            elif response_type == ResponseMessageType.DEBUG:
                response_data = self._decode_debug_response(msg.data)
            
            return {
                'type': response_type,
                'module_id': module_id,
                'data': response_data
            }
        except Exception as e:
            print(f"Error decoding response: {e}")
            return {
                'type': ResponseMessageType.DEBUG,
                'module_id': msg.arbitration_id & 0xFF,
                'data': {'error': str(e)}
            }

    def _decode_common_response(self, data: bytes) -> Dict:
        """Decode common command response
        
        Args:
            data: Response message data bytes
            
        Returns:
            Dictionary containing decoded common response data
        """
        command_type = data[0]
        command_index = data[1]
        params = data[2:]
        value_raw = int.from_bytes(data[2:], byteorder='little', signed=True)
        value = value_raw
        unit = None

        if command_type == CommandType.CMD_RD:
            if command_index == CommandIndex.SYS_VOLTAGE:
                value = value_raw * UnitScaleFactor.VOLTAGE
                unit = "V"
            elif command_index == CommandIndex.SYS_TEMP:
                value = value_raw * UnitScaleFactor.TEMPERATURE
                unit = "°C"
            elif command_index == CommandIndex.CUR_CURRENT_L:
                value = value_raw * UnitScaleFactor.CURRENT_MODEL10 
                unit = "mA"
            elif command_index == CommandIndex.CUR_SPEED_L:
                value = value_raw * UnitScaleFactor.ACTUAL_SPEED
                unit = "RPM"
            elif command_index == CommandIndex.CUR_POSITION_L:
                value = value_raw * UnitScaleFactor.POSITION
                unit = "deg"
            elif command_index == CommandIndex.TAG_CURRENT_L:
                value = value_raw * UnitScaleFactor.CURRENT_MODEL10
                unit = "mA"
            elif command_index == CommandIndex.TAG_SPEED_L:
                value = value_raw * UnitScaleFactor.TARGET_SPEED
                unit = "RPM"
            elif command_index == CommandIndex.TAG_POSITION_L:
                value = value_raw * UnitScaleFactor.POSITION
                unit = "deg"
        elif command_type == CommandType.CMD_WR:
            print(f"Write response: {data}")

        return {
                'command': command_index,
                'params': params,
                'value': value,
                'unit': unit
                }




        

    def _decode_servo_response(self, data: bytes) -> Dict:
        """Decode servo command response
        
        Args:
            data: Response message data bytes
            
        Returns:
            Dictionary containing decoded servo response data
        """
        return {
            'status': data[0],
            'servo_mode': ServoMode(data[1]) if len(data) > 1 else None,
            'params': data[2:] if len(data) > 2 else None
        }

    def _decode_joint_state_response(self, data: bytes) -> Dict:
        """Decode joint state response"""
        if len(data) != 16:
            return {'error': 'Invalid data length'}
        
        error_code = int.from_bytes(data[0:2], byteorder='little', signed=False)
        voltage_raw = int.from_bytes(data[2:4], byteorder='little', signed=False)
        temp_raw = int.from_bytes(data[4:6], byteorder='little', signed=False)
        position_raw = int.from_bytes(data[8:12], byteorder='little', signed=True)
        current_raw = int.from_bytes(data[12:16], byteorder='little', signed=True)
        
        return {
            'error_code': error_code,
            'system_voltage': voltage_raw * UnitScaleFactor.VOLTAGE,
            'system_temperature': temp_raw * UnitScaleFactor.TEMPERATURE,
            'enable_state': data[6],
            'brake_state': data[7],
            'position': position_raw * UnitScaleFactor.POSITION,
            'current': current_raw * UnitScaleFactor.CURRENT_MODEL10
        }


    def _decode_debug_response(self, data: bytes) -> Dict:
        """Decode debug information response
        
        Args:
            data: Response message data bytes
            
        Returns:
            Dictionary containing decoded debug data
        """
        return {
            'debug_data': list(data)
        }

    def format_response(self, response: Dict) -> str:
        """Format response data as human-readable string
        
        Args:
            response: Decoded response dictionary
            
        Returns:
            Formatted string representation of the response
        """
        output = [
            "\n=== Motor Response ===",
            f"Module ID: 0x{response['module_id']:02X}",
            f"Message Type: {ResponseMessageType(response['type']).name} (0x{response['type']:03X})"
        ]

        data = response['data']
        if response['type'] == ResponseMessageType.COMMON:
            command_name = CommandIndex(data['command']).name if data['command'] is not None else None
            command_index = data['command']
            value = data['value'] if 'value' in data else None
            unit = data['unit'] if 'unit' in data else None
            output.extend([
                f"Command: {command_name} (0x{command_index:02X})" if command_name is not None else "",
                f"Parameters: {[hex(x) for x in data['params']]}" if data['params'] is not None else "",
                f"Value: {value}" if value is not None else "",
                f"Unit: {unit}" if unit is not None else ""
            ])
        elif response['type'] == ResponseMessageType.SERVO:
            output.extend([
                f"Servo Mode: {data['servo_mode'].name}" if data['servo_mode'] is not None else "",
                f"Parameters: {[hex(x) for x in data['params']]}" if data['params'] is not None else ""
            ])
        elif response['type'] == ResponseMessageType.JSTATE:
            output.extend([
                f"Error Code: 0x{data['error_code']:02X}",
                f"Voltage: {data['system_voltage']:.2f} V",
                f"Temperature: {data['system_temperature']:.1f} °C",
                f"Enable State: {data['enable_state']}",
                f"Brake State: {data['brake_state']}",
                f"Position: {data['position']:.4f} deg",
                f"Current: {data['current']:.1f} mA"
            ])

        #output = [line for line in output if line]  # Remove empty lines
        output.append("===================\n")
        return "\n".join(output)

    def monitor_messages(self, callback, timeout: float = 0.1) -> None:
        """Monitor and process incoming messages
        
        Args:
            callback: Function to call with decoded response
            timeout: Reception timeout in seconds
        """
        try:
            msg = self.bus.recv(timeout=timeout)
            if msg:
                response = self.decode_response(msg)
                callback(response)
        except Exception as e:
            print(f"Error in monitor_messages: {e}")
    
    def iap_update(self, module_id: int) -> Optional[Dict]:
        """IAP update"""
        command_id = CommandMessageType.COMMON | module_id
        data = [
            CommandType.CMD_WR,
            CommandIndex.IAP_FLAG,
            0x00]
        return self.send_and_receive(command_id, data)
    
    def get_parameter(self, module_id: int, parameter: str) -> Optional[Dict]:
        size = 0x01
        if parameter in [
            "CUR_CURRENT",
            "CUR_SPEED",
            "CUR_POSITION",
            "TAG_CURRENT",
            "TAG_SPEED",
            "TAG_POSITION",
            "LIT_MIN_POSITION",
            "LIT_MAX_POSITION"
        ]:
            size = 0x02
            parameter = parameter + "_L"
        
        # CommandIndexからparameterを取得
        command_index = getattr(CommandIndex, parameter)
        if command_index is None:
            print(f"Invalid parameter: {parameter}")
            return None
        
        command_id = CommandMessageType.COMMON | module_id
        
        data = [
            CommandType.CMD_RD,
            command_index,
            size
        ]
        
        return self.send_and_receive(command_id, data)

    def set_parameter(self, module_id: int, parameter: str, value: int) -> Optional[Dict]:
        size = 1
        if parameter in [
            "CUR_CURRENT",
            "CUR_SPEED",
            "CUR_POSITION",
            "TAG_CURRENT",
            "TAG_SPEED",
            "TAG_POSITION",
            "LIT_MIN_POSITION",
            "LIT_MAX_POSITION"
        ]:
            parameter = parameter + "_L"
            size = 4
        
        # CommandIndexからparameterを取得
        command_index = getattr(CommandIndex, parameter)
        if command_index is None:
            print(f"Invalid parameter: {parameter}")
            return None
        
        command_id = CommandMessageType.COMMON | module_id

        data = [
            CommandType.CMD_WR,
            command_index,
        ]

        value_bytes = value.to_bytes(size, byteorder='little', signed=True)
        data.extend(value_bytes)
        
        return self.send_and_receive(command_id, data)



    def get_current_state(self, module_id: int) -> Optional[Dict]:
        """Get current state"""
        command_id = CommandMessageType.JSTATE | module_id
        data = []
        return self.send_and_receive(command_id, data)
    
        
