#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pandas as pd
import random
import os
import webbrowser
import tempfile
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent / "sportsfestival_data.csv"
LOGG_FILE = Path(__file__).parent / "sportsfestival_logg.csv"

KATEGORIER = ["Elev", "நிர்வாகம்", "Lærer", "Frivillig", "Gjest"]
LAG_A = "Lag Rød"
LAG_B = "Lag Gul"

BG_COLOR = "#0F0F13"
PANEL_COLOR = "#1C1C23"
ACCENT_COLOR = "#6C5CE7"
ACCENT_HOVER = "#5A4BCC"
SUCCESS_COLOR = "#00B894"
DANGER_COLOR = "#D63031"
TEXT_COLOR = "#DFDFE5"

class DataManager:
    def __init__(self):
        self.kolonner = ["ID", "Navn", "Kategori", "Kull", "Lag"]
        self.logg_kolonner = ["Tidspunkt", "Handling", "Detaljer"]
        self.df = self.last_inn()
        self.logg_df = self.last_inn_logg()

    def last_inn(self):
        if DATA_FILE.exists():
            try:
                df = pd.read_csv(DATA_FILE, encoding="utf-8-sig", dtype=str)
                if not df.empty and "ID" in df.columns:
                    return df.fillna("")
            except Exception as e:
                print(f"Lese-feil ved oppstart: {e}")
        return pd.DataFrame(columns=self.kolonner)

    def last_inn_logg(self):
        if LOGG_FILE.exists():
            try:
                df = pd.read_csv(LOGG_FILE, encoding="utf-8-sig", dtype=str)
                if not df.empty:
                    return df.fillna("")
            except Exception as e:
                print(f"Logg-lese-feil: {e}")
        return pd.DataFrame(columns=self.logg_kolonner)

    def lagre(self):
        try:
            self.df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            return True
        except PermissionError:
            messagebox.showerror("Feil", f"Lukk {DATA_FILE.name} i Excel for å lagre.")
            return False

    def lagre_logg(self):
        try:
            self.logg_df.to_csv(LOGG_FILE, index=False, encoding="utf-8-sig")
        except PermissionError:
            pass

    def loggfor(self, handling, detaljer):
        tid = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ny_rad = pd.DataFrame([[tid, handling, detaljer]], columns=self.logg_kolonner)
        self.logg_df = pd.concat([ny_rad, self.logg_df], ignore_index=True)
        self.lagre_logg()

    def finn_ledig_id(self):
        eksisterende = []
        for val in self.df["ID"]:
            try:
                eksisterende.append(int(val))
            except ValueError:
                pass
        
        ny_id = 1
        while ny_id in eksisterende and ny_id < 100:
            ny_id += 1
            
        return ny_id

    def legg_til(self, navn, kategori, kull):
        ny_id_num = self.finn_ledig_id()
        if ny_id_num > 99:
            messagebox.showerror("Fullt", "Maksimalt antall deltakere (99) er nådd!")
            return False
            
        ny_id = f"{ny_id_num:02d}"
        ny_rad = pd.DataFrame([[ny_id, navn.strip(), kategori, kull, ""]], columns=self.kolonner)
        self.df = pd.concat([self.df, ny_rad], ignore_index=True)
        
        if self.lagre():
            self.loggfor("Lagt til", f"ID {ny_id}: {navn} ({kategori})")
            return True
        return False

    def oppdater(self, rad_id, navn, kategori, kull):
        rad_id = str(rad_id).zfill(2)
        idx = self.df.index[self.df["ID"] == rad_id].tolist()
        if idx:
            gammelt_navn = self.df.at[idx[0], "Navn"]
            self.df.at[idx[0], "Navn"] = navn
            self.df.at[idx[0], "Kategori"] = kategori
            self.df.at[idx[0], "Kull"] = kull
            if self.lagre():
                self.loggfor("Oppdatert", f"ID {rad_id}: {gammelt_navn} endret til {navn} ({kategori})")

    def slett(self, rad_id):
        rad_id = str(rad_id).zfill(2)
        idx = self.df.index[self.df["ID"] == rad_id].tolist()
        navn = self.df.at[idx[0], "Navn"] if idx else "Ukjent"
        
        self.df = self.df[self.df["ID"] != rad_id].reset_index(drop=True)
        if self.lagre():
            self.loggfor("Slettet", f"ID {rad_id}: {navn}")

    def generer_lag_alle(self):
        elever = self.df[self.df["Kategori"] == "Elev"].copy()
        indekser = elever.index.tolist()
        random.shuffle(indekser)
        
        midtpunkt = len(indekser) // 2
        for i, idx in enumerate(indekser):
            self.df.at[idx, "Lag"] = LAG_A if i < midtpunkt else LAG_B
        
        self.df.loc[self.df["Kategori"] != "Elev", "Lag"] = ""
        if self.lagre():
            self.loggfor("Laginndeling", "Autogenerert lag for ALLE elever (Nullstilt 50/50)")

    def flytt_deltaker(self, rad_id, nytt_lag):
        rad_id = str(rad_id).zfill(2)
        idx = self.df.index[self.df["ID"] == rad_id].tolist()
        if idx:
            navn = self.df.at[idx[0], "Navn"]
            gammelt_lag = self.df.at[idx[0], "Lag"]
            self.df.at[idx[0], "Lag"] = nytt_lag
            if self.lagre():
                self.loggfor("Flyttet", f"{navn} flyttet fra {gammelt_lag if gammelt_lag else 'Ufordelt'} til {nytt_lag if nytt_lag else 'Ufordelt'}")

    def sok(self, tekst):
        if not tekst:
            return self.df
        
        mask = (
            self.df["ID"].str.contains(tekst, case=False, na=False) |
            self.df["Navn"].str.contains(tekst, case=False, na=False) |
            self.df["Kategori"].str.contains(tekst, case=False, na=False) |
            self.df["Kull"].str.contains(tekst, case=False, na=False) |
            self.df["Lag"].str.contains(tekst, case=False, na=False)
        )
        return self.df[mask]

