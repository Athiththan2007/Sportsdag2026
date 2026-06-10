import streamlit as st
import pandas as pd
import random
import io
from datetime import datetime
from github import Github

try:
    from weasyprint import HTML
    PDF_TILGJENGELIG = True
except ImportError:
    PDF_TILGJENGELIG = False

KATEGORIER = ["Elev", "நிர்வாகம்", "Lærer", "Frivillig", "Gjest"]
AVDELINGER = ["Ålesund", "Ulsteinvik", "Florø"]
LAG_A = "Lag Rød"
LAG_B = "Lag Gul"

# Aldersgrupper for sportsfestivalen (slik dei er definert i programmet)
KULL_GRUPPER = [
    "2023",        # 3 år
    "2022",        # 4 år
    "2021",        # 5 år
    "2020",        # 6 år
    "2019-2018",   # 7-8 år
    "2017-2016",   # 9-10 år
    "2015-2014",   # 11-12 år
    "2013-2012",   # 13-14 år
    "2011-2010",   # 15-16 år
    "2009-2008",   # 17-18 år
]

# Aldersgrupper for vaksne deltakere (frivillige, lærarar, gjestar osv.)
VOKSEN_GRUPPER = [
    "18-25",
    "25-35",
    "35-45",
    "45+",
]

ALLE_KULL_GRUPPER = KULL_GRUPPER + VOKSEN_GRUPPER

def alder_til_voksengruppe(alder_str):
    """Konverter ein alder (t.d. '32' eller '32 år' eller '32år') til vaksengruppe."""
    if not alder_str or not str(alder_str).strip():
        return ""
    s = str(alder_str).strip().lower()
    s = s.replace("år", "").replace("ar", "").strip()
    try:
        alder = int(s)
    except ValueError:
        return ""
    if 18 <= alder < 25:
        return "18-25"
    elif 25 <= alder < 35:
        return "25-35"
    elif 35 <= alder < 45:
        return "35-45"
    elif alder >= 45:
        return "45+"
    return ""

def kull_til_gruppe(kull):
    """Konverter eit kull-felt (enkeltår, alder, eller gruppe) til gruppe-format."""
    if not kull or not str(kull).strip():
        return ""
    kull_str = str(kull).strip()
    # Allereie ei gyldig gruppe (born eller vaksen)
    if kull_str in ALLE_KULL_GRUPPER:
        return kull_str
    # Sjekk om det er skrive som alder (t.d. "32 år", "18år")
    if "år" in kull_str.lower() or "ar" in kull_str.lower():
        gruppe = alder_til_voksengruppe(kull_str)
        if gruppe:
            return gruppe
    try:
        tal = int(kull_str)
        # Skil mellom fødselsår (4-sifra, typisk 1900-2030) og alder (1-120)
        if tal >= 1900:
            year = tal
            if year >= 2020:
                return str(year)
            elif year in (2019, 2018):  return "2019-2018"
            elif year in (2017, 2016):  return "2017-2016"
            elif year in (2015, 2014):  return "2015-2014"
            elif year in (2013, 2012):  return "2013-2012"
            elif year in (2011, 2010):  return "2011-2010"
            elif year in (2009, 2008):  return "2009-2008"
            else:
                # Eldre fødselsår → rekn ut alder basert på festivalåret 2026
                alder = 2026 - year
                gruppe = alder_til_voksengruppe(str(alder))
                if gruppe:
                    return gruppe
        else:
            # Tolk som alder direkte
            gruppe = alder_til_voksengruppe(str(tal))
            if gruppe:
                return gruppe
    except ValueError:
        pass
    return kull_str

def ikoniser_lag(lagnavn):
    if lagnavn == LAG_A: return f"🔴 {LAG_A}"
    elif lagnavn == LAG_B: return f"🟡 {LAG_B}"
    return "⚪ Ufordelt"

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
    st.session_state.lagspill_kolonner = ["Spill", "Lag Rød", "Lag Gul"]


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
        # Migrer Kull frå enkeltår til gruppe-format
        df["Kull"] = df["Kull"].apply(kull_til_gruppe)
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

def last_inn_lagspill():
    df = les_fra_github("sportsfestival_lagspill.csv")
    if not df.empty:
        df = df.fillna("0")
        if "Lag Rød" not in df.columns: df["Lag Rød"] = "0"
        if "Lag Gul" not in df.columns: df["Lag Gul"] = "0"
        return df
    return pd.DataFrame(columns=st.session_state.lagspill_kolonner)

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
if "lagspill_df" not in st.session_state:
    st.session_state.lagspill_df = last_inn_lagspill()

