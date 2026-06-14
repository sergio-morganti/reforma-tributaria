#!/usr/bin/env python3
"""Simula o impacto da reforma tributária (IBS/CBS) sobre os dados parseados
do SPED (saída do sped_parser.py).

Uso:
  python simula_impacto.py parsed.json [--aliquota 28] [--simples-share 0.0]
      [--reducao-receita 0.0] [--reducao-compras 0.0] [--json impacto.json]

Parâmetros:
  --aliquota          alíquota de referência somada IBS+CBS, em % (default 28)
  --simples-share     fração (0-1) das compras vindas de fornecedores do Simples
                      "puro" (crédito limitado — modelado como 30% do crédito cheio)
  --reducao-receita   redução média ponderada de alíquota das RECEITAS (0, 0.3, 0.6...)
                      conforme o mix de produtos (cesta básica/saúde/educação etc.)
  --reducao-compras   idem para as COMPRAS (alíquota efetiva dos fornecedores)

Imprime relatório markdown no stdout e grava JSON com todos os números.
"""
import json
import sys
from decimal import Decimal

D = Decimal
CRED_SIMPLES_FRACAO = D("0.30")  # crédito limitado ao cobrado no regime único (premissa)

# trajetória: fração do sistema NOVO e fator sobre ICMS/ISS remanescente
TRAJETORIA = [
    ("2026", D("0.01"), D("1.00"), "ano-teste 0,9%+0,1% (compensável; dispensa se destacar)"),
    ("2027", None, D("1.00"), "CBS plena; PIS/COFINS extintos; IS entra; IPI zerado (exceto ZFM)"),
    ("2028", None, D("1.00"), "idem 2027"),
    ("2029", None, D("0.90"), "ICMS/ISS a 90%; IBS sobe proporcionalmente"),
    ("2030", None, D("0.80"), "ICMS/ISS a 80%"),
    ("2031", None, D("0.70"), "ICMS/ISS a 70%"),
    ("2032", None, D("0.60"), "ICMS/ISS a 60%"),
    ("2033", D("1.00"), D("0.00"), "regime integral IBS/CBS"),
]


