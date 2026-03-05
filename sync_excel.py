import pandas as pd
import requests
from supabase import create_client
from io import BytesIO
import math
import warnings

warnings.filterwarnings("ignore")

SUPABASE_URL = "HIDDEN_URL_BY_BOT"
SUPABASE_KEY = "REMOVED_BY_BOT"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

url_excel = "https://1drv.ms/x/c/0d5c40b4737f8815/IQDzUkM5JHqdQYcpgfqJ2La3AQi7vEk3zjDk8OOFdcNJANs?download=1"

response = requests.get(url_excel)

arquivo = BytesIO(response.content)

# ler TODAS as abas
abas = pd.read_excel(arquivo, sheet_name=None)

total_processos = 0
total_andamentos = 0

for nome_aba, df in abas.items():

    if nome_aba.lower().endswith("_bkp"):
        continue

    if nome_aba == "Processos":
        continue

    print(f"Processando aba: {nome_aba}")

    # ignorar abas sem coluna NÚMERO
    if "NÚMERO" not in df.columns:
        print(f"Aba ignorada (sem coluna NÚMERO): {nome_aba}")
        continue

    df = df.rename(columns={
        "NÚMERO": "numero_processo",
        "COMARCA": "comarca",
        "INSTÂNCIA": "instancia",
        "SINISTRO ALLIANZ": "sinistro_allianz",
        "AUTOR": "autor",
        "UF": "uf"
    })

    # remover linhas sem processo
    df = df.dropna(subset=["numero_processo"])

    for _, row in df.iterrows():

        numero = str(row.get("numero_processo"))

        processo = {
            "numero_processo": numero,
            "comarca": str(row.get("comarca", "")),
            "instancia": str(row.get("instancia", "")),
            "sinistro_allianz": str(row.get("sinistro_allianz", "")),
            "autor": str(row.get("autor", "")),
            "responsavel": nome_aba,
            "uf": str(row.get("uf", "")),
        }

        # limpar NaN
        processo = {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in processo.items()}

        resp = supabase.table("processos").upsert(
        processo,
        on_conflict="numero_processo"
        ).execute()

        if resp.data:
            processo_id = resp.data[0]["id"]
        else:
            busca = supabase.table("processos").select("id").eq("numero_processo", numero).execute()
            processo_id = busca.data[0]["id"]

        total_processos += 1

        # última coluna = andamento
        andamento = row.iloc[-1]

        if pd.notna(andamento):

            andamento_registro = {
                "processo_id": processo_id,
                "descricao": str(andamento),
                "responsavel_nome": nome_aba
            }

            supabase.table("andamentos").insert(andamento_registro).execute()

            total_andamentos += 1


print("=================================")
print(f"Processos sincronizados: {total_processos}")
print(f"Andamentos sincronizados: {total_andamentos}")