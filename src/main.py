from motor_controller import MotorController

def main():
    controller = MotorController()
    try:
        controller.run()
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()