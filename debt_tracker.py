import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
import os
from datetime import date, datetime
import re
import sys
from pathlib import Path

# ---------- Font ----------

FONT_FACE = "Arial Unicode MS"

_INPUT_FONT_CACHE = {}

def get_font(size=10, style=""):
    return (FONT_FACE, size) + ((style,) if style else ())

def get_input_font(size=10, style=""):
    import tkinter.font as tkfont
    key = (size, style)
    if key not in _INPUT_FONT_CACHE:
        kwargs = {"family": FONT_FACE, "size": size}
        if "bold"   in style: kwargs["weight"] = "bold"
        if "italic" in style: kwargs["slant"]  = "italic"
        try:
            _INPUT_FONT_CACHE[key] = tkfont.Font(**kwargs)
        except Exception:
            _INPUT_FONT_CACHE[key] = (FONT_FACE, size)
    return _INPUT_FONT_CACHE[key]

# ---------- Validation ----------

_NAME_FORBIDDEN = re.compile(r'[!@#$%^&*()\[\]{}|\\;:\'"<>?/=+]')

def validate_name_chars(name):
    return not bool(_NAME_FORBIDDEN.search(name))

def validate_phone_chars(phone):
    if phone == "":
        return True
    return bool(re.match(r'^[\d\s\+\-\(\)]+$', phone))

# ---------- Data Folder / Date ----------

def get_data_folder():
    if getattr(sys, 'frozen', False):
        folder = Path.home() / "Documents" / "DebtTracker"
    else:
        folder = Path(os.path.dirname(os.path.abspath(__file__)))
    folder.mkdir(parents=True, exist_ok=True)
    return folder

DATA_FOLDER = get_data_folder()
DB_FILE     = DATA_FOLDER / "debt_tracker.db"
CONFIG_FILE = DATA_FOLDER / "date_format.txt"

def get_saved_date_format():
    if CONFIG_FILE.exists():
        try:
            return CONFIG_FILE.read_text().strip()
        except Exception:
            pass
    return "yyyy-mm-dd"

def save_date_format(fmt):
    try:
        CONFIG_FILE.write_text(fmt)
    except Exception:
        pass

def detect_date_format(date_str):
    patterns = [
        (r'^\d{4}-\d{2}-\d{2}$', '%Y-%m-%d'),
        (r'^\d{2}/\d{2}/\d{4}$', '%m/%d/%Y'),
        (r'^\d{1,2}/\d{1,2}/\d{2}$', '%m/%d/%y'),
        (r'^\d{2}-\d{2}-\d{4}$', '%d-%m-%Y'),
        (r'^\d{4}/\d{2}/\d{2}$', '%Y/%m/%d'),
        (r'^\d{2}\.\d{2}\.\d{4}$', '%d.%m.%Y'),
    ]
    for pattern, fmt in patterns:
        if re.match(pattern, date_str):
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
    return None

def format_number(num):
    return f"{num:,.2f}"

# ---------- Themes ----------

THEMES = {
    "light": {
        "bg":           "#f0f4f8",
        "bg2":          "#ffffff",
        "fg":           "#31506e",
        "fg_dim":       "#7f8c8d",
        "header_bg":    "#2c3e50",
        "header_fg":    "#ffffff",
        "entry_bg":     "#ffffff",
        "entry_fg":     "#2c3e50",
        "tree_bg":      "#ffffff",
        "tree_fg":      "#2c3e50",
        "tree_head_bg": "#dce3ea",
        "tree_head_fg": "#2c3e50",
        "tree_sel_bg":  "#bbdefb",
        "tree_sel_fg":  "#0d3349",
        "tree_border":  "#b0bec5",
        "unpaid_odd":   ("#fdecea", "#c0392b"),
        "unpaid_even":  ("#fdf6f5", "#c0392b"),
        "paid_odd":     ("#eafaf1", "#1e8449"),
        "paid_even":    ("#f4fdf6", "#1e8449"),
        "summary_fg":   "#e74c3c",
        "toggle_btn":   "#34495e",
    },
    "dark": {
        "bg":           "#1e2328",
        "bg2":          "#2c313a",
        "fg":           "#559adf",
        "fg_dim":       "#6c757d",
        "header_bg":    "#2B75BE",
        "header_fg":    "#e0e6ed",
        "entry_bg":     "#2c313a",
        "entry_fg":     "#e0e6ed",
        "tree_bg":      "#2c313a",
        "tree_fg":      "#e0e6ed",
        "tree_head_bg": "#3a4049",
        "tree_head_fg": "#e0e6ed",
        "tree_sel_bg":  "#1a4a6b",
        "tree_sel_fg":  "#e0e6ed",
        "tree_border":  "#4a5260",
        "unpaid_odd":   ("#3d1c1c", "#e87878"),
        "unpaid_even":  ("#341818", "#e87878"),
        "paid_odd":     ("#1a3326", "#5dba7d"),
        "paid_even":    ("#162b20", "#5dba7d"),
        "summary_fg":   "#e87878",
        "toggle_btn":   "#f0c040",
    },
}

