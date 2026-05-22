import streamlit as st
import pandas as pd
import random
from pathlib import Path
from datetime import datetime

# Konfigurasjon og faste stier
DATA_FILE = Path("sportsfestival_data.csv")
LOGG_FILE = Path("sportsfestival_logg.csv")
SETTING_FILE = Path("sportsfestival_innstillinger.csv")
POENG_FILE = Path("sportsfestival_poeng.csv")

KATEGORIER = ["Elev", "நிர்வாகம்", "Lærer", "Frivillig", "Gjest"]
LAG_A = "Lag Rød"
LAG_B = "Lag Gul"

st.set_page_config(
    page_title="Sportsfestival 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "kolonner" not in st.session_state:
    st.session_state.kolonner = ["ID", "Navn", "Kategori", "Kull", "Kjønn", "Lag"]
    st.session_state.logg_kolonner = ["Tidspunkt", "Rolle", "Handling", "Detaljer"]
    st.session_state.poeng_kolonner = ["ID", "Øvelse 1", "Øvelse 2", "Øvelse 3"]

def last_inn_innstillinger():
    standard = {
        "passord": "Admin2026",
        "las_nullstill": "True",
        "las_autofordel": "True",
        "las_import": "False",
        "las_slett_enkel": "False",
        "las_poengforing": "True"
    }
    if SETTING_FILE.exists():
        try:
            df = pd.read_csv(SETTING_FILE, dtype=str)
            lagrede = dict(zip(df["Nøkkel"], df["Verdi"]))
            standard.update(lagrede)
            return standard
        except Exception:
            pass
    return standard

def lagre_innstillinger():
    try:
        data = {"Nøkkel": list(st.session_state.innstillinger.keys()), "Verdi": list(st.session_state.innstillinger.values())}
        pd.DataFrame(data).to_csv(SETTING_FILE, index=False, encoding="utf-8-sig")
    except Exception as e:
        st.error(f"Kunne ikke lagre innstillinger: {e}")

def last_inn_data():
    if DATA_FILE.exists():
        try:
            df = pd.read_csv(DATA_FILE, encoding="utf-8-sig", dtype=str).fillna("")
            if "Kjønn" not in df.columns:
                df["Kjønn"] = ""
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=st.session_state.kolonner)

def last_inn_logg():
    if LOGG_FILE.exists():
        try:
            df = pd.read_csv(LOGG_FILE, encoding="utf-8-sig", dtype=str).fillna("")
            # Bakoverkompatibilitet: legg til Rolle-kolonne hvis den mangler
            if "Rolle" not in df.columns:
                df.insert(1, "Rolle", "—")
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=st.session_state.logg_kolonner)

