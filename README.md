## realman-motor-toolについて

CANバス上にあるRealman社製モーターに対してCANFD通信でコミュニケーションするツールです。

## インストール方法

以下の手順に従って、ツールをインストールしてください。

1. リポジトリをクローンします。
```bash
git clone https://github.com/FuminoriSugawara/realman-motor-tool.git
```
2. ターミナルでプロジェクトのディレクトリに移動します。
3. 最新のリリースをチェックアウトします。
4. venvで仮想環境を有効化します。
```bash
python3 -m venv venv
source venv/bin/activate
```
5. 依存関係をインストールします。

```bash
pip install -r requirements.txt
```

## CANインターフェイスの起動

1. USB CANFDデバイスを接続します。
2. `sudo chmod +x setup-canfd.sh` を実行します。
3. `sudo ./setup-canfd.sh`を実行します。


## ツールの起動

1. `python3 src/main.py`を実行します。
2. コマンドの実行方法は`help`を入力すると確認できます。


## モーターとのコミュニケーション開始

モーターとのコミュニケーションを開始するために、`online {モーターID}`を入力します。  
例えば、モーターID 1とのコミュニケーションを開始する場合、`online 1`を入力します。  


## モーターの現在状態取得

モーターの現在状態を取得する場合は、`state {モーターID}`を入力します。

## モーターのレジスタ情報の取得

モーターのパラメータを取得する場合は `get {モーターID} {パラメータ名}`を入力します。  
パラメータ名の一覧は `parameters`を入力すると表示されます。  

### モーターのレジスタ情報の取得例

現在位置を取得する場合は `get 1 CUR_POSITION`を入力します。  
位置制御のPゲインを取得する場合は `get 1 SEV_POSITION_P`を入力します。


## モーターへの情報の送信

モーターに情報を送信する場合は、 `set {モーターID} {パラメータ名}　{値}`を入力します。

### モーターへの情報送信例

モーター1をブレーキ状態にする場合は、`set 1 SYS_ENABLE_DRIVER 0`を入力します。  
モーター1のブレーキ状態を解除する場合は、`set 1 SYS_ENABLE_DRIVER 1`を入力します。

## モーターの制御指令値と制御応答レスポンスのCSV保存

制御指令値と制御応答レスポンスをCSV保存する場合は、 `startlog`を入力します。
その後、`stoplog`を入力すると、can_outputディレクトリにCSVファイルが出力されます。


## ツールの終了

ツールを終了する場合`exit`と入力するか、Ctrl+CもしくはCtrl+Dをキーボードで入力します。