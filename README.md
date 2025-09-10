
# XXXTreme Lightning Roulette – Analyzer (CasinoScores compatibile)

**⚠️ Avviso importante**  
Questo strumento fa **analisi descrittiva** delle ultime giocate (frequenze, hot/cold, ritardi, ecc.) e genera 5 numeri *suggeriti* secondo diverse strategie euristiche (hot, overdue, recency-weighted, combo). **Non predice** i prossimi numeri e non può battere il vantaggio del banco.

## Come usare
1. Vai su `https://casinoscores.com/it/xxxtreme-lightning-roulette/` e apri **DevTools → Network**.
2. Identifica la richiesta HTTP che fornisce la lista delle ultime giocate (JSON). Copia:
   - **URL** dell'endpoint
   - eventuali **Headers** (es. `Authorization`)
   - eventuali **Params** (es. `limit=500`)
   - il **campo** dove sta la lista (root) e i nomi dei campi per numero/timestamp/lightning
3. Avvio UI:
   ```bash
   python -m venv .venv && . .venv/bin/activate   # (opzionale)
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Incolla i dati nella UI, premi **Fetch & Analyze**.
5. In basso vedrai i **5 numeri suggeriti** per la prossima mano secondo la strategia scelta.

## CLI
```bash
python run_cli.py --url "https://api.tuo-endpoint" \
  --headers '{"Authorization":"..."}' \
  --params '{"limit":500}' \
  --root results \
  --number number \
  --time time \
  --l-list lightningNumbers \
  --l-num number \
  --l-mul multiplier \
  --strategy combo
```

## Deploy rapido (Streamlit Community Cloud)
1. Fai un fork/commit di questi file in un repository Git.
2. Vai su **share.streamlit.io** con il tuo account e collega il repo.
3. Scegli `app.py` come entrypoint e avvia.
4. Copia l'URL pubblico della tua app (sarà il tuo **link di deploy**).

> Non posso pubblicare un deploy esterno dal mio ambiente, ma questi file sono pronti per il deploy immediato.

## Limiti
- Se l'endpoint è protetto o cambia formato, aggiorna gli header e i dot-path nella UI.
- Se il feed è solo WebSocket, serve un adattamento (non incluso qui).
- Nessuna garanzia di performance: **gioco aleatorio**.
