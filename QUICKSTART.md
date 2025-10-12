# 快速啟動指南

## 一鍵啟動

```bash
cd /home/orson/Downloads/hwmonitor-mqtt
docker compose up -d
```

## 訪問監控介面

開啟瀏覽器訪問：
```
http://localhost:8080
```

## 服務說明

### 1. sys_agent (系統監控)
- 收集 CPU、RAM、Swap、磁碟、網路資料
- 發送到 MQTT Broker (`192.168.5.32:1883`)
- Topic: `hwmon/<hostname>`

### 2. web_monitor (Web 介面)
- Nginx 靜態檔案伺服器
- 提供 `monitor.html` 監控介面
- Port: `8080`

## 監控資料流程

```
┌─────────────┐     MQTT      ┌──────────────┐
│  sys_agent  │──────────────>│ MQTT Broker  │
│  (Docker)   │   publish     │ 192.168.5.32 │
└─────────────┘               └──────┬───────┘
                                     │
                                     │ WebSocket
                                     │ subscribe
                                     ↓
┌─────────────┐    HTTP       ┌─────────────┐
│   Browser   │<──────────────│web_monitor  │
│             │   monitor.html│  (Nginx)    │
└─────────────┘               └─────────────┘
```

## 常用指令

```bash
# 查看服務狀態
docker compose ps

# 查看日誌
docker compose logs -f

# 只看 agent 日誌
docker compose logs -f sys_agent

# 只看 web 日誌
docker compose logs -f web_monitor

# 停止服務
docker compose down

# 重建並啟動
docker compose up -d --build

# 只重啟 agent
docker compose restart sys_agent
```

## MQTT 連線確認

### 確認 Broker 可連線

```bash
# 安裝 mosquitto 客戶端
sudo apt install mosquitto-clients

# 訂閱監控主題
mosquitto_sub -h 192.168.5.32 -p 1883 -u mqtter -P seven777 -t "hwmon/#" -v
```

### 預期輸出

```
hwmon/your-hostname {"cpu": {...}, "memory": {...}, ...}
```

## 疑難排解

### Agent 無法連線到 MQTT

```bash
# 檢查 Broker 是否運行
telnet 192.168.5.32 1883

# 檢查 Agent 日誌
docker compose logs sys_agent | tail -20
```

### Web 介面無法訪問

```bash
# 確認 port 8080 沒被佔用
sudo netstat -tuln | grep 8080

# 確認容器運行
docker compose ps web_monitor

# 確認 monitor.html 存在
ls -lh monitor.html
```

### 監控介面顯示「連線中」

1. 確認 MQTT Broker 啟用 WebSocket (port 9001)
2. 開啟瀏覽器 DevTools → Console 查看錯誤
3. 確認 `monitor.html` 中的連線設定正確

## 自訂設定

### 修改 MQTT Broker 位址

編輯 `docker-compose.yml`:

```yaml
environment:
  BROKER_HOST: "your-broker-ip"
  BROKER_PORT: "1883"
  MQTT_USER: "your-user"
  MQTT_PASS: "your-password"
```

### 修改 Web Server Port

編輯 `docker-compose.yml`:

```yaml
ports:
  - "3000:80"  # 改用 3000 port
```

### 修改 WebSocket 連線

編輯 `monitor.html`，找到：

```javascript
const brokerUrl = "ws://192.168.5.32:9001";
const username = "mqtter";
const password = "seven777";
```

## 生產環境建議

1. **環境變數** - 使用 `.env` 檔案儲存敏感資訊
2. **HTTPS** - 使用反向代理 (如 Caddy) 提供 HTTPS
3. **認證** - 在 Nginx 前面加上 Basic Auth
4. **監控** - 設定 Docker health check

## 進階功能

### 多台主機監控

每台主機運行一個 `sys_agent`，都發送到同一個 MQTT Broker，Web 介面會自動顯示所有主機。

### 資料保留

MQTT 訊息預設不保留歷史，若需要歷史資料：

1. 使用 InfluxDB 訂閱 MQTT 主題
2. Grafana 視覺化歷史資料
3. 設定告警規則

## 更多資訊

- [WEB_SERVER.md](WEB_SERVER.md) - Web Server 詳細說明
- [README.md](README.md) - 專案完整文件
