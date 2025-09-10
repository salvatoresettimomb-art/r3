
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from analyzer import analyze, standardize_spins, suggest_numbers
from clients import fetch_http_items

st.set_page_config(page_title="XXXTreme Lightning Roulette – Analyzer", layout="wide")

st.title("XXXTreme Lightning Roulette – Analyzer (CasinoScores compatibile)")

st.markdown("""
**Disclaimer:** gioco aleatorio. Questo tool fa **analisi descrittiva** (hot/cold, ritardi, ecc.).
Le *suggerite* non aumentano le probabilità reali del prossimo esito.
""")

with st.expander("Sorgente dati (HTTP) – incolla l'endpoint trovato con DevTools → Network"):
    url = st.text_input("Endpoint URL", value="", placeholder="https://...")
    headers_text = st.text_area("Headers (JSON)", value="", placeholder='{"Authorization":"..."}')
    params_text = st.text_area("Params (JSON)", value="", placeholder='{"limit": 500}')
    root_list_path = st.text_input("Root list path (dot-path)", value="results")

with st.expander("Mapping dei campi (dot-path)"):
    number_path = st.text_input("Path del numero vincente", value="number")
    time_path = st.text_input("Path del timestamp (opzionale)", value="time")
    lightning_list_path = st.text_input("Path lista 'lightning' (opzionale)", value="lightningNumbers")
    lightning_number_path = st.text_input("Path numero dentro ogni lightning item", value="number")
    lightning_multiplier_path = st.text_input("Path moltiplicatore dentro ogni lightning item", value="multiplier")

left, right = st.columns([1,1])
n_spins = left.number_input("Quante giocate considerare (se supportato)", min_value=50, max_value=5000, value=500, step=50)
strategy = right.selectbox("Strategia suggerimenti (5 numeri)", ["combo","hot","overdue","recency_weighted"])

go = st.button("Fetch & Analyze")

def _safe_json(txt):
    if not txt.strip():
        return {}
    return json.loads(txt)

if go:
    if not url:
        st.error("Inserisci l'URL dell'endpoint HTTP.")
        st.stop()

    try:
        headers = _safe_json(headers_text)
        params = _safe_json(params_text)
    except Exception as e:
        st.error(f"Errore parse Headers/Params: {e}")
        st.stop()

    try:
        raw_items = fetch_http_items(url, headers=headers, params=params, root_list_path=root_list_path)
    except Exception as e:
        st.error(f"Errore durante la richiesta HTTP: {e}")
        st.stop()

    mapping = {
        "number_path": number_path,
        "time_path": time_path if time_path else None,
        "lightning_list_path": lightning_list_path if lightning_list_path else None,
        "lightning_number_path": lightning_number_path if lightning_number_path else None,
        "lightning_multiplier_path": lightning_multiplier_path if lightning_multiplier_path else None,
    }

    spins = standardize_spins(raw_items, mapping)
    if not spins:
        st.warning("Nessuna giocata riconosciuta. Controlla i path e mostra un esempio JSON (vedi sotto).")
        st.json(raw_items[:3])
        st.stop()

    stats = analyze(spins)

    st.subheader("Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totale giocate", stats["total_spins"])
    c2.metric("Lightning hit rate", f"{stats['lightning_rate']*100:.2f}%")
    c3.metric("Più frequente", f"{stats['hot_top10'][0][0]} ({stats['hot_top10'][0][1]})" if stats["hot_top10"] else "-")
    c4.metric("Più in ritardo", f"{stats['longest_gaps_top10'][0][0]} ({stats['longest_gaps_top10'][0][1]})" if stats["longest_gaps_top10"] else "-")

    # Frequenze per numero
    st.subheader("Frequenza per numero (0–36)")
    freq_series = pd.Series(stats["freq"]).reindex(range(37)).fillna(0).astype(int)
    fig1 = plt.figure()
    freq_series.plot(kind="bar")
    plt.xlabel("Numero")
    plt.ylabel("Frequenza")
    st.pyplot(fig1, clear_figure=True)

    # Tabelle hot/cold/ritardi
    hot_df = pd.DataFrame(stats["hot_top10"], columns=["Numero","Frequenza"])
    cold_df = pd.DataFrame(stats["cold_bottom10"], columns=["Numero","Frequenza"])
    gap_df = pd.DataFrame(stats["longest_gaps_top10"], columns=["Numero","Gap dall'ultima uscita"])

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**Top 10 caldi**")
        st.dataframe(hot_df, use_container_width=True)
    with col_b:
        st.markdown("**Top 10 freddi**")
        st.dataframe(cold_df, use_container_width=True)
    with col_c:
        st.markdown("**Top 10 ritardi**")
        st.dataframe(gap_df, use_container_width=True)

    # Aggregazioni
    st.subheader("Aggregazioni")
    agg_cols = st.columns(4)
    by_color = pd.Series(stats["by_color"]).rename_axis("Colore").reset_index(name="Conta")
    by_parity = pd.Series(stats["by_parity"]).rename_axis("Parità").reset_index(name="Conta")
    by_dozen = pd.Series(stats["by_dozen"]).rename_axis("Dozzina").reset_index(name="Conta")
    by_column = pd.Series(stats["by_column"]).rename_axis("Colonna").reset_index(name="Conta")

    with agg_cols[0]:
        st.markdown("**Rosso/Nero/Zero**")
        st.dataframe(by_color, use_container_width=True)
    with agg_cols[1]:
        st.markdown("**Pari/Dispari**")
        st.dataframe(by_parity, use_container_width=True)
    with agg_cols[2]:
        st.markdown("**Dozzine**")
        st.dataframe(by_dozen, use_container_width=True)
    with agg_cols[3]:
        st.markdown("**Colonne**")
        st.dataframe(by_column, use_container_width=True)

    # Suggerimenti: 5 numeri
    st.subheader("Suggerimento 5 numeri (per la prossima mano)")
    picks, all_buckets = suggest_numbers(spins, strategy=strategy, k=5, decay=0.97)
    st.write(f"**Strategia selezionata:** {strategy}")
    st.write(f"**Numeri suggeriti:** {picks}")
    with st.expander("Vedi suggerimenti per tutte le strategie"):
        st.json(all_buckets)

    st.caption("Nota: non è una previsione. Giri indipendenti; il banco mantiene vantaggio nel lungo periodo.")

else:
    st.info("Compila la sorgente e i mapping, poi premi **Fetch & Analyze**.")
