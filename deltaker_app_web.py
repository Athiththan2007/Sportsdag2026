import streamlit as st
import pandas as pd
import random
import io
from datetime import datetime
from github import Github

KATEGORIER = ["Elev", "நிர்வாகம்", "Lærer", "Frivillig", "Gjest"]
AVDELINGER = ["Ålesund", "Ulsteinvik", "Florø"]
LAG_A = "Lag Rød"
LAG_B = "Lag Gul"

st.set_page_config(
    page_title="Sportsfestival 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "kolonner" not in st.session_state:
    st.session_state.kolonner = ["ID", "Navn", "Kategori", "Kull", "Kjønn", "Avdeling", "Lag"]
    st.session_state.logg_kolonner = ["Tidspunkt", "Rolle", "Handling", "Detaljer"]
    st.session_state.poeng_kolonner = ["ID", "Øvelse 1", "Øvelse 2", "Øvelse 3"]


# ═════════════════════════════════════════════════════════════════════════════
#  GITHUB I/O
# ═════════════════════════════════════════════════════════════════════════════

def les_fra_github(filnavn):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        file = repo.get_contents(filnavn)
        innhold = file.decoded_content.decode("utf-8")
        return pd.read_csv(io.StringIO(innhold), dtype=str)
    except Exception:
        return pd.DataFrame()

def lagre_til_github(df, filnavn):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        try:
            file = repo.get_contents(filnavn)
            repo.update_file(file.path, f"Oppdaterer {filnavn}", csv_data, file.sha)
        except Exception:
            repo.create_file(filnavn, f"Oppretter {filnavn}", csv_data)
        return True
    except Exception as e:
        st.error(f"Feil ved lagring av {filnavn}: {e}")
        return False


# ═════════════════════════════════════════════════════════════════════════════
#  INNSTILLINGER OG DATALASTING
# ═════════════════════════════════════════════════════════════════════════════

def last_inn_innstillinger():
    standard = {
        "passord": "Admin2026",
        "las_nullstill": "True",
        "las_autofordel": "True",
        "las_import": "False",
        "las_slett_enkel": "False",
        "las_poengforing": "True"
    }
    df = les_fra_github("sportsfestival_innstillinger.csv")
    if not df.empty:
        try:
            lagrede = dict(zip(df["Nøkkel"], df["Verdi"]))
            standard.update(lagrede)
        except Exception:
            pass
    return standard

def lagre_innstillinger():
    data = {"Nøkkel": list(st.session_state.innstillinger.keys()), "Verdi": list(st.session_state.innstillinger.values())}
    df = pd.DataFrame(data)
    lagre_til_github(df, "sportsfestival_innstillinger.csv")

def last_inn_data():
    df = les_fra_github("sportsfestival_data.csv")
    if not df.empty:
        df = df.fillna("")
        if "Kjønn" not in df.columns:
            df["Kjønn"] = ""
        if "Avdeling" not in df.columns:
            df["Avdeling"] = "Ålesund"
        return df
    return pd.DataFrame(columns=st.session_state.kolonner)

def last_inn_logg():
    df = les_fra_github("sportsfestival_logg.csv")
    if not df.empty:
        df = df.fillna("")
        if "Rolle" not in df.columns:
            df.insert(1, "Rolle", "—")
        return df
    return pd.DataFrame(columns=st.session_state.logg_kolonner)

def last_inn_poeng():
    df = les_fra_github("sportsfestival_poeng.csv")
    if not df.empty:
        return df.fillna("0")
    return pd.DataFrame(columns=st.session_state.poeng_kolonner)

if "innstillinger" not in st.session_state:
    st.session_state.innstillinger = last_inn_innstillinger()
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "df" not in st.session_state:
    st.session_state.df = last_inn_data()
if "logg_df" not in st.session_state:
    st.session_state.logg_df = last_inn_logg()
if "poeng_df" not in st.session_state:
    st.session_state.poeng_df = last_inn_poeng()

def lagre_alle_data():
    with st.spinner("Synkroniserer endringer med GitHub..."):
        s1 = lagre_til_github(st.session_state.df, "sportsfestival_data.csv")
        s2 = lagre_til_github(st.session_state.logg_df, "sportsfestival_logg.csv")
        s3 = lagre_til_github(st.session_state.poeng_df, "sportsfestival_poeng.csv")
        return s1 and s2 and s3

def loggfor_handling(handling, detaljer):
    tid = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rolle = "🔒 Admin" if st.session_state.is_admin else "👤 Bruker"
    ny_rad = pd.DataFrame([[tid, rolle, handling, detaljer]], columns=st.session_state.logg_kolonner)
    st.session_state.logg_df = pd.concat([ny_rad, st.session_state.logg_df], ignore_index=True)

def finn_laveste_ledige_id():
    eksisterende = []
    for val in st.session_state.df["ID"]:
        try:
            eksisterende.append(int(val))
        except ValueError:
            pass
    ny_id = 1
    while ny_id in eksisterende and ny_id < 1000:
        ny_id += 1
    return ny_id

def har_tilgang(nokkel):
    if str(st.session_state.innstillinger.get(nokkel, "False")) == "True":
        return st.session_state.is_admin
    return True


# ── Sidemeny ────────────────────────────────────────────────────────────────

st.sidebar.title("🏆 Sportsfestival")
st.sidebar.write("Admin System 2026")
side = st.sidebar.radio("Navigasjon", [
    "📋 Registrering", 
    "🏁 Laginndeling", 
    "🎯 Poeng & Resultater", 
    "📊 Informasjon", 
    "📜 Historikk", 
    "⚙️ Admin-meny"
])

st.sidebar.markdown("---")
if st.session_state.is_admin:
    st.sidebar.markdown("🔓 **Status:** Innlogget som Administrator")
    if st.sidebar.button("🔒 Logg ut av admin"):
        st.session_state.is_admin = False
        st.rerun()
else:
    st.sidebar.markdown("🟢 **Status:** Begrenset brukermodus")


# ═════════════════════════════════════════════════════════════════════════════
#  📋 REGISTRERING
# ═════════════════════════════════════════════════════════════════════════════

if side == "📋 Registrering":
    st.title("Deltakerregistrering")
    
    reg_modus = st.radio("Velg handling", ["Legg til ny", "Rediger / Slett eksisterende"], horizontal=True)
    
    if reg_modus == "Legg til ny":
        with st.form("ny_deltaker_form", clear_on_submit=True):
            navn = st.text_input("Fullt navn")
            kategori = st.selectbox("Kategori", KATEGORIER)
            avdeling = st.selectbox("Avdeling", AVDELINGER)
            
            kol1, kol2 = st.columns(2)
            with kol1:
                kull = st.text_input("Fødselsår / Klasse (Kun for elever)")
            with kol2:
                kjonn = st.selectbox("Kjønn (Kun for elever)", ["", "Gutt", "Jente"])
                
            opprett_knapp = st.form_submit_button("Legg til deltaker")
            
            if opprett_knapp:
                if not navn.strip():
                    st.warning("Navn er et påkrevd felt.")
                else:
                    ny_id_num = finn_laveste_ledige_id()
                    ny_id_str = f"{ny_id_num:02d}"
                    kull_verdi = kull.strip() if kategori == "Elev" else ""
                    kjonn_verdi = kjonn if kategori == "Elev" else ""
                    ny_rad = pd.DataFrame([[ny_id_str, navn.strip(), kategori, kull_verdi, kjonn_verdi, avdeling, ""]], columns=st.session_state.kolonner)
                    st.session_state.df = pd.concat([st.session_state.df, ny_rad], ignore_index=True)
                    loggfor_handling("Lagt til", f"ID {ny_id_str}: {navn} ({avdeling})")
                    if lagre_alle_data():
                        st.success(f"{navn} ble lagt til med ID {ny_id_str} ({avdeling})")
                        st.rerun()

    else:
        if st.session_state.df.empty:
            st.info("Det er ingen registrerte deltakere i systemet ennå.")
        else:
            deltaker_valg = st.selectbox("Velg deltaker som skal behandles", st.session_state.df["ID"] + " - " + st.session_state.df["Navn"])
            valgt_id = deltaker_valg.split(" - ")[0]
            idx = st.session_state.df.index[st.session_state.df["ID"] == valgt_id].tolist()[0]
            
            oppdatert_navn = st.text_input("Navn", st.session_state.df.at[idx, "Navn"])
            oppdatert_kat = st.selectbox("Kategori", KATEGORIER, index=KATEGORIER.index(st.session_state.df.at[idx, "Kategori"]))
            
            na_avd = st.session_state.df.at[idx, "Avdeling"]
            if na_avd not in AVDELINGER: na_avd = "Ålesund"
            oppdatert_avd = st.selectbox("Avdeling", AVDELINGER, index=AVDELINGER.index(na_avd))
            
            kol_e1, kol_e2 = st.columns(2)
            with kol_e1:
                oppdatert_kull = st.text_input("Fødselsår / Klasse", st.session_state.df.at[idx, "Kull"], disabled=(oppdatert_kat != "Elev"))
            with kol_e2:
                nåværende_kjønn = st.session_state.df.at[idx, "Kjønn"]
                kjønn_index = 0
                if nåværende_kjønn == "Gutt": kjønn_index = 1
                elif nåværende_kjønn == "Jente": kjønn_index = 2
                oppdatert_kjonn = st.selectbox("Kjønn", ["", "Gutt", "Jente"], index=kjønn_index, disabled=(oppdatert_kat != "Elev"))
            
            kol1, kol2 = st.columns(2)
            with kol1:
                if st.button("💾 Oppdater informasjon", use_container_width=True):
                    gammelt_navn = st.session_state.df.at[idx, "Navn"]
                    st.session_state.df.at[idx, "Navn"] = oppdatert_navn.strip()
                    st.session_state.df.at[idx, "Kategori"] = oppdatert_kat
                    st.session_state.df.at[idx, "Avdeling"] = oppdatert_avd
                    st.session_state.df.at[idx, "Kull"] = oppdatert_kull.strip() if oppdatert_kat == "Elev" else ""
                    st.session_state.df.at[idx, "Kjønn"] = oppdatert_kjonn if oppdatert_kat == "Elev" else ""
                    loggfor_handling("Oppdatert", f"ID {valgt_id}: {gammelt_navn} endret.")
                    if lagre_alle_data():
                        st.success("Endringene ble lagret i skyen.")
                        st.rerun()
            with kol2:
                tilgang_slett = har_tilgang("las_slett_enkel")
                slett_tekst = "🗑️ Slett deltaker permanent" if tilgang_slett else "🗑️ Slett deltaker (Krever admin)"
                if st.button(slett_tekst, type="primary", disabled=not tilgang_slett, use_container_width=True):
                    slettet_navn = st.session_state.df.at[idx, "Navn"]
                    st.session_state.df = st.session_state.df[st.session_state.df["ID"] != valgt_id].reset_index(drop=True)
                    st.session_state.poeng_df = st.session_state.poeng_df[st.session_state.poeng_df["ID"] != valgt_id].reset_index(drop=True)
                    loggfor_handling("Slettet", f"ID {valgt_id}: {slettet_navn}")
                    if lagre_alle_data():
                        st.success("Deltakeren ble slettet fra databasen.")
                        st.rerun()

    # ── Filimport (fikset: bruker knapp for å unngå loop) ────────────────
    st.markdown("---")
    st.subheader("Filimport")
    tilgang_import = har_tilgang("las_import")
    if not tilgang_import:
        st.info("Filimport er låst. Vennligst logg inn i Admin-menyen for å aktivere denne funksjonen.")
    
    opplastet_fil = st.file_uploader(
        "Last opp Excel eller CSV for å hente inn deltakere", 
        type=["csv", "xlsx"], 
        disabled=not tilgang_import,
        key="import_uploader"
    )
    
    if opplastet_fil and tilgang_import:
        # Vis forhåndsvisning uten å importere automatisk
        try:
            if opplastet_fil.name.endswith(".xlsx"):
                ny_df = pd.read_excel(opplastet_fil, dtype=str).fillna("")
            else:
                ny_df = pd.read_csv(opplastet_fil, dtype=str).fillna("")
            
            st.write(f"Filen inneholder **{len(ny_df)} rader**. Forhåndsvisning:")
            st.dataframe(ny_df.head(10), use_container_width=True, hide_index=True)
            
            # Bruker trykker eksplisitt for å starte import
            if st.button("📥 Importer deltakerne fra filen nå", type="primary"):
                eksisterende_navn = set(st.session_state.df["Navn"].str.lower().str.strip())
                importert_teller = 0
                hoppet_over_teller = 0
                
                for _, rad in ny_df.iterrows():
                    importert_navn = rad.get("Navn", "").strip()
                    if importert_navn:
                        navn_sjekk = importert_navn.lower()
                        if navn_sjekk in eksisterende_navn:
                            hoppet_over_teller += 1
                            continue
                            
                        neste_id = finn_laveste_ledige_id()
                        neste_id_str = f"{neste_id:02d}"
                        importert_kat = rad.get("Kategori", "Elev")
                        importert_avd = rad.get("Avdeling", "Ålesund")
                        if importert_avd not in AVDELINGER: importert_avd = "Ålesund"
                        importert_kull = rad.get("Kull", "") if importert_kat == "Elev" else ""
                        importert_kjonn = rad.get("Kjønn", "") if importert_kat == "Elev" else ""
                        
                        midlertidig_rad = pd.DataFrame(
                            [[neste_id_str, importert_navn, importert_kat, importert_kull, importert_kjonn, importert_avd, ""]], 
                            columns=st.session_state.kolonner
                        )
                        st.session_state.df = pd.concat([st.session_state.df, midlertidig_rad], ignore_index=True)
                        eksisterende_navn.add(navn_sjekk)
                        importert_teller += 1
                
                loggfor_handling("Import", f"Importerte {importert_teller} nye. Ignorerte {hoppet_over_teller} duplikater.")
                lagre_alle_data()
                st.success(f"La til {importert_teller} nye og hoppet over {hoppet_over_teller} duplikater.")
                st.rerun()
        except Exception as e:
            st.error(f"Kunne ikke tolke filen: {e}")

    # ── Søk og oversikt ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Globalt søk og oversikt")
    sok_tekst = st.text_input("Søk i sanntid på tvers av ID, navn, kull, kategori, lag eller avdeling")
    
    if sok_tekst.strip():
        filtrert_df = st.session_state.df[
            st.session_state.df["ID"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Navn"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Kategori"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Kull"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Avdeling"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Lag"].str.contains(sok_tekst, case=False, na=False)
        ]
    else:
        filtrert_df = st.session_state.df

    st.dataframe(filtrert_df, use_container_width=True, hide_index=True)

    if st.button("🔄 Tving filoppdatering fra skyen"):
        st.session_state.df = last_inn_data()
        st.session_state.logg_df = last_inn_logg()
        st.session_state.poeng_df = last_inn_poeng()
        st.rerun()

    st.markdown("---")
    st.subheader("🧹 Opprydding og sikkerhetssjekk")
    if st.button("Fjern duplikater i systemet automatisk"):
        originalt_antall = len(st.session_state.df)
        midlertidig_df = st.session_state.df.copy()
        midlertidig_df["Soke_nokkel"] = midlertidig_df["Navn"].str.lower().str.strip() + midlertidig_df["Kategori"]
        midlertidig_df = midlertidig_df.drop_duplicates(subset=["Soke_nokkel"], keep="first")
        st.session_state.df = midlertidig_df.drop(columns=["Soke_nokkel"]).reset_index(drop=True)
        nytt_antall = len(st.session_state.df)
        forskjell = originalt_antall - nytt_antall
        
        if forskjell > 0:
            loggfor_handling("Opprydding", f"Fjernet {forskjell} duplikater automatisk.")
            lagre_alle_data()
            st.success(f"Fjernet {forskjell} dupliserte registreringer.")
        else:
            st.info("Ingen duplikater ble funnet.")
        st.rerun()

    st.markdown("---")
    st.subheader("🚨 Faresone - Nullstill systemet fullstendig")
    tilgang_nullstill = har_tilgang("las_nullstill")
    if not tilgang_nullstill:
        st.info("Full systemnullstilling er låst bak admin-tilgang.")
    
    bekreft_sletting = st.checkbox("Jeg bekrefter at jeg vil slette alt av data og historikk permanent.", disabled=not tilgang_nullstill)
    if st.button("🔥 Slett alle deltakere og resette alt", type="primary", disabled=not (bekreft_sletting and tilgang_nullstill), use_container_width=True):
        st.session_state.df = pd.DataFrame(columns=st.session_state.kolonner)
        st.session_state.logg_df = pd.DataFrame(columns=st.session_state.logg_kolonner)
        st.session_state.poeng_df = pd.DataFrame(columns=st.session_state.poeng_kolonner)
        loggfor_handling("Systemnullstilling", "Alt slettet av administrator.")
        if lagre_alle_data():
            st.success("Hele systemet har blitt nullstilt!")
            st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  🏁 LAGINNDELING (Oppgradert med pilknapper + eksport)
# ═════════════════════════════════════════════════════════════════════════════

elif side == "🏁 Laginndeling":
    st.title("Laginndeling og balansering")
    tilgang_fordel = har_tilgang("las_autofordel")
    
    # ── Handlingsknapper ─────────────────────────────────────────────────
    b_kol1, b_kol2 = st.columns(2)
    with b_kol1:
        autofordel_tekst = "✨ Auto-fordel ufordelte" if tilgang_fordel else "✨ Auto-fordel (Admin)"
        if st.button(autofordel_tekst, disabled=not tilgang_fordel, use_container_width=True):
            ufordelte = st.session_state.df[(st.session_state.df["Kategori"] == "Elev") & (st.session_state.df["Lag"] == "")]
            if ufordelte.empty:
                st.info("Ingen ufordelte elever ble funnet.")
            else:
                indekser = ufordelte.index.tolist()
                random.shuffle(indekser)
                antall_a = len(st.session_state.df[st.session_state.df["Lag"] == LAG_A])
                antall_b = len(st.session_state.df[st.session_state.df["Lag"] == LAG_B])
                for idx_val in indekser:
                    if antall_a <= antall_b:
                        st.session_state.df.at[idx_val, "Lag"] = LAG_A
                        antall_a += 1
                    else:
                        st.session_state.df.at[idx_val, "Lag"] = LAG_B
                        antall_b += 1
                loggfor_handling("Laginndeling", f"Balanserte {len(indekser)} nye elever")
                lagre_alle_data()
                st.rerun()
                
    with b_kol2:
        omfordel_tekst = "⚠️ Nullstill og fordel alle" if tilgang_fordel else "⚠️ Omgjør lag (Admin)"
        if st.button(omfordel_tekst, disabled=not tilgang_fordel, use_container_width=True):
            elever = st.session_state.df[st.session_state.df["Kategori"] == "Elev"].copy()
            indekser = elever.index.tolist()
            random.shuffle(indekser)
            midt = len(indekser) // 2
            for i, idx_val in enumerate(indekser):
                st.session_state.df.at[idx_val, "Lag"] = LAG_A if i < midt else LAG_B
            st.session_state.df.loc[st.session_state.df["Kategori"] != "Elev", "Lag"] = ""
            loggfor_handling("Laginndeling", "Nullstilte og omfordelte alle elever")
            lagre_alle_data()
            st.rerun()

    # ── Eksport-knapper (tilbake fra beta) ───────────────────────────────
    st.markdown("---")
    eks_kol1, eks_kol2 = st.columns(2)
    with eks_kol1:
        csv_data = st.session_state.df[st.session_state.df["Lag"] != ""].to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "💾 Last ned CSV-eksport av lag", 
            data=csv_data, file_name="lagfordeling_eksport.csv", 
            mime="text/csv", use_container_width=True
        )
    with eks_kol2:
        df_a_print = st.session_state.df[st.session_state.df["Lag"] == LAG_A]
        df_b_print = st.session_state.df[st.session_state.df["Lag"] == LAG_B]
        html_print = f"""<html><head><meta charset="utf-8"><style>
body{{font-family:Arial,sans-serif;padding:30px}}
h2{{border-bottom:2px solid #333;padding-bottom:6px}}
table{{width:100%;border-collapse:collapse;margin-bottom:30px}}
th,td{{border:1px solid #ccc;padding:8px 12px;text-align:left}}
th{{background:#eee}}
</style></head><body>
<h1>Sportsfestival 2026 — Lagfordeling</h1>
<h2>🔴 {LAG_A} ({len(df_a_print)} stk)</h2>
<table><tr><th>ID</th><th>Navn</th><th>Kull</th><th>Kjønn</th></tr>
{"".join(f"<tr><td>{r['ID']}</td><td>{r['Navn']}</td><td>{r['Kull']}</td><td>{r['Kjønn']}</td></tr>" for _, r in df_a_print.iterrows())}
</table>
<h2>🟡 {LAG_B} ({len(df_b_print)} stk)</h2>
<table><tr><th>ID</th><th>Navn</th><th>Kull</th><th>Kjønn</th></tr>
{"".join(f"<tr><td>{r['ID']}</td><td>{r['Navn']}</td><td>{r['Kull']}</td><td>{r['Kjønn']}</td></tr>" for _, r in df_b_print.iterrows())}
</table>
</body></html>"""
        st.download_button(
            "🖨️ Last ned utskriftsklar HTML", 
            data=html_print, file_name="utskrift_lag.html", 
            mime="text/html", use_container_width=True
        )

    # ── Lag-kolonner med pilknapper ──────────────────────────────────────
    st.markdown("---")
    
    df_rod = st.session_state.df[st.session_state.df["Lag"] == LAG_A].reset_index()
    df_ufordelt = st.session_state.df[(st.session_state.df["Kategori"] == "Elev") & (st.session_state.df["Lag"] == "")].reset_index()
    df_gul = st.session_state.df[st.session_state.df["Lag"] == LAG_B].reset_index()

    l_kol1, l_kol2, l_kol3 = st.columns(3)
    
    with l_kol1:
        st.markdown(f"### 🔴 {LAG_A} ({len(df_rod)})")
        for _, r in df_rod.iterrows():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.text(f"{r['ID']} - {r['Navn']} ({r['Kull']})")
            with c2:
                if st.button("→🟡", key=f"rod_til_gul_{r['index']}"):
                    st.session_state.df.at[r["index"], "Lag"] = LAG_B
                    loggfor_handling("Flyttet", f"{r['Navn']} → {LAG_B}")
                    lagre_alle_data()
                    st.rerun()
    
    with l_kol2:
        st.markdown(f"### ⚪ Ufordelte ({len(df_ufordelt)})")
        for _, r in df_ufordelt.iterrows():
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1:
                if st.button("🔴←", key=f"uf_til_rod_{r['index']}"):
                    st.session_state.df.at[r["index"], "Lag"] = LAG_A
                    loggfor_handling("Fordelt", f"{r['Navn']} → {LAG_A}")
                    lagre_alle_data()
                    st.rerun()
            with c2:
                st.text(f"{r['ID']} - {r['Navn']}")
            with c3:
                if st.button("→🟡", key=f"uf_til_gul_{r['index']}"):
                    st.session_state.df.at[r["index"], "Lag"] = LAG_B
                    loggfor_handling("Fordelt", f"{r['Navn']} → {LAG_B}")
                    lagre_alle_data()
                    st.rerun()
    
    with l_kol3:
        st.markdown(f"### 🟡 {LAG_B} ({len(df_gul)})")
        for _, r in df_gul.iterrows():
            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button("🔴←", key=f"gul_til_rod_{r['index']}"):
                    st.session_state.df.at[r["index"], "Lag"] = LAG_A
                    loggfor_handling("Flyttet", f"{r['Navn']} → {LAG_A}")
                    lagre_alle_data()
                    st.rerun()
            with c2:
                st.text(f"{r['ID']} - {r['Navn']} ({r['Kull']})")

    # Fjern fra lag-knapp
    st.markdown("---")
    st.subheader("Fjern fra lag")
    lag_spillere = st.session_state.df[(st.session_state.df["Lag"] == LAG_A) | (st.session_state.df["Lag"] == LAG_B)]
    if not lag_spillere.empty:
        fjern_valg = st.selectbox("Velg spiller å fjerne fra laget", lag_spillere["ID"] + " - " + lag_spillere["Navn"] + " (" + lag_spillere["Lag"] + ")")
        if st.button("❌ Fjern fra lag (sett til ufordelt)"):
            fjern_id = fjern_valg.split(" - ")[0]
            fjern_idx = st.session_state.df.index[st.session_state.df["ID"] == fjern_id].tolist()[0]
            fjern_navn = st.session_state.df.at[fjern_idx, "Navn"]
            st.session_state.df.at[fjern_idx, "Lag"] = ""
            loggfor_handling("Fjernet fra lag", f"{fjern_navn} satt til ufordelt")
            lagre_alle_data()
            st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  🎯 POENG & RESULTATER (Komplett med alle beta-funksjoner)
# ═════════════════════════════════════════════════════════════════════════════

elif side == "🎯 Poeng & Resultater":
    tilgang_poeng = har_tilgang("las_poengforing")
    if not tilgang_poeng:
        st.warning("🔒 Poengføring er låst av administrator. Gå til Admin-menyen for å logge inn.")
    else:
        st.title("🎯 Poengregistrering og Resultater")
        
        poeng_fane1, poeng_fane2, poeng_fane3 = st.tabs([
            "📝 Før inn poeng", 
            "🏆 Resultattavle", 
            "⚔️ Lagpoeng"
        ])
        
        elever_df = st.session_state.df[st.session_state.df["Kategori"] == "Elev"]
        alle_kull = sorted([k for k in elever_df["Kull"].unique() if k.strip() != ""])

        # ── FANE 1: Før inn poeng ────────────────────────────────────────
        with poeng_fane1:
            st.subheader("Registrer poeng for øvelser")
            st.write("Huk av «Nullstill poeng ⚠️» for å slette poengene til en enkelt deltaker.")
            
            p_kol1, p_kol2 = st.columns(2)
            with p_kol1:
                valgt_kull = st.selectbox("Velg Kull", [""] + alle_kull, key="poeng_kull")
            with p_kol2:
                valgt_kjonn = st.selectbox("Filtrer på kjønn (valgfritt)", ["Alle", "Gutt", "Jente"], key="poeng_kjonn")
                
            if valgt_kull:
                if valgt_kjonn == "Alle":
                    aktuelle_elever = elever_df[elever_df["Kull"] == valgt_kull][["ID", "Navn", "Kjønn"]].copy()
                else:
                    aktuelle_elever = elever_df[
                        (elever_df["Kull"] == valgt_kull) & (elever_df["Kjønn"] == valgt_kjonn)
                    ][["ID", "Navn", "Kjønn"]].copy()
                
                if aktuelle_elever.empty:
                    st.info("Fant ingen registrerte elever i dette kullet.")
                else:
                    redigerings_df = pd.merge(aktuelle_elever, st.session_state.poeng_df, on="ID", how="left").fillna("0")
                    redigerings_df["Kjønn"] = redigerings_df["Kjønn"].replace("0", "")
                    redigerings_df["Nullstill"] = False
                    
                    redigert_data = st.data_editor(
                        redigerings_df,
                        column_config={
                            "ID": st.column_config.TextColumn("ID", disabled=True, width="small"),
                            "Navn": st.column_config.TextColumn("Navn", disabled=True),
                            "Kjønn": st.column_config.SelectboxColumn("Kjønn", options=["", "Gutt", "Jente"], width="small"),
                            "Øvelse 1": st.column_config.TextColumn("Øvelse 1", width="small"),
                            "Øvelse 2": st.column_config.TextColumn("Øvelse 2", width="small"),
                            "Øvelse 3": st.column_config.TextColumn("Øvelse 3", width="small"),
                            "Nullstill": st.column_config.CheckboxColumn("Nullstill poeng ⚠️", default=False, width="small")
                        },
                        hide_index=True,
                        use_container_width=True,
                        key="poeng_editor"
                    )
                    
                    if st.button("💾 Lagre poeng og endringer", type="primary"):
                        endret_kjonn_teller = 0
                        resatt_teller = 0
                        
                        for _, rad in redigert_data.iterrows():
                            pid = rad["ID"]
                            
                            # Kjønnsendring i hoveddataen
                            main_idx = st.session_state.df.index[st.session_state.df["ID"] == pid].tolist()
                            if main_idx:
                                gammelt_kjonn = st.session_state.df.at[main_idx[0], "Kjønn"]
                                nytt_kjonn = rad["Kjønn"] if pd.notna(rad["Kjønn"]) else ""
                                if gammelt_kjonn != nytt_kjonn:
                                    st.session_state.df.at[main_idx[0], "Kjønn"] = nytt_kjonn
                                    endret_kjonn_teller += 1
                            
                            # Poeng + nullstilling
                            poeng_idx = st.session_state.poeng_df.index[st.session_state.poeng_df["ID"] == pid].tolist()
                            skal_resettes = rad.get("Nullstill", False)
                            
                            if skal_resettes:
                                if poeng_idx:
                                    st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 1"] = "0"
                                    st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 2"] = "0"
                                    st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 3"] = "0"
                                resatt_teller += 1
                            else:
                                if poeng_idx:
                                    st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 1"] = rad["Øvelse 1"]
                                    st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 2"] = rad["Øvelse 2"]
                                    st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 3"] = rad["Øvelse 3"]
                                else:
                                    ny_poeng = pd.DataFrame(
                                        [[pid, rad["Øvelse 1"], rad["Øvelse 2"], rad["Øvelse 3"]]], 
                                        columns=st.session_state.poeng_kolonner
                                    )
                                    st.session_state.poeng_df = pd.concat([st.session_state.poeng_df, ny_poeng], ignore_index=True)
                        
                        detalj_tekst = f"Lagret poeng for {valgt_kull}"
                        if valgt_kjonn != "Alle":
                            detalj_tekst += f" ({valgt_kjonn})"
                        if resatt_teller > 0:
                            detalj_tekst += f" — nullstilt {resatt_teller} stk"
                        if endret_kjonn_teller > 0:
                            detalj_tekst += f" — endret kjønn for {endret_kjonn_teller}"
                        
                        loggfor_handling("Poeng oppdatert", detalj_tekst)
                        if lagre_alle_data():
                            st.success("Poeng og endringer ble lagret i skyen!")
                            st.rerun()

        # ── FANE 2: Resultattavle (med pall + kjønnsfilter) ──────────────
        with poeng_fane2:
            st.subheader("Resultattavle og vinnere")
            r_kol1, r_kol2 = st.columns(2)
            with r_kol1:
                res_kull = st.selectbox("Vis resultater for Kull", [""] + alle_kull, key="res_kull")
            with r_kol2:
                res_kjonn = st.selectbox("Filtrer på kjønn (valgfritt)", ["Alle", "Gutt", "Jente"], key="res_kjonn")
                
            if res_kull:
                if res_kjonn == "Alle":
                    aktuelle_elever = elever_df[elever_df["Kull"] == res_kull][["ID", "Navn", "Kjønn", "Lag"]]
                else:
                    aktuelle_elever = elever_df[
                        (elever_df["Kull"] == res_kull) & (elever_df["Kjønn"] == res_kjonn)
                    ][["ID", "Navn", "Kjønn", "Lag"]]
                
                res_df = pd.merge(aktuelle_elever, st.session_state.poeng_df, on="ID", how="left").fillna("0")
                res_df["Kjønn"] = res_df["Kjønn"].replace("0", "")
                res_df["Lag"] = res_df["Lag"].replace("0", "")
                
                for ov in ["Øvelse 1", "Øvelse 2", "Øvelse 3"]:
                    res_df[ov] = pd.to_numeric(res_df[ov], errors='coerce').fillna(0)
                res_df["Totalt"] = res_df["Øvelse 1"] + res_df["Øvelse 2"] + res_df["Øvelse 3"]
                res_df = res_df.sort_values(by="Totalt", ascending=False).reset_index(drop=True)
                
                if res_df.empty or res_df["Totalt"].sum() == 0:
                    st.info("Ingen poeng registrert for denne gruppen ennå.")
                else:
                    st.markdown("### 🥇 Pallen")
                    pall_k1, pall_k2, pall_k3 = st.columns(3)
                    if len(res_df) > 0 and res_df.at[0, "Totalt"] > 0:
                        with pall_k1:
                            st.success(f"**🏆 1. plass**\n\n{res_df.at[0, 'Navn']} ({int(res_df.at[0, 'Totalt'])} poeng)")
                    if len(res_df) > 1 and res_df.at[1, "Totalt"] > 0:
                        with pall_k2:
                            st.info(f"**🥈 2. plass**\n\n{res_df.at[1, 'Navn']} ({int(res_df.at[1, 'Totalt'])} poeng)")
                    if len(res_df) > 2 and res_df.at[2, "Totalt"] > 0:
                        with pall_k3:
                            st.warning(f"**🥉 3. plass**\n\n{res_df.at[2, 'Navn']} ({int(res_df.at[2, 'Totalt'])} poeng)")
                    
                    st.markdown("### Hele poengtabellen")
                    vis_kolonner = ["ID", "Navn", "Kjønn", "Lag", "Øvelse 1", "Øvelse 2", "Øvelse 3", "Totalt"]
                    st.dataframe(res_df[vis_kolonner], use_container_width=True, hide_index=True)

        # ── FANE 3: Lagpoeng ─────────────────────────────────────────────
        with poeng_fane3:
            st.subheader("⚔️ Lagsammenligning — Rød vs Gul")
            
            lag_elever = st.session_state.df[
                (st.session_state.df["Kategori"] == "Elev") & (st.session_state.df["Lag"] != "")
            ][["ID", "Navn", "Kull", "Lag"]].copy()
            
            if lag_elever.empty:
                st.info("Ingen elever er fordelt i lag ennå. Gå til Laginndeling først.")
            else:
                lag_med_poeng = pd.merge(lag_elever, st.session_state.poeng_df, on="ID", how="left").fillna("0")
                for ov in ["Øvelse 1", "Øvelse 2", "Øvelse 3"]:
                    lag_med_poeng[ov] = pd.to_numeric(lag_med_poeng[ov], errors='coerce').fillna(0)
                lag_med_poeng["Totalt"] = lag_med_poeng["Øvelse 1"] + lag_med_poeng["Øvelse 2"] + lag_med_poeng["Øvelse 3"]
                
                rod_df = lag_med_poeng[lag_med_poeng["Lag"] == LAG_A]
                gul_df = lag_med_poeng[lag_med_poeng["Lag"] == LAG_B]
                rod_total, gul_total = int(rod_df["Totalt"].sum()), int(gul_df["Totalt"].sum())
                rod_ov1, rod_ov2, rod_ov3 = int(rod_df["Øvelse 1"].sum()), int(rod_df["Øvelse 2"].sum()), int(rod_df["Øvelse 3"].sum())
                gul_ov1, gul_ov2, gul_ov3 = int(gul_df["Øvelse 1"].sum()), int(gul_df["Øvelse 2"].sum()), int(gul_df["Øvelse 3"].sum())
                
                if rod_total > gul_total:
                    ledertekst = f"🔴 {LAG_A} leder med {rod_total - gul_total} poeng!"
                elif gul_total > rod_total:
                    ledertekst = f"🟡 {LAG_B} leder med {gul_total - rod_total} poeng!"
                else:
                    ledertekst = "⚖️ Det er helt likt!"
                
                st.markdown(f"### {ledertekst}")
                
                mk1, mk2 = st.columns(2)
                with mk1:
                    st.metric(f"🔴 {LAG_A}", f"{rod_total} poeng", delta=f"{len(rod_df)} spillere")
                with mk2:
                    st.metric(f"🟡 {LAG_B}", f"{gul_total} poeng", delta=f"{len(gul_df)} spillere")
                
                st.markdown("### Poengfordeling per øvelse")
                bar_data = pd.DataFrame({
                    "Lag": [LAG_A, LAG_B],
                    "Øvelse 1": [rod_ov1, gul_ov1],
                    "Øvelse 2": [rod_ov2, gul_ov2],
                    "Øvelse 3": [rod_ov3, gul_ov3],
                }).set_index("Lag")
                st.bar_chart(bar_data, color=["#EF4444", "#F59E0B", "#10B981"])
                
                st.markdown("---")
                d_kol1, d_kol2 = st.columns(2)
                with d_kol1:
                    st.markdown(f"#### 🔴 {LAG_A} — Individuelle bidrag")
                    rod_vis = rod_df[["ID", "Navn", "Kull", "Øvelse 1", "Øvelse 2", "Øvelse 3", "Totalt"]].sort_values("Totalt", ascending=False).reset_index(drop=True)
                    st.dataframe(rod_vis, use_container_width=True, hide_index=True)
                with d_kol2:
                    st.markdown(f"#### 🟡 {LAG_B} — Individuelle bidrag")
                    gul_vis = gul_df[["ID", "Navn", "Kull", "Øvelse 1", "Øvelse 2", "Øvelse 3", "Totalt"]].sort_values("Totalt", ascending=False).reset_index(drop=True)
                    st.dataframe(gul_vis, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.markdown("### Poeng per kull")
                kull_lag_df = lag_med_poeng.groupby(["Kull", "Lag"])["Totalt"].sum().unstack(fill_value=0)
                if not kull_lag_df.empty:
                    st.bar_chart(kull_lag_df)


# ═════════════════════════════════════════════════════════════════════════════
#  📊 INFORMASJON
# ═════════════════════════════════════════════════════════════════════════════

elif side == "📊 Informasjon":
    st.title("Festivalinformasjon og statistikk")
    total_registrerte = len(st.session_state.df)
    kategoritelling = st.session_state.df["Kategori"].value_counts()
    avdelingstelling = st.session_state.df["Avdeling"].value_counts()
    antall_rod = len(st.session_state.df[st.session_state.df["Lag"] == LAG_A])
    antall_gul = len(st.session_state.df[st.session_state.df["Lag"] == LAG_B])
    mangler_lag = len(st.session_state.df[(st.session_state.df["Kategori"] == "Elev") & (st.session_state.df["Lag"] == "")])

    m_kol1, m_kol2, m_kol3 = st.columns(3)
    with m_kol1:
        st.metric("Totalt registrerte", f"{total_registrerte} personer")
        st.metric("Elever på rød", f"{antall_rod} stk")
    with m_kol2:
        st.metric("Elever totalt", f"{kategoritelling.get('Elev', 0)} stk")
        st.metric("Elever på gul", f"{antall_gul} stk")
    with m_kol3:
        st.metric("Frivillige mannskap", f"{kategoritelling.get('Frivillig', 0)} stk")
        st.metric("Mangler laginndeling", f"{mangler_lag} elever")

    st.markdown("---")
    info_k1, info_k2 = st.columns(2)
    with info_k1:
        st.subheader("Fordelt på roller")
        for kat in KATEGORIER:
            st.write(f"**{kat}**: {kategoritelling.get(kat, 0)} personer")
    with info_k2:
        st.subheader("Fordelt på avdeling")
        for avd in AVDELINGER:
            st.write(f"**{avd}**: {avdelingstelling.get(avd, 0)} personer")


# ═════════════════════════════════════════════════════════════════════════════
#  📜 HISTORIKK (med Bruker/Admin-filtrering)
# ═════════════════════════════════════════════════════════════════════════════

elif side == "📜 Historikk":
    st.title("Systemhistorikk og endringslogg")
    logg_data = st.session_state.logg_df.copy()
    
    if logg_data.empty:
        st.info("Ingen historikk ennå.")
    else:
        filt_kol1, filt_kol2 = st.columns(2)
        with filt_kol1:
            rolle_filter = st.selectbox("Filtrer på rolle", ["Alle", "🔒 Admin", "👤 Bruker"], key="hist_rolle")
        with filt_kol2:
            handling_filter = st.selectbox(
                "Filtrer på handlingstype", 
                ["Alle"] + sorted(logg_data["Handling"].unique().tolist()), 
                key="hist_handling"
            )
        
        vis_logg = logg_data.copy()
        if rolle_filter != "Alle":
            vis_logg = vis_logg[vis_logg["Rolle"] == rolle_filter]
        if handling_filter != "Alle":
            vis_logg = vis_logg[vis_logg["Handling"] == handling_filter]
        
        st.markdown(f"Viser **{len(vis_logg)}** av {len(logg_data)} loggoppføringer.")
        st.dataframe(
            vis_logg, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Tidspunkt": st.column_config.TextColumn("Tidspunkt", width="medium"),
                "Rolle": st.column_config.TextColumn("Utført av", width="small"),
                "Handling": st.column_config.TextColumn("Handling", width="small"),
                "Detaljer": st.column_config.TextColumn("Detaljer", width="large"),
            }
        )


# ═════════════════════════════════════════════════════════════════════════════
#  ⚙️ ADMIN-MENY
# ═════════════════════════════════════════════════════════════════════════════

elif side == "⚙️ Admin-meny":
    st.title("⚙️ Kontrollpanel for Administrator")
    
    if not st.session_state.is_admin:
        st.subheader("Sikkerhetsinnlogging")
        passord_input = st.text_input("Vennligst oppgi admin-passord for å låse opp", type="password")
        if st.button("Lås opp meny"):
            if passord_input == st.session_state.innstillinger.get("passord", "Admin2026"):
                st.session_state.is_admin = True
                st.success("Innlogging godkjent. Rettigheter aktivert.")
                st.rerun()
            else:
                st.error("Ugyldig passord.")
    else:
        st.success("🔒 Du har full administratortilgang.")
        st.markdown("---")
        st.subheader("Rettigheter og adgangskontroll")
        
        c_nullstill = st.checkbox("Lås full systemnullstilling (Faresone)", value=(str(st.session_state.innstillinger.get("las_nullstill", "True")) == "True"))
        c_autofordel = st.checkbox("Lås automatisk lagfordeling", value=(str(st.session_state.innstillinger.get("las_autofordel", "True")) == "True"))
        c_import = st.checkbox("Lås filimport fra Excel/CSV", value=(str(st.session_state.innstillinger.get("las_import", "True")) == "True"))
        c_slett = st.checkbox("Lås sletting av enkelt-deltakere", value=(str(st.session_state.innstillinger.get("las_slett_enkel", "True")) == "True"))
        c_poeng = st.checkbox("Lås Poeng & Resultater menyen", value=(str(st.session_state.innstillinger.get("las_poengforing", "True")) == "True"))
        
        if st.button("💾 Lagre konfigurasjon"):
            st.session_state.innstillinger["las_nullstill"] = "True" if c_nullstill else "False"
            st.session_state.innstillinger["las_autofordel"] = "True" if c_autofordel else "False"
            st.session_state.innstillinger["las_import"] = "True" if c_import else "False"
            st.session_state.innstillinger["las_slett_enkel"] = "True" if c_slett else "False"
            st.session_state.innstillinger["las_poengforing"] = "True" if c_poeng else "False"
            lagre_innstillinger()
            loggfor_handling("Admin", "Rettighetsmatrisen ble oppdatert")
            st.success("Rettighetsmatrisen ble oppdatert og lagret til skyen!")
            
        st.markdown("---")
        st.subheader("Endre administratorpassord")
        nytt_passord = st.text_input("Skriv inn nytt master-passord", type="password")
        gjenta_passord = st.text_input("Gjenta det nye master-passordet", type="password")
        
        if st.button("Oppdater passord"):
            if not nytt_passord.strip():
                st.warning("Passordet kan ikke være tomt.")
            elif nytt_passord != gjenta_passord:
                st.error("Passordene er ikke like.")
            else:
                st.session_state.innstillinger["passord"] = nytt_passord.strip()
                lagre_innstillinger()
                loggfor_handling("Admin", "Admin-passord ble endret")
                st.success("Admin-passordet ble endret og synkronisert!")
