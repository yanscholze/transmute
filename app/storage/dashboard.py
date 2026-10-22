"""Indicadores derivados do último estado salvo de cada trabalho.

Não contamos eventos técnicos como novas importações nem medimos aceite no ERP.
Trabalhos aguardando/interrompidos não possuem resultado concluído e ficam fora
do denominador. A ausência de resultados produz None, nunca sucesso fictício.
"""
SUCCESS = {"Pronta para exportar", "Exportada"}
ASSESSED = SUCCESS | {"Revisar pendências"}


def summarize(jobs):
    ready = sum(job["status"] == "Pronta para exportar" for job in jobs)
    exported = sum(job["status"] == "Exportada" for job in jobs)
    assessed = sum(job["status"] in ASSESSED for job in jobs)
    pending = sum(job["status"] in {"Revisar pendências", "Interrompida"} for job in jobs)
    return {"total": len(jobs), "ready": ready, "exported": exported, "assessed": assessed,
            "successful": ready + exported, "pending": pending,
            "rate": round(100 * (ready + exported) / assessed) if assessed else None}