def last_inn_poeng():
    if POENG_FILE.exists():
        try:
            return pd.read_csv(POENG_FILE, encoding="utf-8-sig", dtype=str).fillna("0")
        except Exception:
            pass
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
    try:
        st.session_state.df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        st.session_state.logg_df.to_csv(LOGG_FILE, index=False, encoding="utf-8-sig")
        st.session_state.poeng_df.to_csv(POENG_FILE, index=False, encoding="utf-8-sig")
        return True
    except Exception as e:
        st.error(f"Kunne ikke lagre til filen akkurat nå: {e}")
        return False

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
    while ny_id in eksisterende and ny_id < 100:
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
                    if ny_id_num > 99:
                        st.error("Maksgrensen på 99 deltakere er nådd.")
                    else:
                        ny_id_str = f"{ny_id_num:02d}"
                        kull_verdi = kull.strip() if kategori == "Elev" else ""
                        kjonn_verdi = kjonn if kategori == "Elev" else ""
                        ny_rad = pd.DataFrame([[ny_id_str, navn.strip(), kategori, kull_verdi, kjonn_verdi, ""]], columns=st.session_state.kolonner)
                        st.session_state.df = pd.concat([st.session_state.df, ny_rad], ignore_index=True)
                        loggfor_handling("Lagt til", f"ID {ny_id_str}: {navn} ({kategori})")
                        if lagre_alle_data():
                            st.success(f"{navn} ble lagt til med ID {ny_id_str}")
                            st.rerun()

    else:
        if st.session_state.df.empty:
            st.info("Det er ingen registrerte deltakere i systemet ennå.")
        else:
            deltaker_valg = st.selectbox(
                "Velg deltaker som skal behandles",
                st.session_state.df["ID"] + " - " + st.session_state.df["Navn"]
            )
            valgt_id = deltaker_valg.split(" - ")[0]
            idx = st.session_state.df.index[st.session_state.df["ID"] == valgt_id].tolist()[0]
            
            oppdatert_navn = st.text_input("Navn", st.session_state.df.at[idx, "Navn"])
            oppdatert_kat = st.selectbox("Kategori", KATEGORIER, index=KATEGORIER.index(st.session_state.df.at[idx, "Kategori"]))
            
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
                    st.session_state.df.at[idx, "Kull"] = oppdatert_kull.strip() if oppdatert_kat == "Elev" else ""
                    st.session_state.df.at[idx, "Kjønn"] = oppdatert_kjonn if oppdatert_kat == "Elev" else ""
                    loggfor_handling("Oppdatert", f"ID {valgt_id}: {gammelt_navn} endret til {oppdatert_navn}")
                    if lagre_alle_data():
                        st.success("Endringene ble lagret.")
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
                        st.success("Deltakeren ble slettet.")
                        st.rerun()

    st.markdown("---")
    st.subheader("Filimport")
    tilgang_import = har_tilgang("las_import")
    if not tilgang_import:
        st.info("Filimport er låst. Vennligst logg inn i Admin-menyen for å aktivere denne funksjonen.")
    opplastet_fil = st.file_uploader("Last opp Excel eller CSV for å hente inn deltakere", type=["csv", "xlsx"], disabled=not tilgang_import)
    if opplastet_fil and tilgang_import:
        try:
            if opplastet_fil.name.endswith(".xlsx"):
                ny_df = pd.read_excel(opplastet_fil, dtype=str).fillna("")
            else:
                ny_df = pd.read_csv(opplastet_fil, dtype=str).fillna("")
            
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
                    if neste_id <= 99:
                        neste_id_str = f"{neste_id:02d}"
                        importert_kat = rad.get("Kategori", "Elev")
                        importert_kull = rad.get("Kull", "") if importert_kat == "Elev" else ""
                        importert_kjonn = rad.get("Kjønn", "") if importert_kat == "Elev" else ""
                        midlertidig_rad = pd.DataFrame([[neste_id_str, importert_navn, importert_kat, importert_kull, importert_kjonn, ""]], columns=st.session_state.kolonner)
                        st.session_state.df = pd.concat([st.session_state.df, midlertidig_rad], ignore_index=True)
                        eksisterende_navn.add(navn_sjekk)
                        importert_teller += 1
            
            if importert_teller > 0 or hoppet_over_teller > 0:
                loggfor_handling("Import", f"Importerte {importert_teller} nye. Ignorerte {hoppet_over_teller} duplikater.")
                lagre_alle_data()
                st.success(f"Vellykket import. La til {importert_teller} nye personer og hoppet over {hoppet_over_teller} duplikater.")
                st.rerun()
        except Exception as e:
            st.error(f"Kunne ikke tolke filen: {e}")

    st.markdown("---")
    st.subheader("Globalt søk og oversikt")
    sok_tekst = st.text_input("Søk i sanntid på tvers av ID, navn, kull, kategori eller lag")
    
    if sok_tekst.strip():
        filtrert_df = st.session_state.df[
            st.session_state.df["ID"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Navn"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Kategori"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Kull"].str.contains(sok_tekst, case=False, na=False) |
            st.session_state.df["Lag"].str.contains(sok_tekst, case=False, na=False)
        ]
    else:
        filtrert_df = st.session_state.df

    st.dataframe(filtrert_df, use_container_width=True, hide_index=True)

    if st.button("🔄 Tving manuell filoppdatering"):
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
            st.success(f"Skanning fullført. Fjernet {forskjell} dupliserte registreringer.")
        else:
            st.info("Skanning fullført. Ingen duplikater ble funnet.")
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
        loggfor_handling("Systemnullstilling", "Absolutt alt av deltakerdata, poeng og historikk ble slettet av administrator.")
        if lagre_alle_data():
            st.success("Hele systemet har blitt nullstilt og tømt!")
            st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  🏁 LAGINNDELING
# ═════════════════════════════════════════════════════════════════════════════

elif side == "🏁 Laginndeling":
    st.title("Laginndeling og balansering")
    tilgang_fordel = har_tilgang("las_autofordel")
    
    b_kol1, b_kol2, b_kol3, b_kol4 = st.columns(4)
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

    with b_kol3:
        csv_data = st.session_state.df[st.session_state.df["Lag"] != ""].to_csv(index=False, encoding="utf-8-sig")
        st.download_button("💾 Last ned CSV-eksport", data=csv_data, file_name="lagfordeling_eksport.csv", mime="text/csv", use_container_width=True)

    with b_kol4:
        df_a_print = st.session_state.df[st.session_state.df["Lag"] == LAG_A]
        df_b_print = st.session_state.df[st.session_state.df["Lag"] == LAG_B]
        html_print = f"""
        <html><body style='font-family:Arial;padding:20px;'>
        <h2>{LAG_A}</h2><ul>{"".join(f"<li>{r['ID']} - {r['Navn']} ({r['Kull']})</li>" for _, r in df_a_print.iterrows())}</ul>
        <h2>{LAG_B}</h2><ul>{"".join(f"<li>{r['ID']} - {r['Navn']} ({r['Kull']})</li>" for _, r in df_b_print.iterrows())}</ul>
        </body></html>
        """
        st.download_button("🖨️ Last ned utskriftsklar HTML", data=html_print, file_name="utskrift_lag.html", mime="text/html", use_container_width=True)

    st.markdown("---")
    st.subheader("Manuell flytting av spillere")
    elever_kun = st.session_state.df[st.session_state.df["Kategori"] == "Elev"]
    if not elever_kun.empty:
        flytt_valg = st.selectbox("Velg elev som skal flyttes eller endres manuelt", elever_kun["ID"] + " - " + elever_kun["Navn"])
        flytt_id = flytt_valg.split(" - ")[0]
        f_idx = st.session_state.df.index[st.session_state.df["ID"] == flytt_id].tolist()[0]
        
        aktivt_lag = st.session_state.df.at[f_idx, "Lag"]
        standard_index = 0
        if aktivt_lag == LAG_A: standard_index = 1
        elif aktivt_lag == LAG_B: standard_index = 2

        nytt_lag_valg = st.radio(f"Velg lagtilhørighet for {st.session_state.df.at[f_idx, 'Navn']}", ["Ufordelt", LAG_A, LAG_B], index=standard_index, horizontal=True)
        nytt_lag_verdi = "" if nytt_lag_valg == "Ufordelt" else nytt_lag_valg
        
        if st.session_state.df.at[f_idx, "Lag"] != nytt_lag_verdi:
            st.session_state.df.at[f_idx, "Lag"] = nytt_lag_verdi
            loggfor_handling("Flyttet", f"{st.session_state.df.at[f_idx, 'Navn']} flyttet til {nytt_lag_valg}")
            lagre_alle_data()
            st.rerun()

    st.markdown("---")
    l_kol1, l_kol2, l_kol3 = st.columns(3)
    with l_kol1:
        st.markdown(f"### 🔴 {LAG_A}")
        st.dataframe(st.session_state.df[st.session_state.df["Lag"] == LAG_A][["ID", "Navn", "Kull"]], use_container_width=True, hide_index=True)
    with l_kol2:
        st.markdown("### ⚪ Ufordelte Elever")
        st.dataframe(st.session_state.df[(st.session_state.df["Kategori"] == "Elev") & (st.session_state.df["Lag"] == "")][["ID", "Navn", "Kull"]], use_container_width=True, hide_index=True)
    with l_kol3:
        st.markdown(f"### 🟡 {LAG_B}")
        st.dataframe(st.session_state.df[st.session_state.df["Lag"] == LAG_B][["ID", "Navn", "Kull"]], use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════════════════════
#  🎯 POENG & RESULTATER (Oppgradert med 3 faner + valgfritt kjønn)
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
            st.write("Skriv inn poeng (f.eks. 3 for 1. plass, 2 for 2. plass, 1 for 3. plass).")
            
            p_kol1, p_kol2 = st.columns(2)
            with p_kol1:
                valgt_kull = st.selectbox("Velg Kull", [""] + alle_kull, key="poeng_kull")
            with p_kol2:
                valgt_kjonn = st.selectbox(
                    "Filtrer på kjønn (valgfritt)", 
                    ["Alle", "Gutt", "Jente"], 
                    key="poeng_kjonn"
                )
                
            if valgt_kull:
                # Filtrer elever — kjønn er nå valgfritt
                if valgt_kjonn == "Alle":
                    aktuelle_elever = elever_df[elever_df["Kull"] == valgt_kull][["ID", "Navn", "Kjønn"]].copy()
                else:
                    aktuelle_elever = elever_df[
                        (elever_df["Kull"] == valgt_kull) & (elever_df["Kjønn"] == valgt_kjonn)
                    ][["ID", "Navn", "Kjønn"]].copy()
                
                if aktuelle_elever.empty:
                    st.info("Fant ingen registrerte elever i dette kullet.")
                else:
                    # Slå sammen med eksisterende poengdata
                    redigerings_df = pd.merge(
                        aktuelle_elever, st.session_state.poeng_df, 
                        on="ID", how="left"
                    ).fillna("0")
                    # Sett Kjønn til "" der det er "0" fra fillna
                    redigerings_df["Kjønn"] = redigerings_df["Kjønn"].replace("0", "")
                    
                    st.markdown("Rediger poengene og kjønn direkte i tabellen under:")
                    redigert_data = st.data_editor(
                        redigerings_df,
                        column_config={
                            "ID": st.column_config.TextColumn("ID", disabled=True, width="small"),
                            "Navn": st.column_config.TextColumn("Navn", disabled=True),
                            "Kjønn": st.column_config.SelectboxColumn(
                                "Kjønn",
                                options=["", "Gutt", "Jente"],
                                width="small"
                            ),
                            "Øvelse 1": st.column_config.TextColumn("Øvelse 1", width="small"),
                            "Øvelse 2": st.column_config.TextColumn("Øvelse 2", width="small"),
                            "Øvelse 3": st.column_config.TextColumn("Øvelse 3", width="small"),
                        },
                        hide_index=True,
                        use_container_width=True,
                        key="poeng_editor"
                    )
                    
                    if st.button("💾 Lagre poeng og endringer", type="primary"):
                        endret_kjonn_teller = 0
                        for _, rad in redigert_data.iterrows():
                            pid = rad["ID"]
                            
                            # Oppdater kjønn i hoveddataen
                            main_idx = st.session_state.df.index[st.session_state.df["ID"] == pid].tolist()
                            if main_idx:
                                gammelt_kjonn = st.session_state.df.at[main_idx[0], "Kjønn"]
                                nytt_kjonn = rad["Kjønn"] if pd.notna(rad["Kjønn"]) else ""
                                if gammelt_kjonn != nytt_kjonn:
                                    st.session_state.df.at[main_idx[0], "Kjønn"] = nytt_kjonn
                                    endret_kjonn_teller += 1
                            
                            # Oppdater poeng
                            poeng_idx = st.session_state.poeng_df.index[st.session_state.poeng_df["ID"] == pid].tolist()
                            if poeng_idx:
                                st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 1"] = rad["Øvelse 1"]
                                st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 2"] = rad["Øvelse 2"]
                                st.session_state.poeng_df.at[poeng_idx[0], "Øvelse 3"] = rad["Øvelse 3"]
                            else:
                                ny_poeng = pd.DataFrame(
                                    [[pid, rad["Øvelse 1"], rad["Øvelse 2"], rad["Øvelse 3"]]], 
                                    columns=st.session_state.poeng_kolonner
                                )
                                st.session_state.poeng_df = pd.concat(
                                    [st.session_state.poeng_df, ny_poeng], ignore_index=True
                                )
                        
                        detalj_tekst = f"Lagret poeng for {valgt_kull}"
                        if valgt_kjonn != "Alle":
                            detalj_tekst += f" ({valgt_kjonn})"
                        if endret_kjonn_teller > 0:
                            detalj_tekst += f" + endret kjønn for {endret_kjonn_teller} elever"
                        
                        loggfor_handling("Poeng lagret", detalj_tekst)
                        if lagre_alle_data():
                            st.success("Poeng og eventuelle kjønnsendringer er lagret!")
                            st.rerun()

        # ── FANE 2: Resultattavle ────────────────────────────────────────
        with poeng_fane2:
            st.subheader("Resultattavle og vinnere")
            
            r_kol1, r_kol2 = st.columns(2)
            with r_kol1:
                res_kull = st.selectbox("Vis resultater for Kull", [""] + alle_kull, key="res_kull")
            with r_kol2:
                res_kjonn = st.selectbox(
                    "Filtrer på kjønn (valgfritt)", 
                    ["Alle", "Gutt", "Jente"], 
                    key="res_kjonn"
                )
                
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
                
                res_df["Øvelse 1"] = pd.to_numeric(res_df["Øvelse 1"], errors='coerce').fillna(0)
                res_df["Øvelse 2"] = pd.to_numeric(res_df["Øvelse 2"], errors='coerce').fillna(0)
                res_df["Øvelse 3"] = pd.to_numeric(res_df["Øvelse 3"], errors='coerce').fillna(0)
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

        # ── FANE 3: Lagpoeng (ny!) ───────────────────────────────────────
        with poeng_fane3:
            st.subheader("⚔️ Lagsammenligning — Rød vs Gul")
            st.write("Oversikt over total poengsum per lag, beregnet fra alle individuelle poeng.")
            
            # Hent alle elever med lag og poeng
            lag_elever = st.session_state.df[
                (st.session_state.df["Kategori"] == "Elev") & 
                (st.session_state.df["Lag"] != "")
            ][["ID", "Navn", "Kull", "Lag"]].copy()
            
            if lag_elever.empty:
                st.info("Ingen elever er fordelt i lag ennå. Gå til Laginndeling først.")
            else:
                lag_med_poeng = pd.merge(
                    lag_elever, st.session_state.poeng_df, on="ID", how="left"
                ).fillna("0")
                
                for ov in ["Øvelse 1", "Øvelse 2", "Øvelse 3"]:
                    lag_med_poeng[ov] = pd.to_numeric(lag_med_poeng[ov], errors='coerce').fillna(0)
                lag_med_poeng["Totalt"] = lag_med_poeng["Øvelse 1"] + lag_med_poeng["Øvelse 2"] + lag_med_poeng["Øvelse 3"]
                
                # Beregn lagsummer
                rod_df = lag_med_poeng[lag_med_poeng["Lag"] == LAG_A]
                gul_df = lag_med_poeng[lag_med_poeng["Lag"] == LAG_B]
                
                rod_total = int(rod_df["Totalt"].sum())
                gul_total = int(gul_df["Totalt"].sum())
                rod_ov1 = int(rod_df["Øvelse 1"].sum())
                rod_ov2 = int(rod_df["Øvelse 2"].sum())
                rod_ov3 = int(rod_df["Øvelse 3"].sum())
                gul_ov1 = int(gul_df["Øvelse 1"].sum())
                gul_ov2 = int(gul_df["Øvelse 2"].sum())
                gul_ov3 = int(gul_df["Øvelse 3"].sum())
                
                # Visuell sammenligning
                samlet_max = max(rod_total, gul_total, 1)
                rod_pst = rod_total / samlet_max * 100
                gul_pst = gul_total / samlet_max * 100
                
                # Hvem leder?
                if rod_total > gul_total:
                    ledertekst = f"🔴 {LAG_A} leder med {rod_total - gul_total} poeng!"
                elif gul_total > rod_total:
                    ledertekst = f"🟡 {LAG_B} leder med {gul_total - rod_total} poeng!"
                else:
                    ledertekst = "⚖️ Det er helt likt!"
                
                st.markdown(f"### {ledertekst}")
                
                # Total-metrikk
                mk1, mk2 = st.columns(2)
                with mk1:
                    st.metric(
                        f"🔴 {LAG_A}",
                        f"{rod_total} poeng",
                        delta=f"{len(rod_df)} spillere"
                    )
                with mk2:
                    st.metric(
                        f"🟡 {LAG_B}",
                        f"{gul_total} poeng",
                        delta=f"{len(gul_df)} spillere"
                    )
                
                # Stolpediagram (prosentbar)
                st.markdown("### Poengfordeling")
                bar_data = pd.DataFrame({
                    "Lag": [LAG_A, LAG_B],
                    "Øvelse 1": [rod_ov1, gul_ov1],
                    "Øvelse 2": [rod_ov2, gul_ov2],
                    "Øvelse 3": [rod_ov3, gul_ov3],
                }).set_index("Lag")
                st.bar_chart(bar_data, color=["#EF4444", "#F59E0B", "#10B981"])
                
                # Detaljtabell per lag
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
                
                # Fordeling per kull
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
    st.subheader("Komplett fordeling fordelt på roller")
    for kat in KATEGORIER:
        antall_kat = kategoritelling.get(kat, 0)
        st.write(f"Kategori {kat}: {antall_kat} personer")


# ═════════════════════════════════════════════════════════════════════════════
#  📜 HISTORIKK (Oppgradert med Bruker vs Admin)
# ═════════════════════════════════════════════════════════════════════════════

elif side == "📜 Historikk":
    st.title("Systemhistorikk og endringslogg")
    st.write("Alle endringer logges automatisk med hvem som utførte dem.")
    
    logg_data = st.session_state.logg_df.copy()
    
    if logg_data.empty:
        st.info("Ingen historikk ennå. Endringer vil dukke opp her etterhvert.")
    else:
        # Filtreringsmuligheter
        filt_kol1, filt_kol2 = st.columns(2)
        with filt_kol1:
            rolle_filter = st.selectbox(
                "Filtrer på rolle", 
                ["Alle", "🔒 Admin", "👤 Bruker"],
                key="hist_rolle"
            )
        with filt_kol2:
            handling_typer = ["Alle"] + sorted(logg_data["Handling"].unique().tolist())
            handling_filter = st.selectbox(
                "Filtrer på handlingstype",
                handling_typer,
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
        passord_input = st.text_input("Vennligst oppgi admin-passord for å låse opp innstillinger", type="password")
        if st.button("Lås opp meny"):
            if passord_input == st.session_state.innstillinger["passord"]:
                st.session_state.is_admin = True
                st.success("Innlogging godkjent. Rettigheter aktivert.")
                st.rerun()
            else:
                st.error("Ugyldig passord. Vennligst prøv igjen.")
    else:
        st.success("🔒 Du har full administratortilgang.")
        
        st.markdown("---")
        st.subheader("Rettigheter og adgangskontroll")
        st.write("Velg hvilke funksjoner som skal kreve admin-passord for å kunne brukes:")
        
        c_nullstill = st.checkbox("Lås full systemnullstilling (Faresone)", value=(str(st.session_state.innstillinger["las_nullstill"]) == "True"))
        c_autofordel = st.checkbox("Lås automatisk lagfordeling", value=(str(st.session_state.innstillinger["las_autofordel"]) == "True"))
        c_import = st.checkbox("Lås filimport fra Excel/CSV", value=(str(st.session_state.innstillinger["las_import"]) == "True"))
        c_slett = st.checkbox("Lås sletting av enkelt-deltakere", value=(str(st.session_state.innstillinger["las_slett_enkel"]) == "True"))
        c_poeng = st.checkbox("Lås Poeng & Resultater menyen", value=(str(st.session_state.innstillinger.get("las_poengforing", "True")) == "True"))
        
        if st.button("💾 Lagre konfigurasjon"):
            st.session_state.innstillinger["las_nullstill"] = "True" if c_nullstill else "False"
            st.session_state.innstillinger["las_autofordel"] = "True" if c_autofordel else "False"
            st.session_state.innstillinger["las_import"] = "True" if c_import else "False"
            st.session_state.innstillinger["las_slett_enkel"] = "True" if c_slett else "False"
            st.session_state.innstillinger["las_poengforing"] = "True" if c_poeng else "False"
            lagre_innstillinger()
            loggfor_handling("Admin", "Rettighetsmatrisen ble oppdatert")
            st.success("Rettighetsmatrisen ble oppdatert og lagret!")
            
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
                st.success("Admin-passordet ble endret!")