class ModerneTreeview(tk.Frame):
    def __init__(self, master, kolonner, bredder):
        super().__init__(master, bg=PANEL_COLOR)
        
        stil = ttk.Style()
        stil.theme_use("default")
        stil.configure("Moderne.Treeview", background=PANEL_COLOR, foreground=TEXT_COLOR, 
                       fieldbackground=PANEL_COLOR, rowheight=35, borderwidth=0, font=("Helvetica", 11))
        stil.configure("Moderne.Treeview.Heading", background="#2D3436", foreground="#FFFFFF", 
                       font=("Helvetica", 11, "bold"), borderwidth=0, padding=5)
        stil.map("Moderne.Treeview", background=[("selected", ACCENT_COLOR)])

        self.tree = ttk.Treeview(self, columns=kolonner, show="headings", style="Moderne.Treeview")
        for col, w in zip(kolonner, bredder):
            self.tree.heading(col, text=col, anchor="w", command=lambda c=col: self.sorter_kolonne(c, False))
            self.tree.column(col, width=w, anchor="w")

        scroll = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def fyll_data(self, df):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for _, rad in df.iterrows():
            self.tree.insert("", "end", values=rad.tolist())

    def hent_valgt(self):
        valgt = self.tree.selection()
        if valgt:
            verdier = list(self.tree.item(valgt[0])["values"])
            verdier[0] = str(verdier[0]).zfill(2)
            return verdier
        return None

    def sorter_kolonne(self, kol, reverse):
        l = [(self.tree.set(k, kol), k) for k in self.tree.get_children("")]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)
            
        for index, (_, k) in enumerate(l):
            self.tree.move(k, "", index)
            
        self.tree.heading(kol, command=lambda: self.sorter_kolonne(kol, not reverse))

