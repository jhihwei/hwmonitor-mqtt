# 專案更新紀錄

## 2025-10-12 - Web 監控介面與 UI 改進

### 新增功能

#### 1. Web Server 服務
- ✅ 新增 `web_monitor` 服務至 `docker-compose.yml`
- ✅ 使用 Nginx Alpine 映像檔（輕量級 ~8MB）
- ✅ Port 8080 提供 Web 介面存取
- ✅ 唯讀檔案系統與安全設定
- ✅ 自動重啟機制

**訪問方式**:
```bash
http://localhost:8080
```

#### 2. RAM 與 Swap 分離顯示
- ✅ 將原本的記憶體顯示分為 RAM 和 Swap 兩個獨立區塊
- ✅ 三欄式佈局：CPU | RAM | Swap
- ✅ 每個區塊顯示：
  - 使用率百分比
  - 視覺化進度條
  - 詳細容量資訊（已用 / 總量 GB）

**視覺設計**:
- CPU: 藍紫色 (indigo)
- RAM: 綠色 (emerald)
- Swap: 琥珀色 (amber)

#### 3. 網路介面顯示優化
- ✅ 移除 pps (packets per second) 顯示
- ✅ 只保留 MB/s 單位
- ✅ 預設折疊詳細介面列表
- ✅ 總合顯示：總 RX 和 TX (MB/s)
- ✅ 展開/收合按鈕切換詳細資訊

**顯示內容**:
```
總合： RX XX.XXX MB/s  TX XX.XXX MB/s
[展開詳細]

展開後顯示各網路介面：
- eth0: RX / TX
- wlan0: RX / TX
- ...
```

### 檔案修改

#### docker-compose.yml
```yaml
# 新增 web_monitor 服務
services:
  web_monitor:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./monitor.html:/usr/share/nginx/html/index.html:ro
```

#### monitor.html (前端介面)
**RAM/Swap 分離**:
- 更新佈局為三欄 (CPU/RAM/Swap)
- 新增獨立的 UI 元素和資料處理
- 分別計算和顯示 RAM 與 Swap 百分比

**網路介面優化**:
- 移除 pps 欄位和資料處理
- 新增折疊/展開功能
- 總合顯示更突出

### 新增文件

1. **WEB_SERVER.md** - Web Server 詳細說明
   - 服務架構
   - 使用方式
   - 配置說明
   - 安全建議
   - 疑難排解

2. **QUICKSTART.md** - 快速啟動指南
   - 一鍵啟動
   - 常用指令
   - MQTT 連線確認
   - 自訂設定
   - 進階功能

3. **test-web.sh** - Web 服務測試腳本
   - 自動化測試流程
   - 服務狀態檢查
   - HTTP 連線測試

### 使用方式

#### 快速啟動
```bash
# 啟動所有服務（Agent + Web）
docker compose up -d

# 只啟動 Web Server
docker compose up -d web_monitor

# 測試 Web 服務
./test-web.sh
```

#### 訪問監控介面
```bash
# 本機訪問
http://localhost:8080

# 遠端訪問
http://<主機IP>:8080
```

### 技術細節

#### 前端資料結構
```javascript
// monitor.html 現在分別處理
data.memory.ram = {
  total: Number,
  used: Number,
  available: Number,
  percent: Number
}

data.memory.swap = {
  total: Number,
  used: Number,
  free: Number,
  percent: Number
}

data.network.total.rate = {
  rx_bytes_per_s: Number,
  tx_bytes_per_s: Number
}
```

#### 後端資料（無需修改）
Python agent 已經提供正確的資料結構：
```python
# agent_sender_async.py
def get_mem_block():
    return {
        "ram": {...},
        "swap": {...}
    }

def get_network_block():
    return {
        "total": {"rate": {...}},
        "per_nic": {...}
    }
```

### 效能影響

- Web Server 記憶體使用: ~10MB
- Web Server CPU 使用: 接近 0%
- 前端顯示效能: 無明顯影響
- 網路流量: 減少（移除 pps 資料）

### 相容性

- ✅ 向下相容現有 agent 資料格式
- ✅ 響應式設計（手機/平板/桌面）
- ✅ 現代瀏覽器支援
- ✅ 無需修改後端 Python 程式碼

### 安全性

#### Web Server
- 唯讀檔案系統
- 禁止權限提升
- tmpfs 掛載臨時檔案
- Alpine 基礎映像（更小的攻擊面）

#### 建議改進（生產環境）
- 使用 HTTPS
- 啟用 HTTP Basic Auth
- 限制訪問 IP
- 使用反向代理（如 Caddy）

### 測試檢查清單

- [x] docker-compose.yml 語法正確
- [x] Web Server 容器可啟動
- [x] Port 8080 可訪問
- [x] monitor.html 正確載入
- [x] RAM/Swap 分離顯示正確
- [x] 網路總合顯示正確
- [x] 展開/收合功能運作
- [x] 響應式佈局正常
- [x] 文件齊全

### 下一步建議

1. **HTTPS 支援** - 使用 Caddy 或 Traefik
2. **環境變數** - 使用 `.env` 檔案
3. **Health Check** - 添加 Docker health check
4. **多主機監控** - 測試多台主機同時監控
5. **歷史資料** - 整合 InfluxDB + Grafana
6. **告警系統** - 設定閾值告警

### 問題與解決

#### 問題 1: 找不到 mqtt.html
**解決**: 專案實際使用 `monitor.html`，已更新所有引用

#### 問題 2: docker-compose 語法警告
**解決**: 保留 `version: "3.9"` 以保持相容性（警告可忽略）

### 版本資訊

- Docker Compose: 3.9
- Nginx: alpine (latest)
- Python Agent: 無變更
- 前端框架: Tailwind CSS (CDN)
- MQTT Library: Paho MQTT (WebSocket)