# ---------- Database ----------

def get_connection():
    try:
        return sqlite3.connect(DB_FILE)
    except Exception as e:
        messagebox.showerror("Database Error",
            f"Cannot open database:\n\n{DB_FILE}\n\nError: {e}")
        raise

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                phone         TEXT    NOT NULL DEFAULT '',
                amount        REAL    NOT NULL,
                interest_rate REAL    NOT NULL DEFAULT 0.0,
                date          TEXT    NOT NULL,
                notes         TEXT,
                status        TEXT    NOT NULL DEFAULT 'Unpaid'
            )
        """)
        for col_def in (
            "ALTER TABLE debts ADD COLUMN interest_rate REAL NOT NULL DEFAULT 0.0",
            "ALTER TABLE debts ADD COLUMN phone TEXT NOT NULL DEFAULT ''",
        ):
            try:
                conn.execute(col_def)
            except sqlite3.OperationalError:
                pass
        conn.commit()

def db_add(name, phone, amount, interest_rate, date_val, notes, status):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO debts (name, phone, amount, interest_rate, date, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, amount, interest_rate, date_val, notes, status)
        )
        conn.commit()

def db_all():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, phone, amount, interest_rate, date, notes, status FROM debts ORDER BY id DESC"
        ).fetchall()

def db_update_status(record_id, status):
    with get_connection() as conn:
        conn.execute("UPDATE debts SET status=? WHERE id=?", (status, record_id))
        conn.commit()

def db_update_record(record_id, name, phone, amount, interest_rate, date_val, notes, status):
    with get_connection() as conn:
        conn.execute(
            "UPDATE debts SET name=?, phone=?, amount=?, interest_rate=?, date=?, notes=?, status=? WHERE id=?",
            (name, phone, amount, interest_rate, date_val, notes, status, record_id)
        )
        conn.commit()

def db_delete(record_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM debts WHERE id=?", (record_id,))
        conn.commit()

def db_total_unpaid():
    with get_connection() as conn:
        result = conn.execute(
            "SELECT SUM(amount * (1 + interest_rate / 100.0)) FROM debts WHERE status='Unpaid'"
        ).fetchone()[0]
        return result or 0.0

def db_search(query):
    with get_connection() as conn:
        like = f"%{query}%"
        return conn.execute(
            """SELECT id, name, phone, amount, interest_rate, date, notes, status FROM debts
               WHERE name LIKE ? OR phone LIKE ? OR notes LIKE ? OR status LIKE ?
               ORDER BY id DESC""",
            (like, like, like, like)
        ).fetchall()

def db_get_record(record_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, phone, amount, interest_rate, date, notes, status FROM debts WHERE id=?",
            (record_id,)
        ).fetchone()

def calculate_total_with_interest(amount, interest_rate):
    return amount * (1 + interest_rate / 100)

# ---------- Edit Dialog ----------

class EditDialog(tk.Toplevel):
    def __init__(self, parent, record_id, on_save, theme):
        super().__init__(parent)
        self.record_id = record_id
        self.on_save   = on_save
        self.t         = theme
        self.title("Edit Record")
        self.resizable(False, False)
        self.configure(bg=self.t["bg"])
        self.grab_set()

        record = db_get_record(record_id)
        if not record:
            self.destroy()
            return
        _, name, phone, amount, interest_rate, date_val, notes, status = record

        # Header
        tk.Label(self, text="Edit Record",
                 font=get_font(13, "bold"),
                 bg=self.t["header_bg"], fg=self.t["header_fg"]).pack(fill="x", pady=(0, 10), ipady=8)

        form = tk.Frame(self, bg=self.t["bg"])
        form.pack(fill="both", expand=True, padx=16, pady=4)

        def lbl(text, row_i):
            tk.Label(form, text=text, font=get_font(10),
                     bg=self.t["bg"], fg=self.t["fg"], anchor="w").grid(
                         row=row_i, column=0, sticky="w", pady=(8, 2))

        def make_entry(row_i, value, width=32):
            e = tk.Entry(form, width=width, font=get_input_font(10),
                         relief="solid", bd=1,
                         bg=self.t["entry_bg"], fg=self.t["entry_fg"],
                         insertbackground=self.t["entry_fg"])
            e.insert(0, value)
            e.grid(row=row_i, column=1, sticky="ew", padx=(8, 0), pady=(8, 2))
            return e

        lbl("Name", 0)
        self.e_name = make_entry(0, name)
        def _vcmd_name(P):
            return not any(ch in set('!@#$%^&*()=+[]{}|\\;:\'"<>?/') for ch in P)
        self.e_name.config(validate="key", validatecommand=(form.register(_vcmd_name), '%P'))

        lbl("Phone Number", 1)
        self.e_phone = make_entry(1, phone or "")
        def _vcmd_phone(P):
            return P == "" or bool(re.match(r'^[\d\s\+\-\(\)]*$', P))
        self.e_phone.config(validate="key", validatecommand=(form.register(_vcmd_phone), '%P'))

        lbl("Amount ($)", 2)
        self.e_amount = make_entry(2, f"{amount:.2f}")
        def _vcmd_amount(P):
            if P == "": return True
            if P.replace(".", "", 1).isdigit():
                try: return float(P) <= 10000
                except ValueError: return False
            return False
        self.e_amount.config(validate="key", validatecommand=(form.register(_vcmd_amount), '%P'))

        lbl("Interest Rate (%)", 3)
        interest_frame = tk.Frame(form, bg=self.t["bg"])
        interest_frame.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 2))
        self.e_interest = tk.Entry(interest_frame, width=12, font=get_input_font(10),
                                   relief="solid", bd=1,
                                   bg=self.t["entry_bg"], fg=self.t["entry_fg"],
                                   insertbackground=self.t["entry_fg"])
        self.e_interest.insert(0, f"{interest_rate:.2f}")
        self.e_interest.pack(side="left")
        tk.Label(interest_frame, text="%  →  Total:",
                 font=get_font(9), bg=self.t["bg"], fg=self.t["fg_dim"]).pack(side="left", padx=(4, 4))
        self.e_total_lbl = tk.Label(interest_frame, text="",
                                    font=get_font(9, "bold"),
                                    bg=self.t["bg"], fg=self.t["fg"])
        self.e_total_lbl.pack(side="left")

        def _vcmd_interest(P):
            if P == "": return True
            if P.replace(".", "", 1).isdigit():
                try: return float(P) <= 100
                except ValueError: return False
            return False
        self.e_interest.config(validate="key", validatecommand=(form.register(_vcmd_interest), '%P'))

        def update_total(*_):
            try:
                total = calculate_total_with_interest(
                    float(self.e_amount.get() or 0),
                    float(self.e_interest.get() or 0))
                self.e_total_lbl.config(text=f"${format_number(total)}")
            except ValueError:
                self.e_total_lbl.config(text="—")
        self.e_amount.bind("<KeyRelease>", update_total)
        self.e_interest.bind("<KeyRelease>", update_total)
        update_total()

        lbl("Date", 4)
        try:
            parsed_date = datetime.strptime(date_val, '%Y-%m-%d').date()
        except ValueError:
            parsed_date = date.today()
        self.e_date = DateEntry(form, width=30,
                                background='darkblue', foreground='white',
                                borderwidth=1, date_pattern='yyyy-mm-dd',
                                font=get_input_font(10))
        self.e_date.set_date(parsed_date)
        self.e_date.grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=(8, 2))

        lbl("Notes", 5)
        self.e_notes = tk.Text(form, height=4, width=32,
                               font=get_input_font(10), relief="solid", bd=1,
                               bg=self.t["entry_bg"], fg=self.t["entry_fg"],
                               insertbackground=self.t["entry_fg"])
        self.e_notes.insert("1.0", notes or "")
        self.e_notes.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=(8, 2))

        lbl("Status", 6)
        self.e_status_var = tk.StringVar(value=status)
        sf = tk.Frame(form, bg=self.t["bg"])
        sf.grid(row=6, column=1, sticky="w", padx=(8, 0), pady=(8, 2))
        self._edit_btns = {}
        s_colors = {
            "Unpaid": {"active": "#e74c3c", "inactive": "#f07569"},
            "Paid":   {"active": "#27ae60", "inactive": "#7bd19e"},
        }
        def update_edit_btns():
            chosen = self.e_status_var.get()
            for val, btn in self._edit_btns.items():
                if val == chosen:
                    btn.config(bg=s_colors[val]["active"], fg="white",
                               relief="sunken", font=get_font(10, "bold"))
                else:
                    btn.config(bg=s_colors[val]["inactive"], fg="#555555",
                               relief="flat", font=get_font(10))
        for val, label in [("Unpaid", "Unpaid"), ("Paid", "Paid")]:
            b = tk.Button(sf, text=label, width=10, font=get_font(10),
                          relief="flat", padx=10, pady=6, cursor="hand2",
                          command=lambda v=val: [self.e_status_var.set(v), update_edit_btns()])
            b.pack(side="left", padx=(0, 8))
            self._edit_btns[val] = b
        update_edit_btns()
        form.columnconfigure(1, weight=1)

        btn_row = tk.Frame(self, bg=self.t["bg"])
        btn_row.pack(fill="x", padx=16, pady=12)
        tk.Button(btn_row, text="Save", command=self._save,
                  bg="#27ae60", fg="white", font=get_font(10, "bold"),
                  relief="flat", padx=14, pady=7, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="Cancel", command=self.destroy,
                  bg="#95a5a6", fg="white", font=get_font(10),
                  relief="flat", padx=14, pady=7, cursor="hand2").pack(side="left")

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _save(self):
        name         = self.e_name.get().strip()
        phone        = self.e_phone.get().strip()
        amount_str   = self.e_amount.get().strip().replace(",", "")
        interest_str = self.e_interest.get().strip()
        date_val     = self.e_date.get_date().strftime('%Y-%m-%d')
        notes        = self.e_notes.get("1.0", "end").strip()
        status       = self.e_status_var.get()

        if not name:
            messagebox.showwarning("Missing Info", "Name cannot be empty.", parent=self)
            return
        if not validate_name_chars(name):
            messagebox.showwarning("Invalid Name",
                "Name cannot contain special characters like: ! @ # $ % ^ & * ( ) = + [ ] { } | \\ ; : ' \" , < > ? /",
                parent=self)
            return
        if not validate_phone_chars(phone):
            messagebox.showwarning("Invalid Phone",
                "Phone number can only contain digits, spaces, +, -, ( and ).", parent=self)
            return
        try:
            amount = float(amount_str)
            if amount <= 0: raise ValueError
            if amount > 10000:
                messagebox.showwarning("Amount Too Large", "Maximum amount is $10,000.00", parent=self)
                return
        except ValueError:
            messagebox.showwarning("Invalid Amount",
                "Please enter a valid positive number (max $10,000).", parent=self)
            return
        try:
            interest_rate = float(interest_str) if interest_str else 0.0
            if not (0 <= interest_rate <= 100): raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Interest Rate",
                "Interest rate must be between 0 and 100.", parent=self)
            return

        db_update_record(self.record_id, name, phone, amount, interest_rate, date_val, notes, status)
        self.on_save()
        self.destroy()


# ---------- Main App ----------

class DebtTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # hide during setup to prevent flash
        self.title("Debt Tracker")
        self._dark_mode = False
        self.t          = THEMES["light"]

        self.date_format = get_saved_date_format()
        self.use_picker  = tk.BooleanVar(value=True)
        self._sort_col   = None
        self._sort_asc   = True

        self._header_widgets = set()
        self._apply_global_font()
        init_db()
        self._build_ui()
        self._apply_theme()
        self._refresh_table()

        w, h = 1500, 900
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(True, True)
        self.deiconify()  # show fully built window

    def _apply_global_font(self):
        import tkinter.font as tkfont
        for named in ("TkDefaultFont", "TkTextFont", "TkFixedFont",
                      "TkMenuFont", "TkHeadingFont", "TkCaptionFont",
                      "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
            try:
                tkfont.nametofont(named).configure(family=FONT_FACE, size=10)
            except Exception:
                pass
        style = ttk.Style()
        style.configure("Treeview",         font=(FONT_FACE, 11), rowheight=30)
        style.configure("Treeview.Heading", font=(FONT_FACE, 12, "bold"))

    def _toggle_dark_mode(self):
        self._dark_mode = not self._dark_mode
        self.t = THEMES["dark"] if self._dark_mode else THEMES["light"]
        self._apply_theme()
        self._refresh_table()

    def _apply_theme(self):
        t = self.t
        self.configure(bg=t["bg"])
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        rowheight=30, font=(FONT_FACE, 11),
                        background=t["tree_bg"], foreground=t["tree_fg"],
                        fieldbackground=t["tree_bg"],
                        bordercolor=t["tree_border"], borderwidth=1, relief="solid")
        style.configure("Treeview.Heading",
                        font=(FONT_FACE, 12, "bold"),
                        background=t["tree_head_bg"], foreground=t["tree_head_fg"],
                        bordercolor=t["tree_border"], relief="solid")
        style.map("Treeview",
                  background=[("selected", t["tree_sel_bg"])],
                  foreground=[("selected", t["tree_sel_fg"])])

        self.tree.tag_configure("unpaid_odd",  background=t["unpaid_odd"][0],  foreground=t["unpaid_odd"][1])
        self.tree.tag_configure("unpaid_even", background=t["unpaid_even"][0], foreground=t["unpaid_even"][1])
        self.tree.tag_configure("paid_odd",    background=t["paid_odd"][0],    foreground=t["paid_odd"][1])
        self.tree.tag_configure("paid_even",   background=t["paid_even"][0],   foreground=t["paid_even"][1])

        self.summary_lbl.config(bg=t["bg"], fg=t["summary_fg"])
        self.dark_btn.config(bg=t["toggle_btn"], fg="#ffffff",
                             text="Light Mode" if self._dark_mode else "Dark Mode")
        self._recolor_widgets(self)
        self._recolor_entries(self)

    def _recolor_widgets(self, widget):
        t = self.t
        cls = widget.__class__.__name__
        try:
            if cls in ("Frame", "LabelFrame"):
                widget.config(bg=t["bg"])
            elif cls == "Label":
                if widget.cget("bg") not in (t["header_bg"],):
                    widget.config(bg=t["bg"], fg=t["fg"])
            elif cls == "Checkbutton":
                widget.config(bg=t["bg"], fg=t["fg"],
                              activebackground=t["bg"], activeforeground=t["fg"],
                              selectcolor=t["bg2"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._recolor_widgets(child)

    def _recolor_entries(self, widget):
        t = self.t
        cls = widget.__class__.__name__
        try:
            if cls == "Entry":
                widget.config(bg=t["entry_bg"], fg=t["entry_fg"],
                              insertbackground=t["entry_fg"])
            elif cls == "Text":
                widget.config(bg=t["entry_bg"], fg=t["entry_fg"],
                              insertbackground=t["entry_fg"])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._recolor_entries(child)

    def _build_ui(self):
        t = self.t

        # Title bar
        title_frame = tk.Frame(self, bg=t["header_bg"], pady=10)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="Debt Tracker",
                 font=get_font(18, "bold"),
                 fg=t["header_fg"]).pack(side="left", padx=20)
        self.dark_btn = tk.Button(title_frame, text="Dark Mode",
                                  command=self._toggle_dark_mode,
                                  bg=t["toggle_btn"], fg="#ffffff",
                                  font=get_font(10, "bold"),
                                  relief="flat", padx=12, pady=4, cursor="hand2")
        self.dark_btn.pack(side="right", padx=8)

        # Body
        body = tk.Frame(self, bg=t["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=15)

        # ---- Left: form ----
        form_frame = tk.LabelFrame(body, text=" Add New Entry ",
                                   font=get_font(12, "bold"),
                                   bg=t["bg"], fg=t["fg"], padx=15, pady=10)
        form_frame.pack(side="left", fill="y", padx=(0, 15))

        self.entries = {}

        def field_label(text):
            tk.Label(form_frame, text=text, font=get_font(10),
                     bg=t["bg"], fg=t["fg"], anchor="w").pack(fill="x", pady=(8, 2))

        def field_entry(key, width=25):
            e = tk.Entry(form_frame, width=width, font=get_input_font(10),
                         relief="solid", bd=1,
                         bg=t["entry_bg"], fg=t["entry_fg"],
                         insertbackground=t["entry_fg"])
            e.pack(fill="x")
            self.entries[key] = e
            return e

        # Name
        field_label("Name")
        name_entry = field_entry("name")
        def _vcmd_name(P):
            return not any(ch in set('!@#$%^&*()=+[]{}|\\;:\'"<>?/') for ch in P)
        name_entry.config(validate="key", validatecommand=(form_frame.register(_vcmd_name), '%P'))

        # Phone
        field_label("Phone Number")
        phone_entry = field_entry("phone")
        def _vcmd_phone(P):
            return P == "" or bool(re.match(r'^[\d\s\+\-\(\)]*$', P))
        phone_entry.config(validate="key", validatecommand=(form_frame.register(_vcmd_phone), '%P'))

        # Amount
        field_label("Amount Owed ($) — Max $10,000")
        amount_entry = field_entry("amount")
        def _vcmd_amount(P):
            if P == "": return True
            if P.replace(".", "", 1).isdigit():
                try: return float(P) <= 10000
                except ValueError: return False
            return False
        amount_entry.config(validate="key", validatecommand=(form_frame.register(_vcmd_amount), '%P'))

        # Interest
        field_label("Interest Rate (%) — 0 = none")
        interest_row = tk.Frame(form_frame, bg=t["bg"])
        interest_row.pack(fill="x")
        interest_entry = tk.Entry(interest_row, width=10, font=get_input_font(10),
                                  relief="solid", bd=1,
                                  bg=t["entry_bg"], fg=t["entry_fg"],
                                  insertbackground=t["entry_fg"])
        interest_entry.insert(0, "0")
        interest_entry.pack(side="left")
        tk.Label(interest_row, text="%", font=get_font(10),
                 bg=t["bg"], fg=t["fg"]).pack(side="left", padx=(3, 8))
        self.total_preview_lbl = tk.Label(interest_row, text="Total: $0.00",
                                          font=get_font(9), bg=t["bg"], fg=t["fg_dim"])
        self.total_preview_lbl.pack(side="left")
        self.entries["interest"] = interest_entry

        def _vcmd_interest(P):
            if P == "": return True
            if P.replace(".", "", 1).isdigit():
                try: return float(P) <= 100
                except ValueError: return False
            return False
        interest_entry.config(validate="key", validatecommand=(form_frame.register(_vcmd_interest), '%P'))

        def update_preview(*_):
            try:
                a = float(amount_entry.get() or 0)
                r = float(interest_entry.get() or 0)
                total = calculate_total_with_interest(a, r)
                self.total_preview_lbl.config(
                    text=f"Total: ${format_number(total)}",
                    fg="#27ae60" if r > 0 else self.t["fg_dim"])
            except ValueError:
                self.total_preview_lbl.config(text="Total: —")
        amount_entry.bind("<KeyRelease>", update_preview)
        interest_entry.bind("<KeyRelease>", update_preview)

        # Date
        date_header = tk.Frame(form_frame, bg=t["bg"])
        date_header.pack(fill="x", pady=(8, 2))
        tk.Label(date_header, text="Date", font=get_font(10),
                 bg=t["bg"], fg=t["fg"], anchor="w").pack(side="left")
        self.format_label = tk.Label(date_header, text=f"({self.date_format})",
                                     font=get_font(8), bg=t["bg"], fg=t["fg_dim"])
        self.format_label.pack(side="right")

        self.date_container = tk.Frame(form_frame, bg=t["bg"])
        self.date_container.pack(fill="x")
        self.date_picker = DateEntry(self.date_container, width=26,
                                     background='darkblue', foreground='white',
                                     borderwidth=1, date_pattern=self.date_format,
                                     font=get_font(10))
        self.date_text = tk.Entry(self.date_container, width=28,
                                  font=get_input_font(10), relief="solid", bd=1,
                                  bg=t["entry_bg"], fg=t["entry_fg"],
                                  insertbackground=t["entry_fg"])
        self.date_text.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self._switch_date_input()

        toggle_frame = tk.Frame(form_frame, bg=t["bg"])
        toggle_frame.pack(fill="x", pady=(2, 0))
        tk.Checkbutton(toggle_frame, text="Use Date Picker",
                       variable=self.use_picker,
                       command=self._switch_date_input,
                       bg=t["bg"], fg=t["fg"],
                       activebackground=t["bg"], activeforeground=t["fg"],
                       selectcolor=t["bg2"],
                       font=get_font(9)).pack(anchor="w")

        # Notes
        field_label("Notes")
        notes_text = tk.Text(form_frame, height=4, width=28,
                             font=get_input_font(10), relief="solid", bd=1,
                             bg=t["entry_bg"], fg=t["entry_fg"],
                             insertbackground=t["entry_fg"])
        notes_text.pack(fill="x")
        self.entries["notes"] = notes_text

        # Status
        tk.Label(form_frame, text="Status", font=get_font(10),
                 bg=t["bg"], fg=t["fg"], anchor="w").pack(fill="x", pady=(10, 2))
        self.status_var = tk.StringVar(value="Unpaid")
        status_row = tk.Frame(form_frame, bg=t["bg"])
        status_row.pack(fill="x", pady=(0, 4))
        self._status_buttons = {}
        self._status_colors = {
            "Unpaid": {"active": "#e74c3c", "inactive": "#f5b7b1"},
            "Paid":   {"active": "#27ae60", "inactive": "#a9dfbf"},
        }
        def update_status_buttons():
            chosen = self.status_var.get()
            for val, btn in self._status_buttons.items():
                if val == chosen:
                    btn.config(bg=self._status_colors[val]["active"], fg="white",
                               relief="sunken", font=get_font(10, "bold"))
                else:
                    btn.config(bg=self._status_colors[val]["inactive"], fg="#555555",
                               relief="flat", font=get_font(10))
        self._update_status_buttons = update_status_buttons
        for val, label in [("Unpaid", "Unpaid"), ("Paid", "Paid")]:
            btn = tk.Button(status_row, text=label, width=10,
                            font=get_font(10), relief="flat",
                            padx=10, pady=6, cursor="hand2",
                            command=lambda v=val: [self.status_var.set(v), update_status_buttons()])
            btn.pack(side="left", padx=(0, 8))
            self._status_buttons[val] = btn
        update_status_buttons()

        # Add / Clear
        btn_frame = tk.Frame(form_frame, bg=t["bg"])
        btn_frame.pack(fill="x", pady=(15, 0))
        tk.Button(btn_frame, text="Add", command=self._add_record,
                  bg="#27ae60", fg="white", font=get_font(10, "bold"),
                  relief="flat", padx=10, pady=6, cursor="hand2",
                  width=10).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Clear", command=self._clear_form,
                  bg="#95a5a6", fg="white", font=get_font(10),
                  relief="flat", padx=10, pady=6, cursor="hand2",
                  width=10).pack(side="left")

        # ---- Right: table ----
        right_frame = tk.Frame(body, bg=t["bg"])
        right_frame.pack(side="left", fill="both", expand=True)

        table_frame = tk.LabelFrame(right_frame, text=" Records ",
                                    font=get_font(10, "bold"),
                                    bg=t["bg"], fg=t["fg"], padx=5, pady=5)
        table_frame.pack(fill="both", expand=True)

        # Controls bar
        ctrl_bar = tk.Frame(table_frame, bg=t["bg"])
        ctrl_bar.pack(fill="x", pady=(0, 6))
        tk.Label(ctrl_bar, text="🔍", bg=t["bg"], fg=t["fg"],
                 font=get_font(11)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_table())
        tk.Entry(ctrl_bar, textvariable=self.search_var,
                 font=get_input_font(10), relief="solid", bd=1,
                 width=20, bg=t["entry_bg"], fg=t["entry_fg"],
                 insertbackground=t["entry_fg"]).pack(side="left", padx=(4, 12))

        tk.Label(ctrl_bar, text="Sort by:", font=get_font(10),
                 bg=t["bg"], fg=t["fg"]).pack(side="left")
        self.sort_dir_var = tk.StringVar(value="↓ Descending (Z→A)")
        sort_dir_menu = ttk.Combobox(ctrl_bar, textvariable=self.sort_dir_var,
                                     values=["↑ Ascending (A→Z)", "↓ Descending (Z→A)"],
                                     width=18, state="readonly", font=get_font(10))
        sort_dir_menu.pack(side="left", padx=(0, 6))
        sort_dir_menu.bind("<<ComboboxSelected>>", lambda e: self._apply_sort())

        tk.Label(ctrl_bar, text="Filter:", font=get_font(10),
                 bg=t["bg"], fg=t["fg"]).pack(side="left", padx=(6, 0))
        self.filter_var = tk.StringVar(value="All")
        filter_menu = ttk.Combobox(ctrl_bar, textvariable=self.filter_var,
                                   values=["All", "Unpaid", "Paid"],
                                   width=12, state="readonly", font=get_font(10))
        filter_menu.pack(side="left", padx=(4, 0))
        filter_menu.bind("<<ComboboxSelected>>", lambda e: self._refresh_table())

        # Summary
        self.summary_var = tk.StringVar()
        self.summary_lbl = tk.Label(table_frame, textvariable=self.summary_var,
                                    font=get_font(10, "bold"),
                                    bg=t["bg"], fg=t["summary_fg"])
        self.summary_lbl.pack(anchor="e", padx=5)

        # Treeview
        cols = ("ID", "Name", "Phone", "Amount", "Interest", "Total", "Date", "Notes", "Status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
        col_cfg = {
            "ID":       (40,  "center"),
            "Name":     (110, "w"),
            "Phone":    (100, "center"),
            "Amount":   (90,  "e"),
            "Interest": (75,  "center"),
            "Total":    (95,  "e"),
            "Date":     (90,  "center"),
            "Notes":    (130, "w"),
            "Status":   (90,  "center"),
        }
        for c, (w, anchor) in col_cfg.items():
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=anchor, minwidth=w)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._edit_record())

        # Action buttons
        action_frame = tk.Frame(self, bg=t["bg"])
        action_frame.pack(pady=(0, 12))
        for text, cmd, color in [
            ("Edit Selected",   self._edit_record,   "#8e44ad"),
            ("Mark as Paid",    self._mark_paid,     "#2980b9"),
            ("Mark as Unpaid",  self._mark_unpaid,   "#f39c12"),
            ("Delete Selected", self._delete_record, "#e74c3c"),
        ]:
            tk.Button(action_frame, text=text, command=cmd,
                      bg=color, fg="white", font=get_font(10),
                      relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=8)

        self._setup_navigation()

    def _apply_sort(self):
        self._sort_col = "name"
        self._sort_asc = self.sort_dir_var.get() == "↑ Ascending (A→Z)"
        self._refresh_table()

    def _switch_date_input(self):
        for widget in self.date_container.winfo_children():
            widget.pack_forget()
        if self.use_picker.get():
            self.date_picker.pack(fill="x")
            self.entries["date"] = self.date_picker
        else:
            self.date_text.pack(fill="x")
            self.entries["date"] = self.date_text

    def _setup_navigation(self):
        self.entries["name"].bind("<Return>",     lambda e: self.entries["phone"].focus())
        self.entries["phone"].bind("<Return>",    lambda e: self.entries["amount"].focus())
        self.entries["amount"].bind("<Return>",   lambda e: self.entries["interest"].focus())
        self.entries["interest"].bind("<Return>", lambda e: self._focus_date())

        def date_to_notes(e):
            if not self.use_picker.get():
                date_str = self.date_text.get().strip()
                if date_str:
                    detected = detect_date_format(date_str)
                    if detected and detected != self.date_format:
                        self.date_format = detected
                        save_date_format(detected)
                        self.format_label.config(text=f"({self.date_format})")
            self.entries["notes"].focus()

        self.date_picker.bind("<Return>", date_to_notes)
        self.date_text.bind("<Return>",   date_to_notes)

        def notes_enter(e):
            if e.state & 0x4:
                self._add_record()
                return "break"
        self.entries["notes"].bind("<Control-Return>", notes_enter)

    def _focus_date(self):
        if self.use_picker.get():
            self.date_picker.focus()
        else:
            self.date_text.focus()

    def _get_field(self, key):
        widget = self.entries[key]
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end").strip()
        elif isinstance(widget, DateEntry):
            return widget.get_date().strftime('%Y-%m-%d')
        return widget.get().strip()

    def _clear_form(self):
        for key, widget in self.entries.items():
            if isinstance(widget, tk.Text):
                widget.delete("1.0", "end")
            elif isinstance(widget, DateEntry):
                widget.set_date(date.today())
            else:
                widget.delete(0, "end")
                if key == "date":
                    widget.insert(0, datetime.now().strftime('%Y-%m-%d'))
                if key == "interest":
                    widget.insert(0, "0")
        self.status_var.set("Unpaid")
        self._update_status_buttons()
        self.total_preview_lbl.config(text="Total: $0.00", fg=self.t["fg_dim"])
        self.entries["name"].focus()

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        query      = self.search_var.get().strip() if hasattr(self, "search_var") else ""
        filter_val = self.filter_var.get()         if hasattr(self, "filter_var")  else "All"

        rows = db_search(query) if query else db_all()
        if filter_val in ("Paid", "Unpaid"):
            rows = [r for r in rows if r[7] == filter_val]

        if self._sort_col:
            rows = sorted(rows, key=lambda r: r[1].lower(), reverse=not self._sort_asc)

        for i, r in enumerate(rows):
            rid, name, phone, amount, interest_rate, d, notes, status = r
            total  = calculate_total_with_interest(amount, interest_rate)
            stripe = "odd" if i % 2 == 0 else "even"
            tag    = f"{'paid' if status == 'Paid' else 'unpaid'}_{stripe}"
            status_display = "🟢  Paid" if status == "Paid" else "🔴  Unpaid"
            self.tree.insert("", "end", iid=str(rid),
                             values=(rid, name, phone or "",
                                     f"${format_number(amount)}",
                                     f"{interest_rate:.1f}%",
                                     f"${format_number(total)}",
                                     d, notes or "", status_display),
                             tags=(tag,))

        total_unpaid = db_total_unpaid()
        self.summary_var.set(
            f"{len(rows)} record(s)   |   Total Unpaid: ${format_number(total_unpaid)}")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select a record first.")
            return None
        return int(sel[0])

    def _edit_record(self):
        rid = self._selected_id()
        if rid is None: return
        EditDialog(self, rid, on_save=self._refresh_table, theme=self.t)

    def _add_record(self):
        name         = self._get_field("name")
        phone        = self._get_field("phone")
        amount_str   = self._get_field("amount")
        interest_str = self._get_field("interest")
        date_val     = self._get_field("date")
        notes        = self._get_field("notes")
        status       = self.status_var.get()

        if not name:
            messagebox.showwarning("Missing Info", "Please enter a name.")
            self.entries["name"].focus()
            return
        if not validate_name_chars(name):
            messagebox.showwarning("Invalid Name",
                "Name cannot contain special characters like: ! @ # $ % ^ & * ( ) = + [ ] { } | \\ ; : ' \" , < > ? /")
            self.entries["name"].focus()
            return
        if not validate_phone_chars(phone):
            messagebox.showwarning("Invalid Phone",
                "Phone number can only contain digits, spaces, +, -, ( and ).")
            self.entries["phone"].focus()
            return
        try:
            amount = float(amount_str.replace(",", ""))
            if amount <= 0: raise ValueError
            if amount > 10000:
                messagebox.showwarning("Amount Too Large", "Maximum amount is $10,000.00")
                self.entries["amount"].focus()
                return
        except ValueError:
            messagebox.showwarning("Invalid Amount",
                "Please enter a valid positive number (max $10,000).")
            self.entries["amount"].focus()
            return
        try:
            interest_rate = float(interest_str) if interest_str else 0.0
            if not (0 <= interest_rate <= 100): raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Interest Rate",
                "Interest rate must be between 0 and 100.")
            self.entries["interest"].focus()
            return
        if not self.use_picker.get():
            detected = detect_date_format(date_val)
            if detected:
                date_val = detected
                if detected != self.date_format:
                    self.date_format = detected
                    save_date_format(detected)
                    self.format_label.config(text=f"({self.date_format})")
            else:
                messagebox.showwarning("Invalid Date",
                    f"Please use a recognised date format, e.g. {self.date_format}")
                self._focus_date()
                return

        db_add(name, phone, amount, interest_rate, date_val, notes, status)
        self._refresh_table()
        self._clear_form()

    def _mark_paid(self):
        rid = self._selected_id()
        if rid is None: return
        db_update_status(rid, "Paid")
        self._refresh_table()

    def _mark_unpaid(self):
        rid = self._selected_id()
        if rid is None: return
        db_update_status(rid, "Unpaid")
        self._refresh_table()

    def _delete_record(self):
        rid = self._selected_id()
        if rid is None: return
        name = self.tree.set(str(rid), "Name")
        if messagebox.askyesno("Confirm Delete", f"Delete record for '{name}'?"):
            db_delete(rid)
            self._refresh_table()


if __name__ == "__main__":
    app = DebtTrackerApp()
    app.mainloop()