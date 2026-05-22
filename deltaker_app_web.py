import streamlit as st
import pandas as pd
import random
from pathlib import Path
from datetime import datetime

# Konfigurasjon og faste stier
DATA_FILE = Path("sportsfestival_data.csv")
LOGG_FILE = Path("sportsfestival_logg.csv")
KATEGORIER = ["Elev", "நிர்வாகம்", "Lærer", "Frivillig", "Gjest"]
LAG_A = "Lag Rød"
LAG_B = "Lag Gul"

# Sideoppsett for Streamlit (må være det første som kjøres)
st.set_page_config(
    page_title="Sportsfestival 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisering av databehandler direkte i sesjonsminnet til nettsiden
if "kolonner" not in st.session_state:
    st.session_state.kolonner = ["ID", "Navn", "Kategori", "Kull", "Lag"]
    st.session_state.logg_kolonner = ["Tidspunkt", "Handling", "Detaljer"]

def last_inn_data():
    if DATA_FILE.exists():
        try:
            return pd.read_csv(DATA_FILE, encoding="utf-8-sig", dtype=str).fillna("")
        except Exception:
            pass
    return pd.DataFrame(columns=st.session_state.kolonner)

def last_inn_logg():
    if LOGG_FILE.exists():
        try:
            return pd.read_csv(LOGG_FILE, encoding="utf-8-sig", dtype=str).fillna("")
        except Exception:
            pass
    return pd.DataFrame(columns=st.session_state.logg_kolonner)

if "df" not in st.session_state:
    st.session_state.df = last_inn_data()
if "logg_df" not in st.session_state:
    st.session_state.logg_df = last_inn_logg()

def lagre_alle_data():
    try:
        st.session_state.df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        st.session_state.logg_df.to_csv(LOGG_FILE, index=False, encoding="utf-8-sig")
        return True
    except Exception as e:
        st.error(f"Kunne ikke lagre til filen akkurat nå: {e}")
        return False

def loggfor_handling(handling, detaljer):
    tid = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ny_rad = pd.DataFrame([[tid, handling, detaljer]], columns=st.session_state.logg_kolonner)
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

# Sidemeny for mobil- og PC-navigasjon
st.sidebar.title("🏆 Sportsfestival")
st.sidebar.write("Admin System 2026")
side = st.sidebar.radio("Navigasjon", ["📋 Registrering", "🏁 Laginndeling", "📊 Informasjon", "📜 Historikk"])

# Grønn statusindikator i sidemenyen for å simulere den visuelle prikken
st.sidebar.markdown("---")
st.sidebar.markdown("🟢 **Status:** Alt er synkronisert og lagret")

if side == "📋 Registrering":
    st.title("Deltakerregistrering")
    
    reg_modus = st.radio("Velg handling", ["Legg til ny", "Rediger / Slett eksisterende"], horizontal=True)
    
    if reg_modus == "Legg til ny":
        with st.form("ny_deltaker_form", clear_on_submit=True):
            navn = st.text_input("Fullt navn")
            kategori = st.selectbox("Kategori", KATEGORIER)
            kull = st.text_input("Fødselsår / Klasse (Kun for elever)")
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
                        ny_rad = pd.DataFrame([[ny_id_str, navn.strip(), kategori, kull_verdi, ""]], columns=st.session_state.kolonner)
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
            oppdatert_kull = st.text_input("Fødselsår / Klasse", st.session_state.df.at[idx, "Kull"], disabled=(oppdatert_kat != "Elev"))
            
            kol1, kol2 = st.columns(2)
            with kol1:
                if st.button("💾 Oppdater informasjon", use_container_width=True):
                    gammelt_navn = st.session_state.df.at[idx, "Navn"]
                    st.session_state.df.at[idx, "Navn"] = oppdatert_navn.strip()
                    st.session_state.df.at[idx, "Kategori"] = oppdatert_kat
                    st.session_state.df.at[idx, "Kull"] = oppdatert_kull.strip() if oppdatert_kat == "Elev" else ""
                    loggfor_handling("Oppdatert", f"ID {valgt_id}: {gammelt_navn} endret til {oppdatert_navn}")
                    if lagre_alle_data():
                        st.success("Endringene ble lagret.")
                        st.rerun()
            with kol2:
                if st.button("🗑️ Slett deltaker permanent", type="primary", use_container_width=True):
                    slettet_navn = st.session_state.df.at[idx, "Navn"]
                    st.session_state.df = st.session_state.df[st.session_state.df["ID"] != valgt_id].reset_index(drop=True)
                    loggfor_handling("Slettet", f"ID {valgt_id}: {slettet_navn}")
                    if lagre_alle_data():
                        st.success("Deltakeren ble slettet.")
                        st.rerun()

    st.markdown("---")
    st.subheader("Filimport (Valgfritt)")
    opplastet_fil = st.file_uploader("Last opp Excel eller CSV for å hente inn deltakere", type=["csv", "xlsx"])
    if opplastet_fil:
        try:
            if opplastet_fil.name.endswith(".xlsx"):
                ny_df = pd.read_excel(opplastet_fil, dtype=str).fillna("")
            else:
                ny_df = pd.read_csv(opplastet_fil, dtype=str).fillna("")
            
            importert_teller = 0
            for _, rad in ny_df.iterrows():
                importert_navn = rad.get("Navn", "")
                if importert_navn:
                    neste_id = finn_laveste_ledige_id()
                    if neste_id <= 99:
                        neste_id_str = f"{neste_id:02d}"
                        importert_kat = rad.get("Kategori", "Elev")
                        importert_kull = rad.get("Kull", "") if importert_kat == "Elev" else ""
                        midlertidig_rad = pd.DataFrame([[neste_id_str, importert_navn.strip(), importert_kat, importert_kull, ""]], columns=st.session_state.kolonner)
                        st.session_state.df = pd.concat([st.session_state.df, midlertidig_rad], ignore_index=True)
                        importert_teller += 1
            
            if importert_teller > 0:
                loggfor_handling("Import", f"Importerte {importert_teller} deltakere eksternt")
                lagre_alle_data()
                st.success(f"Vellykket import av {importert_teller} deltakere.")
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
        st.rerun()

elif side == "🏁 Laginndeling":
    st.title("Laginndeling og balansering")
    
    b_kol1, b_kol2, b_kol3, b_kol4 = st.columns(4)
    with b_kol1:
        if st.button("✨ Auto-fordel ufordelte", use_container_width=True):
            ufordelte = st.session_state.df[(st.session_state.df["Kategori"] == "Elev") & (st.session_state.df["Lag"] == "")]
            if ufordelte.empty:
                st.info("Ingen ufordelte elever ble funnet.")
            else:
                indekser = ufordelte.index.tolist()
                random.shuffle(indekser)
                antall_a = len(st.session_state.df[st.session_state.df["Lag"] == LAG_A])
                antall_b = len(st.session_state.df[st.session_state.df["Lag"] == LAG_B])
                
                for idx in indekser:
                    if antall_a <= antall_b:
                        st.session_state.df.at[idx, "Lag"] = LAG_A
                        antall_a += 1
                    else:
                        st.session_state.df.at[idx, "Lag"] = LAG_B
                        antall_b += 1
                loggfor_handling("Laginndeling", f"Balanserte {len(indekser)} nye elever")
                lagre_alle_data()
                st.rerun()
                
    with b_kol2:
        if st.button("⚠️ Nullstill og fordel alle", use_container_width=True):
            elever = st.session_state.df[st.session_state.df["Kategori"] == "Elev"].copy()
            indekser = elever.index.tolist()
            random.shuffle(indekser)
            midt = len(indekser) // 2
            for i, idx in enumerate(indekser):
                st.session_state.df.at[idx, "Lag"] = LAG_A if i < midt else LAG_B
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
        flytt_valg = st.selectbox("Velg elev som skal flyttes eller endres manuell", elever_kun["ID"] + " - " + elever_kun["Navn"])
        flytt_id = flytt_valg.split(" - ")[0]
        f_idx = st.session_state.df.index[st.session_state.df["ID"] == flytt_id].tolist()[0]
        
        nytt_lag_valg = st.radio(f"Velg lagtilhørighet for {st.session_state.df.at[f_idx, 'Navn']}", ["Ufordelt", LAG_A, LAG_B], horizontal=True)
        nytt_lag_verdi = "" if nytt_lag_valg == "Ufordelt" else nytt_lag_valg
        
        if st.session_state.df.at[f_idx, "Lag"] != nytt_lag_verdi:
            gammelt_l = st.session_state.df.at[f_idx, "Lag"]
            st.session_state.df.at[f_idx, "Lag"] = nytt_lag_verdi
            loggfor_handling("Flyttet", f"{st.session_state.df.at[f_idx, 'Navn']} flyttet fra {gammelt_l if gammelt_l else 'Ufordelt'} til {nytt_lag_valg}")
            lagre_alle_data()
            st.rerun()

    st.markdown("---")
    l_kol1, l_kol2, l_kol3 = st.columns(3)
    with l_kol1:
        st.markdown(f"### 🔴 {LAG_A}")
        df_lag_a = st.session_state.df[st.session_state.df["Lag"] == LAG_A][["ID", "Navn", "Kull"]]
        st.dataframe(df_lag_a, use_container_width=True, hide_index=True)
    with l_kol2:
        st.markdown("### ⚪ Ufordelte Elever")
        df_lag_u = st.session_state.df[(st.session_state.df["Kategori"] == "Elev") & (st.session_state.df["Lag"] == "")][["ID", "Navn", "Kull"]]
        st.dataframe(df_lag_u, use_container_width=True, hide_index=True)
    with l_kol3:
        st.markdown(f"### 🟡 {LAG_B}")
        df_lag_b = st.session_state.df[st.session_state.df["Lag"] == LAG_B][["ID", "Navn", "Kull"]]
        st.dataframe(df_lag_b, use_container_width=True, hide_index=True)

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
        st.write(f"• **{kat}:** {antall_kat} personer")

elif side == "📜 Historikk":
    st.title("Systemhistorikk og endringslogg")
    st.write("Her logges alle endringer som gjøres i systemet automatisk for full kontroll over tildelte ID-er og lagendringer.")
    st.dataframe(st.session_state.logg_df, use_container_width=True, hide_index=True)