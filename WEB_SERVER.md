# Web Monitor Server

## 服務說明

新增了一個輕量級的 Nginx Web Server 來提供 `monitor.html` 監控介面。

## 架構

```
docker-compose.yml
├── sys_agent       (系統監控 Agent - 發送資料到 MQTT)
└── web_monitor     (Nginx Web Server - 提供監控介面)
```

## 使用方式

### 啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 只啟動 Web Server
docker-compose up -d web_monitor

# 查看服務狀態
docker-compose ps
```

### 訪問監控介面

瀏覽器開啟：
```
http://localhost:8080
```

或從其他電腦訪問：
```
http://<主機IP>:8080
```

### 停止服務

```bash
# 停止所有服務
docker-compose down

# 只停止 Web Server
docker-compose stop web_monitor
```

## 服務配置

### web_monitor 容器

- **映像檔**: `nginx:alpine` (輕量級 ~8MB)
- **Port 映射**: `8080:80` (主機 8080 → 容器 80)
- **掛載檔案**: `./monitor.html` → `/usr/share/nginx/html/index.html`
- **安全設定**:
  - `read_only: true` - 唯讀檔案系統
  - `no-new-privileges` - 禁止權限提升
  - tmpfs 掛載 - 臨時檔案使用記憶體

### 自訂 Port

如果 8080 被佔用，可修改 `docker-compose.yml`:

```yaml
ports:
  - "3000:80"  # 改用 3000 port
```

## 監控介面功能

`monitor.html` 提供即時監控：

1. **CPU 使用率** - 總體 + 核心數 + 溫度
2. **RAM 使用率** - 記憶體使用量和百分比
3. **Swap 使用率** - 交換空間使用量和百分比
4. **磁碟 I/O** - 各磁碟讀寫速度
5. **網路 I/O** - 各網路介面 RX/TX (MB/s)
   - 預設折疊，只顯示總合
   - 點擊「展開詳細」查看各介面

### MQTT 連線設定

監控介面透過 MQTT over WebSocket 連線，預設連線到：

```javascript
// 在 monitor.html 中可以修改
const brokerUrl = "ws://192.168.5.32:9001";  // WebSocket port
const username = "mqtter";
const password = "seven777";
```

**注意**: 確保 MQTT Broker 啟用 WebSocket 支援 (通常是 9001 port)

## 疑難排解

### 網頁無法訪問

1. 檢查容器是否運行：
   ```bash
   docker-compose ps
   ```

2. 檢查 port 是否被佔用：
   ```bash
   netstat -tuln | grep 8080
   ```

3. 查看容器日誌：
   ```bash
   docker-compose logs web_monitor
   ```

### MQTT 連線失敗

1. 確認 MQTT Broker 啟用 WebSocket (port 9001)
2. 檢查 `monitor.html` 中的連線設定
3. 查看瀏覽器 Console 錯誤訊息

### 修改 monitor.html 後沒有更新

容器掛載的是檔案，直接修改 `monitor.html` 後重新整理瀏覽器即可，無需重啟容器。

## 安全建議

### 生產環境

1. **使用 Nginx 配置檔**（非直接掛載 HTML）
2. **啟用 HTTPS**
3. **設定 HTTP Basic Auth**
4. **限制訪問 IP**

範例：建立 `nginx.conf`:

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    
    # Basic Auth
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    # IP 限制
    allow 192.168.0.0/16;
    deny all;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
```

修改 `docker-compose.yml`:

```yaml
volumes:
  - ./monitor.html:/usr/share/nginx/html/index.html:ro
  - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
  - ./htpasswd:/etc/nginx/.htpasswd:ro
```

## 效能說明

- **記憶體使用**: ~10MB (Nginx Alpine)
- **CPU 使用**: 幾乎為 0 (靜態檔案)
- **啟動時間**: ~1 秒
- **並發連線**: 可處理數千個同時連線

