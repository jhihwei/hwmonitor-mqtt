#!/bin/bash
# 快速測試 Web 監控服務

set -e

echo "🚀 測試 Web 監控服務"
echo "===================="
echo ""

# 檢查 monitor.html 是否存在
if [ ! -f "monitor.html" ]; then
    echo "❌ 錯誤: monitor.html 不存在"
    exit 1
fi
echo "✅ monitor.html 存在"

# 啟動服務
echo ""
echo "📦 啟動 Web Server..."
docker compose up -d web_monitor

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 3

# 檢查容器狀態
if docker compose ps web_monitor | grep -q "Up"; then
    echo "✅ Web Server 運行中"
else
    echo "❌ Web Server 啟動失敗"
    docker compose logs web_monitor
    exit 1
fi

# 測試 HTTP 連線
echo ""
echo "🌐 測試 HTTP 連線..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200"; then
    echo "✅ HTTP 連線成功 (http://localhost:8080)"
else
    echo "❌ HTTP 連線失敗"
    exit 1
fi

# 檢查 HTML 內容
echo ""
echo "📄 檢查頁面內容..."
if curl -s http://localhost:8080 | grep -q "hwmonitor-mqtt"; then
    echo "✅ 頁面內容正確"
else
    echo "⚠️  警告: 頁面內容可能不完整"
fi

# 顯示服務資訊
echo ""
echo "📊 服務資訊"
echo "=========="
docker compose ps web_monitor

echo ""
echo "🎉 測試完成！"
echo ""
echo "訪問監控介面："
echo "  http://localhost:8080"
echo ""
echo "查看日誌："
echo "  docker compose logs -f web_monitor"
echo ""
echo "停止服務："
echo "  docker compose stop web_monitor"