def carrega(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def fontes_presentes(ops):
    return {chave.split("|")[0] for chave in ops}


def soma_ops(ops, fluxo, classes, fonte_pref=None):
    """Soma operações. Se as duas EFDs do mesmo período estiverem presentes,
    usa apenas `fonte_pref` para evitar dupla contagem dos documentos de
    mercadoria (que aparecem nos blocos C de ambas)."""
    tot = D(0)
    for chave, campos in ops.items():
        fonte, f, cls, _ = chave.split("|")
        if fonte_pref and fonte != fonte_pref:
            continue
        if f == fluxo and cls in classes:
            tot += D(campos.get("valor", "0")) - D(campos.get("desconto", "0"))
    return tot


def main():
    argv = sys.argv[1:]
    if not argv:
        sys.exit(__doc__)
    src = argv[0]

    def par(nome, default):
        return D(argv[argv.index(nome) + 1]) if nome in argv else D(default)

    t_ref = par("--aliquota", "28") / 100
    simples = par("--simples-share", "0")
    red_rec = par("--reducao-receita", "0")
    red_cmp = par("--reducao-compras", "0")
    json_out = (argv[argv.index("--json") + 1] if "--json" in argv else "impacto.json")

    p = carrega(src)
    ops = p.get("operacoes", {})
    ap = {k: D(v) for k, v in p.get("apuracao", {}).items()}
    sv = {k: D(v) for k, v in p.get("servicos", {}).items()}
    at = {k: D(v) for k, v in p.get("ativo", {}).items()}

    # Dedupe: se as duas EFDs do mesmo período foram enviadas, os documentos de
    # mercadoria (bloco C) aparecem em ambas — usar só a EFD ICMS/IPI para o
    # bloco C; serviços (bloco A/F) vêm da Contribuições via dict `servicos`.
    fontes = fontes_presentes(ops)
    fonte_pref = "efd_icms_ipi" if {"efd_icms_ipi", "efd_contribuicoes"} <= fontes else None

    # ---- Receitas e débito novo --------------------------------------------
    receita_trib = soma_ops(ops, "saida", {"venda", "servico_transporte_prestado"},
                            fonte_pref)
    receita_trib += sv.get("prestado_valor", D(0)) + sv.get("f100_receitas", D(0))
    dev_venda = soma_ops(ops, "entrada", {"devolucao_de_venda"}, fonte_pref)
    exportacao = soma_ops(ops, "saida", {"exportacao"}, fonte_pref)
    base_debito = receita_trib - dev_venda
    t_rec = t_ref * (1 - red_rec)
    debito_novo = base_debito * t_rec

    # ---- Compras e crédito novo --------------------------------------------
    classes_cred = {"compra_revenda", "compra_insumo", "uso_e_consumo",
                    "ativo_imobilizado", "energia", "comunicacao", "frete_tomado",
                    "outras_entradas"}
    compras = {cls: soma_ops(ops, "entrada", {cls}, fonte_pref)
               for cls in classes_cred}
    servicos_tomados = sv.get("tomado_valor", D(0)) + sv.get("f100_aquisicoes", D(0))
    dev_compra = soma_ops(ops, "saida", {"devolucao_de_compra"}, fonte_pref)
    base_credito = sum(compras.values()) + servicos_tomados - dev_compra
    t_cmp = t_ref * (1 - red_cmp)
    t_medio = t_cmp * (1 - simples) + t_cmp * CRED_SIMPLES_FRACAO * simples
    credito_novo = base_credito * t_medio

    # créditos que NASCEM com a reforma (hoje inexistentes/restritos)
    creditos_novos_categorias = {
        "uso_e_consumo (CFOP x556)": compras["uso_e_consumo"] * t_medio,
        "servicos_tomados (bloco A/F100)": servicos_tomados * t_medio,
        "energia_comunicacao": (compras["energia"] + compras["comunicacao"]) * t_medio,
        "ativo_imediato_vs_parcelado": compras["ativo_imobilizado"] * t_medio,
        "icms_st_que_deixa_de_ser_custo": D(p.get("icms_st_em_entradas", "0")),
    }

    # ---- Baseline ----------------------------------------------------------
    iss = sv.get("prestado_iss", D(0))
    baseline = (ap.get("icms_a_recolher", D(0)) + ap.get("icms_st_a_recolher", D(0))
                + ap.get("ipi_a_recolher", D(0)) + ap.get("pis_a_recolher", D(0))
                + ap.get("cofins_a_recolher", D(0)) + iss)
    carga_nova = debito_novo - credito_novo
    delta = carga_nova - baseline

    # ---- Trajetória --------------------------------------------------------
    linhas = []
    for ano, frac_novo, fator_velho, nota in TRAJETORIA:
        if frac_novo is None:
            # 2027-2032: CBS plena (~t_ref*0.93 da carga nova é federal — usar
            # partilha simplificada: CBS ≈ 8,8/28 e IBS o restante? Manter
            # aproximação linear: novo = carga_nova × participação)
            # Aproximação: peso do novo sistema = 1 − fator_velho×(peso ICMS+ISS)
            # com PIS/COFINS já extintos a partir de 2027.
            pis_cof = ap.get("pis_a_recolher", D(0)) + ap.get("cofins_a_recolher", D(0))
            peso_pis_cof = pis_cof / baseline if baseline else D(0)
            novo = carga_nova * (peso_pis_cof + (1 - peso_pis_cof) * (1 - fator_velho))
            velho = (baseline - pis_cof) * fator_velho
        else:
            novo = carga_nova * frac_novo
            velho = baseline * (D(1) if ano == "2026" else fator_velho)
            if ano == "2026":
                novo = D(0)  # teste compensável/dispensado
        linhas.append({"ano": ano, "sistema_novo": novo, "sistema_antigo": velho,
                       "total": novo + velho, "nota": nota})

    resultado = {
        "premissas": {"t_ref_pct": str(t_ref * 100), "reducao_receita": str(red_rec),
                      "reducao_compras": str(red_cmp), "share_simples": str(simples),
                      "credito_simples_fracao": str(CRED_SIMPLES_FRACAO),
                      "fonte_mercadorias": fonte_pref or "única"},
        "receitas": {"tributavel": str(base_debito), "exportacao_imune": str(exportacao)},
        "debito_novo": str(debito_novo),
        "base_credito": str(base_credito),
        "credito_novo": str(credito_novo),
        "creditos_que_nascem_com_a_reforma":
            {k: str(v) for k, v in creditos_novos_categorias.items()},
        "compras_por_classe": {k: str(v) for k, v in compras.items()},
        "baseline_atual": {**{k: str(v) for k, v in ap.items()},
                           "iss_estimado": str(iss), "total": str(baseline)},
        "carga_nova_regime_pleno": str(carga_nova),
        "delta_carga": str(delta),
        "trajetoria": [{**l, "sistema_novo": str(l["sistema_novo"]),
                        "sistema_antigo": str(l["sistema_antigo"]),
                        "total": str(l["total"])} for l in linhas],
        "ativo_detalhe": {k: str(v) for k, v in at.items()},
    }
    with open(json_out, "w", encoding="utf-8") as fh:
        json.dump(resultado, fh, ensure_ascii=False, indent=2)

    f = lambda x: f"R$ {x:,.2f}"
    print("# Simulação de impacto IBS/CBS (regime pleno, valores do período analisado)\n")
    print(f"Alíquota de referência: {t_ref*100}% | redução receitas: {red_rec} | "
          f"redução compras: {red_cmp} | share Simples: {simples}\n")
    print(f"- Receita tributável: {f(base_debito)} (exportação imune: {f(exportacao)})")
    print(f"- **Débito novo**: {f(debito_novo)}")
    print(f"- Base de crédito (ampla): {f(base_credito)}")
    print(f"- **Crédito novo**: {f(credito_novo)}")
    print(f"- **Carga nova (pleno)**: {f(carga_nova)}")
    print(f"- Carga atual (baseline): {f(baseline)}")
    pct = f" ({(delta / baseline * 100):.1f}% vs. atual)" if baseline else ""
    print(f"- **ΔCarga**: {f(delta)}{pct}")
    print("\n## Créditos que nascem com a reforma")
    for k, v in creditos_novos_categorias.items():
        print(f"- {k}: {f(v)}")
    print("\n## Trajetória 2026-2033 (aproximação linear)")
    print("| Ano | Sistema novo | Sistema antigo | Total | Nota |")
    print("|---|---|---|---|---|")
    for l in linhas:
        print(f"| {l['ano']} | {f(l['sistema_novo'])} | {f(l['sistema_antigo'])} "
              f"| {f(l['total'])} | {l['nota']} |")
    print(f"\nJSON: {json_out}")


if __name__ == "__main__":
    main()
