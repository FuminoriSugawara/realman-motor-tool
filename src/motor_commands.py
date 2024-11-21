from enum import IntEnum, Enum
from typing import Dict, Optional
import can
import struct
from dataclasses import dataclass

@dataclass
class CommonResponseMessage:
    message_type: int
    module_id: int
    timestamp: float
    data: bytes
    command: int
    operation_type: int
    value: int
    unit: str


@dataclass
class ServoResponseMessage:
    message_type: int
    module_id: int
    timestamp: float
    current: int
    velocity: int
    position: int
    error: int


@dataclass
class CommonCommandMessage:
    message_type: int
    module_id: int
    timestamp: float
    data: bytes


@dataclass
class ControlCommandMessage:
    message_type: int
    module_id: int
    timestamp: float
    value: int

@dataclass
class DebugMessage:
    message_type: int
    module_id: int
    timestamp: float
    data: bytes

@dataclass
class JointStateResponseMessage:
    message_type: int
    module_id: int
    timestamp: float
    error_code: int
    system_voltage: float
    system_temperature: float
    enable_state: int
    brake_state: int
    position: float
    current: float


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

class CommandOperationType(IntEnum):
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

class MotorModel(IntEnum):
    WHJ10 = 10
    WHJ30 = 30
    WHJ60 = 60


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

# 読み書き可能なパラメータ名のリスト
PARAMETERS = [
    "SYS_ID",
    "SYS_FW_VERSION",
    "SYS_ERROR",
    "SYS_VOLTAGE",
    "SYS_TEMP",
    "SYS_REDU_RATIO",
    "SYS_ENABLE_DRIVER",
    "SYS_ENABLE_ON_POWER",
    "SYS_SAVE_TO_FLASH",
    "SYS_ABSOLUTE_POS_AUTO_CALIB",
    "SYS_SET_ZERO_POS",
    "SYS_CLEAR_ERROR",
    "CUR_CURRENT",
    "CUR_SPEED",
    "CUR_POSITION",
    "MOT_MODEL_ID0",
    "MOT_MODEL_ID1",
    "MOT_MODEL_ID2",
    "MOT_MODEL_ID3",
    "MOT_MODEL_ID4",
    "MOT_MODEL_ID5",
    "TAG_WORK_MODE",
    "TAG_CURRENT",
    "TAG_SPEED",
    "TAG_POSITION",
    "SPEED_FEED_FORWARD_SWITCH",
    "LIT_MAX_CURRENT",
    "LIT_MAX_SPEED",
    "LIT_MAX_ACC",
    "LIT_MAX_DEC",
    "LIT_MIN_POSITION",
    "LIT_MAX_POSITION",
    "IAP_FLAG",
    "SEV_CURRENT_P",
    "SEV_CURRENT_I",
    "SEV_CURRENT_D",
    "SEV_SPEED_P",
    "SEV_SPEED_I",
    "SEV_SPEED_D",
    "SEV_SPEED_DS",
    "SEV_POSITION_P",
    "SEV_POSITION_I",
    "SEV_POSITION_D",
    "SEV_POSITION_DS",
    "ERROR"
]


# 4バイトのパラメータ名のリスト
FOUR_BYTE_PARAMETERS = [
    "CUR_CURRENT",
    "CUR_SPEED",
    "CUR_POSITION",
    "TAG_CURRENT",
    "TAG_SPEED",
    "TAG_POSITION",
    "LIT_MIN_POSITION",
    "LIT_MAX_POSITION"
]

