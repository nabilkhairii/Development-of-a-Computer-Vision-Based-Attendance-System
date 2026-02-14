import tkinter as tk
from tkinter import font, ttk
import cv2
from PIL import Image, ImageTk
from datetime import datetime
import mysql.connector
import os

class AttendanceSystem:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry('1950x1100')
        self.window.title('Sistem Presensi')

        # Initialize camera
        self.vid = cv2.VideoCapture(0)

        self.notif1 = tk.StringVar()
        self.current_frame = None
        self.captured_photo = None

        # Database configuration (SAFE VERSION)
        self.db_config = {
            'user': os.getenv('DB_USER', 'your_username'),
            'password': os.getenv('DB_PASSWORD', 'your_password'),
            'host': '127.0.0.1',
            'database': 'your_database',
            'raise_on_warnings': True
        }

        self.class_options = [
            "Pemrograman Komputer",
            "Praktik Instrumentasi",
            "Praktik Sistem Kendali",
            "Praktik Elektronika Daya",
            "Bahasa Inggris Komunikasi",
            "Praktik Microprocesor"
        ]

        self.title_font = font.Font(weight="bold", size=12)
        self.regular_font = font.Font(size=11)
        self.bold_font = font.Font(weight="bold", size=11)

        self.setup_ui()

    def setup_ui(self):
        self.header_frame = tk.Frame(self.window, bg='#A9A9A9')
        self.header_frame.place(x=0, y=0, width=1950, height=160)

        self.content_frame = tk.Frame(self.window, bg='#000080')
        self.content_frame.place(x=0, y=165, width=1950, height=900)

        self.setup_camera_section()
        self.setup_info_section()

    def setup_camera_section(self):
        camera_frame = tk.Frame(self.content_frame, bg='#000080')
        camera_frame.place(x=420, y=90, width=650, height=650)

        self.canvas = tk.Canvas(camera_frame, width=613, height=650, bg='#000080')
        self.canvas.pack()

    def setup_info_section(self):
        info_panel = tk.Frame(self.content_frame, bd=5, relief=tk.GROOVE, bg='#FFFAF0')
        info_panel.place(x=1050, y=90, width=450, height=650)

        self.time_label = tk.Label(info_panel, font=self.bold_font, bg='#FFFAF0')
        self.time_label.pack(pady=10)

        self.date_label = tk.Label(info_panel, font=self.bold_font, bg='#FFFAF0')
        self.date_label.pack(pady=5)

        tk.Label(info_panel, text="Masukkan NIM:", font=self.regular_font, bg='#FFFAF0').pack()
        self.entry = tk.Entry(info_panel, width=25, font=self.regular_font)
        self.entry.pack(pady=10)

        tk.Label(info_panel, text="Pilih Kelas:", font=self.regular_font, bg='#FFFAF0').pack()
        self.class_var = tk.StringVar()
        self.class_dropdown = ttk.Combobox(info_panel, textvariable=self.class_var,
                                          values=self.class_options, state="readonly")
        self.class_dropdown.pack(pady=10)
        self.class_dropdown.set(self.class_options[0])

        self.presensi_button = tk.Button(info_panel, text="Presensi",
                                         width=20, height=2,
                                         command=self.process_attendance)
        self.presensi_button.pack(pady=15)

        self.photo_canvas = tk.Canvas(info_panel, width=150, height=150, bg='#FFFAF0')
        self.photo_canvas.pack(pady=10)

        self.label_notif1 = tk.Label(info_panel, textvariable=self.notif1,
                                     font=self.regular_font, bg='#FFFAF0',
                                     wraplength=300, justify='center')
        self.label_notif1.pack()

    def update_clock(self):
        now = datetime.now()
        self.time_label.config(text=f"Waktu: {now.strftime('%H:%M:%S')}")
        self.date_label.config(text=f"Tanggal: {now.strftime('%d-%m-%Y')}")
        self.window.after(1000, self.update_clock)

    def capture_photo(self):
        if self.current_frame is not None:
            filename = f"capture_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            frame = cv2.flip(self.current_frame, 1)
            crop = frame[60:470, 160:470]
            cv2.imwrite(filename, crop)

            img = Image.open(filename).resize((150,150), Image.Resampling.LANCZOS)
            self.captured_photo = ImageTk.PhotoImage(img)
            self.photo_canvas.create_image(0,0,image=self.captured_photo,anchor=tk.NW)

            return filename
        return None

    def process_attendance(self):
        nim = self.entry.get()
        kelas = self.class_var.get()

        if not nim.isnumeric():
            self.notif1.set("NIM tidak valid")
            return

        try:
            cnx = mysql.connector.connect(**self.db_config)
            cursor = cnx.cursor()

            query = "SELECT nama FROM tb_member WHERE id_nim = %s"
            cursor.execute(query, (nim,))
            result = cursor.fetchone()

            if not result:
                self.notif1.set("Data mahasiswa tidak ditemukan")
                return

            self.capture_photo()
            now = datetime.now()

            self.notif1.set(
                f"Presensi Berhasil\n"
                f"Nama: {result[0]}\n"
                f"NIM: {nim}\n"
                f"Kelas: {kelas}\n"
                f"Jam: {now.strftime('%H:%M:%S')}\n"
                f"Tanggal: {now.strftime('%d-%m-%Y')}"
            )

            cursor.close()
            cnx.close()

        except mysql.connector.Error as err:
            self.notif1.set("Database Error")

    def update_camera(self):
        ret, frame = self.vid.read()
        if ret:
            self.current_frame = frame
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (613, 650))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=img, anchor=tk.NW)
            self.canvas.image = img

        self.window.after(10, self.update_camera)

    def run(self):
        self.update_clock()
        self.update_camera()
        self.window.mainloop()


if __name__ == "__main__":
    AttendanceSystem().run()