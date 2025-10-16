# LCD Monitor Viewer - 480x320 TFT 優化版本

針對 3.5" TFT LCD (480x320) 終端設備優化的硬體監控介面。

## 特色

### 🖥️ LCD 優化設計
- **單欄顯示**：一次只顯示一台設備，自動輪播
- **大字體**：提升小螢幕可讀性
- **高對比**：黑底配色，適合 LCD 顯示
- **簡化資訊**：只顯示關鍵指標

### 📊 顯示內容

```
┌─────────────────────────┐
│     hostname.local      │  ← 設備名稱（反白顯示）
├─────────────────────────┤
│ CPU  45.2% ███████░░░░  62C │  ← CPU 使用率 + 進度條 + 溫度
│ RAM  68.5% ██████████░░ │  ← RAM 使用率 + 進度條
│ NET  ↑ 125K  ↓  1.2M   │  ← 網路上傳/下載速度
│ DSK  R 2.5M  W 850K 52C │  ← 磁碟讀寫速度 + 溫度
│        ● LIVE           │  ← 狀態指示器
└─────────────────────────┘
```

### 🎨 顏色編碼

**使用率（CPU/RAM）**：
- 🟢 < 50%：亮綠色
- 🟢 50-75%：綠色
- 🟡 75-90%：黃色
- 🔴 ≥ 90%：紅色

**溫度**：
- 🔵 < 60°C：青色
- 🟢 60-70°C：綠色
- 🟡 70-80°C：黃色
- 🔴 ≥ 80°C：紅色

**網路 I/O**：
- 🟡 上傳（↑）：黃色
- 🔵 下載（↓）：青色

**磁碟 I/O**：
- 🔵 讀取（R）：青色
- 🟡 寫入（W）：黃色

## 安裝與執行

### 快速啟動

```bash
# 方式 1：使用啟動腳本（推薦）
./run_lcd.sh

# 方式 2：直接執行
uv run python tui_viewer_lcd.py

# 方式 3：在指定終端尺寸下執行
COLUMNS=60 LINES=20 uv run python tui_viewer_lcd.py
```

### 系統需求

- Python 3.10+
- `textual` - TUI 框架
- `paho-mqtt` - MQTT 客戶端
- 已配置的 MQTT broker

### 環境變數配置

在 `.env` 檔案中設定 MQTT 連線資訊：

```env
BROKER_HOST=192.168.5.33
BROKER_PORT=1883
MQTT_USER=mqtter
MQTT_PASS=seven777
```

## LCD 特定優化

### 佈局設計
- **無 Header/Footer**：最大化顯示空間
- **垂直佈局**：適合小螢幕閱讀
- **固定高度**：每個指標佔用固定行數

### 文字優化
- **簡化溫度符號**：`°C` → `C`（節省空間）
- **對齊數字**：使用固定寬度格式化
- **進度條**：15 字元寬的視覺化顯示

### 自動輪播
- **輪播間隔**：8 秒（可調整）
- **單設備模式**：一次只顯示一台設備
- **自動切換**：多設備時自動輪播

### 效能優化
- **降低更新頻率**：適應 LCD 響應速度
- **簡化動畫**：避免閃爍
- **靜默錯誤**：不顯示通知訊息

## 與標準版本的差異

| 特性 | 標準版 (tui_viewer.py) | LCD 版 (tui_viewer_lcd.py) |
|------|----------------------|--------------------------|
| 顯示模式 | 3 欄並排 | 單欄輪播 |
| 同時顯示設備 | 最多 3 台 | 1 台 |
| Header/Footer | 有 | 無 |
| 進度條 | 無 | 有（15 字元） |
| 字體大小 | 標準 | 放大 |
| 輪播間隔 | 5 秒 | 8 秒 |
| 通知訊息 | 顯示 | 靜默 |
| 適用解析度 | ≥1024x768 | 480x320 |

## 終端設備設定建議

### Raspberry Pi 配置

```bash
# /etc/profile.d/lcd_setup.sh
export COLUMNS=60
export LINES=20
export TERM=xterm-256color

# 自動啟動
cd /path/to/hwmonitor-mqtt
./run_lcd.sh
```

### fbterm 配置（framebuffer 終端）

```bash
# 安裝 fbterm
sudo apt install fbterm

# 設定字體大小
fbterm --font-size=16 -- ./run_lcd.sh
```

### tmux 配置

```bash
# 建立 LCD 專用 session
tmux new-session -s lcd -x 60 -y 20 './run_lcd.sh'
```

## 疑難排解

### 顯示不完整
- 檢查終端尺寸：`echo $COLUMNS x $LINES`
- 調整字體大小或終端解析度

### 顏色不正確
- 確認終端支援 256 色：`echo $TERM`
- 設定：`export TERM=xterm-256color`

### 資料不更新
- 檢查 MQTT 連線：查看 MQTT broker 日誌
- 確認 `.env` 配置正確

### 文字重疊
- 減小字體大小
- 調整 `LCD_WIDTH` 和 `LCD_HEIGHT` 常數

## 客製化調整

### 調整輪播速度

編輯 `tui_viewer_lcd.py`：

```python
ROTATION_INTERVAL_SECONDS = 8  # 改為你想要的秒數
```

### 調整進度條寬度

```python
def _get_bar(self, percent: float, width: int) -> str:
    """width 參數控制進度條寬度"""
    # 在 watch_device_data 中調整 width
    cpu_bar = self._get_bar(cpu_percent, 15)  # 改為你想要的寬度
```

### 調整顯示指標

可以在 `watch_device_data()` 中添加或移除指標，例如：

```python
# 添加 SWAP 使用率
swap_percent = data.get("memory", {}).get("swap", {}).get("percent", 0)
self.swap_label.update(f"[bold white]SWP[/bold white] {swap_percent:5.1f}%")
```

## 授權

MIT License

## 相關檔案

- `tui_viewer.py` - 標準版本（多欄顯示）
- `tui_viewer_lcd.py` - LCD 優化版本（本檔案說明）
- `run_lcd.sh` - LCD 版本啟動腳本
- `agent_sender_async.py` - 資料收集端