def lagre_alle_data():
    with st.spinner("Synkroniserer endringer med GitHub..."):
        s1 = lagre_til_github(st.session_state.df, "sportsfestival_data.csv")
        s2 = lagre_til_github(st.session_state.logg_df, "sportsfestival_logg.csv")
        s3 = lagre_til_github(st.session_state.poeng_df, "sportsfestival_poeng.csv")
        s4 = lagre_til_github(st.session_state.lagspill_df, "sportsfestival_lagspill.csv")
        return s1 and s2 and s3 and s4

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
        navn = st.text_input("Fullt navn", key="ny_navn")
        kategori = st.selectbox("Kategori", KATEGORIER, key="ny_kategori")
        avdeling = st.selectbox("Avdeling", AVDELINGER, key="ny_avdeling")
        
        kol1, kol2 = st.columns(2)
        with kol1:
            kull_modus = st.radio(
                "Kull / Aldersgruppe",
                ["Velg fra liste", "Skriv inn manuelt"],
                horizontal=True,
                key="ny_kull_modus",
                help="Born: velg fødselsårsgruppe. Vaksne: velg aldersgruppe (18-25, 25-35, 35-45, 45+) eller skriv inn alder/fødselsår manuelt."
            )
            if kull_modus == "Velg fra liste":
                kull = st.selectbox(
                    "Kull / Aldersgruppe",
                    [""] + ALLE_KULL_GRUPPER,
                    label_visibility="collapsed",
                    help="Born: 2008-2023 (fødselsårsgrupper). Voksne: 18-25, 25-35, 35-45, 45+"
                )
            else:
                kull_manuell = st.text_input(
                    "Skriv inn alder eller fødselsår",
                    label_visibility="collapsed",
                    placeholder="F.eks. 32, 32 år, eller 1994",
                    help="Skriv inn alder (t.d. '32' eller '32 år') eller fødselsår (t.d. '1994'). Konverteres automatisk til riktig gruppe."
                )
                kull = kull_til_gruppe(kull_manuell) if kull_manuell.strip() else ""
                if kull_manuell.strip() and kull:
                    st.caption(f"→ Plasseres i gruppe: **{kull}**")
                elif kull_manuell.strip() and not kull:
                    st.caption("⚠️ Kunne ikke tolke verdien. Bruk tall (alder eller fødselsår).")
        with kol2:
            kjonn = st.selectbox("Kjønn (valgfritt)", ["", "Gutt", "Jente"], key="ny_kjonn")
            
        opprett_knapp = st.button("Legg til deltaker", type="primary")
        
        if opprett_knapp:
            if not navn.strip():
                st.warning("Navn er et påkrevd felt.")
            else:
                ny_id_num = finn_laveste_ledige_id()
                ny_id_str = f"{ny_id_num:02d}"
                kull_verdi = kull.strip() if kull else ""
                kjonn_verdi = kjonn
                ny_rad = pd.DataFrame([[ny_id_str, navn.strip(), kategori, kull_verdi, kjonn_verdi, avdeling, ""]], columns=st.session_state.kolonner)
                st.session_state.df = pd.concat([st.session_state.df, ny_rad], ignore_index=True)
                loggfor_handling("Lagt til", f"ID {ny_id_str}: {navn} ({kategori}, {avdeling}, kull={kull_verdi or '–'})")
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
            nv_kat = st.session_state.df.at[idx, "Kategori"]
            kat_idx = KATEGORIER.index(nv_kat) if nv_kat in KATEGORIER else 0
            oppdatert_kat = st.selectbox("Kategori", KATEGORIER, index=kat_idx)
            
            na_avd = st.session_state.df.at[idx, "Avdeling"]
            if na_avd not in AVDELINGER: na_avd = "Ålesund"
            oppdatert_avd = st.selectbox("Avdeling", AVDELINGER, index=AVDELINGER.index(na_avd))
            
            kol_e1, kol_e2 = st.columns(2)
            with kol_e1:
                nv_kull = kull_til_gruppe(st.session_state.df.at[idx, "Kull"])
                edit_kull_modus = st.radio(
                    "Kull / Aldersgruppe",
                    ["Velg fra liste", "Skriv inn manuelt"],
                    horizontal=True,
                    key="edit_kull_modus"
                )
                if edit_kull_modus == "Velg fra liste":
                    kull_alt = [""] + ALLE_KULL_GRUPPER
                    kull_idx = kull_alt.index(nv_kull) if nv_kull in kull_alt else 0
                    oppdatert_kull = st.selectbox(
                        "Kull / Aldersgruppe", kull_alt, index=kull_idx,
                        label_visibility="collapsed"
                    )
                else:
                    kull_manuell_e = st.text_input(
                        "Skriv inn alder eller fødselsår",
                        value=nv_kull if nv_kull not in ALLE_KULL_GRUPPER else "",
                        label_visibility="collapsed",
                        placeholder="F.eks. 32, 32 år, eller 1994"
                    )
                    oppdatert_kull = kull_til_gruppe(kull_manuell_e) if kull_manuell_e.strip() else ""
                    if kull_manuell_e.strip() and oppdatert_kull:
                        st.caption(f"→ Plasseres i gruppe: **{oppdatert_kull}**")
                    elif kull_manuell_e.strip() and not oppdatert_kull:
                        st.caption("⚠️ Kunne ikke tolke verdien. Bruk tall (alder eller fødselsår).")
            with kol_e2:
                nåværende_kjønn = st.session_state.df.at[idx, "Kjønn"]
                kjønn_index = 0
                if nåværende_kjønn == "Gutt": kjønn_index = 1
                elif nåværende_kjønn == "Jente": kjønn_index = 2
                oppdatert_kjonn = st.selectbox("Kjønn (valgfritt)", ["", "Gutt", "Jente"], index=kjønn_index)
            
            kol1, kol2 = st.columns(2)
            with kol1:
                if st.button("💾 Oppdater informasjon", use_container_width=True):
                    gammelt_navn = st.session_state.df.at[idx, "Navn"]
                    st.session_state.df.at[idx, "Navn"] = oppdatert_navn.strip()
                    st.session_state.df.at[idx, "Kategori"] = oppdatert_kat
                    st.session_state.df.at[idx, "Avdeling"] = oppdatert_avd
                    st.session_state.df.at[idx, "Kull"] = oppdatert_kull.strip() if oppdatert_kull else ""
                    st.session_state.df.at[idx, "Kjønn"] = oppdatert_kjonn
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
        # Guard: reset import state when a new file is uploaded
        if st.session_state.get("_import_filnavn") != opplastet_fil.name:
            st.session_state["_import_filnavn"] = opplastet_fil.name
            st.session_state["_import_ferdig"] = False
        
        if not st.session_state.get("_import_ferdig", False):
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
                            importert_kull = kull_til_gruppe(rad.get("Kull", ""))
                            importert_kjonn = rad.get("Kjønn", "")
                            
                            midlertidig_rad = pd.DataFrame(
                                [[neste_id_str, importert_navn, importert_kat, importert_kull, importert_kjonn, importert_avd, ""]], 
                                columns=st.session_state.kolonner
                            )
                            st.session_state.df = pd.concat([st.session_state.df, midlertidig_rad], ignore_index=True)
                            eksisterende_navn.add(navn_sjekk)
                            importert_teller += 1
                    
                    loggfor_handling("Import", f"Importerte {importert_teller} nye. Ignorerte {hoppet_over_teller} duplikater.")
                    lagre_alle_data()
                    st.session_state["_import_ferdig"] = True
                    st.success(f"La til {importert_teller} nye og hoppet over {hoppet_over_teller} duplikater.")
                    st.rerun()
            except Exception as e:
                st.error(f"Kunne ikke tolke filen: {e}")

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
        st.session_state.lagspill_df = last_inn_lagspill()
        st.rerun()

    st.markdown("---")
    st.subheader("🧹 Opprydding og sikkerhetssjekk")
    
    if st.button("🔍 Skann etter duplikater"):
        midlertidig_df = st.session_state.df.copy()
        midlertidig_df["_sokekode"] = midlertidig_df["Navn"].str.lower().str.strip() + "|" + midlertidig_df["Kategori"]
        duplikat_mask = midlertidig_df.duplicated(subset=["_sokekode"], keep="first")
        duplikater = midlertidig_df[duplikat_mask].drop(columns=["_sokekode"])
        
        if duplikater.empty:
            st.success("✅ Ingen duplikater funnet i systemet.")
        else:
            st.session_state["_duplikater_funnet"] = True
            st.session_state["_duplikat_ider"] = duplikater["ID"].tolist()
            
            dup_med_poeng = pd.merge(
                duplikater[["ID", "Navn", "Kategori", "Kull", "Kjønn", "Avdeling", "Lag"]],
                st.session_state.poeng_df, on="ID", how="left"
            ).fillna("0")
            for ov in ["Øvelse 1", "Øvelse 2", "Øvelse 3"]:
                dup_med_poeng[ov] = pd.to_numeric(dup_med_poeng[ov], errors="coerce").fillna(0).astype(int)
            dup_med_poeng["Totalt"] = dup_med_poeng["Øvelse 1"] + dup_med_poeng["Øvelse 2"] + dup_med_poeng["Øvelse 3"]
            
            st.warning(f"⚠️ Fant **{len(duplikater)} duplikater** som vil bli fjernet:")
            
            kat_tell = duplikater["Kategori"].value_counts()
            med_lag = len(duplikater[duplikater["Lag"] != ""])
            med_poeng = len(dup_med_poeng[dup_med_poeng["Totalt"] > 0])
            
            opps_k1, opps_k2, opps_k3, opps_k4 = st.columns(4)
            with opps_k1:
                st.metric("Totalt duplikater", f"{len(duplikater)} stk")
            with opps_k2:
                st.metric("Har lagfordeling", f"{med_lag} stk")
            with opps_k3:
                st.metric("Har poeng", f"{med_poeng} stk")
            with opps_k4:
                st.metric("Kategorier", ", ".join(f"{k}: {v}" for k, v in kat_tell.items()))
            
            with st.expander("📋 Se full liste over duplikater som fjernes", expanded=True):
                vis_kols = ["ID", "Navn", "Kategori", "Avdeling", "Lag", "Øvelse 1", "Øvelse 2", "Øvelse 3", "Totalt"]
                st.dataframe(dup_med_poeng[vis_kols], use_container_width=True, hide_index=True)
    
    if st.session_state.get("_duplikater_funnet", False):
        dup_ider = st.session_state.get("_duplikat_ider", [])
        if dup_ider:
            if st.button(f"🗑️ Bekreft: Fjern {len(dup_ider)} duplikater permanent", type="primary"):
                midlertidig_df = st.session_state.df.copy()
                midlertidig_df["_sokekode"] = midlertidig_df["Navn"].str.lower().str.strip() + "|" + midlertidig_df["Kategori"]
                midlertidig_df = midlertidig_df.drop_duplicates(subset=["_sokekode"], keep="first")
                st.session_state.df = midlertidig_df.drop(columns=["_sokekode"]).reset_index(drop=True)
                
                gjenværende_ider = set(st.session_state.df["ID"].tolist())
                st.session_state.poeng_df = st.session_state.poeng_df[st.session_state.poeng_df["ID"].isin(gjenværende_ider)].reset_index(drop=True)
                
                loggfor_handling("Opprydding", f"Fjernet {len(dup_ider)} duplikater med forhåndsvisning og bekreftelse.")
                lagre_alle_data()
                
                st.session_state["_duplikater_funnet"] = False
                st.session_state["_duplikat_ider"] = []
                st.success(f"Fjernet {len(dup_ider)} duplikater og ryddet tilhørende poengdata.")
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
        st.session_state.lagspill_df = pd.DataFrame(columns=st.session_state.lagspill_kolonner)
        loggfor_handling("Systemnullstilling", "Alt slettet av administrator.")
        if lagre_alle_data():
            st.success("Hele systemet har blitt nullstilt!")
            st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  🏁 LAGINNDELING
