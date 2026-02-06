"""
ClaudeUsageWindow - Always-on-top widget showing real Claude.ai usage
Fetches data from claude.ai/settings/usage via Firefox cookies
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import math
import os
import subprocess
import threading
import re
from datetime import datetime, timedelta
from pathlib import Path
import time
import urllib.request
import urllib.error

# Try to import browser_cookie3
try:
    import browser_cookie3
    HAS_BROWSER_COOKIES = True
except ImportError:
    HAS_BROWSER_COOKIES = False


class TokenMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude Usage")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(False)

        # Window settings
        self.root.geometry("320x200+50+50")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a2e')

        # State
        self.state_file = Path(__file__).parent / "state.json"
        self.org_uuid = None
        self.whatsapp_number = '+33XXXXXXXXX'
        self.load_state()

        # Usage data
        self.session_pct = 0
        self.session_reset = None
        self.weekly_pct = 0
        self.weekly_reset = None

        # Notification tracking
        self.session_notified = False
        self.last_session_reset = None

        self.setup_ui()
        self.setup_drag()

        # Initial fetch
        self.refresh_data()

    def load_state(self):
        """Load saved state"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.org_uuid = data.get('org_uuid')
                    self.whatsapp_number = data.get('whatsapp_number', '+33XXXXXXXXX')
                    self.session_notified = data.get('session_notified', False)
                    self.last_session_reset = data.get('last_session_reset')
        except Exception:
            pass

    def save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'org_uuid': self.org_uuid,
                    'whatsapp_number': self.whatsapp_number,
                    'session_notified': self.session_notified,
                    'last_session_reset': self.last_session_reset
                }, f)
        except Exception as e:
            print(f"Error saving state: {e}")

    def _draw_claude_logo(self, parent, bg_color):
        """Draw the Claude logo (sunburst) on a canvas"""
        size = 24
        canvas = tk.Canvas(parent, width=size, height=size, bg=bg_color, highlightthickness=0)
        color = '#D97757'
        cx, cy = size / 2, size / 2

        # Center circle
        r = 2.5
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline='')

        # 5 petals radiating outward
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            x1 = cx + 3.5 * math.cos(angle)
            y1 = cy + 3.5 * math.sin(angle)
            x2 = cx + 10 * math.cos(angle)
            y2 = cy + 10 * math.sin(angle)
            canvas.create_line(x1, y1, x2, y2, fill=color, width=3.5, capstyle='round')

        return canvas

    def setup_ui(self):
        # Main frame
        self.main_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.main_frame.pack(fill='both', expand=True, padx=8, pady=8)

        # Header - Claude logo only + refresh button
        title_frame = tk.Frame(self.main_frame, bg='#16213e')
        title_frame.pack(fill='x', pady=(0, 8))

        logo_canvas = self._draw_claude_logo(title_frame, '#16213e')
        logo_canvas.pack(side='left', padx=8, pady=4)

        # Refresh button
        self.refresh_btn = tk.Button(
            title_frame,
            text="\u21bb",
            command=self.refresh_with_animation,
            bg='#16213e',
            fg='#ffffff',
            font=('Segoe UI', 11),
            relief='flat',
            width=2,
            cursor='hand2'
        )
        self.refresh_btn.pack(side='right', padx=2, pady=2)

        # Content frame
        self.content_frame = tk.Frame(self.main_frame, bg='#1a1a2e')
        self.content_frame.pack(fill='both', expand=True)

        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Session.Horizontal.TProgressbar", troughcolor='#16213e', background='#4ecca3', thickness=12)
        style.configure("Weekly.Horizontal.TProgressbar", troughcolor='#16213e', background='#4ecca3', thickness=12)

        # --- Session (5h) section ---
        tk.Label(
            self.content_frame,
            text="Session (5h)",
            bg='#1a1a2e',
            fg='#a0a0a0',
            font=('Segoe UI', 9)
        ).pack(anchor='w')

        # Session bar row: progress bar + percentage outside
        session_bar_frame = tk.Frame(self.content_frame, bg='#1a1a2e')
        session_bar_frame.pack(fill='x', pady=(2, 0))

        self.session_progress = ttk.Progressbar(
            session_bar_frame,
            style="Session.Horizontal.TProgressbar",
            mode='determinate'
        )
        self.session_progress.pack(side='left', fill='x', expand=True)

        self.session_pct_label = tk.Label(
            session_bar_frame,
            text="---%",
            bg='#1a1a2e',
            fg='#4ecca3',
            font=('Segoe UI', 10, 'bold'),
            width=5,
            anchor='e'
        )
        self.session_pct_label.pack(side='right', padx=(4, 0))

        self.session_reset_label = tk.Label(
            self.content_frame,
            text="Reset: ---",
            bg='#1a1a2e',
            fg='#666666',
            font=('Segoe UI', 8)
        )
        self.session_reset_label.pack(anchor='e', pady=(0, 8))

        # --- Weekly section ---
        tk.Label(
            self.content_frame,
            text="Hebdomadaire",
            bg='#1a1a2e',
            fg='#a0a0a0',
            font=('Segoe UI', 9)
        ).pack(anchor='w')

        # Weekly bar row: progress bar + percentage outside
        weekly_bar_frame = tk.Frame(self.content_frame, bg='#1a1a2e')
        weekly_bar_frame.pack(fill='x', pady=(2, 0))

        self.weekly_progress = ttk.Progressbar(
            weekly_bar_frame,
            style="Weekly.Horizontal.TProgressbar",
            mode='determinate'
        )
        self.weekly_progress.pack(side='left', fill='x', expand=True)

        self.weekly_pct_label = tk.Label(
            weekly_bar_frame,
            text="---%",
            bg='#1a1a2e',
            fg='#4ecca3',
            font=('Segoe UI', 10, 'bold'),
            width=5,
            anchor='e'
        )
        self.weekly_pct_label.pack(side='right', padx=(4, 0))

        self.weekly_reset_label = tk.Label(
            self.content_frame,
            text="Reset: ---",
            bg='#1a1a2e',
            fg='#666666',
            font=('Segoe UI', 8)
        )
        self.weekly_reset_label.pack(anchor='e', pady=(0, 8))

        # Status label
        self.status_label = tk.Label(
            self.content_frame,
            text="",
            bg='#1a1a2e',
            fg='#666666',
            font=('Segoe UI', 8)
        )
        self.status_label.pack(pady=(4, 0))

    def setup_drag(self):
        """Enable window dragging"""
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.do_drag)

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def do_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")

    def refresh_with_animation(self):
        """Refresh with a single circular rotation animation"""
        self.refresh_btn.config(state='disabled')

        # One full clockwise rotation
        frames = ['\u2191', '\u2197', '\u2192', '\u2198', '\u2193', '\u2199', '\u2190', '\u2196']

        def animate(i=0):
            if i < len(frames):
                self.refresh_btn.config(text=frames[i], fg='#4ecca3')
                self.root.after(80, lambda: animate(i + 1))
            else:
                self.refresh_btn.config(text='\u21bb', fg='#ffffff', state='normal')

        animate()
        self.refresh_data()

    def refresh_data(self):
        """Fetch usage data in background"""
        self.status_label.config(text="Chargement...", fg='#666666')
        threading.Thread(target=self._fetch_usage, daemon=True).start()

    def _get_cookies(self):
        """Get cookies from Firefox"""
        if not HAS_BROWSER_COOKIES:
            return None
        try:
            cj = browser_cookie3.firefox(domain_name='claude.ai')
            return '; '.join([f'{c.name}={c.value}' for c in cj])
        except Exception as e:
            print(f"Cookie error: {e}")
            return None

    def _get_org_uuid(self, cookies):
        """Fetch organization UUID"""
        if self.org_uuid:
            return self.org_uuid

        try:
            url = 'https://claude.ai/api/organizations'
            req = urllib.request.Request(url)
            req.add_header('Cookie', cookies)
            req.add_header('Accept', 'application/json')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data and len(data) > 0:
                    self.org_uuid = data[0]['uuid']
                    self.save_state()
                    return self.org_uuid
        except Exception as e:
            print(f"Org fetch error: {e}")
        return None

    def _fetch_usage(self):
        """Fetch usage from Claude.ai API"""
        try:
            if not HAS_BROWSER_COOKIES:
                self._update_error("pip install browser-cookie3")
                return

            cookies = self._get_cookies()
            if not cookies:
                self._update_error("Ouvre Firefox sur claude.ai")
                return

            org_uuid = self._get_org_uuid(cookies)
            if not org_uuid:
                self._update_error("Org non trouvée")
                return

            # Fetch usage
            url = f'https://claude.ai/api/organizations/{org_uuid}/usage'
            req = urllib.request.Request(url)
            req.add_header('Cookie', cookies)
            req.add_header('Accept', 'application/json')
            req.add_header('Origin', 'https://claude.ai')
            req.add_header('Referer', 'https://claude.ai/settings/usage')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                self._process_usage(data)

        except urllib.error.HTTPError as e:
            if e.code == 403:
                self._update_error("Session expirée - reconnecte-toi sur claude.ai")
            else:
                self._update_error(f"Erreur HTTP {e.code}")
        except Exception as e:
            self._update_error(f"Erreur: {str(e)[:30]}")

    def _process_usage(self, data):
        """Process usage data and update UI"""
        five_hour = data.get('five_hour', {})
        seven_day = data.get('seven_day', {})

        self.session_pct = five_hour.get('utilization', 0) or 0
        self.weekly_pct = seven_day.get('utilization', 0) or 0

        session_reset_str = five_hour.get('resets_at')
        weekly_reset_str = seven_day.get('resets_at')

        # Parse reset times
        if session_reset_str:
            self.session_reset = datetime.fromisoformat(session_reset_str.replace('Z', '+00:00'))
        if weekly_reset_str:
            self.weekly_reset = datetime.fromisoformat(weekly_reset_str.replace('Z', '+00:00'))

        # Check if session reset changed (new session available)
        if session_reset_str != self.last_session_reset:
            if self.last_session_reset is not None and self.session_pct < 10:
                # Session was reset - send notification if we were waiting
                self._send_notification()
            self.last_session_reset = session_reset_str
            self.session_notified = False
            self.save_state()

        # Schedule notification if usage is high
        if self.session_pct >= 95 and not self.session_notified:
            self._schedule_notification()

        self._update_ui()

    def _update_ui(self):
        """Update the UI from main thread"""
        def update():
            # Session
            self.session_pct_label.config(text=f"{self.session_pct:.0f}%")
            self.session_progress['value'] = self.session_pct

            if self.session_reset:
                local_reset = self.session_reset.astimezone()
                self.session_reset_label.config(text=f"Reset: {local_reset.strftime('%H:%M')}")

            # Color coding
            if self.session_pct >= 90:
                self.session_pct_label.config(fg='#e94560')
                style = ttk.Style()
                style.configure("Session.Horizontal.TProgressbar", background='#e94560')
            elif self.session_pct >= 70:
                self.session_pct_label.config(fg='#f4a261')
                style = ttk.Style()
                style.configure("Session.Horizontal.TProgressbar", background='#f4a261')
            else:
                self.session_pct_label.config(fg='#4ecca3')
                style = ttk.Style()
                style.configure("Session.Horizontal.TProgressbar", background='#4ecca3')

            # Weekly
            self.weekly_pct_label.config(text=f"{self.weekly_pct:.0f}%")
            self.weekly_progress['value'] = self.weekly_pct

            if self.weekly_reset:
                local_reset = self.weekly_reset.astimezone()
                self.weekly_reset_label.config(text=f"Reset: {local_reset.strftime('%d/%m %H:%M')}")

            if self.weekly_pct >= 90:
                self.weekly_pct_label.config(fg='#e94560')
                style = ttk.Style()
                style.configure("Weekly.Horizontal.TProgressbar", background='#e94560')
            elif self.weekly_pct >= 70:
                self.weekly_pct_label.config(fg='#f4a261')
                style = ttk.Style()
                style.configure("Weekly.Horizontal.TProgressbar", background='#f4a261')
            else:
                self.weekly_pct_label.config(fg='#4ecca3')
                style = ttk.Style()
                style.configure("Weekly.Horizontal.TProgressbar", background='#4ecca3')

            # Status
            now = datetime.now().strftime('%H:%M:%S')
            self.status_label.config(text=f"Mis à jour: {now}", fg='#4ecca3')

        self.root.after(0, update)

    def _update_error(self, msg):
        """Update UI with error message"""
        def update():
            self.status_label.config(text=msg, fg='#e94560')
        self.root.after(0, update)

    def _schedule_notification(self):
        """Schedule a WhatsApp notification for when session resets"""
        if self.session_reset and not self.session_notified:
            self.session_notified = True
            self.save_state()

            # Calculate delay
            now = datetime.now(self.session_reset.tzinfo)
            delay = (self.session_reset - now).total_seconds()

            if delay > 0:
                def notify_later():
                    time.sleep(delay)
                    self._send_notification()

                threading.Thread(target=notify_later, daemon=True).start()

    def _send_notification(self):
        """Send WhatsApp notification via OpenClaw"""
        try:
            message = "Tes tokens Claude sont de nouveau disponibles! Session réinitialisée."

            cmd = [
                'openclaw', 'message', 'send',
                '--channel', 'whatsapp',
                '--target', self.whatsapp_number,
                '--message', message
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            if result.returncode == 0:
                print("WhatsApp notification sent!")
            else:
                print(f"WhatsApp error: {result.stderr}")

        except Exception as e:
            print(f"Notification error: {e}")

    def run(self):
        # Auto-refresh every 2 minutes
        def auto_refresh():
            self.refresh_data()
            self.root.after(120000, auto_refresh)  # 2 minutes

        self.root.after(120000, auto_refresh)
        self.root.mainloop()


if __name__ == "__main__":
    app = TokenMonitor()
    app.run()
