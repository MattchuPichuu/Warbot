"""Desktop GUI application for War Timer tracking."""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
import threading
import time

load_dotenv()

API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')
API_KEY = os.getenv('API_KEY', '')


class TimerApp:
    """Main application class for War Timer desktop GUI."""

    def __init__(self, root):
        """Initialize the application."""
        self.root = root
        self.root.title("⚔️ War Timer - Desktop App")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

        # Create main container
        self.create_widgets()

        # Start auto-refresh
        self.auto_refresh = True
        self.refresh_thread = threading.Thread(target=self.auto_refresh_timers, daemon=True)
        self.refresh_thread.start()

    def create_widgets(self):
        """Create all GUI widgets."""
        # Title
        title_frame = tk.Frame(self.root, bg='#667eea', pady=15)
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(
            title_frame,
            text="⚔️ War Timer Desktop App",
            font=('Arial', 20, 'bold'),
            bg='#667eea',
            fg='white'
        )
        title_label.pack()

        # Input Frame
        input_frame = tk.LabelFrame(self.root, text="Add New Timer", padx=20, pady=15)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Player Name
        tk.Label(input_frame, text="Player Name:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = tk.Entry(input_frame, width=25, font=('Arial', 11))
        self.name_entry.grid(row=0, column=1, pady=5, padx=5)

        # Time Input
        tk.Label(input_frame, text="Time (HH:MM:SS):", font=('Arial', 10)).grid(row=0, column=2, sticky=tk.W, pady=5)
        self.time_entry = tk.Entry(input_frame, width=15, font=('Arial', 11))
        self.time_entry.grid(row=0, column=3, pady=5, padx=5)

        # Current time button
        current_time_btn = tk.Button(
            input_frame,
            text="Use Now",
            command=self.insert_current_time,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 9)
        )
        current_time_btn.grid(row=0, column=4, pady=5, padx=5)

        # Timer Type Buttons
        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=1, column=0, columnspan=5, pady=10)

        self.friendly_btn = tk.Button(
            button_frame,
            text="🛡️ Friendly Hit",
            command=lambda: self.add_timer('friendly_hit'),
            bg='#2196F3',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=15,
            height=2
        )
        self.friendly_btn.pack(side=tk.LEFT, padx=5)

        self.whack_btn = tk.Button(
            button_frame,
            text="💀 Pro Whack",
            command=lambda: self.add_timer('pro_whack'),
            bg='#9C27B0',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=15,
            height=2
        )
        self.whack_btn.pack(side=tk.LEFT, padx=5)

        self.enemy_btn = tk.Button(
            button_frame,
            text="⚔️ Enemy Hit",
            command=lambda: self.add_timer('enemy_hit'),
            bg='#F44336',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=15,
            height=2
        )
        self.enemy_btn.pack(side=tk.LEFT, padx=5)

        # Timer Display
        display_frame = tk.LabelFrame(self.root, text="Active Timers", padx=10, pady=10)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Text widget for displaying timers
        self.timer_display = scrolledtext.ScrolledText(
            display_frame,
            width=80,
            height=15,
            font=('Courier', 10),
            bg='#f5f5f5'
        )
        self.timer_display.pack(fill=tk.BOTH, expand=True)

        # Control Buttons
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        refresh_btn = tk.Button(
            control_frame,
            text="🔄 Refresh",
            command=self.refresh_timers,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10)
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(
            control_frame,
            text="🗑️ Clear All",
            command=self.clear_all_timers,
            bg='#F44336',
            fg='white',
            font=('Arial', 10)
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = tk.Label(
            control_frame,
            text="Ready",
            font=('Arial', 9),
            fg='#666'
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Initial refresh
        self.refresh_timers()

    def insert_current_time(self):
        """Insert current time into the time entry field."""
        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, time_str)

    def add_timer(self, timer_type):
        """Add a new timer via API."""
        player_name = self.name_entry.get().strip()
        time_str = self.time_entry.get().strip()

        if not player_name:
            messagebox.showerror("Error", "Please enter a player name")
            return

        if not time_str:
            messagebox.showerror("Error", "Please enter a time or click 'Use Now'")
            return

        try:
            # Parse time
            hit_time = datetime.strptime(time_str, '%H:%M:%S').time()

            # Create full datetime
            now = datetime.now(timezone.utc)
            time_shot = now.replace(
                hour=hit_time.hour,
                minute=hit_time.minute,
                second=hit_time.second,
                microsecond=0
            )

            # If in future, assume yesterday
            if time_shot > now:
                time_shot = time_shot - timedelta(days=1)

            # Send to API
            headers = {"X-API-Key": API_KEY} if API_KEY else {}
            payload = {
                "user_name": player_name,
                "timer_type": timer_type,
                "time_shot": time_shot.isoformat()
            }

            response = requests.post(
                f"{API_URL}/timers/",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self.status_label.config(text=f"✅ Timer added for {player_name}", fg='green')
                self.refresh_timers()

                # Clear inputs
                self.name_entry.delete(0, tk.END)
                self.time_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", f"API error: {response.status_code}")

        except ValueError:
            messagebox.showerror("Error", "Invalid time format. Use HH:MM:SS")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to connect to API: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def refresh_timers(self):
        """Fetch and display all timers."""
        try:
            headers = {"X-API-Key": API_KEY} if API_KEY else {}
            response = requests.get(
                f"{API_URL}/timers/?limit=500",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                timers = response.json()
                self.display_timers(timers)
                self.status_label.config(
                    text=f"Last updated: {datetime.now().strftime('%H:%M:%S')}",
                    fg='#666'
                )
            else:
                self.status_label.config(text=f"Error: API returned {response.status_code}", fg='red')

        except requests.RequestException as e:
            self.status_label.config(text=f"Connection error", fg='red')
        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg='red')

    def display_timers(self, timers):
        """Display timers in the text widget."""
        self.timer_display.config(state=tk.NORMAL)
        self.timer_display.delete(1.0, tk.END)

        if not timers:
            self.timer_display.insert(tk.END, "No active timers\n")
            self.timer_display.config(state=tk.DISABLED)
            return

        # Group by type
        friendly = [t for t in timers if t['timer_type'] == 'friendly_hit']
        whacks = [t for t in timers if t['timer_type'] == 'pro_whack']
        enemy = [t for t in timers if t['timer_type'] == 'enemy_hit']

        # Display friendly hits
        if friendly:
            self.timer_display.insert(tk.END, "=" * 80 + "\n")
            self.timer_display.insert(tk.END, "🛡️  FRIENDLY HITS\n")
            self.timer_display.insert(tk.END, "=" * 80 + "\n")
            for timer in friendly:
                self.format_timer(timer)
            self.timer_display.insert(tk.END, "\n")

        # Display pro whacks
        if whacks:
            self.timer_display.insert(tk.END, "=" * 80 + "\n")
            self.timer_display.insert(tk.END, "💀 PRO WHACKS\n")
            self.timer_display.insert(tk.END, "=" * 80 + "\n")
            for timer in whacks:
                self.format_timer(timer)
            self.timer_display.insert(tk.END, "\n")

        # Display enemy hits
        if enemy:
            self.timer_display.insert(tk.END, "=" * 80 + "\n")
            self.timer_display.insert(tk.END, "⚔️  ENEMY HITS\n")
            self.timer_display.insert(tk.END, "=" * 80 + "\n")
            for timer in enemy:
                self.format_timer(timer)

        self.timer_display.config(state=tk.DISABLED)

    def format_timer(self, timer):
        """Format a single timer for display."""
        time_shot = datetime.fromisoformat(timer['time_shot'].replace('Z', '+00:00'))
        pro_start = datetime.fromisoformat(timer['pro_drop_start'].replace('Z', '+00:00')) if timer.get('pro_drop_start') else None
        pro_end = datetime.fromisoformat(timer['pro_drop_end'].replace('Z', '+00:00')) if timer.get('pro_drop_end') else None

        self.timer_display.insert(tk.END, f"Player: {timer['user_name']:<20} ")
        self.timer_display.insert(tk.END, f"Hit: {time_shot.strftime('%H:%M:%S')}\n")

        if pro_start:
            if pro_end and timer['timer_type'] == 'friendly_hit':
                self.timer_display.insert(
                    tk.END,
                    f"  └─ Pro Drop: {pro_start.strftime('%H:%M:%S')} - {pro_end.strftime('%H:%M:%S')}\n"
                )
            else:
                self.timer_display.insert(
                    tk.END,
                    f"  └─ Pro Drop: {pro_start.strftime('%H:%M:%S')}\n"
                )

        self.timer_display.insert(tk.END, "\n")

    def clear_all_timers(self):
        """Clear all timers with confirmation."""
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear all timers?"):
            return

        try:
            headers = {"X-API-Key": API_KEY} if API_KEY else {}
            response = requests.get(f"{API_URL}/timers/?limit=500", headers=headers, timeout=10)

            if response.status_code == 200:
                timers = response.json()

                for timer in timers:
                    requests.delete(
                        f"{API_URL}/timers/{timer['id']}",
                        headers=headers,
                        timeout=10
                    )

                self.status_label.config(text="✅ All timers cleared", fg='green')
                self.refresh_timers()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear timers: {e}")

    def auto_refresh_timers(self):
        """Auto-refresh timers every 5 seconds."""
        while self.auto_refresh:
            time.sleep(5)
            try:
                self.refresh_timers()
            except:
                pass


def main():
    """Main entry point."""
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