# ═════════════════════════════════════════════════════════════════════════════

elif side == "🏁 Laginndeling":
    st.title("Laginndeling og balansering")
    tilgang_fordel = har_tilgang("las_autofordel")
    
    st.markdown("### 🔍 Filtrer visning")
    # Søkefelt øverst — for rask å finne person på namn
    sok_navn = st.text_input("🔎 Søk på navn", placeholder="Skriv inn navn for å filtrere", key="lag_sok")
    
    f_kol1, f_kol2, f_kol3, f_kol4 = st.columns(4)
    with f_kol1:
        f_avd = st.multiselect("Avdeling", AVDELINGER, default=AVDELINGER)
    with f_kol2:
        f_kat = st.multiselect("Kategori", KATEGORIER, default=["Elev"])
    with f_kol3:
        f_kull = st.multiselect("Kull", ALLE_KULL_GRUPPER, default=ALLE_KULL_GRUPPER)
    with f_kol4:
        f_kjonn = st.multiselect("Kjønn", ["Gutt", "Jente", ""], default=["Gutt", "Jente", ""])
        
    f_mask = pd.Series(True, index=st.session_state.df.index)
    if f_avd: f_mask &= st.session_state.df["Avdeling"].isin(f_avd)
    if f_kat: f_mask &= st.session_state.df["Kategori"].isin(f_kat)
    if f_kull: f_mask &= (st.session_state.df["Kull"].isin(f_kull) | (st.session_state.df["Kull"] == ""))
    if f_kjonn: f_mask &= st.session_state.df["Kjønn"].isin(f_kjonn)
    if sok_navn.strip():
        f_mask &= st.session_state.df["Navn"].str.contains(sok_navn.strip(), case=False, na=False)
    
    filtrert_df = st.session_state.df[f_mask]
    
    st.markdown("---")
    b_kol1, b_kol2 = st.columns(2)
    with b_kol1:
        autofordel_tekst = "✨ Auto-fordel utvalget (Balansert)" if tilgang_fordel else "✨ Auto-fordel (Admin)"
        if st.button(autofordel_tekst, disabled=not tilgang_fordel, use_container_width=True, type="primary"):
            ufordelte_i_visning = filtrert_df[filtrert_df["Lag"] == ""]
            if ufordelte_i_visning.empty:
                st.info("Ingen ufordelte deltakere matcher det valgte filteret.")
            else:
                antall_a = len(st.session_state.df[st.session_state.df["Lag"] == LAG_A])
                antall_b = len(st.session_state.df[st.session_state.df["Lag"] == LAG_B])
                
                tmp = ufordelte_i_visning.copy()
                tmp["_kull_g"] = tmp["Kull"].fillna("").replace("", "_voksen")
                tmp["_kjonn_g"] = tmp["Kjønn"].fillna("").replace("", "_ukjent")
                grupper = tmp.groupby(["_kull_g", "_kjonn_g"])
                for _, gruppe in grupper:
                    indekser = gruppe.index.tolist()
                    random.shuffle(indekser)
                    for idx_val in indekser:
                        if antall_a <= antall_b:
                            st.session_state.df.at[idx_val, "Lag"] = LAG_A
                            antall_a += 1
                        else:
                            st.session_state.df.at[idx_val, "Lag"] = LAG_B
                            antall_b += 1
                            
                loggfor_handling("Avansert Laginndeling", f"Balanserte {len(ufordelte_i_visning)} deltakere fra gjeldende filter.")
                lagre_alle_data()
                st.success(f"Suksess! {len(ufordelte_i_visning)} personer ble balansert fordelt i lag.")
                st.rerun()
                
    with b_kol2:
        nullstill_tekst = "⚠️ Nullstill laginndeling" if tilgang_fordel else "⚠️ Nullstill lag (Admin)"
        if st.button(nullstill_tekst, disabled=not tilgang_fordel, use_container_width=True):
            antall_nullstilt = len(st.session_state.df[st.session_state.df["Lag"] != ""])
            st.session_state.df["Lag"] = ""
            loggfor_handling("Laginndeling", f"Nullstilte lagtilhørighet for alle {antall_nullstilt} deltakere")
            lagre_alle_data()
            st.rerun()

    st.markdown("---")
    with st.expander("📥 Importer laginndeling fra fil"):
        if not tilgang_fordel:
            st.info("Import av laginndeling er låst bak admin-tilgang.")
        
        import_lag_fil = st.file_uploader("Last opp CSV eller Excel med kolonner for 'ID' og 'Lag'", type=["csv", "xlsx"], key="import_lag_uploader", disabled=not tilgang_fordel)
        
        if import_lag_fil and tilgang_fordel:
            try:
                if import_lag_fil.name.endswith(".xlsx"):
                    import_df = pd.read_excel(import_lag_fil, dtype=str).fillna("")
                else:
                    import_df = pd.read_csv(import_lag_fil, dtype=str).fillna("")
                
                if "ID" not in import_df.columns or "Lag" not in import_df.columns:
                    st.error("Filen må inneholde kolonnene 'ID' og 'Lag'.")
                else:
                    st.write(f"Fant {len(import_df)} rader. Forhåndsvisning:")
                    st.dataframe(import_df[["ID", "Navn", "Lag"]].head(5) if "Navn" in import_df.columns else import_df.head(5), use_container_width=True, hide_index=True)
                    
                    if st.button("📥 Oppdater laginndeling med denne filen", type="primary"):
                        oppdatert_teller = 0
                        for _, rad in import_df.iterrows():
                            pid = str(rad["ID"]).strip()
                            nytt_lag = str(rad["Lag"]).strip()
                            
                            if pid in st.session_state.df["ID"].values:
                                idx = st.session_state.df.index[st.session_state.df["ID"] == pid].tolist()[0]
                                if st.session_state.df.at[idx, "Lag"] != nytt_lag:
                                    st.session_state.df.at[idx, "Lag"] = nytt_lag
                                    oppdatert_teller += 1
                        
                        loggfor_handling("Import", f"Oppdaterte lag for {oppdatert_teller} deltakere via fil.")
                        lagre_alle_data()
                        st.success(f"Laginndelingen ble oppdatert for {oppdatert_teller} deltakere!")
                        st.rerun()
            except Exception as e:
                st.error(f"Kunne ikke lese filen: {e}")

    st.markdown("---")
    st.subheader("🖨️ Utskrift og Eksport")
    
    ut_k1, ut_k2, ut_k3, ut_k4 = st.columns(4)
    with ut_k1:
        utskrift_avd = st.multiselect("Avdeling", AVDELINGER, default=AVDELINGER, key="print_avd")
    with ut_k2:
        utskrift_kat = st.multiselect("Kategori", KATEGORIER, default=["Elev"], key="print_kat")
    with ut_k3:
        alle_print_kull = ALLE_KULL_GRUPPER
        utskrift_kull = st.multiselect("Kull / Aldersgruppe", alle_print_kull, default=alle_print_kull, key="print_kull")
    with ut_k4:
        sortering = st.selectbox("Sorter etter", ["Navn", "Kull", "Avdeling", "Kjønn", "ID"], key="print_sort")
    
    eksport_mask = (
        (st.session_state.df["Lag"] != "") & 
        (st.session_state.df["Avdeling"].isin(utskrift_avd)) &
        (st.session_state.df["Kategori"].isin(utskrift_kat))
    )
    if utskrift_kull:
        eksport_mask &= (st.session_state.df["Kull"].isin(utskrift_kull) | (st.session_state.df["Kull"] == ""))
    
    eksport_df = st.session_state.df[eksport_mask].sort_values(by=sortering).reset_index(drop=True)
    
    st.caption(f"Utvalget inneholder {len(eksport_df)} deltakere fra {len(utskrift_avd)} avdeling(er) og {len(utskrift_kat)} kategori(er).")
    
    eks_kol1, eks_kol2, eks_kol3 = st.columns(3)
    with eks_kol1:
        csv_data = eksport_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("💾 CSV", data=csv_data, file_name="lagfordeling.csv", mime="text/csv", use_container_width=True)
    
    df_a_print = eksport_df[eksport_df["Lag"] == LAG_A]
    df_b_print = eksport_df[eksport_df["Lag"] == LAG_B]
    
    filter_tekst = f"{', '.join(utskrift_avd)}  ·  {', '.join(utskrift_kat)}  ·  Sortert: {sortering}"
    if utskrift_kull and len(utskrift_kull) < len(alle_print_kull):
        filter_tekst += f"  ·  Kull: {', '.join(utskrift_kull)}"
    
    def _rader(df_lag):
        r = ""
        for i, (_, p) in enumerate(df_lag.iterrows()):
            r += f'<tr><td class="id">{p["ID"]}</td><td class="navn">{p["Navn"]}</td><td>{p["Kull"]}</td><td>{p["Avdeling"]}</td></tr>'
        return r
    
    dok_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