PARAMTETER_DESCRIPTIONS = {
    "SYS_ID": "System ID",
    "SYS_FW_VERSION": "Firmware version",
    "SYS_ERROR": "Error code",
    "SYS_VOLTAGE": "System voltage (V)",
    "SYS_TEMP": "System temperature (°C)",
    "SYS_REDU_RATIO": "Reduction ratio",
    "SYS_ENABLE_DRIVER": "Enable driver",
    "SYS_ENABLE_ON_POWER": "Enable on power",
    "SYS_SAVE_TO_FLASH": "Save to flash",
    "SYS_ABSOLUTE_POS_AUTO_CALIB": "Absolute position auto calibration",
    "SYS_SET_ZERO_POS": "Set zero position",
    "SYS_CLEAR_ERROR": "Clear error",
    "CUR_CURRENT": "Current (mA)",
    "CUR_SPEED": "Speed (RPM)",
    "CUR_POSITION": "Position (deg)",
    "MOT_MODEL_ID0": "Motor model ID 0",
    "MOT_MODEL_ID1": "Motor model ID 1",
    "MOT_MODEL_ID2": "Motor model ID 2",
    "MOT_MODEL_ID3": "Motor model ID 3",
    "MOT_MODEL_ID4": "Motor model ID 4",
    "MOT_MODEL_ID5": "Motor model ID 5",
    "TAG_WORK_MODE": "Target work mode",
    "TAG_CURRENT": "Target current (mA)",
    "TAG_SPEED": "Target speed (RPM)",
    "TAG_POSITION": "Target position (deg)",
    "SPEED_FEED_FORWARD_SWITCH": "Speed feed forward switch",
    "LIT_MAX_CURRENT": "Limit max current (mA)",
    "LIT_MAX_SPEED": "Limit max speed (RPM)",
    "LIT_MAX_ACC": "Limit max acceleration (RPM/s)",
    "LIT_MAX_DEC": "Limit max deceleration (RPM/s)",
    "LIT_MIN_POSITION": "Limit min position (deg)",
    "LIT_MAX_POSITION": "Limit max position (deg)",
    "IAP_FLAG": "IAP flag",
    "SEV_CURRENT_P": "Servo current P",
    "SEV_CURRENT_I": "Servo current I",
    "SEV_CURRENT_D": "Servo current D",
    "SEV_SPEED_P": "Servo speed P",
    "SEV_SPEED_I": "Servo speed I",
    "SEV_SPEED_D": "Servo speed D",
    "SEV_SPEED_DS": "Servo speed DS",
    "SEV_POSITION_P": "Servo position P",
    "SEV_POSITION_I": "Servo position I",
    "SEV_POSITION_D": "Servo position D",
    "SEV_POSITION_DS": "Servo position DS",
    "ERROR": "Error"
}



