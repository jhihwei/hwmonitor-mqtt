#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HW Monitor MQTT TUI Viewer
- Powered by Textual
- Displays data from agent_sender_async.py
- Rotates devices every 5 seconds if more than 3 are present.
"""
import json
import os
import time
from collections import deque
from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal
from textual.widgets import Header, Footer, Static, Label
from textual.reactive import reactive
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

# --- MQTT Configuration ---
BROKER_HOST = os.getenv("BROKER_HOST", "192.168.5.33")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "mqtter")
MQTT_PASS = os.getenv("MQTT_PASS", "seven777")
TOPIC = "sys/agents/+/metrics"

# --- Display Configuration ---
MAX_DEVICES_PER_PAGE = 3
ROTATION_INTERVAL_SECONDS = 5

def format_bytes(byte_count):
    if byte_count is None or byte_count == 0:
        return "0B"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count >= power and n < len(power_labels) - 1:
        byte_count /= power
        n += 1
    return f"{byte_count:.1f}{power_labels[n]}"

class DeviceDisplay(Static):
    """A widget to display data for a single device."""
    
    device_data = reactive(None, layout=True)

    def __init__(self, host_id: str) -> None:
        super().__init__()
        self.host_id = host_id
        self.last_update = time.time()
        self.title_label = Label(f"[bold white on blue] {self.host_id} [/bold white on blue]", classes="title")
        self.stale_label = Label("", classes="stale")
        self.sys_label = Label("...", classes="data")
        self.io_label = Label("...", classes="data")

    def compose(self) -> ComposeResult:
        with Horizontal(id="title_bar"):
            yield self.title_label
            yield self.stale_label
        yield self.sys_label
        yield self.io_label

    def watch_device_data(self, data: dict) -> None:
        if not data:
            return

        self.last_update = time.time()
        
        # --- System: CPU / RAM ---
        cpu_percent = data.get("cpu", {}).get("percent_total", 0)
        cpu_temp = "N/A"
        if temps := data.get("temperatures"):
            for source, entries in temps.items():
                if "cpu" in source or "k10temp" in source or "coretemp" in source:
                    if entries:
                        temp_val = entries[0].get('current')
                        if isinstance(temp_val, (int, float)):
                            cpu_temp = f"{temp_val:.0f}°C"
                            break
        ram_percent = data.get("memory", {}).get("ram", {}).get("percent", 0)

        # Color-coded based on usage levels
        cpu_color = self._get_usage_color(cpu_percent)
        ram_color = self._get_usage_color(ram_percent)
        temp_color = self._get_temp_color(cpu_temp)

        self.sys_label.update(
            f"[bold cyan]CPU:[/bold cyan][{cpu_color}]{cpu_percent:5.1f}%[/{cpu_color}] "
            f"[{temp_color}]({cpu_temp:>4})[/{temp_color}]  "
            f"[bold cyan]RAM:[/bold cyan][{ram_color}]{ram_percent:5.1f}%[/{ram_color}]"
        )

        # --- IO: Network / Disk ---
        net_total = data.get("network_io", {}).get("total", {}).get("rate", {})
        net_up = net_total.get("tx_bytes_per_s", 0)
        net_down = net_total.get("rx_bytes_per_s", 0)
        
        disk_io = data.get("disk_io", {})
        total_read = sum(d.get("rate", {}).get("read_bytes_per_s", 0) for d in disk_io.values())
        total_write = sum(d.get("rate", {}).get("write_bytes_per_s", 0) for d in disk_io.values())
        
        max_disk_temp = "N/A"
        hottest_disk = ""
        if temps:
            disk_temps = []
            for source, entries in temps.items():
                if any(s in source for s in ["sd", "nvme", "mmcblk", "hd"]):
                    for entry in entries:
                        if isinstance(entry.get('current'), (int, float)):
                            disk_temps.append((entry['current'], source))
            if disk_temps:
                max_temp, disk_name = max(disk_temps, key=lambda x: x[0])
                max_disk_temp = f"{max_temp:.0f}°C"
                hottest_disk = disk_name.split('_')[0] if '_' in disk_name else disk_name

        # Enhanced visual formatting with better spacing and colors
        disk_temp_color = self._get_temp_color(max_disk_temp)

        net_str = (
            f"[bold green]NET:[/bold green]"
            f"⬆[yellow]{format_bytes(net_up):>8}[/yellow]  "
            f"⬇[blue]{format_bytes(net_down):>8}[/blue]"
        )
        disk_label = f"[{hottest_disk}]" if hottest_disk else ""
        dsk_str = (
            f"[bold magenta]DSK:[/bold magenta]"
            f"R[cyan]{format_bytes(total_read):>8}[/cyan]  "
            f"W[yellow]{format_bytes(total_write):>8}[/yellow]  "
            f"[{disk_temp_color}]({max_disk_temp:>4}){disk_label}[/{disk_temp_color}]"
        )
        self.io_label.update(f"{net_str}\n{dsk_str}")

    def _get_usage_color(self, percent: float) -> str:
        """Return color based on usage percentage."""
        if percent >= 90:
            return "red bold"
        elif percent >= 75:
            return "yellow"
        elif percent >= 50:
            return "green"
        else:
            return "bright_green"

    def _get_temp_color(self, temp: str) -> str:
        """Return color based on temperature."""
        if temp == "N/A":
            return "dim"
        try:
            temp_val = float(temp.replace("°C", ""))
            if temp_val >= 80:
                return "red bold"
            elif temp_val >= 70:
                return "yellow"
            elif temp_val >= 60:
                return "green"
            else:
                return "cyan"
        except (ValueError, AttributeError):
            return "dim"
        
    def check_staleness(self, now: float):
        if now - self.last_update > 15:
            self.stale_label.update("[bold yellow on black] ⚠ STALE [/bold yellow on black]")
        else:
            self.stale_label.update("")


class MonitorApp(App):
    """A Textual app to monitor hardware stats from MQTT."""

    CSS = """
    Screen {
        align: center middle;
        background: $surface;
    }
    #devices_container {
        layout: grid;
        grid-size: 3;  /* 3 columns for 3 devices */
        grid-gutter: 1 2;  /* vertical horizontal spacing */
        width: 100%;
        height: 100%;
        padding: 1;
    }
    DeviceDisplay {
        border: heavy $accent;
        background: $panel;
        height: 100%;
        padding: 1 2;
    }
    #title_bar {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }
    .title {
        width: 1fr;
        content-align: left middle;
        text-style: bold;
    }
    .stale {
        width: auto;
        content-align: right middle;
    }
    .data {
        height: auto;
        padding: 1 0;
        margin: 0;
    }

    Header {
        background: $accent-darken-2;
    }

    Footer {
        background: $accent-darken-2;
    }
    """

    def __init__(self):
        super().__init__()
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.all_devices_data = {}
        self.device_widgets = {}
        self.display_order = deque()
        self.current_page = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Grid(id="devices_container")
        yield Footer()

    def on_mount(self) -> None:
        self.setup_mqtt()
        self.set_interval(ROTATION_INTERVAL_SECONDS, self.rotate_devices)
        self.set_interval(5, self.check_stale_status)

    def setup_mqtt(self):
        """Configure and connect the MQTT client."""
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        try:
            self.mqtt_client.connect(BROKER_HOST, BROKER_PORT, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.notify(f"MQTT Connection Error: {e}", severity="error")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            client.subscribe(TOPIC)
            self.call_from_thread(self.notify, f"Connected to MQTT Broker and subscribed to {TOPIC}")
        else:
            self.call_from_thread(self.notify, f"Failed to connect, return code {rc}", severity="error")

    def on_message(self, client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""
        try:
            payload = json.loads(msg.payload.decode())
            host = payload.get("host")

            if not host:
                return

            self.all_devices_data[host] = payload

            if host not in self.device_widgets:
                # New device found, add to rotation
                new_widget = DeviceDisplay(host_id=host)
                self.device_widgets[host] = new_widget
                self.display_order.append(host)
                self.call_from_thread(self.notify, f"New device detected: {host}")

            # Update widget data via call_from_thread to ensure thread safety
            self.call_from_thread(self.update_widget_data, host)

        except json.JSONDecodeError:
            self.call_from_thread(self.notify, "Received malformed JSON", severity="warning")
        except Exception as e:
            self.call_from_thread(self.notify, f"Error processing message: {e}", severity="error")

    def update_widget_data(self, host: str):
        """Safely update a widget's data from the main thread."""
        if host in self.device_widgets and host in self.all_devices_data:
            widget = self.device_widgets[host]
            widget.device_data = self.all_devices_data[host]
            self.update_display()

    def rotate_devices(self) -> None:
        """Rotate the displayed devices if there are more than fit on a page."""
        num_devices = len(self.display_order)
        if num_devices <= MAX_DEVICES_PER_PAGE:
            self.current_page = 0
            return

        num_pages = (num_devices + MAX_DEVICES_PER_PAGE - 1) // MAX_DEVICES_PER_PAGE
        self.current_page = (self.current_page + 1) % num_pages
        self.update_display()

    def update_display(self) -> None:
        """Update the visible widgets based on the current page."""
        container = self.query_one("#devices_container")

        # Determine which slice of devices to show
        start_index = self.current_page * MAX_DEVICES_PER_PAGE
        end_index = start_index + MAX_DEVICES_PER_PAGE

        visible_hosts = [self.display_order[i] for i in range(len(self.display_order)) if start_index <= i < end_index]

        # Mount only the widgets that should be visible
        current_widgets = {child.host_id: child for child in container.children if isinstance(child, DeviceDisplay)}

        # Unmount widgets that are no longer visible
        for host_id, widget in current_widgets.items():
            if host_id not in visible_hosts:
                widget.remove()

        # Mount new widgets that should be visible
        for host_id in visible_hosts:
            if host_id not in current_widgets:
                container.mount(self.device_widgets[host_id])
    
    def check_stale_status(self) -> None:
        """Periodically check if devices are stale."""
        now = time.time()
        for widget in self.device_widgets.values():
            widget.check_staleness(now)


if __name__ == "__main__":
    app = MonitorApp()
    app.run()
