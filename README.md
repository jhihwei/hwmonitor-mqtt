# Hardware Monitor via MQTT

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![MQTT](https://img.shields.io/badge/MQTT-Protocol-orange.svg)](https://mqtt.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

輕量級系統監控解決方案，透過 MQTT 協定收集並發送硬體監控資料，提供即時 Web 介面查看系統狀態。

## ✨ 特色

- 🚀 **輕量高效** - Docker 容器化部署，資源佔用極低
- 📊 **即時監控** - 透過 MQTT 即時推送系統狀態
- 🌐 **Web 介面** - 現代化響應式監控介面
- 🔒 **安全設計** - 唯讀檔案系統、最小權限原則
- 🔧 **易於部署** - 一鍵啟動，無需複雜配置
- 📡 **多主機支援** - 支援監控多台主機

## 📸 預覽

監控介面提供以下資訊：

- **CPU** - 使用率、核心數、溫度
- **RAM** - 記憶體使用量和百分比
- **Swap** - 交換空間使用量和百分比
- **磁碟 I/O** - 各磁碟讀寫速度、IOPS
- **網路 I/O** - 各網路介面 RX/TX 流量（MB/s）

## 🚀 快速開始

### 前置需求

- Docker & Docker Compose
- MQTT Broker（支援 WebSocket）

### 一鍵部署

```bash
# 克隆專案
git clone https://github.com/your-username/hwmonitor-mqtt.git
cd hwmonitor-mqtt

# 啟動服務
docker compose up -d

# 訪問監控介面
open http://localhost:8080
```

### 配置說明

編輯 `docker-compose.yml` 設定 MQTT Broker 連線：

```yaml
environment:
  BROKER_HOST: "192.168.5.32"  # MQTT Broker IP
  BROKER_PORT: "1883"           # MQTT Port
  MQTT_USER: "mqtter"           # MQTT 使用者名稱
  MQTT_PASS: "seven777"         # MQTT 密碼
```

編輯 `monitor.html` 設定 WebSocket 連線：

```javascript
const brokerUrl = "ws://192.168.5.32:9001";  // MQTT WebSocket URL
const username = "mqtter";
const password = "seven777";
```

## 📡 架構說明

```
┌─────────────┐     MQTT      ┌──────────────┐
│  sys_agent  │──────────────>│ MQTT Broker  │
│  (Docker)   │   publish     │  (External)  │
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

### 組件說明

#### 1. sys_agent（系統監控代理）

- 使用 Python + psutil 收集系統資訊
- 每秒發送一次監控資料到 MQTT
- Topic: `hwmon/<hostname>`
- 支援溫度、磁碟、網路監控

#### 2. web_monitor（Web 監控介面）

- Nginx Alpine 靜態檔案伺服器
- 透過 MQTT WebSocket 訂閱監控資料
- 響應式設計，支援手機/平板/桌面
- Port: 8080

## 🛠️ 常用指令

```bash
# 查看服務狀態
docker compose ps

# 查看即時日誌
docker compose logs -f

# 只查看 Agent 日誌
docker compose logs -f sys_agent

# 停止服務
docker compose down

# 重建並啟動
docker compose up -d --build

# 重啟特定服務
docker compose restart sys_agent
```

## 📊 監控資料格式

MQTT 訊息格式（JSON）：

```json
{
  "ts": 1697123456.789,
  "hostname": "server-01",
  "cpu": {
    "percent_total": 25.5,
    "percent_per_core": [20.1, 30.5, ...],
    "count_physical": 4,
    "count_logical": 8
  },
  "memory": {
    "ram": {
      "total": 17179869184,
      "used": 8589934592,
      "available": 8589934592,
      "percent": 50.0
    },
    "swap": {
      "total": 4294967296,
      "used": 0,
      "free": 4294967296,
      "percent": 0.0
    }
  },
  "disks": {
    "nvme0n1": {
      "read_bytes_per_s": 1048576,
      "write_bytes_per_s": 2097152,
      "read_iops": 100,
      "write_iops": 200
    }
  },
  "network": {
    "total": {
      "rate": {
        "rx_bytes_per_s": 1048576,
        "tx_bytes_per_s": 524288
      }
    },
    "per_nic": {
      "eth0": {
        "rate": {
          "rx_bytes_per_s": 1048576,
          "tx_bytes_per_s": 524288
        }
      }
    }
  },
  "temperatures": {
    "coretemp": [...],
    "k10temp": [...],
    "nvme": [...]
  }
}
```

## 🔧 進階配置

### 多主機監控

每台主機運行一個 `sys_agent`，發送到同一個 MQTT Broker：

```bash
# 主機 1
docker compose up -d sys_agent

# 主機 2
docker compose up -d sys_agent

# 主機 3
docker compose up -d sys_agent

# Web 介面（任一台主機或獨立伺服器）
docker compose up -d web_monitor
```

Web 介面會自動顯示所有主機的監控資料。

### 自訂 Web Server Port

修改 `docker-compose.yml`：

```yaml
web_monitor:
  ports:
    - "3000:80"  # 使用 3000 port
```

### MQTT 測試

安裝 Mosquitto 客戶端測試連線：

```bash
# 安裝
sudo apt install mosquitto-clients

# 訂閱監控主題
mosquitto_sub -h 192.168.5.32 -p 1883 \
  -u mqtter -P seven777 \
  -t "hwmon/#" -v

# 預期輸出
hwmon/server-01 {"cpu": {...}, "memory": {...}, ...}
```

## 🔒 安全性

### 內建安全措施

- ✅ 容器唯讀檔案系統
- ✅ 禁止權限提升（no-new-privileges）
- ✅ 最小權限原則（非 privileged mode）
- ✅ tmpfs 掛載臨時目錄
- ✅ Alpine Linux 基礎映像

### 生產環境建議

1. **使用 HTTPS** - 透過 Caddy 或 Traefik 反向代理
2. **啟用認證** - 在 Nginx 前加上 Basic Auth
3. **環境變數** - 使用 `.env` 檔案管理敏感資訊
4. **網路隔離** - 限制訪問 IP 範圍
5. **定期更新** - 保持 Docker 映像檔最新

## 🐛 疑難排解

### Agent 無法連線到 MQTT

```bash
# 1. 檢查 Broker 是否運行
telnet 192.168.5.32 1883

# 2. 檢查 Agent 日誌
docker compose logs sys_agent | tail -20

# 3. 驗證環境變數
docker compose config | grep BROKER
```

### Web 介面無法訪問

```bash
# 1. 確認 port 沒被佔用
sudo netstat -tuln | grep 8080

# 2. 確認容器運行
docker compose ps web_monitor

# 3. 測試 HTTP 連線
curl -v http://localhost:8080
```

### 監控介面顯示「連線中」

1. 確認 MQTT Broker 啟用 WebSocket（通常是 port 9001）
2. 開啟瀏覽器 DevTools → Console 查看錯誤訊息
3. 確認 `monitor.html` 中的 WebSocket 連線設定正確
4. 檢查防火牆是否阻擋 WebSocket 連線

## 📈 效能指標

| 組件 | 記憶體使用 | CPU 使用 | 啟動時間 |
|------|-----------|---------|---------|
| sys_agent | ~50MB | <1% | ~2秒 |
| web_monitor | ~10MB | <0.5% | ~1秒 |

## 🛣️ 未來規劃

- [ ] 支援 GPU 監控（NVIDIA、AMD）
- [ ] 歷史資料記錄（InfluxDB 整合）
- [ ] Grafana 儀表板範本
- [ ] 告警系統（閾值觸發）
- [ ] Docker Health Check
- [ ] Kubernetes 部署範例
- [ ] 更多溫度感測器支援

## 📚 相關文件

- [QUICKSTART.md](QUICKSTART.md) - 快速啟動指南
- [WEB_SERVER.md](WEB_SERVER.md) - Web Server 詳細說明
- [CHANGES.md](CHANGES.md) - 更新紀錄

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- [psutil](https://github.com/giampaolo/psutil) - 系統監控函式庫
- [Paho MQTT](https://github.com/eclipse/paho.mqtt.python) - MQTT 客戶端
- [Nginx](https://nginx.org/) - Web 伺服器
- [Tailwind CSS](https://tailwindcss.com/) - UI 框架

## 📞 聯絡

如有問題或建議，歡迎開啟 Issue 討論。

---

⭐ 如果這個專案對你有幫助，請給個 Star！