class RegistreringPanel(ctk.CTkFrame):
    def __init__(self, master, data_manager, oppdaterings_callback):
        super().__init__(master, fg_color="transparent")
        self.db = data_manager
        self.oppdater_eksternt = oppdaterings_callback
        self.valgt_id = None
        self.bygg_grensesnitt()
        self.oppdater_liste()

    def bygg_grensesnitt(self):
        venstre = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=10, width=350)
        venstre.pack(side="left", fill="y", padx=10, pady=10)
        venstre.pack_propagate(False)

        ctk.CTkLabel(venstre, text="Deltakerinfo", font=("Helvetica", 20, "bold")).pack(pady=20)

        self.navn_input = ctk.CTkEntry(venstre, placeholder_text="Fullt navn", height=40)
        self.navn_input.pack(fill="x", padx=20, pady=10)

        self.kat_var = ctk.StringVar(value=KATEGORIER[0])
        self.kat_meny = ctk.CTkComboBox(venstre, values=KATEGORIER, variable=self.kat_var, height=40, command=self.sjekk_kategori)
        self.kat_meny.pack(fill="x", padx=20, pady=10)

        self.kull_input = ctk.CTkEntry(venstre, placeholder_text="Fødselsår / Klasse", height=40)
        self.kull_input.pack(fill="x", padx=20, pady=10)

        self.lagre_knapp = ctk.CTkButton(venstre, text="Legg til deltaker", fg_color=SUCCESS_COLOR, height=40, command=self.lagre_deltaker)
        self.lagre_knapp.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(venstre, text="Slett valgt", fg_color=DANGER_COLOR, height=40, command=self.slett_deltaker).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(venstre, text="Manuelt Importer (CSV/Excel)", fg_color="#0984E3", height=40, command=self.importer).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(venstre, text="🔄 Oppdater fra lagringsfil", fg_color="#0984E3", hover_color="#0760A8", height=40, command=self.last_inn_manuelt).pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(venstre, text="Tøm felt / Avbryt redigering", fg_color="#636E72", height=40, command=self.tom_felt).pack(fill="x", padx=20, pady=5)

        self.status_frame = ctk.CTkFrame(venstre, fg_color="transparent")
        self.status_frame.pack(side="bottom", pady=15, padx=20, fill="x")
        
        self.status_prikk = ctk.CTkFrame(self.status_frame, width=10, height=10, corner_radius=5, fg_color=SUCCESS_COLOR)
        self.status_prikk.pack(side="left", padx=(0, 8))
        
        self.status_tekst = ctk.CTkLabel(self.status_frame, text="Alt er lagret", font=("Helvetica", 12), text_color="#7889a8")
        self.status_tekst.pack(side="left")

        hoyre = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=10)
        hoyre.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        topprad = ctk.CTkFrame(hoyre, fg_color="transparent")
        topprad.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(topprad, text="Oversikt", font=("Helvetica", 20, "bold")).pack(side="left")
        self.sok_input = ctk.CTkEntry(topprad, placeholder_text="Søk på lag, kull, navn, ID...", width=300, height=35)
        self.sok_input.pack(side="right")
        self.sok_input.bind("<KeyRelease>", self.utfor_sok)

        self.tabell = ModerneTreeview(hoyre, self.db.kolonner, [50, 250, 150, 100, 150])
        self.tabell.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.tabell.tree.bind("<<TreeviewSelect>>", self.last_inn_valgt)

    def sjekk_kategori(self, valg):
        if valg == "Elev":
            self.kull_input.configure(state="normal")
        else:
            self.kull_input.delete(0, "end")
            self.kull_input.configure(state="disabled")

    def utfor_sok(self, event):
        tekst = self.sok_input.get()
        df = self.db.sok(tekst)
        self.tabell.fyll_data(df)

    def vis_lagring_animasjon(self):
        self.status_prikk.configure(fg_color="#FDCB6E")
        self.status_tekst.configure(text="Synkroniserer endringer...")
        self.update_idletasks()
        self.after(600, self._tilbakestill_status)

    def _tilbakestill_status(self):
        self.status_prikk.configure(fg_color=SUCCESS_COLOR)
        self.status_tekst.configure(text="Alt er lagret")

    def last_inn_manuelt(self):
        self.db.df = self.db.last_inn()
        self.db.logg_df = self.db.last_inn_logg()
        self.oppdater_liste()
        self.vis_lagring_animasjon()
        self.status_tekst.configure(text="Data lastet inn på nytt")

    def lagre_deltaker(self):
        navn = self.navn_input.get()
        kategori = self.kat_var.get()
        kull = self.kull_input.get() if kategori == "Elev" else ""

        if not navn:
            messagebox.showwarning("Feil", "Navn er påkrevd.")
            return

        self.vis_lagring_animasjon()

        if self.valgt_id:
            self.db.oppdater(str(self.valgt_id), navn, kategori, kull)
        else:
            suksess = self.db.legg_til(navn, kategori, kull)
            if not suksess:
                return

        self.tom_felt()
        self.utfor_sok(None)
        self.oppdater_eksternt()

    def last_inn_valgt(self, event):
        valgt = self.tabell.hent_valgt()
        if valgt:
            self.valgt_id = valgt[0]
            self.navn_input.delete(0, "end")
            self.navn_input.insert(0, valgt[1])
            self.kat_var.set(valgt[2])
            self.kull_input.configure(state="normal")
            self.kull_input.delete(0, "end")
            self.kull_input.insert(0, valgt[3])
            self.sjekk_kategori(valgt[2])
            self.lagre_knapp.configure(text=f"Oppdater ID: {self.valgt_id}")

    def tom_felt(self):
        self.navn_input.delete(0, "end")
        self.kull_input.delete(0, "end")
        self.valgt_id = None
        self.lagre_knapp.configure(text="Legg til deltaker")
        for item in self.tabell.tree.selection():
            self.tabell.tree.selection_remove(item)

    def slett_deltaker(self):
        if self.valgt_id:
            bekreft = messagebox.askyesno("Slett", f"Er du sikker på at du vil slette deltaker ID {self.valgt_id}?")
            if bekreft:
                self.vis_lagring_animasjon()
                self.db.slett(str(self.valgt_id))
                self.tom_felt()
                self.utfor_sok(None)
                self.oppdater_eksternt()

    def importer(self):
        fil = filedialog.askopenfilename(filetypes=[("Støttede filer", "*.csv *.xlsx"), ("CSV filer", "*.csv"), ("Excel filer", "*.xlsx")])
        if fil:
            self.vis_lagring_animasjon()
            try:
                if fil.endswith(".xlsx"):
                    ny_df = pd.read_excel(fil, dtype=str).fillna("")
                else:
                    ny_df = pd.read_csv(fil, dtype=str).fillna("")
                    
                importert_antall = 0
                for _, rad in ny_df.iterrows():
                    navn = rad.get("Navn", "")
                    kat = rad.get("Kategori", "Elev")
                    kull = rad.get("Kull", "")
                    if navn:
                        self.db.legg_til(navn, kat, kull)
                        importert_antall += 1
                self.db.loggfor("Import", f"Importerte {importert_antall} deltakere fra fil")
                self.oppdater_liste()
                messagebox.showinfo("Suksess", f"{importert_antall} deltakere ble importert i systemet.")
            except Exception as e:
                messagebox.showerror("Feil", f"Kunne ikke lese importfilen. Sikre at den er riktig formatert: {e}")

    def oppdater_liste(self):
        self.utfor_sok(None)
        self.oppdater_eksternt()