@page {{ size: A4; margin: 22mm 20mm; }}
body {{ font-family: 'Inter', 'Noto Sans Tamil', Helvetica, Arial, sans-serif; color: #111; font-size: 10px; line-height: 1.45; margin: 0; padding: 0; }}

.title {{ font-size: 20px; font-weight: 300; letter-spacing: 3px; text-transform: uppercase; color: #111; margin: 0 0 2px 0; }}
.org {{ font-size: 9px; color: #999; letter-spacing: 1px; margin-bottom: 20px; }}
.line {{ height: 1px; background: #111; margin-bottom: 14px; }}
.meta {{ font-size: 8px; color: #888; margin-bottom: 24px; letter-spacing: 0.3px; }}

.counts {{ margin-bottom: 22px; }}
.counts table {{ width: 100%; border: none; }}
.counts td {{ text-align: center; padding: 0; }}
.counts .n {{ font-size: 28px; font-weight: 300; color: #111; letter-spacing: 1px; }}
.counts .n-red {{ font-size: 28px; font-weight: 300; color: #c0392b; letter-spacing: 1px; }}
.counts .n-yel {{ font-size: 28px; font-weight: 300; color: #c89000; letter-spacing: 1px; }}
.counts .lbl {{ font-size: 7px; color: #aaa; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 1px; }}

.team-section {{ page-break-inside: auto; }}
.team-section:not(:first-of-type) {{ page-break-before: auto; }}
table.data {{ width: 100%; border-collapse: collapse; margin-bottom: 18px; }}
table.data thead {{ display: table-header-group; }}
table.data tr {{ page-break-inside: avoid; }}
table.data th.team-header-red {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 12px 4px 7px;
    text-align: left;
    border-bottom: 2px solid #c0392b;
    color: #c0392b;
    background: white;
}}
table.data th.team-header-yel {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 12px 4px 7px;
    text-align: left;
    border-bottom: 2px solid #c89000;
    color: #c89000;
    background: white;
}}
table.data th.team-header-red span,
table.data th.team-header-yel span {{
    font-weight: 300;
    font-size: 10px;
    color: #999;
    float: right;
    text-transform: none;
    letter-spacing: 0;
    margin-top: 4px;
}}
table.data th {{
    font-size: 7px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #999;
    padding: 6px 4px 4px;
    text-align: left;
    border-bottom: 1px solid #ddd;
    background: white;
}}
table.data td {{
    padding: 4px;
    border-bottom: 1px solid #f0f0f0;
    font-size: 10px;
    color: #333;
}}
table.data td.id {{ color: #bbb; font-size: 9px; }}
table.data td.navn {{ font-weight: 500; color: #111; }}

.footer {{
    margin-top: 30px;
    padding-top: 8px;
    border-top: 1px solid #ddd;
    font-size: 7px;
    color: #bbb;
    letter-spacing: 0.5px;
}}
</style></head>
<body>

<div class="title">Lagfordeling</div>
<div class="org">Sportsfestival 2026</div>
<div class="line"></div>
<div class="meta">{filter_tekst}</div>

<div class="counts">
<table><tr>
<td><div class="n">{len(eksport_df)}</div><div class="lbl">Totalt</div></td>
<td><div class="n-red">{len(df_a_print)}</div><div class="lbl">{LAG_A}</div></td>
<td><div class="n-yel">{len(df_b_print)}</div><div class="lbl">{LAG_B}</div></td>
</tr></table>
</div>

<div class="team-label team-label-red" style="display:none"></div>
<table class="data">
<thead>
<tr><th class="team-header-red" colspan="4">{LAG_A} <span>{len(df_a_print)} deltakere</span></th></tr>
<tr><th>ID</th><th>Navn</th><th>Kull</th><th>Avdeling</th></tr>
</thead>
<tbody>
{_rader(df_a_print)}
</tbody>
</table>

<table class="data">
<thead>
<tr><th class="team-header-yel" colspan="4">{LAG_B} <span>{len(df_b_print)} deltakere</span></th></tr>
<tr><th>ID</th><th>Navn</th><th>Kull</th><th>Avdeling</th></tr>
</thead>
<tbody>
{_rader(df_b_print)}
</tbody>
</table>

<div class="footer">Sportsfestival Admin System</div>

</body></html>"""
    
    with eks_kol2:
        st.download_button("🌐 HTML", data=dok_html, file_name="lagfordeling.html", mime="text/html", use_container_width=True)
    
    with eks_kol3:
        if not PDF_TILGJENGELIG:
            st.info("Installer: `pip install weasyprint`")
        else:
            try:
                pdf_bytes = HTML(string=dok_html).write_pdf()
                st.download_button("📄 PDF", data=pdf_bytes, file_name="lagfordeling.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"PDF-feil: {e}")

    st.markdown("---")
    
    df_rod = filtrert_df[filtrert_df["Lag"] == LAG_A].reset_index()
    df_ufordelt = filtrert_df[filtrert_df["Lag"] == ""].reset_index()
    df_gul = filtrert_df[filtrert_df["Lag"] == LAG_B].reset_index()

    l_kol1, l_kol2, l_kol3 = st.columns(3)
    
    if not tilgang_fordel:
        st.info("🔒 Flyttknappene er låst. Logg inn som admin for å flytte spillere.")

    with l_kol1:
        st.markdown(f"### 🔴 {LAG_A} ({len(df_rod)})")
        for _, r in df_rod.iterrows():
            c1, c2 = st.columns([4, 1])
            with c1:
                kull_vis = f" · {r['Kull']}" if r['Kull'] else ""
                st.text(f"{r['ID']} - {r['Navn']}{kull_vis}")
            with c2:
                if st.button("→🟡", key=f"rod_til_gul_{r['index']}", disabled=not tilgang_fordel):
                    st.session_state.df.at[r["index"], "Lag"] = LAG_B
                    loggfor_handling("Flyttet", f"{r['Navn']} → {LAG_B}")
                    lagre_alle_data()
                    st.rerun()
    
    with l_kol2:
        st.markdown(f"### ⚪ Ufordelte ({len(df_ufordelt)})")
        for _, r in df_ufordelt.iterrows():
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1:
                if st.button("🔴←", key=f"uf_til_rod_{r['index']}", disabled=not tilgang_fordel):
                    st.session_state.df.at[r["index"], "Lag"] = LAG_A
                    loggfor_handling("Fordelt", f"{r['Navn']} → {LAG_A}")
                    lagre_alle_data()
                    st.rerun()
            with c2:
                kull_vis = f" · {r['Kull']}" if r['Kull'] else ""
                st.text(f"{r['ID']} - {r['Navn']}{kull_vis}")
            with c3:
                if st.button("→🟡", key=f"uf_til_gul_{r['index']}", disabled=not tilgang_fordel):
                    st.session_state.df.at[r["index"], "Lag"] = LAG_B
                    loggfor_handling("Fordelt", f"{r['Navn']} → {LAG_B}")
                    lagre_alle_data()
                    st.rerun()
    
    with l_kol3:
        st.markdown(f"### 🟡 {LAG_B} ({len(df_gul)})")
        for _, r in df_gul.iterrows():
            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button("🔴←", key=f"gul_til_rod_{r['index']}", disabled=not tilgang_fordel):
                    st.session_state.df.at[r["index"], "Lag"] = LAG_A
                    loggfor_handling("Flyttet", f"{r['Navn']} → {LAG_A}")
                    lagre_alle_data()
                    st.rerun()
            with c2:
                kull_vis = f" · {r['Kull']}" if r['Kull'] else ""
                st.text(f"{r['ID']} - {r['Navn']}{kull_vis}")

    st.markdown("---")
    st.subheader("Fjern fra lag")
    lag_spillere = filtrert_df[(filtrert_df["Lag"] == LAG_A) | (filtrert_df["Lag"] == LAG_B)]
    if not lag_spillere.empty:
        fjern_valg = st.selectbox("Velg spiller i gjeldende visning å fjerne fra laget", lag_spillere["ID"] + " - " + lag_spillere["Navn"] + " (" + lag_spillere["Lag"] + ")")
        if st.button("❌ Fjern fra lag (sett til ufordelt)"):
            fjern_id = fjern_valg.split(" - ")[0]
            fjern_idx = st.session_state.df.index[st.session_state.df["ID"] == fjern_id].tolist()[0]
            fjern_navn = st.session_state.df.at[fjern_idx, "Navn"]
            st.session_state.df.at[fjern_idx, "Lag"] = ""
            loggfor_handling("Fjernet fra lag", f"{fjern_navn} satt til ufordelt")
            lagre_alle_data()
            st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  🎯 POENG & RESULTATER
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
        
        alle_deltakere_df = st.session_state.df.copy()

        with poeng_fane1:
            st.subheader("Registrer poeng for øvelser")
            st.write("Huk av «Nullstill poeng ⚠️» for å slette poengene til en enkelt deltaker.")
            
            # Søkefelt øverst — over kategori-menyen
            sok_poeng = st.text_input("🔎 Søk på navn", placeholder="Skriv inn navn for å filtrere", key="poeng_sok")
            
            p_kol1, p_kol2, p_kol3 = st.columns(3)
            with p_kol1:
                poeng_kat = st.selectbox("Kategori", ["Alle"] + KATEGORIER, key="poeng_kat")
            with p_kol2:
                valgt_kull = st.selectbox("Kull / Aldersgruppe (valgfritt)", ["Alle"] + ALLE_KULL_GRUPPER, key="poeng_kull")
            with p_kol3:
                valgt_kjonn = st.selectbox("Kjønn (valgfritt)", ["Alle", "Gutt", "Jente"], key="poeng_kjonn")
            
            poeng_mask = pd.Series(True, index=alle_deltakere_df.index)
            if poeng_kat != "Alle":
                poeng_mask &= alle_deltakere_df["Kategori"] == poeng_kat
            if valgt_kull != "Alle":
                if valgt_kull in KULL_GRUPPER and "-" in valgt_kull:
                    aar = valgt_kull.split("-")
                    poeng_mask &= alle_deltakere_df["Kull"].isin([valgt_kull, aar[0], aar[1]])
                else:
                    poeng_mask &= alle_deltakere_df["Kull"] == valgt_kull
            if valgt_kjonn != "Alle":
                poeng_mask &= alle_deltakere_df["Kjønn"] == valgt_kjonn
            if sok_poeng.strip():
                poeng_mask &= alle_deltakere_df["Navn"].str.contains(sok_poeng.strip(), case=False, na=False)
            
            aktuelle = alle_deltakere_df[poeng_mask][["ID", "Navn", "Kategori", "Kull", "Kjønn", "Lag"]].copy()
            
            if poeng_kat == "Alle" and valgt_kull == "Alle" and not sok_poeng.strip():
                st.info("Velg minst en kategori, et kull, eller søk på navn for å føre inn poeng.")
            elif aktuelle.empty:
                st.info("Ingen deltakere matcher det valgte filteret.")
            else:
                redigerings_df = pd.merge(aktuelle, st.session_state.poeng_df, on="ID", how="left").fillna("0")
                redigerings_df["Kjønn"] = redigerings_df["Kjønn"].replace("0", "")
                redigerings_df["Kategori"] = redigerings_df["Kategori"].replace("0", "")
                redigerings_df["Kull"] = redigerings_df["Kull"].replace("0", "")
                
                # Fargekode lagvisning
                redigerings_df["Lag"] = redigerings_df["Lag"].fillna("").apply(ikoniser_lag)
                redigerings_df["Nullstill"] = False
                
                # Sorter kolonnene for en bedre visning i editoren
                redigerings_df = redigerings_df[["ID", "Navn", "Lag", "Kategori", "Kull", "Kjønn", "Øvelse 1", "Øvelse 2", "Øvelse 3", "Nullstill"]]
                
                redigert_data = st.data_editor(
                    redigerings_df,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", disabled=True, width="small"),
                        "Navn": st.column_config.TextColumn("Navn", disabled=True),
                        "Lag": st.column_config.TextColumn("Lag", disabled=True, width="small"),
                        "Kategori": st.column_config.TextColumn("Kategori", disabled=True, width="small"),
                        "Kull": st.column_config.TextColumn("Kull", disabled=True, width="small"),
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
                        
                        main_idx = st.session_state.df.index[st.session_state.df["ID"] == pid].tolist()
                        if main_idx:
                            gammelt_kjonn = st.session_state.df.at[main_idx[0], "Kjønn"]
                            nytt_kjonn = rad["Kjønn"] if pd.notna(rad["Kjønn"]) else ""
                            if gammelt_kjonn != nytt_kjonn:
                                st.session_state.df.at[main_idx[0], "Kjønn"] = nytt_kjonn
                                endret_kjonn_teller += 1
                        
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
                    
                    detalj_tekst = f"Lagret poeng"
                    if poeng_kat != "Alle":
                        detalj_tekst += f" for {poeng_kat}"
                    if valgt_kull != "Alle":
                        detalj_tekst += f" kull {valgt_kull}"
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

        with poeng_fane2:
            st.subheader("🏆 Resultattavle og vinnere")
            r_kol1, r_kol2, r_kol3 = st.columns(3)
            with r_kol1:
                res_kat = st.selectbox("Kategori", ["Alle"] + KATEGORIER, key="res_kat")
            with r_kol2:
                res_kull = st.selectbox("Kull / Aldersgruppe", ["Alle"] + ALLE_KULL_GRUPPER, key="res_kull")
            with r_kol3:
                res_kjonn = st.selectbox("Kjønn (valgfritt)", ["Alle", "Gutt", "Jente"], key="res_kjonn")
            
            if res_kat == "Alle" and res_kull == "Alle":
                st.info("Velg minst en kategori eller et kull for å vise resultater.")
            else:
                res_mask = pd.Series(True, index=alle_deltakere_df.index)
                if res_kat != "Alle":
                    res_mask &= alle_deltakere_df["Kategori"] == res_kat
                if res_kull != "Alle":
                    if res_kull in KULL_GRUPPER and "-" in res_kull:
                        aar = res_kull.split("-")
                        res_mask &= alle_deltakere_df["Kull"].isin([res_kull, aar[0], aar[1]])
                    else:
                        res_mask &= alle_deltakere_df["Kull"] == res_kull
                if res_kjonn != "Alle":
                    res_mask &= alle_deltakere_df["Kjønn"] == res_kjonn
                
                aktuelle_res = alle_deltakere_df[res_mask][["ID", "Navn", "Kategori", "Kull", "Kjønn", "Lag"]]
                
                res_df = pd.merge(aktuelle_res, st.session_state.poeng_df, on="ID", how="left").fillna("0")
                res_df["Kjønn"] = res_df["Kjønn"].replace("0", "")
                res_df["Kategori"] = res_df["Kategori"].replace("0", "")
                res_df["Kull"] = res_df["Kull"].replace("0", "")
                
                for ov in ["Øvelse 1", "Øvelse 2", "Øvelse 3"]:
                    res_df[ov] = pd.to_numeric(res_df[ov], errors='coerce').fillna(0)
                res_df["Totalt"] = res_df["Øvelse 1"] + res_df["Øvelse 2"] + res_df["Øvelse 3"]
                
                if res_df.empty or res_df["Totalt"].sum() == 0:
                    st.info("Ingen poeng registrert for denne gruppen ennå.")
                else:
                    # ── CHAMPION ─────────────────────────────────────────────
                    res_sortert = res_df.sort_values(by="Totalt", ascending=False).reset_index(drop=True)
                    champion = res_sortert.iloc[0]
                    
                    st.markdown("---")
                    st.markdown(f"""
<div style="background:linear-gradient(135deg,#1a3a5c,#2e75b6);border-radius:12px;padding:20px 28px;margin-bottom:20px;text-align:center">
<div style="font-size:36px">🏆</div>
<div style="color:#FFD700;font-size:22px;font-weight:700;letter-spacing:1px">CHAMPION</div>
<div style="color:white;font-size:28px;font-weight:600;margin:6px 0">{champion['Navn']}</div>
<div style="color:#aaa;font-size:14px">{int(champion['Totalt'])} poeng totalt · {champion['Kull']} · {champion['Lag']}</div>
</div>
""", unsafe_allow_html=True)
                    
                    # ── VINNERE PER ØVELSE ────────────────────────────────────
                    st.markdown("### 🥇 Vinnere per øvelse")
                    ov_kol1, ov_kol2, ov_kol3 = st.columns(3)
                    OVELSE_NAMN = ["Øvelse 1", "Øvelse 2", "Øvelse 3"]
                    OVELSE_FARGER = ["#e74c3c", "#e67e22", "#27ae60"]
                    
                    for kol, ov_namn, farge in zip(
                        [ov_kol1, ov_kol2, ov_kol3],
                        OVELSE_NAMN,
                        OVELSE_FARGER
                    ):
                        with kol:
                            ov_sortert = res_df[res_df[ov_namn] > 0].sort_values(by=ov_namn, ascending=False).reset_index(drop=True)
                            st.markdown(f"**{ov_namn}**")
                            if ov_sortert.empty:
                                st.caption("Ingen poeng ennå")
                            else:
                                medaljer = ["🥇", "🥈", "🥉"]
                                for i, (_, row) in enumerate(ov_sortert.head(3).iterrows()):
                                    plass = medaljer[i] if i < 3 else f"{i+1}."
                                    poeng = int(row[ov_namn])
                                    st.markdown(
                                        f"<div style='padding:6px 10px;margin:3px 0;border-radius:8px;"
                                        f"background:{farge}18;border-left:3px solid {farge}'>"
                                        f"<span style='font-size:16px'>{plass}</span> "
                                        f"<strong>{row['Navn']}</strong> "
                                        f"<span style='color:#888;font-size:12px'>({poeng} p)</span>"
                                        f"</div>",
                                        unsafe_allow_html=True
                                    )
                    
                    # ── TOTALRESULTAT-PALL (med delt plassering ved likt poeng) ──
                    st.markdown("---")
                    st.markdown("### 🏅 Totalpall")
                    
                    # Bygg rangering der like poengsummer deler plass
                    res_sortert["_rank"] = res_sortert["Totalt"].rank(method="min", ascending=False).astype(int)
                    
                    forste = res_sortert[(res_sortert["_rank"] == 1) & (res_sortert["Totalt"] > 0)]
                    andre  = res_sortert[(res_sortert["_rank"] == 2) & (res_sortert["Totalt"] > 0)]
                    tredje = res_sortert[(res_sortert["_rank"] == 3) & (res_sortert["Totalt"] > 0)]
                    
                    pall_k1, pall_k2, pall_k3 = st.columns(3)
                    with pall_k1:
                        if not forste.empty:
                            navn_liste = "\n\n".join(forste["Navn"].tolist())
                            delt_tekst = " (delt)" if len(forste) > 1 else ""
                            st.success(f"**🥇 1. plass{delt_tekst}**\n\n{navn_liste}\n\n**{int(forste.iloc[0]['Totalt'])} poeng**")
                    with pall_k2:
                        if not andre.empty:
                            navn_liste = "\n\n".join(andre["Navn"].tolist())
                            delt_tekst = " (delt)" if len(andre) > 1 else ""
                            st.info(f"**🥈 2. plass{delt_tekst}**\n\n{navn_liste}\n\n**{int(andre.iloc[0]['Totalt'])} poeng**")
                    with pall_k3:
                        if not tredje.empty:
                            navn_liste = "\n\n".join(tredje["Navn"].tolist())
                            delt_tekst = " (delt)" if len(tredje) > 1 else ""
                            st.warning(f"**🥉 3. plass{delt_tekst}**\n\n{navn_liste}\n\n**{int(tredje.iloc[0]['Totalt'])} poeng**")
                    
                    # ── FULL TABELL ───────────────────────────────────────────
                    st.markdown("---")
                    st.markdown("### Hele poengtabellen")
                    # Legg til lag-ikon uten å endre rå data (vis-kopi)
                    vis_df = res_sortert.copy()
                    vis_df["Lag"] = vis_df["Lag"].apply(ikoniser_lag)
                    vis_df = vis_df.rename(columns={"_rank": "Plass"})
                    vis_df.index = range(1, len(vis_df) + 1)
                    vis_kolonner = ["Plass", "Navn", "Lag", "Kategori", "Kull", "Kjønn", "Øvelse 1", "Øvelse 2", "Øvelse 3", "Totalt"]
                    st.dataframe(vis_df[vis_kolonner], use_container_width=True)

        with poeng_fane3:
            st.subheader("⚔️ Lagsammenligning — Rød vs Gul")
            
            lag_deltakere = st.session_state.df[
                (st.session_state.df["Lag"] != "")
            ][["ID", "Navn", "Kategori", "Kull", "Lag"]].copy()
            
            # ── Lagspill-poeng (manuelt registrerte lagøvelser) ──────────────
            for kol in ["Lag Rød", "Lag Gul"]:
                if kol not in st.session_state.lagspill_df.columns:
                    st.session_state.lagspill_df[kol] = "0"
            lagspill_df_num = st.session_state.lagspill_df.copy()
            for kol in ["Lag Rød", "Lag Gul"]:
                lagspill_df_num[kol] = pd.to_numeric(lagspill_df_num[kol], errors="coerce").fillna(0)
            lagspill_rod_sum = int(lagspill_df_num["Lag Rød"].sum())
            lagspill_gul_sum = int(lagspill_df_num["Lag Gul"].sum())
            
            if lag_deltakere.empty and st.session_state.lagspill_df.empty:
                st.info("Ingen deltakere er fordelt i lag ennå, og ingen lagspill er registrert. Gå til Laginndeling først.")
            else:
                if lag_deltakere.empty:
                    lag_med_poeng = pd.DataFrame(columns=["ID","Navn","Kategori","Kull","Lag","Øvelse 1","Øvelse 2","Øvelse 3","Totalt"])
                    rod_df = lag_med_poeng.copy()
                    gul_df = lag_med_poeng.copy()
                    rod_ind_total, gul_ind_total = 0, 0
                    rod_ov1=rod_ov2=rod_ov3=gul_ov1=gul_ov2=gul_ov3=0
                else:
                    lag_med_poeng = pd.merge(lag_deltakere, st.session_state.poeng_df, on="ID", how="left").fillna("0")
                    for ov in ["Øvelse 1", "Øvelse 2", "Øvelse 3"]:
                        lag_med_poeng[ov] = pd.to_numeric(lag_med_poeng[ov], errors='coerce').fillna(0)
                    lag_med_poeng["Totalt"] = lag_med_poeng["Øvelse 1"] + lag_med_poeng["Øvelse 2"] + lag_med_poeng["Øvelse 3"]
                    
                    rod_df = lag_med_poeng[lag_med_poeng["Lag"] == LAG_A].copy()
                    gul_df = lag_med_poeng[lag_med_poeng["Lag"] == LAG_B].copy()
                    rod_ind_total, gul_ind_total = int(rod_df["Totalt"].sum()), int(gul_df["Totalt"].sum())
                    rod_ov1, rod_ov2, rod_ov3 = int(rod_df["Øvelse 1"].sum()), int(rod_df["Øvelse 2"].sum()), int(rod_df["Øvelse 3"].sum())
                    gul_ov1, gul_ov2, gul_ov3 = int(gul_df["Øvelse 1"].sum()), int(gul_df["Øvelse 2"].sum()), int(gul_df["Øvelse 3"].sum())
                
                # Samla totalt = individuelle poeng + lagspill-poeng
                rod_total = rod_ind_total + lagspill_rod_sum
                gul_total = gul_ind_total + lagspill_gul_sum
                
                if rod_total > gul_total:
                    ledertekst = f"🔴 {LAG_A} leder med {rod_total - gul_total} poeng!"
                elif gul_total > rod_total:
                    ledertekst = f"🟡 {LAG_B} leder med {gul_total - rod_total} poeng!"
                else:
                    ledertekst = "⚖️ Det er helt likt!"
                
                st.markdown(f"### {ledertekst}")
                
                mk1, mk2 = st.columns(2)
                with mk1:
                    st.metric(f"🔴 {LAG_A}", f"{rod_total} poeng totalt", 
                              delta=f"{rod_ind_total} individuelt + {lagspill_rod_sum} lagspill")
                with mk2:
                    st.metric(f"🟡 {LAG_B}", f"{gul_total} poeng totalt",
                              delta=f"{gul_ind_total} individuelt + {lagspill_gul_sum} lagspill")
                
                if not lag_med_poeng.empty:
                    st.markdown("### Poengfordeling per øvelse")
                    bar_data = pd.DataFrame({
                        "Lag": [LAG_A, LAG_B],
                        "Øvelse 1": [rod_ov1, gul_ov1],
                        "Øvelse 2": [rod_ov2, gul_ov2],
                        "Øvelse 3": [rod_ov3, gul_ov3],
                    }).set_index("Lag")
                    st.bar_chart(bar_data, color=["#EF4444", "#F59E0B", "#10B981"])
                
                # ── 🏐 LAGSPILL-MENY ──────────────────────────────────────────
                st.markdown("---")
                st.markdown("### 🏐 Lagspill — manuell poengregistrering")
                st.caption("Her kan du legge til lagspill (f.eks. tautrekking, stafett) og gi poeng direkte til Lag Rød eller Lag Gul. Endringer her teller med i lagtotalen over.")
                
                tilgang_lagspill = har_tilgang("las_poengforing")
                
                if not st.session_state.lagspill_df.empty:
                    lagspill_vis = st.session_state.lagspill_df.copy()
                    for kol in ["Lag Rød", "Lag Gul"]:
                        lagspill_vis[kol] = pd.to_numeric(lagspill_vis[kol], errors="coerce").fillna(0).astype(int)
                    lagspill_vis["Slett"] = False
                    
                    redigert_lagspill = st.data_editor(
                        lagspill_vis,
                        column_config={
                            "Spill": st.column_config.TextColumn("Spill / Øvelse", width="medium"),
                            "Lag Rød": st.column_config.NumberColumn("🔴 Lag Rød poeng", min_value=0, step=1, width="small"),
                            "Lag Gul": st.column_config.NumberColumn("🟡 Lag Gul poeng", min_value=0, step=1, width="small"),
                            "Slett": st.column_config.CheckboxColumn("🗑️ Slett", default=False, width="small"),
                        },
                        hide_index=True,
                        use_container_width=True,
                        disabled=not tilgang_lagspill,
                        key="lagspill_editor"
                    )
                    
                    if tilgang_lagspill and st.button("💾 Lagre endringer i lagspill", type="primary"):
                        behold = redigert_lagspill[~redigert_lagspill["Slett"]].copy()
                        antall_slettet = len(redigert_lagspill) - len(behold)
                        st.session_state.lagspill_df = behold[["Spill", "Lag Rød", "Lag Gul"]].astype(str).reset_index(drop=True)
                        loggfor_handling("Lagspill oppdatert", f"Oppdaterte lagspill-poeng. Slettet {antall_slettet} oppføring(er).")
                        if lagre_alle_data():
                            st.success("Lagspill-poeng oppdatert!")
                            st.rerun()
                else:
                    st.info("Ingen lagspill registrert ennå. Legg til et nytt under.")
                
                with st.expander("➕ Legg til nytt lagspill"):
                    if not tilgang_lagspill:
                        st.info("🔒 Poengføring er låst. Logg inn som admin for å legge til lagspill.")
                    else:
                        ls_kol1, ls_kol2, ls_kol3, ls_kol4 = st.columns([2,1,1,1])
                        with ls_kol1:
                            nytt_spill_navn = st.text_input("Navn på spill / øvelse", key="nytt_lagspill_navn", placeholder="F.eks. Tautrekking")
                        with ls_kol2:
                            nytt_spill_rod = st.number_input(f"🔴 {LAG_A} poeng", min_value=0, step=1, value=0, key="nytt_lagspill_rod")
                        with ls_kol3:
                            nytt_spill_gul = st.number_input(f"🟡 {LAG_B} poeng", min_value=0, step=1, value=0, key="nytt_lagspill_gul")
                        with ls_kol4:
                            st.write("")
                            st.write("")
                            if st.button("➕ Legg til", use_container_width=True):
                                if not nytt_spill_navn.strip():
                                    st.warning("Skriv inn navn på spillet.")
                                else:
                                    ny_rad = pd.DataFrame(
                                        [[nytt_spill_navn.strip(), str(int(nytt_spill_rod)), str(int(nytt_spill_gul))]],
                                        columns=st.session_state.lagspill_kolonner
                                    )
                                    st.session_state.lagspill_df = pd.concat([st.session_state.lagspill_df, ny_rad], ignore_index=True)
                                    loggfor_handling("Lagspill lagt til", f"{nytt_spill_navn}: {LAG_A}={nytt_spill_rod}, {LAG_B}={nytt_spill_gul}")
                                    if lagre_alle_data():
                                        st.success(f"La til '{nytt_spill_navn}'!")
                                        st.rerun()
                
                if not lag_deltakere.empty:
                    st.markdown("---")
                    d_kol1, d_kol2 = st.columns(2)
                    with d_kol1:
                        st.markdown(f"#### 🔴 {LAG_A} — Individuelle bidrag")
                        rod_vis = rod_df[["ID", "Navn", "Kategori", "Kull", "Øvelse 1", "Øvelse 2", "Øvelse 3", "Totalt"]].sort_values("Totalt", ascending=False).reset_index(drop=True)
                        st.dataframe(rod_vis, use_container_width=True, hide_index=True)
                    with d_kol2:
                        st.markdown(f"#### 🟡 {LAG_B} — Individuelle bidrag")
                        gul_vis = gul_df[["ID", "Navn", "Kategori", "Kull", "Øvelse 1", "Øvelse 2", "Øvelse 3", "Totalt"]].sort_values("Totalt", ascending=False).reset_index(drop=True)
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
    st.title("📊 Festivalinformasjon")
    
    df = st.session_state.df
    total = len(df)
    
    if total == 0:
        st.info("Ingen deltakere registrert ennå.")
    else:
        # ── Hovedtall (rad 1) ────────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("👥 Totalt registrert", f"{total}")
        with m2:
            antall_rod = len(df[df["Lag"] == LAG_A])
            st.metric(f"🔴 På {LAG_A}", f"{antall_rod}")
        with m3:
            antall_gul = len(df[df["Lag"] == LAG_B])
            st.metric(f"🟡 På {LAG_B}", f"{antall_gul}")
        with m4:
            ufordelt = len(df[df["Lag"] == ""])
            st.metric("⚪ Ufordelt på lag", f"{ufordelt}")
        
        # ── Sekundærtall (rad 2) ─────────────────────────────────────────
        m5, m6, m7, m8 = st.columns(4)
        kategoritelling = df["Kategori"].value_counts()
        kjonnstelling = df["Kjønn"].value_counts()
        with m5:
            st.metric("🎓 Elever", f"{kategoritelling.get('Elev', 0)}")
        with m6:
            st.metric("👨‍🏫 Lærere", f"{kategoritelling.get('Lærer', 0)}")
        with m7:
            antall_gutt = kjonnstelling.get("Gutt", 0)
            antall_jente = kjonnstelling.get("Jente", 0)
            st.metric("♂️ Gutter / ♀️ Jenter", f"{antall_gutt} / {antall_jente}")
        with m8:
            elever_uten_lag = len(df[(df["Kategori"] == "Elev") & (df["Lag"] == "")])
            st.metric("Elever uten lag", f"{elever_uten_lag}")
        
        st.markdown("---")
        
        # ── Fordeling: Kategori og Avdeling som bar charts ───────────────
        info_k1, info_k2 = st.columns(2)
        
        with info_k1:
            st.subheader("Fordelt på kategori")
            kat_data = pd.DataFrame({
                "Kategori": KATEGORIER,
                "Antall": [int(kategoritelling.get(k, 0)) for k in KATEGORIER]
            }).set_index("Kategori")
            st.bar_chart(kat_data, color="#3498DB", height=240)
        
        with info_k2:
            st.subheader("Fordelt på avdeling")
            avdelingstelling = df["Avdeling"].value_counts()
            avd_data = pd.DataFrame({
                "Avdeling": AVDELINGER,
                "Antall": [int(avdelingstelling.get(a, 0)) for a in AVDELINGER]
            }).set_index("Avdeling")
            st.bar_chart(avd_data, color="#27AE60", height=240)
        
        # ── Lagfordeling per avdeling og per kategori ────────────────────
        st.markdown("---")
        lag_k1, lag_k2 = st.columns(2)
        
        with lag_k1:
            st.subheader("Lag pr. avdeling")
            avd_lag = df[df["Lag"] != ""].groupby(["Avdeling", "Lag"]).size().unstack(fill_value=0)
            if not avd_lag.empty:
                # Sikre konsistent rekkefølge på lag-kolonner
                for lag in [LAG_A, LAG_B]:
                    if lag not in avd_lag.columns:
                        avd_lag[lag] = 0
                avd_lag = avd_lag[[LAG_A, LAG_B]]
                st.bar_chart(avd_lag, color=["#E74C3C", "#F1C40F"], height=240)
            else:
                st.caption("Ingen deltakere fordelt på lag ennå.")
        
        with lag_k2:
            st.subheader("Lag pr. kategori")
            kat_lag = df[df["Lag"] != ""].groupby(["Kategori", "Lag"]).size().unstack(fill_value=0)
            if not kat_lag.empty:
                for lag in [LAG_A, LAG_B]:
                    if lag not in kat_lag.columns:
                        kat_lag[lag] = 0
                kat_lag = kat_lag[[LAG_A, LAG_B]]
                st.bar_chart(kat_lag, color=["#E74C3C", "#F1C40F"], height=240)
            else:
                st.caption("Ingen deltakere fordelt på lag ennå.")
        
        # ── Detaljert tabellvisning ──────────────────────────────────────
        st.markdown("---")
        st.subheader("Detaljert oversikt")
        
        # Krysstabell: Avdeling × Kategori
        krysstab = df.groupby(["Avdeling", "Kategori"]).size().unstack(fill_value=0)
        # Sikre at alle kategorier vises
        for kat in KATEGORIER:
            if kat not in krysstab.columns:
                krysstab[kat] = 0
        krysstab = krysstab[KATEGORIER]
        krysstab["Sum"] = krysstab.sum(axis=1)
        krysstab.loc["Sum"] = krysstab.sum()
        st.dataframe(krysstab, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
#  📜 HISTORIKK
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
