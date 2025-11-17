"""Desktop GUI application for War Timer tracking - Visual Command Center."""
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
import threading
import time

load_dotenv()

API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')
API_KEY = os.getenv('API_KEY', '')


class VisualTimerCard(tk.Frame):
    """Visual card for displaying a single timer."""

    def __init__(self, parent, timer, bg_color, emoji):
        super().__init__(parent, bg=bg_color, relief=tk.RAISED, borderwidth=2)

        self.pack(fill=tk.X, padx=5, pady=5)

        # Player name - BIG
        name_label = tk.Label(
            self,
            text=f"{emoji} {timer['user_name']}",
            font=('Arial', 16, 'bold'),
            bg=bg_color,
            fg='white'
        )
        name_label.pack(anchor=tk.W, padx=10, pady=(10, 5))

        # Time shot
        time_shot = datetime.fromisoformat(timer['time_shot'].replace('Z', '+00:00'))
        shot_label = tk.Label(
            self,
            text=f"Hit Time: {time_shot.strftime('%H:%M:%S')}",
            font=('Arial', 12),
            bg=bg_color,
            fg='white'
        )
        shot_label.pack(anchor=tk.W, padx=10)

        # Pro Drop - VERY BIG AND HIGHLIGHTED
        if timer.get('pro_drop_start'):
            pro_start = datetime.fromisoformat(timer['pro_drop_start'].replace('Z', '+00:00'))
            pro_end = timer.get('pro_drop_end')

            pro_frame = tk.Frame(self, bg='#FFD700', relief=tk.SOLID, borderwidth=2)
            pro_frame.pack(fill=tk.X, padx=10, pady=10)

            if pro_end and timer['timer_type'] == 'friendly_hit':
                pro_end_time = datetime.fromisoformat(pro_end.replace('Z', '+00:00'))
                pro_text = f"⭐ PRO DROP: {pro_start.strftime('%H:%M:%S')} - {pro_end_time.strftime('%H:%M:%S')}"
            else:
                pro_text = f"⭐ PRO DROP: {pro_start.strftime('%H:%M:%S')}"

            pro_label = tk.Label(
                pro_frame,
                text=pro_text,
                font=('Arial', 14, 'bold'),
                bg='#FFD700',
                fg='#000000'
            )
            pro_label.pack(pady=8, padx=10)

            # Time remaining
            now = datetime.now(timezone.utc)
            time_remaining = pro_start - now

            if time_remaining.total_seconds() > 0:
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)

                remaining_label = tk.Label(
                    pro_frame,
                    text=f"⏰ {hours}h {minutes}m remaining",
                    font=('Arial', 11),
                    bg='#FFD700',
                    fg='#FF0000' if time_remaining.total_seconds() < 600 else '#000000'
                )
                remaining_label.pack(pady=(0, 8))


