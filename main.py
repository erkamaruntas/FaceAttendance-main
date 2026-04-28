print("--- PROGRAM BAŞLATILIYOR 1/5: Kütüphaneler Yükleniyor... ---")
import customtkinter as ctk
import cv2
import face_recognition
import os
import pandas as pd
from datetime import datetime
from PIL import Image, ImageTk
import numpy as np
from tkinter import filedialog
import threading 

print("--- PROGRAM BAŞLATILIYOR 2/5: Ayarlar Yapılıyor... ---")

# --- MODERN AYARLAR ---
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("dark-blue") 

RENK_MENU = "#1e2129"
RENK_ANA = "#282c34"
RENK_KART = "#323642"
RENK_ACCENT = "#3B8ED0"
RENK_SIL = "#CF6679"
RENK_TURUNCU = "#FFA500" # Arayüz için turuncu
FONT_BASLIK = ("Roboto", 24, "bold")

class YoklamaSistemi(ctk.CTk):
    def __init__(self):
        super().__init__()
        print("--- PROGRAM BAŞLATILIYOR 3/5: Arayüz Çiziliyor... ---")

        self.title("FaceAttendance Pro - Modern Yoklama Sistemi")
        self.geometry("1200x850") # Biraz daha uzun yaptık (isim listesi için)
        self.configure(fg_color=RENK_ANA)

        if not os.path.exists("ogrenci_yuzleri"):
            os.makedirs("ogrenci_yuzleri")
        
        self.dosya_adi = f"yoklama_{datetime.now().strftime('%Y-%m-%d')}.csv"
        self.known_face_encodings = []
        self.known_face_names = []
        self.kamera_aktif = False

        self.arayuzu_olustur()
        self.after(1000, self.baslangic_yuklemeleri)

    def arayuzu_olustur(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SOL MENÜ
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=RENK_MENU)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FACE\nATTENDANCE", 
                                     font=("Montserrat", 26, "bold"), text_color="white")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 30))

        self.menu_butonu_olustur("Canlı Yoklama", self.sekme_yoklama, 1)
        self.menu_butonu_olustur("Öğrenci Yönetimi", self.sekme_kayit, 2)
        self.menu_butonu_olustur("Geçmiş & Rapor", self.sekme_liste, 3)

        ctk.CTkLabel(self.sidebar_frame, text="v2.3 Final", text_color="gray").grid(row=6, column=0, pady=20)

        # 2. ANA İÇERİK
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color=RENK_ANA)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.lbl_yukleniyor = ctk.CTkLabel(self.main_frame, text="Sistem Başlatılıyor...\nLütfen Bekleyiniz...", font=FONT_BASLIK)
        self.lbl_yukleniyor.pack(expand=True)

    def baslangic_yuklemeleri(self):
        print("--- PROGRAM BAŞLATILIYOR 4/5: Yüzler Yükleniyor... ---")
        self.yuzleri_yukle()
        print("--- PROGRAM BAŞLATILIYOR 5/5: Kamera Açılıyor... ---")
        self.sekme_yoklama()

    def menu_butonu_olustur(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar_frame, text=f"{text}", command=command, 
                            height=50, corner_radius=10, fg_color="transparent", border_width=2,
                            border_color=RENK_KART, hover_color=RENK_ACCENT, 
                            font=("Roboto", 15, "bold"), anchor="w")
        btn.grid(row=row, column=0, padx=20, pady=10, sticky="ew")

    def yuzleri_yukle(self):
        try:
            self.known_face_encodings = []
            self.known_face_names = []
            klasor = "ogrenci_yuzleri"
            images = os.listdir(klasor)
            for image_name in images:
                if image_name.endswith(('.jpg', '.png', '.jpeg')):
                    img_path = os.path.join(klasor, image_name)
                    image = face_recognition.load_image_file(img_path)
                    encodings = face_recognition.face_encodings(image)
                    if len(encodings) > 0:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_names.append(os.path.splitext(image_name)[0])
            print(f"Yüz yükleme tamamlandı: {len(self.known_face_names)} kişi.")
        except Exception as e:
            print(f"HATA (Yüz Yükleme): {e}")

    def temizle_ekran(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.kamera_aktif = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

    def sekme_yoklama(self):
        self.temizle_ekran()
        
        header = ctk.CTkFrame(self.main_frame, fg_color=RENK_KART, corner_radius=15, height=60)
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Canlı Yoklama Sistemi", font=FONT_BASLIK).pack(side="left", padx=20, pady=15)
        
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True)

        self.lbl_kamera = ctk.CTkLabel(content, text="Kamera Başlatılıyor...", fg_color="black", corner_radius=15)
        self.lbl_kamera.pack(pady=10, expand=True)

        # --- YENİ EKLENTİ: CANLI İSİM LİSTESİ ---
        # Kameranın altına, o an algılanan isimleri yazacağımız alan
        self.frame_isimler = ctk.CTkFrame(content, fg_color=RENK_KART, corner_radius=10)
        self.frame_isimler.pack(fill="x", padx=50, pady=(0, 10))
        
        self.lbl_kisiler_baslik = ctk.CTkLabel(self.frame_isimler, text="KAMERADAKİ KİŞİLER:", 
                                               font=("Roboto", 14, "bold"), text_color="gray")
        self.lbl_kisiler_baslik.pack(pady=(5,0))

        self.lbl_kisiler = ctk.CTkLabel(self.frame_isimler, text="...", 
                                        font=("Roboto", 24, "bold"), text_color=RENK_TURUNCU)
        self.lbl_kisiler.pack(pady=(0, 10))

        # Durum Çubuğu (En altta)
        self.lbl_durum = ctk.CTkLabel(content, text="Sistem Hazır", font=("Roboto", 14), text_color="#4CAF50")
        self.lbl_durum.pack(pady=5)

        self.kamera_aktif = True
        self.cap = cv2.VideoCapture(0)
        self.video_dongusu()

    def video_dongusu(self):
        if self.kamera_aktif and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.lbl_kamera.configure(text="") # Yazıyı temizle

                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                # O anki karede görülen isimleri tutacak liste
                anlik_gorum_isimleri = []

                for face_encoding, face_loc in zip(face_encodings, face_locations):
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
                    name = "Tanimsiz"
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = self.known_face_names[best_match_index]
                            self.yoklamaya_yaz(name)

                    # Listeye ekle (Tekrarları önlemek için en sonda set yapacağız)
                    if name != "Tanimsiz":
                        anlik_gorum_isimleri.append(name)

                    top, right, bottom, left = face_loc
                    top *= 4; right *= 4; bottom *= 4; left *= 4
                    color = (0, 255, 0) if name != "Tanimsiz" else (0, 0, 255)
                    
                    # Kare çiz
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    
                    # İsim Yazısı Ayarları
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.9
                    thickness = 2
                    (w, h), _ = cv2.getTextSize(name, font, font_scale, thickness)
                    
                    text_x = left + (right - left) // 2 - (w // 2)

                    # Arka plan kutusu (Siyah yapalım ki turuncu belli olsun)
                    cv2.rectangle(frame, (text_x - 5, bottom - 35), (text_x + w + 5, bottom), (0, 0, 0), cv2.FILLED)
                    
                    # --- DEĞİŞİKLİK: YAZI RENGİ TURUNCU (BGR: 0, 140, 255) ---
                    cv2.putText(frame, name, (text_x, bottom - 10), font, font_scale, (0, 140, 255), thickness)

                # --- ARAYÜZ GÜNCELLEME: İSİMLERİ YAZDIR ---
                if len(anlik_gorum_isimleri) > 0:
                    # set() ile aynı ismi iki kere yazmayı engelliyoruz
                    isimler_str = ", ".join(list(set(anlik_gorum_isimleri)))
                    self.lbl_kisiler.configure(text=isimler_str)
                else:
                    self.lbl_kisiler.configure(text="Kimse Görünmüyor")

                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(720, 540))
                self.lbl_kamera.configure(image=imgtk)
                self.lbl_kamera.image = imgtk
            
            self.after(20, self.video_dongusu)

    def yoklamaya_yaz(self, isim):
        zaman = datetime.now().strftime('%H:%M:%S')
        tarih = datetime.now().strftime('%Y-%m-%d')
        dosya_adi = f"yoklama_{tarih}.csv"
        
        if not os.path.isfile(dosya_adi):
            df = pd.DataFrame(columns=["Isim", "Tarih", "Saat"])
            df.to_csv(dosya_adi, index=False)
        
        df = pd.read_csv(dosya_adi)
        if not ((df['Isim'] == isim) & (df['Tarih'] == tarih)).any():
            yeni_veri = pd.DataFrame({"Isim": [isim], "Tarih": [tarih], "Saat": [zaman]})
            df = pd.concat([df, yeni_veri], ignore_index=True)
            df.to_csv(dosya_adi, index=False)
            self.lbl_durum.configure(text=f"✅ {isim} yoklaması alındı ({zaman})", text_color="#66BB6A")

    def sekme_kayit(self):
        self.temizle_ekran()
        ctk.CTkLabel(self.main_frame, text="Öğrenci Kayıt Yönetimi", font=FONT_BASLIK).pack(pady=20, anchor="w")
        grid_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)

        left_col = ctk.CTkFrame(grid_frame, fg_color=RENK_KART, corner_radius=15)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_col, text="Yeni Kayıt Oluştur", font=("Roboto", 18, "bold")).pack(pady=20)
        self.entry_isim = ctk.CTkEntry(left_col, placeholder_text="Ad Soyad Giriniz", width=300, height=40)
        self.entry_isim.pack(pady=10)

        btn_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Kameradan Çek", command=self.fotograf_cek_kaydet, 
                      fg_color="#E67E22", hover_color="#D35400", width=140).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="Dosya Yükle", command=self.dosyadan_yukle, 
                      fg_color="#2980B9", hover_color="#2471A3", width=140).grid(row=0, column=1, padx=5)

        self.lbl_kayit_durum = ctk.CTkLabel(left_col, text="", font=("Roboto", 14))
        self.lbl_kayit_durum.pack(pady=10)

        ctk.CTkLabel(left_col, text="Kayıtlı Öğrenciler", font=("Roboto", 16, "bold")).pack(pady=(30, 10))
        self.liste_frame_ogrenci = ctk.CTkScrollableFrame(left_col, height=200, fg_color=RENK_ANA)
        self.liste_frame_ogrenci.pack(fill="x", padx=20, pady=10)
        self.ogrenci_listesini_guncelle()

        right_col = ctk.CTkFrame(grid_frame, fg_color=RENK_KART, corner_radius=15)
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(right_col, text="Kamera Önizleme", font=("Roboto", 16)).pack(pady=10)
        self.lbl_kayit_kamera = ctk.CTkLabel(right_col, text="")
        self.lbl_kayit_kamera.pack(expand=True)

        self.kamera_aktif = True
        self.cap = cv2.VideoCapture(0)
        self.kayit_video_dongusu()

    def kayit_video_dongusu(self):
        if self.kamera_aktif and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)
                imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 300))
                self.lbl_kayit_kamera.configure(image=imgtk)
                self.lbl_kayit_kamera.image = imgtk
                self.frame_cache = frame
            self.after(20, self.kayit_video_dongusu)

    def dosyadan_yukle(self):
        isim = self.entry_isim.get()
        if isim == "":
            self.lbl_kayit_durum.configure(text="⚠ Önce isim giriniz!", text_color="orange")
            return
        dosya_yolu = filedialog.askopenfilename(filetypes=[("Resim Dosyaları", "*.jpg *.png *.jpeg")])
        if dosya_yolu:
            try:
                image = face_recognition.load_image_file(dosya_yolu)
                face_locations = face_recognition.face_locations(image)
                if len(face_locations) == 0:
                    self.lbl_kayit_durum.configure(text="❌ Seçilen fotoğrafta yüz bulunamadı!", text_color="red")
                    return
                hedef_yol = f"ogrenci_yuzleri/{isim}.jpg"
                pil_image = Image.open(dosya_yolu).convert('RGB')
                pil_image.save(hedef_yol)
                self.lbl_kayit_durum.configure(text=f"✅ {isim} dosyadan yüklendi.", text_color="green")
                self.yuzleri_yukle()
                self.ogrenci_listesini_guncelle()
            except Exception as e:
                self.lbl_kayit_durum.configure(text=f"Hata: {e}", text_color="red")

    def fotograf_cek_kaydet(self):
        isim = self.entry_isim.get()
        if isim == "":
            self.lbl_kayit_durum.configure(text="⚠ Lütfen isim girin!", text_color="orange")
            return
        if hasattr(self, 'frame_cache'):
            rgb_frame = cv2.cvtColor(self.frame_cache, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb_frame)
            if len(boxes) == 0:
                self.lbl_kayit_durum.configure(text="❌ Yüz bulunamadı!", text_color="red")
            elif len(boxes) > 1:
                self.lbl_kayit_durum.configure(text="⚠ Birden fazla yüz var!", text_color="orange")
            else:
                dosya_yolu = f"ogrenci_yuzleri/{isim}.jpg"
                cv2.imwrite(dosya_yolu, self.frame_cache)
                self.lbl_kayit_durum.configure(text=f"✅ {isim} kaydedildi.", text_color="green")
                self.yuzleri_yukle()
                self.ogrenci_listesini_guncelle()

    def ogrenci_listesini_guncelle(self):
        for widget in self.liste_frame_ogrenci.winfo_children():
            widget.destroy()
        klasor = "ogrenci_yuzleri"
        if not os.path.exists(klasor): return
        dosyalar = [f for f in os.listdir(klasor) if f.endswith(('.jpg', '.png'))]
        for i, dosya in enumerate(dosyalar):
            isim = os.path.splitext(dosya)[0]
            satir = ctk.CTkFrame(self.liste_frame_ogrenci, fg_color=RENK_ANA)
            satir.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(satir, text=isim, font=("Roboto", 14)).pack(side="left", padx=10)
            ctk.CTkButton(satir, text="Sil", width=50, fg_color=RENK_SIL, hover_color="#B71C1C", height=30,
                          command=lambda d=dosya: self.ogrenci_sil(d)).pack(side="right", padx=5, pady=5)

    def ogrenci_sil(self, dosya_adi):
        try:
            os.remove(f"ogrenci_yuzleri/{dosya_adi}")
            self.yuzleri_yukle()
            self.ogrenci_listesini_guncelle()
            self.lbl_kayit_durum.configure(text=f"🗑 {dosya_adi} silindi.", text_color="orange")
        except Exception as e:
            self.lbl_kayit_durum.configure(text=f"Hata: {e}", text_color="red")

    def sekme_liste(self):
        self.temizle_ekran()
        top_bar = ctk.CTkFrame(self.main_frame, fg_color=RENK_KART, height=80, corner_radius=15)
        top_bar.pack(fill="x", pady=20)
        ctk.CTkLabel(top_bar, text="Detaylı Yoklama Raporu", font=("Roboto", 20, "bold")).pack(side="left", padx=20)
        filter_area = ctk.CTkFrame(top_bar, fg_color="transparent")
        filter_area.pack(side="right", padx=20)
        bugun = datetime.now().strftime('%Y-%m-%d')
        self.entry_tarih = ctk.CTkEntry(filter_area, placeholder_text="YYYY-AA-GG", width=120)
        self.entry_tarih.insert(0, bugun)
        self.entry_tarih.pack(side="left", padx=5)
        self.entry_ara = ctk.CTkEntry(filter_area, placeholder_text="İsim Ara...", width=150)
        self.entry_ara.pack(side="left", padx=5)
        ctk.CTkButton(filter_area, text="Filtrele", width=80, command=self.listeyi_guncelle).pack(side="left", padx=5)
        self.tablo_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=RENK_KART, corner_radius=15)
        self.tablo_frame.pack(fill="both", expand=True)
        self.listeyi_guncelle()

    def listeyi_guncelle(self):
        for widget in self.tablo_frame.winfo_children():
            widget.destroy()
        secilen_tarih = self.entry_tarih.get()
        aranan_isim = self.entry_ara.get().lower()
        dosya_yolu = f"yoklama_{secilen_tarih}.csv"
        if not os.path.exists(dosya_yolu):
            ctk.CTkLabel(self.tablo_frame, text=f"⚠ {secilen_tarih} tarihinde kayıt bulunamadı.", 
                         font=("Roboto", 16)).pack(pady=20)
            return
        df = pd.read_csv(dosya_yolu)
        headers = ctk.CTkFrame(self.tablo_frame, fg_color=RENK_ANA, height=40)
        headers.pack(fill="x", pady=5)
        columns = ["Öğrenci Adı", "Tarih", "Saat", "İşlem"]
        for col in columns:
            ctk.CTkLabel(headers, text=col, font=("Roboto", 14, "bold"), width=150).pack(side="left", padx=10)
        satir_var_mi = False
        for index, row in df.iterrows():
            if aranan_isim == "" or aranan_isim in str(row['Isim']).lower():
                satir_var_mi = True
                row_frame = ctk.CTkFrame(self.tablo_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)
                ctk.CTkLabel(row_frame, text=row['Isim'], width=150).pack(side="left", padx=10)
                ctk.CTkLabel(row_frame, text=row['Tarih'], width=150).pack(side="left", padx=10)
                ctk.CTkLabel(row_frame, text=row['Saat'], width=150).pack(side="left", padx=10)
                ctk.CTkButton(row_frame, text="Sil", width=60, fg_color=RENK_SIL, hover_color="#B71C1C", height=25,
                              command=lambda i=index, d=dosya_yolu: self.yoklama_sil(i, d)).pack(side="left", padx=20)
        if not satir_var_mi:
            ctk.CTkLabel(self.tablo_frame, text="Kriterlere uygun kayıt bulunamadı.").pack(pady=20)

    def yoklama_sil(self, index, dosya_yolu):
        if os.path.exists(dosya_yolu):
            df = pd.read_csv(dosya_yolu)
            df = df.drop(index)
            df.to_csv(dosya_yolu, index=False)
            self.listeyi_guncelle()

if __name__ == "__main__":
    print("--- PROGRAM BAŞLATILIYOR... ---")
    app = YoklamaSistemi()
    app.mainloop()