class LagPanel(ctk.CTkFrame):
    def __init__(self, master, data_manager):
        super().__init__(master, fg_color="transparent")
        self.db = data_manager
        self.bygg_grensesnitt()
        self.oppdater_visning()

    def bygg_grensesnitt(self):
        topp = ctk.CTkFrame(self, fg_color="transparent")
        topp.pack(fill="x", padx=10, pady=10)
        
        knapper_venstre = ctk.CTkFrame(topp, fg_color="transparent")
        knapper_venstre.pack(side="left")
        
        ctk.CTkButton(knapper_venstre, text="✨ Auto-fordel nye elever", font=("Helvetica", 14, "bold"), height=45, fg_color=SUCCESS_COLOR, hover_color="#00a87e", command=self.fordel_ufordelte).pack(side="left", padx=(0, 10))
        ctk.CTkButton(knapper_venstre, text="⚠️ Nullstill & Generer alt på nytt", font=("Helvetica", 14), height=45, fg_color=DANGER_COLOR, hover_color="#b52627", command=self.fordel_alle_lag).pack(side="left")

        knapper_hoyre = ctk.CTkFrame(topp, fg_color="transparent")
        knapper_hoyre.pack(side="right")
        
        ctk.CTkButton(knapper_hoyre, text="🖨️ Utskrift / PDF", font=("Helvetica", 14), height=45, fg_color="#E17055", hover_color="#c25a42", command=self.eksporter_utskrift).pack(side="left", padx=(0, 10))
        ctk.CTkButton(knapper_hoyre, text="Eksporter til CSV", font=("Helvetica", 14), height=45, fg_color="#00CEC9", hover_color="#00b5b0", command=self.eksporter).pack(side="left")

        innhold = ctk.CTkFrame(self, fg_color="transparent")
        innhold.pack(fill="both", expand=True)

        innhold.columnconfigure(0, weight=1)
        innhold.columnconfigure(1, weight=1)
        innhold.columnconfigure(2, weight=1)
        innhold.rowconfigure(0, weight=1)

        ramme_a = ctk.CTkFrame(innhold, fg_color=PANEL_COLOR, corner_radius=10)
        ramme_a.grid(row=0, column=0, sticky="nsew", padx=5, pady=10)
        ctk.CTkLabel(ramme_a, text=LAG_A, font=("Helvetica", 18, "bold"), text_color="#FF7675").pack(pady=10)
        self.tabell_a = ModerneTreeview(ramme_a, ["ID", "Navn", "Kull"], [40, 150, 60])
        self.tabell_a.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkButton(ramme_a, text="Fjern fra lag ➔", fg_color="#636E72", command=self.fjern_fra_a).pack(pady=10)

        ramme_u = ctk.CTkFrame(innhold, fg_color=PANEL_COLOR, corner_radius=10)
        ramme_u.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        ctk.CTkLabel(ramme_u, text="Ufordelte Elever", font=("Helvetica", 18, "bold"), text_color="#DFDFE5").pack(pady=10)
        self.tabell_u = ModerneTreeview(ramme_u, ["ID", "Navn", "Kull"], [40, 150, 60])
        self.tabell_u.pack(fill="both", expand=True, padx=10, pady=5)
        
        u_knapper = ctk.CTkFrame(ramme_u, fg_color="transparent")
        u_knapper.pack(pady=10)
        ctk.CTkButton(u_knapper, text="⬅ Til Rød", width=100, fg_color="#FF7675", hover_color="#d63031", command=self.legg_til_a).pack(side="left", padx=5)
        ctk.CTkButton(u_knapper, text="Til Gul ➔", width=100, fg_color="#FDCB6E", text_color="#2D3436", hover_color="#e1b12c", command=self.legg_til_b).pack(side="left", padx=5)

        ramme_b = ctk.CTkFrame(innhold, fg_color=PANEL_COLOR, corner_radius=10)
        ramme_b.grid(row=0, column=2, sticky="nsew", padx=5, pady=10)
        ctk.CTkLabel(ramme_b, text=LAG_B, font=("Helvetica", 18, "bold"), text_color="#FDCB6E").pack(pady=10)
        self.tabell_b = ModerneTreeview(ramme_b, ["ID", "Navn", "Kull"], [40, 150, 60])
        self.tabell_b.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkButton(ramme_b, text="⬅ Fjern fra lag", fg_color="#636E72", command=self.fjern_fra_b).pack(pady=10)

    def fordel_alle_lag(self):
        if messagebox.askyesno("Advarsel", "Dette vil nullstille lagene til ALLE eksisterende elever og fordele dem på nytt.\n\nEr du helt sikker?"):
            self.db.generer_lag_alle()
            self.oppdater_visning()

    def fordel_ufordelte(self):
        ufordelte = self.db.df[(self.db.df["Kategori"] == "Elev") & (self.db.df["Lag"] == "")]
        if ufordelte.empty:
            messagebox.showinfo("Info", "Det er ingen ufordelte elever i systemet.")
            return

        indekser = ufordelte.index.tolist()
        random.shuffle(indekser)

        antall_a = len(self.db.df[self.db.df["Lag"] == LAG_A])
        antall_b = len(self.db.df[self.db.df["Lag"] == LAG_B])

        for idx in indekser:
            if antall_a <= antall_b:
                self.db.df.at[idx, "Lag"] = LAG_A
                antall_a += 1
            else:
                self.db.df.at[idx, "Lag"] = LAG_B
                antall_b += 1

        if self.db.lagre():
            self.db.loggfor("Laginndeling", f"Auto-fordelte {len(indekser)} ufordelte elever for å balansere lagene.")
            self.oppdater_visning()
            messagebox.showinfo("Suksess", f"{len(indekser)} elever ble fordelt på lagene.")

    def legg_til_a(self):
        valgt = self.tabell_u.hent_valgt()
        if valgt:
            self.db.flytt_deltaker(str(valgt[0]), LAG_A)
            self.oppdater_visning()

    def legg_til_b(self):
        valgt = self.tabell_u.hent_valgt()
        if valgt:
            self.db.flytt_deltaker(str(valgt[0]), LAG_B)
            self.oppdater_visning()

    def fjern_fra_a(self):
        valgt = self.tabell_a.hent_valgt()
        if valgt:
            self.db.flytt_deltaker(str(valgt[0]), "")
            self.oppdater_visning()

    def fjern_fra_b(self):
        valgt = self.tabell_b.hent_valgt()
        if valgt:
            self.db.flytt_deltaker(str(valgt[0]), "")
            self.oppdater_visning()

    def eksporter_utskrift(self):
        df_a = self.db.df[self.db.df["Lag"] == LAG_A]
        df_b = self.db.df[self.db.df["Lag"] == LAG_B]

        html_innhold = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Laginndeling - Sportsfestival 2026</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; color: #2d3436; }}
                h1 {{ text-align: center; color: #2d3436; margin-bottom: 40px; text-transform: uppercase; letter-spacing: 2px; }}
                .container {{ display: flex; justify-content: space-between; gap: 40px; }}
                .team-box {{ width: 48%; }}
                h2 {{ padding-bottom: 10px; margin-bottom: 20px; }}
                h2.red {{ color: #d63031; border-bottom: 3px solid #d63031; }}
                h2.yellow {{ color: #e1b12c; border-bottom: 3px solid #e1b12c; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }}
                th, td {{ border: 1px solid #dfe6e9; padding: 12px 8px; text-align: left; }}
                th {{ background-color: #f5f6fa; font-weight: bold; color: #2d3436; }}
                tr:nth-child(even) {{ background-color: #fbfbfb; }}
            </style>
        </head>
        <body>
            <h1>Annai Poopathi - Sportsfestival 2026</h1>
            <div class="container">
                <div class="team-box">
                    <h2 class="red">🔴 {LAG_A}</h2>
                    <table>
                        <tr><th style="width: 15%;">ID</th><th style="width: 60%;">Navn</th><th style="width: 25%;">Kull</th></tr>
                        {''.join(f"<tr><td>{r['ID']}</td><td>{r['Navn']}</td><td>{r['Kull']}</td></tr>" for _, r in df_a.iterrows())}
                    </table>
                </div>
                <div class="team-box">
                    <h2 class="yellow">🟡 {LAG_B}</h2>
                    <table>
                        <tr><th style="width: 15%;">ID</th><th style="width: 60%;">Navn</th><th style="width: 25%;">Kull</th></tr>
                        {''.join(f"<tr><td>{r['ID']}</td><td>{r['Navn']}</td><td>{r['Kull']}</td></tr>" for _, r in df_b.iterrows())}
                    </table>
                </div>
            </div>
        </body>
        </html>
        """

        filsti = Path(tempfile.gettempdir()) / "laginndeling_utskrift.html"
        try:
            with open(filsti, "w", encoding="utf-8-sig") as f:
                f.write(html_innhold)
            webbrowser.open(f"file://{filsti}")
            self.db.loggfor("Eksport", "Genererte HTML for utskrift/PDF")
        except Exception as e:
            messagebox.showerror("Feil", f"Kunne ikke opprette utskriftsfil: {e}")

    def eksporter(self):
        fil = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV filer", "*.csv")])
        if fil:
            kun_lag = self.db.df[self.db.df["Lag"] != ""]
            kun_lag.to_csv(fil, index=False, encoding="utf-8-sig")
            self.db.loggfor("Eksport", "Eksporterte laginndeling til CSV")
            messagebox.showinfo("Suksess", "Laginndeling er eksportert.")

    def oppdater_visning(self):
        df_a = self.db.df[self.db.df["Lag"] == LAG_A][["ID", "Navn", "Kull"]]
        df_u = self.db.df[(self.db.df["Kategori"] == "Elev") & (self.db.df["Lag"] == "")][["ID", "Navn", "Kull"]]
        df_b = self.db.df[self.db.df["Lag"] == LAG_B][["ID", "Navn", "Kull"]]
        
        self.tabell_a.fyll_data(df_a)
        self.tabell_u.fyll_data(df_u)
        self.tabell_b.fyll_data(df_b)

class InfoPanel(ctk.CTkFrame):
    def __init__(self, master, data_manager):
        super().__init__(master, fg_color="transparent")
        self.db = data_manager
        self.bygg_grensesnitt()

    def bygg_grensesnitt(self):
        topprad = ctk.CTkFrame(self, fg_color="transparent")
        topprad.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(topprad, text="Festivalinformasjon & Statistikk", font=("Helvetica", 24, "bold")).pack(side="left")

        self.stat_ramme = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=10)
        self.stat_ramme.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tekst_felt = ctk.CTkLabel(self.stat_ramme, text="", font=("Helvetica", 16), justify="left", anchor="nw")
        self.tekst_felt.pack(fill="both", expand=True, padx=30, pady=30)
        
    def oppdater_visning(self):
        df = self.db.df
        totalt = len(df)
        
        kategori_tell = df["Kategori"].value_counts()
        lag_a_antall = len(df[df["Lag"] == LAG_A])
        lag_b_antall = len(df[df["Lag"] == LAG_B])
        uten_lag = len(df[(df["Kategori"] == "Elev") & (df["Lag"] == "")])
        
        info_tekst = (
            f"GENERELT:\n"
            f"Totalt antall registrerte deltakere i systemet: {totalt}\n\n"
            
            f"KATEGORIFORDELING:\n"
            f"Elever: {kategori_tell.get('Elev', 0)}\n"
            f"Lærere: {kategori_tell.get('Lærer', 0)}\n"
            f"Styre/Ledelse: {kategori_tell.get('நிர்வாகம்', 0)}\n"
            f"Frivillige: {kategori_tell.get('Frivillig', 0)}\n"
            f"Gjester: {kategori_tell.get('Gjest', 0)}\n\n"
            
            f"LAGINNDELING (Kun elever):\n"
            f"{LAG_A}: {lag_a_antall} elever\n"
            f"{LAG_B}: {lag_b_antall} elever\n"
            f"Elever som mangler lag: {uten_lag}\n"
        )
        self.tekst_felt.configure(text=info_tekst)

class LoggPanel(ctk.CTkFrame):
    def __init__(self, master, data_manager):
        super().__init__(master, fg_color="transparent")
        self.db = data_manager
        self.bygg_grensesnitt()

    def bygg_grensesnitt(self):
        topprad = ctk.CTkFrame(self, fg_color="transparent")
        topprad.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(topprad, text="Systemhistorikk & Endringslogg", font=("Helvetica", 24, "bold")).pack(side="left")

        innhold = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=10)
        innhold.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tabell = ModerneTreeview(innhold, self.db.logg_kolonner, [150, 150, 500])
        self.tabell.pack(fill="both", expand=True, padx=15, pady=15)
        
    def oppdater_visning(self):
        self.tabell.fyll_data(self.db.logg_df)

class HovedApplikasjon(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Annai Poopathi - Sportsfestival 2026")
        self.geometry("1280x800")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=BG_COLOR)

        self.db = DataManager()
        self.bygg_navigasjon()

    def bygg_navigasjon(self):
        meny = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=PANEL_COLOR)
        meny.pack(side="left", fill="y")
        meny.pack_propagate(False)

        ctk.CTkLabel(meny, text="SPORTSFESTIVAL", font=("Helvetica", 22, "bold"), text_color=ACCENT_COLOR).pack(pady=(40, 5))
        ctk.CTkLabel(meny, text="Admin System 2026", font=("Helvetica", 12)).pack(pady=(0, 40))

        self.knapper = {}
        
        self.knapper["reg"] = ctk.CTkButton(meny, text="Registrering", fg_color="transparent", text_color=TEXT_COLOR, font=("Helvetica", 15), anchor="w", command=lambda: self.vis_side("reg"))
        self.knapper["reg"].pack(fill="x", padx=15, pady=5)

        self.knapper["lag"] = ctk.CTkButton(meny, text="Laginndeling", fg_color="transparent", text_color=TEXT_COLOR, font=("Helvetica", 15), anchor="w", command=lambda: self.vis_side("lag"))
        self.knapper["lag"].pack(fill="x", padx=15, pady=5)
        
        self.knapper["info"] = ctk.CTkButton(meny, text="Informasjon", fg_color="transparent", text_color=TEXT_COLOR, font=("Helvetica", 15), anchor="w", command=lambda: self.vis_side("info"))
        self.knapper["info"].pack(fill="x", padx=15, pady=5)
        
        self.knapper["logg"] = ctk.CTkButton(meny, text="Historikk", fg_color="transparent", text_color=TEXT_COLOR, font=("Helvetica", 15), anchor="w", command=lambda: self.vis_side("logg"))
        self.knapper["logg"].pack(fill="x", padx=15, pady=5)

        self.innholdsfelt = ctk.CTkFrame(self, fg_color="transparent")
        self.innholdsfelt.pack(side="right", fill="both", expand=True)

        self.sider = {
            "reg": RegistreringPanel(self.innholdsfelt, self.db, self.synkroniser),
            "lag": LagPanel(self.innholdsfelt, self.db),
            "info": InfoPanel(self.innholdsfelt, self.db),
            "logg": LoggPanel(self.innholdsfelt, self.db)
        }
        
        self.vis_side("reg")

    def vis_side(self, side_navn):
        for side in self.sider.values():
            side.pack_forget()
            
        for knapp_navn, knapp in self.knapper.items():
            if knapp_navn == side_navn:
                knapp.configure(fg_color=ACCENT_COLOR)
            else:
                knapp.configure(fg_color="transparent")
                
        self.sider[side_navn].pack(fill="both", expand=True)
        
        if hasattr(self.sider[side_navn], "oppdater_visning"):
            self.sider[side_navn].oppdater_visning()

    def synkroniser(self):
        if hasattr(self, "sider"):
            if "lag" in self.sider:
                self.sider["lag"].oppdater_visning()
            if "info" in self.sider:
                self.sider["info"].oppdater_visning()
            if "logg" in self.sider:
                self.sider["logg"].oppdater_visning()

if __name__ == "__main__":
    app = HovedApplikasjon()
    app.mainloop()