class TimerApp:
    """Main application class for War Timer desktop GUI."""

    def __init__(self, root):
        """Initialize the application."""
        self.root = root
        self.root.title("⚔️ WAR TIMER COMMAND CENTER")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1a1a1a')

        # Create main container
        self.create_widgets()

        # Start auto-refresh
        self.auto_refresh = True
        self.refresh_thread = threading.Thread(target=self.auto_refresh_timers, daemon=True)
        self.refresh_thread.start()

    def create_widgets(self):
        """Create all GUI widgets."""
        # ==================== HEADER ====================
        header = tk.Frame(self.root, bg='#FF0000', height=80)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="⚔️ WAR TIMER COMMAND CENTER ⚔️",
            font=('Arial', 24, 'bold'),
            bg='#FF0000',
            fg='white'
        )
        title.pack(pady=20)

        # ==================== INPUT SECTION ====================
        input_section = tk.Frame(self.root, bg='#2a2a2a', relief=tk.RAISED, borderwidth=3)
        input_section.pack(fill=tk.X, padx=10, pady=10)

        # Title for input section
        input_title = tk.Label(
            input_section,
            text="ADD NEW TIMER",
            font=('Arial', 14, 'bold'),
            bg='#2a2a2a',
            fg='#FFD700'
        )
        input_title.pack(pady=(10, 5))

        # Input fields
        fields_frame = tk.Frame(input_section, bg='#2a2a2a')
        fields_frame.pack(pady=10)

        # Player name
        tk.Label(
            fields_frame,
            text="PLAYER:",
            font=('Arial', 12, 'bold'),
            bg='#2a2a2a',
            fg='white'
        ).grid(row=0, column=0, padx=10, pady=5)

        self.name_entry = tk.Entry(fields_frame, width=20, font=('Arial', 14))
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        # Time
        tk.Label(
            fields_frame,
            text="TIME:",
            font=('Arial', 12, 'bold'),
            bg='#2a2a2a',
            fg='white'
        ).grid(row=0, column=2, padx=10, pady=5)

        self.time_entry = tk.Entry(fields_frame, width=12, font=('Arial', 14))
        self.time_entry.grid(row=0, column=3, padx=10, pady=5)

        # Use Now button - BIG and GREEN
        now_btn = tk.Button(
            fields_frame,
            text="⏰ USE NOW",
            command=self.insert_current_time,
            bg='#00FF00',
            fg='black',
            font=('Arial', 12, 'bold'),
            width=12,
            height=1
        )
        now_btn.grid(row=0, column=4, padx=10, pady=5)

        # ==================== BIG ACTION BUTTONS ====================
        buttons_frame = tk.Frame(input_section, bg='#2a2a2a')
        buttons_frame.pack(pady=15)

        # Friendly Hit Button - BLUE
        self.friendly_btn = tk.Button(
            buttons_frame,
            text="🛡️\nFRIENDLY HIT",
            command=lambda: self.add_timer('friendly_hit'),
            bg='#2196F3',
            fg='white',
            font=('Arial', 16, 'bold'),
            width=15,
            height=3,
            relief=tk.RAISED,
            borderwidth=5
        )
        self.friendly_btn.pack(side=tk.LEFT, padx=15)

        # Pro Whack Button - PURPLE
        self.whack_btn = tk.Button(
            buttons_frame,
            text="💀\nPRO WHACK",
            command=lambda: self.add_timer('pro_whack'),
            bg='#9C27B0',
            fg='white',
            font=('Arial', 16, 'bold'),
            width=15,
            height=3,
            relief=tk.RAISED,
            borderwidth=5
        )
        self.whack_btn.pack(side=tk.LEFT, padx=15)

        # Enemy Hit Button - RED
        self.enemy_btn = tk.Button(
            buttons_frame,
            text="⚔️\nENEMY HIT",
            command=lambda: self.add_timer('enemy_hit'),
            bg='#F44336',
            fg='white',
            font=('Arial', 16, 'bold'),
            width=15,
            height=3,
            relief=tk.RAISED,
            borderwidth=5
        )
        self.enemy_btn.pack(side=tk.LEFT, padx=15)

        # ==================== TIMER DISPLAY ====================
        display_frame = tk.Frame(self.root, bg='#1a1a1a')
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create canvas with scrollbar
        canvas = tk.Canvas(display_frame, bg='#1a1a1a', highlightthickness=0)
        scrollbar = tk.Scrollbar(display_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ==================== BOTTOM STATUS BAR ====================
        status_frame = tk.Frame(self.root, bg='#FFD700', height=50)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Refresh button
        refresh_btn = tk.Button(
            status_frame,
            text="🔄 REFRESH",
            command=self.refresh_timers,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief=tk.RAISED,
            borderwidth=3
        )
        refresh_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Clear all button
        clear_btn = tk.Button(
            status_frame,
            text="🗑️ CLEAR ALL",
            command=self.clear_all_timers,
            bg='#FF5722',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief=tk.RAISED,
            borderwidth=3
        )
        clear_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="⚡ READY",
            font=('Arial', 12, 'bold'),
            bg='#FFD700',
            fg='#000000'
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)

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
            messagebox.showerror("❌ ERROR", "Please enter a player name")
            return

        if not time_str:
            messagebox.showerror("❌ ERROR", "Please enter a time or click 'USE NOW'")
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
                self.status_label.config(text=f"✅ {player_name} ADDED!", fg='#00FF00')
                self.refresh_timers()

                # Clear inputs
                self.name_entry.delete(0, tk.END)
                self.time_entry.delete(0, tk.END)

                # Flash the button
                btn_map = {
                    'friendly_hit': self.friendly_btn,
                    'pro_whack': self.whack_btn,
                    'enemy_hit': self.enemy_btn
                }
                btn = btn_map[timer_type]
                original_bg = btn['bg']
                btn.config(bg='#00FF00')
                self.root.after(200, lambda: btn.config(bg=original_bg))
            else:
                messagebox.showerror("❌ ERROR", f"API error: {response.status_code}")

        except ValueError:
            messagebox.showerror("❌ ERROR", "Invalid time format. Use HH:MM:SS")
        except requests.RequestException as e:
            messagebox.showerror("❌ ERROR", f"Failed to connect to API: {e}")
        except Exception as e:
            messagebox.showerror("❌ ERROR", f"An error occurred: {e}")

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
                    text=f"🔄 UPDATED: {datetime.now().strftime('%H:%M:%S')}",
                    fg='#000000'
                )
            else:
                self.status_label.config(text=f"❌ API ERROR {response.status_code}", fg='#FF0000')

        except requests.RequestException:
            self.status_label.config(text="❌ CONNECTION ERROR", fg='#FF0000')
        except Exception as e:
            self.status_label.config(text=f"❌ ERROR", fg='#FF0000')

    def display_timers(self, timers):
        """Display timers visually."""
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not timers:
            empty = tk.Label(
                self.scrollable_frame,
                text="NO ACTIVE TIMERS\n\nAdd a timer using the buttons above",
                font=('Arial', 18, 'bold'),
                bg='#1a1a1a',
                fg='#666666'
            )
            empty.pack(pady=50)
            return

        # Group by type
        friendly = [t for t in timers if t['timer_type'] == 'friendly_hit']
        whacks = [t for t in timers if t['timer_type'] == 'pro_whack']
        enemy = [t for t in timers if t['timer_type'] == 'enemy_hit']

        # Display friendly hits
        if friendly:
            header = tk.Label(
                self.scrollable_frame,
                text="🛡️ FRIENDLY HITS",
                font=('Arial', 18, 'bold'),
                bg='#1a1a1a',
                fg='#2196F3'
            )
            header.pack(anchor=tk.W, padx=10, pady=(10, 5))

            for timer in friendly:
                VisualTimerCard(self.scrollable_frame, timer, '#2196F3', '🛡️')

        # Display pro whacks
        if whacks:
            header = tk.Label(
                self.scrollable_frame,
                text="💀 PRO WHACKS",
                font=('Arial', 18, 'bold'),
                bg='#1a1a1a',
                fg='#9C27B0'
            )
            header.pack(anchor=tk.W, padx=10, pady=(20, 5))

            for timer in whacks:
                VisualTimerCard(self.scrollable_frame, timer, '#9C27B0', '💀')

        # Display enemy hits
        if enemy:
            header = tk.Label(
                self.scrollable_frame,
                text="⚔️ ENEMY HITS",
                font=('Arial', 18, 'bold'),
                bg='#1a1a1a',
                fg='#F44336'
            )
            header.pack(anchor=tk.W, padx=10, pady=(20, 5))

            for timer in enemy:
                VisualTimerCard(self.scrollable_frame, timer, '#F44336', '⚔️')

    def clear_all_timers(self):
        """Clear all timers with confirmation."""
        if not messagebox.askyesno("⚠️ CONFIRM", "Clear ALL timers?"):
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

                self.status_label.config(text="✅ ALL CLEARED", fg='#00FF00')
                self.refresh_timers()

        except Exception as e:
            messagebox.showerror("❌ ERROR", f"Failed to clear timers: {e}")

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
