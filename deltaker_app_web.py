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

    # ── Filimport ────────────────────────────────────────────────────────
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
        try:
            if opplastet_fil.name.endswith(".xlsx"):
                ny_df = pd.read_excel(opplastet_fil, dtype=str).fillna("")
            else:
                ny_df = pd.read_csv(opplastet_fil, dtype=str).fillna("")
            
            st.write(f"Filen inneholder **{len(ny_df)} rader**. Forhåndsvisning:")
            st.dataframe(ny_df.head(10), use_container_width=True, hide_index=True)
            
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
#  🏁 LAGINNDELING (NÅ MED AVANSERT FILTRERING OG SORTERING)
# ═════════════════════════════════════════════════════════════════════════════

elif side == "🏁 Laginndeling":
    st.title("Laginndeling og balansering")
    tilgang_fordel = har_tilgang("las_autofordel")
    
    # ── Hurtigknapper ─────────────────────────────────────────────────
    b_kol1, b_kol2 = st.columns(2)
    with b_kol1:
        autofordel_tekst = "✨ Hurtig auto-fordel ufordelte elever" if tilgang_fordel else "✨ Auto-fordel (Admin)"
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
                loggfor_handling("Hurtig laginndeling", f"Balanserte {len(indekser)} elever")
                lagre_alle_data()
                st.rerun()
                
    with b_kol2:
        omfordel_tekst = "⚠️ Nullstill og fordel alle på nytt" if tilgang_fordel else "⚠️ Omgjør lag (Admin)"
        if st.button(omfordel_tekst, disabled=not tilgang_fordel, use_container_width=True):
            elever = st.session_state.df[st.session_state.df["Kategori"] == "Elev"].copy()
            indekser = elever.index.tolist()
            random.shuffle(indekser)
            midt = len(indekser) // 2
            for i, idx_val in enumerate(indekser):
                st.session_state.df.at[idx_val, "Lag"] = LAG_A if i < midt else LAG_B
            st.session_state.df.loc[st.session_state.