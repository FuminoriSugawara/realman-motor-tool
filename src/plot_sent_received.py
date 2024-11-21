import pandas as pd
import matplotlib.pyplot as plt
import sys
import argparse

def plot_motor_data(csv_path):
    # CSVファイルを読み込む
    df = pd.read_csv(csv_path)
    
    # ユニークなモーターIDを取得
    motor_ids = df['motor_id'].unique()
    
    # モーターIDが1つの場合でもリストとして扱えるようにaxesを調整
    fig, axes = plt.subplots(len(motor_ids), 1, figsize=(10, 4*len(motor_ids)), layout='constrained')
    if len(motor_ids) == 1:
        axes = [axes]
    
    fig.suptitle('Commands Sent vs Responses Received by Motor ID')
    
    # 各モーターIDについてプロット
    for idx, motor_id in enumerate(motor_ids):
        motor_data = df[df['motor_id'] == motor_id]
        
        # データをプロット
        axes[idx].scatter(motor_data['second'], motor_data['commands_sent'], 
                         label='Commands Sent', marker='o')
        axes[idx].scatter(motor_data['second'], motor_data['responses_received'], 
                         label='Responses Received', marker='x')
        
        # グラフの設定
        axes[idx].set_xlabel('Time (seconds)')
        axes[idx].set_ylabel('Count')
        axes[idx].set_title(f'Motor ID: {motor_id}')
        axes[idx].grid(True)
        axes[idx].legend()
        
        # y軸の範囲を0-1000に設定
        axes[idx].set_ylim(0, 1000)
    
    # グラフを表示
    plt.show()

def main():
    # コマンドライン引数のパーサーを作成
    parser = argparse.ArgumentParser(description='Plot motor command data from CSV file.')
    parser.add_argument('csv_path', type=str, help='Path to the CSV file containing motor data')
    
    try:
        # 引数をパース
        args = parser.parse_args()
        
        # CSVファイルの存在確認
        with open(args.csv_path, 'r') as f:
            pass
        
        # データをプロット
        plot_motor_data(args.csv_path)
        
    except FileNotFoundError:
        print(f"Error: Could not find CSV file at {args.csv_path}")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty")
        sys.exit(1)
    except pd.errors.ParserError:
        print("Error: Could not parse the CSV file. Please check the file format")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()