class MotorCommands:
    bus: can.BusABC
    motor_model_map: Dict[int, MotorModel]

    # can.BusABC をコンストラクタで受け取る
    # 対象となるモーターのIDとそのモデルのマップを保持する(オプション)
    def __init__(self, bus: can.BusABC, motor_model_map: Dict[int, MotorModel] = {}):
        self.bus = bus
        self.motor_model_map = motor_model_map

    @staticmethod
    def parse_int32(data: bytes) -> int:
        return struct.unpack('<i', data)[0]
    
    @staticmethod
    def parse_uint16(data: bytes) -> int:
        return struct.unpack('<H', data)[0]
    
    


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


    
    def decode_response(self, msg: can.Message) -> Dict | CommonCommandMessage | ControlCommandMessage | DebugMessage | JointStateResponseMessage | ServoResponseMessage | CommonResponseMessage:
        """Decode response message
        
        Args:
            msg: CAN message to decode
            
        Returns:
            Dictionary containing decoded message data
        """
        try:
            message_type = msg.arbitration_id & 0x0F00
            module_id = msg.arbitration_id & 0xFF

            if message_type == ResponseMessageType.COMMON:
                return self._decode_common_response(msg)
            elif message_type == ResponseMessageType.SERVO:
                return self._decode_servo_response(msg)
            elif message_type == ResponseMessageType.JSTATE:
                return self._decode_joint_state_response(msg)
            elif message_type == ResponseMessageType.DEBUG:
                return self._decode_debug_response(msg)
            elif message_type == CommandMessageType.COMMON:
                return self._decode_common_command(msg)
            elif message_type == CommandMessageType.SERVO_POS:
                return self._decode_control_command(msg)
            elif message_type == CommandMessageType.SERVO_VEL:
                return self._decode_control_command(msg)
            elif message_type == CommandMessageType.SERVO_CUR:
                return self._decode_control_command(msg)
            else:
                print(f"Unknown response type: {message_type:02X}")
                return {
                    'type': ResponseMessageType.DEBUG,
                    'module_id': module_id,
                    'data': {'error': 'Unknown response type'}
                }
        except Exception as e:
            print(f"Error decoding response: {e}")
            return {
                'type': ResponseMessageType.DEBUG,
                'module_id': msg.arbitration_id & 0xFF,
                'data': {'error': str(e)}
            }
    
    
    def _get_current_unit_scale_factor(self, module_id: int) -> float:
        """Get the current unit scale factor for the specified module"""
        if module_id in self.motor_model_map:
            model_id = self.motor_model_map[module_id]
            if model_id == MotorModel.WHJ10:
                return UnitScaleFactor.CURRENT_MODEL10.value
            elif model_id == MotorModel.WHJ30:
                return UnitScaleFactor.CURRENT_MODEL30.value
            elif model_id == MotorModel.WHJ60:
                return UnitScaleFactor.CURRENT_MODEL60.value
        return UnitScaleFactor.CURRENT_MODEL10.value



    def _decode_common_response(self, message: can.Message) -> CommonResponseMessage:
        """Decode common command response
        
        Args:
            data: Response message data bytes
            
        Returns:
            Dictionary containing decoded common response data
        """
        message_type = message.arbitration_id & 0xFF00
        module_id = message.arbitration_id & 0xFF
        data = message.data
        timestamp = message.timestamp

        operation_type = data[0]
        command_index = data[1]
        value_raw = int.from_bytes(data[2:], byteorder='little', signed=True)
        value = value_raw
        unit = None

        if operation_type == CommandOperationType.CMD_RD:
            if command_index == CommandIndex.SYS_VOLTAGE:
                value = value_raw * UnitScaleFactor.VOLTAGE
                unit = "V"
            elif command_index == CommandIndex.SYS_TEMP:
                value = value_raw * UnitScaleFactor.TEMPERATURE
                unit = "°C"
            elif command_index == CommandIndex.CUR_CURRENT_L:
                value = value_raw * self._get_current_unit_scale_factor(module_id) 
                unit = "mA"
            elif command_index == CommandIndex.CUR_SPEED_L:
                value = value_raw * UnitScaleFactor.ACTUAL_SPEED
                unit = "RPM"
            elif command_index == CommandIndex.CUR_POSITION_L:
                value = value_raw * UnitScaleFactor.POSITION
                unit = "deg"
            elif command_index == CommandIndex.TAG_CURRENT_L:
                value = value_raw * self._get_current_unit_scale_factor(module_id)
                unit = "mA"
            elif command_index == CommandIndex.TAG_SPEED_L:
                value = value_raw * UnitScaleFactor.TARGET_SPEED
                unit = "RPM"
            elif command_index == CommandIndex.TAG_POSITION_L:
                value = value_raw * UnitScaleFactor.POSITION
                unit = "deg"
        
        return CommonResponseMessage(
            message_type=message_type,
            module_id=module_id,
            timestamp=timestamp,
            data=data,
            command=command_index,
            operation_type=operation_type,
            value=value,
            unit=unit
        )

        

    def _decode_servo_response(self, message: can.Message) -> ServoResponseMessage:
        """Decode servo command response
        
        Args:
            data: Response message data bytes
            
        Returns:
            Dictionary containing decoded servo response data
        """
        message_type = message.arbitration_id & 0xFF00
        module_id = message.arbitration_id & 0xFF
        timestamp = message.timestamp
        data = message.data
        current = self.parse_int32(data[0:4])
        velocity = self.parse_int32(data[4:8])
        position = self.parse_int32(data[8:12])
        error = self.parse_uint16(data[14:16])

        return ServoResponseMessage(
            message_type=message_type,
            module_id=module_id,
            timestamp=timestamp,
            current=current * self._get_current_unit_scale_factor(module_id),
            velocity=velocity * UnitScaleFactor.ACTUAL_SPEED,
            position=position * UnitScaleFactor.POSITION,
            error=error
        )
        



    def _decode_joint_state_response(self, message: can.Message) -> JointStateResponseMessage:
        """Decode joint state response"""
        if len(message.data) != 16:
            return {'error': 'Invalid data length'}
        
        message_type = message.arbitration_id & 0xFF00
        module_id = message.arbitration_id & 0xFF
        timestamp = message.timestamp
        data = message.data
        error_code = int.from_bytes(data[0:2], byteorder='little', signed=False)
        voltage_raw = int.from_bytes(data[2:4], byteorder='little', signed=False)
        temp_raw = int.from_bytes(data[4:6], byteorder='little', signed=False)
        enable_state = data[6]
        brake_state = data[7]
        position_raw = int.from_bytes(data[8:12], byteorder='little', signed=True)
        current_raw = int.from_bytes(data[12:16], byteorder='little', signed=True)


        return JointStateResponseMessage(
            message_type=message_type,
            module_id=module_id,
            timestamp=timestamp,
            error_code=error_code,
            system_voltage=voltage_raw * UnitScaleFactor.VOLTAGE,
            system_temperature=temp_raw * UnitScaleFactor.TEMPERATURE,
            enable_state=enable_state,
            brake_state=brake_state,
            position=position_raw * UnitScaleFactor.POSITION,
            current=current_raw * self._get_current_unit_scale_factor(module_id)
        )
        



    def _decode_debug_response(self, message: can.Message) -> Dict:
        """Decode debug information response
        
        Args:
            data: Response message data bytes
            
        Returns:
            Dictionary containing decoded debug data
        """
        message_type = message.arbitration_id & 0xFF00
        module_id = message.arbitration_id & 0xFF
        data = message.data
        timestamp = message.timestamp

        return DebugMessage(
            message_type= message_type,
            module_id= module_id,
            timestamp= timestamp,
            data= data)

    
    def _decode_common_command(self, message: can.Message) -> CommonCommandMessage:
        """Decode common command message"""
        message_type = message.arbitration_id & 0x0F00
        module_id = message.arbitration_id & 0x00FF
        timestamp = message.timestamp
        data = message.data

        return CommonCommandMessage(
            message_type= message_type,
            module_id= module_id,
            timestamp= timestamp,
            data= data)
        
    
    def _decode_control_command(self, message: can.Message) -> ControlCommandMessage:
        """Decode servo position message"""
        message_type = message.arbitration_id & 0x0F00
        module_id = message.arbitration_id & 0x00FF
        timestamp = message.timestamp
        value = self.parse_int32(message.data)

        return ControlCommandMessage(
            message_type= message_type,
            module_id= module_id,
            timestamp= timestamp,
            value= value)




    def format_response(self, response: CommonCommandMessage | ControlCommandMessage | DebugMessage | JointStateResponseMessage | ServoResponseMessage | CommonResponseMessage) -> str:
        """Format response data as human-readable string
        
        Args:
            response: Decoded response dictionary
            
        Returns:
            Formatted string representation of the response
        """

        module_id = response.module_id
        timestamp = response.timestamp

        output = [
            "\n=== Motor Response ===",
            f"Module ID: 0x{module_id:02X}",
            f"Timestampe: {timestamp}",
        ]
        message_type = response.message_type
        #data = response['data']
        data = {}
        if isinstance(response, CommonResponseMessage):
            command = response.command
            command_name = CommandIndex(command).name if command is not None else None
            message_type = response.message_type
            value = response.value
            unit = response.unit
            output.extend([
                f"Message Type: {ResponseMessageType(message_type).name} (0x{message_type:03X})",
                f"Command: {command_name} (0x{command:02X})" if command_name is not None else "",
                f"Value: {value}" if value is not None else "",
                f"Unit: {unit}" if unit is not None else ""
            ])
        elif isinstance(response, ServoResponseMessage):
            message_type = response.message_type
            current = response.current
            velocity = response.velocity
            position = response.position
            error = response.error

            output.extend([
                f"Message Type: {ResponseMessageType(message_type).name} (0x{message_type:03X})",
                f"Current: {current} mA",
                f"Velocity: {velocity} RPM",
                f"Position: {position} deg",
                f"Error: {error}"
            ])
        elif isinstance(response, JointStateResponseMessage):
            message_type = response.message_type
            error_code = response.error_code
            system_voltage = response.system_voltage
            system_temperature = response.system_temperature
            enable_state = response.enable_state
            brake_state = response.brake_state
            position = response.position
            current = response.current

            output.extend([
                f"Message Type: {ResponseMessageType(message_type).name} (0x{message_type:03X})",
                f"Error Code: 0x{error_code:02X}",
                f"System Voltage: {system_voltage:.2f} V",
                f"System Temperature: {system_temperature:.1f} °C",
                f"Enable State: {enable_state}",
                f"Brake State: {brake_state}",
                f"Position: {position:.4f} deg",
                f"Current: {current:.1f} mA"
            ])
        elif isinstance(response, DebugMessage):
            message_type = response.message_type
            data = response.data

            output.extend([
                f"Message Type: {ResponseMessageType(message_type).name} (0x{message_type:03X})",
                f"Data: {data}"
            ])
        elif isinstance(response, ControlCommandMessage):
            message_type = response.message_type
            value = response.value
            
            output.extend([
                f"Message Type: {ResponseMessageType(message_type).name} (0x{message_type:03X})",
                f"Value: {value}"
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
            CommandOperationType.CMD_WR,
            CommandIndex.IAP_FLAG,
            0x00]
        self.send_message(command_id, data)


    
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
            CommandOperationType.CMD_RD,
            command_index,
            size
        ]

        self.send_message(command_id, data)



    def set_parameter(self, module_id: int, parameter: str, value: int) -> Optional[Dict]:
        if value < 256:
            size = 1
        else:
            size = 2
        if parameter in FOUR_BYTE_PARAMETERS:
            parameter = parameter + "_L"
            size = 4
        
        # CommandIndexからparameterを取得
        command_index = getattr(CommandIndex, parameter)
        if command_index is None:
            print(f"Invalid parameter: {parameter}")
            return None
        
        command_id = CommandMessageType.COMMON | module_id

        data = [
            CommandOperationType.CMD_WR,
            command_index,
        ]

        value_bytes = value.to_bytes(size, byteorder='little', signed=True)
        data.extend(value_bytes)
        
        self.send_message(command_id, data)



    def get_current_state(self, module_id: int) -> Optional[Dict]:
        """Get current state"""
        command_id = CommandMessageType.JSTATE | module_id
        data = []
        self.send_message(command_id, data)
    

    def get_available_parameters(self) -> list[str]:
        # return parameter names and descriptions
        parameters_list = []
        for param in PARAMETERS:
            description = PARAMTETER_DESCRIPTIONS[param]
            parameters_list.append(f"{param}: {description}")

        return parameters_list


        
