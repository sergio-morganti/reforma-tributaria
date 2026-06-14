#!/usr/bin/env python3
"""Parser de arquivos SPED (EFD Contribuições e EFD ICMS/IPI) para simulação
de impacto da reforma tributária.

Uso:
  python sped_parser.py arquivo1.txt [arquivo2.txt ...] --json parsed.json

Detecta o tipo pelo registro 0000, processa em streaming (arquivos grandes OK),
classifica operações por CFOP × TIPO_ITEM e agrega os valores necessários à
simulação (débitos, créditos por natureza, apurações, ativo, serviços).
Biblioteca padrão apenas.
"""
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation

DATA_RE = re.compile(r"^\d{8}$")


def dec(s):
    if not s:
        return Decimal(0)
    try:
        return Decimal(s.replace(",", "."))
    except InvalidOperation:
        return Decimal(0)


def classifica(cfop, tipo_item=None):
    """Classe da operação a partir do CFOP (e TIPO_ITEM do 0200 quando houver)."""
    if not cfop or len(cfop) != 4:
        return "indefinido"
    d1, resto = cfop[0], cfop[1:]
    entrada = d1 in "123"
    saida = d1 in "567"
    if entrada:
        if resto in ("201", "202", "410", "411", "553") or cfop in ("1660", "1661", "1662"):
            return "devolucao_de_venda"
        if resto in ("151", "152", "408", "409"):
            return "transferencia_entrada"
        if resto[0] == "9":
            return "remessa_retorno_entrada"
        if resto in ("551", "406") or cfop == "1604" or resto == "552":
            return "ativo_imobilizado"
        if resto in ("556", "407", "557"):
            return "uso_e_consumo"
        if resto in ("252", "253", "254", "255", "256", "257", "258"):
            return "energia"
        if resto in ("301", "302", "303", "304", "305", "306"):
            return "comunicacao"
        if resto in ("351", "352", "353", "354", "355", "356"):
            return "frete_tomado"
        if resto in ("102", "403", "113", "117", "118", "409"):
            return "compra_revenda"
        if resto in ("101", "401", "111", "116", "120", "122"):
            return "compra_insumo"
        if tipo_item == "07":
            return "uso_e_consumo"
        if tipo_item == "08":
            return "ativo_imobilizado"
        if tipo_item in ("00",):
            return "compra_revenda"
        if tipo_item in ("01", "02", "03", "06", "10"):
            return "compra_insumo"
        return "outras_entradas"
    if saida:
        if resto in ("201", "202", "410", "411", "553"):
            return "devolucao_de_compra"
        if resto in ("151", "152", "408", "409"):
            return "transferencia_saida"
        if resto[0] == "9":
            return "remessa_retorno_saida"
        if d1 == "7":
            return "exportacao"
        if resto in tuple(str(x) for x in range(351, 361)):
            return "servico_transporte_prestado"
        return "venda"
    return "indefinido"


CLASSES_RECEITA = {"venda", "servico_transporte_prestado"}
CLASSES_CREDITO = {"compra_revenda", "compra_insumo", "uso_e_consumo",
                   "ativo_imobilizado", "energia", "comunicacao", "frete_tomado",
                   "outras_entradas"}


class Acumulador:
    def __init__(self):
        self.meta = {"arquivos": []}
        self.itens = {}            # COD_ITEM -> (TIPO_ITEM, NCM)
        self.ops = defaultdict(lambda: defaultdict(Decimal))  # (fluxo,classe,cfop)->campos
        self.ncm = defaultdict(lambda: defaultdict(Decimal))  # (fluxo, ncm2) -> valor
        self.apuracao = defaultdict(Decimal)
        self.cred_nat = defaultdict(Decimal)   # NAT_BC_CRED -> base PIS (M105) usada como proxy
        self.servicos = defaultdict(Decimal)
        self.ativo = defaultdict(Decimal)
        self.inventario = Decimal(0)
        self.st_entradas = Decimal(0)

    def op(self, fonte, fluxo, cfop, tipo_item, valor, desc=Decimal(0),
           icms=Decimal(0), icms_st=Decimal(0), ipi=Decimal(0), pis=Decimal(0),
           cofins=Decimal(0), ncm=None):
        cls = classifica(cfop, tipo_item)
        k = (fonte, fluxo, cls, cfop or "----")
        o = self.ops[k]
        o["valor"] += valor
        o["desconto"] += desc
        o["icms"] += icms
        o["icms_st"] += icms_st
        o["ipi"] += ipi
        o["pis"] += pis
        o["cofins"] += cofins
        if fluxo == "entrada" and icms_st:
            self.st_entradas += icms_st
        if ncm and len(ncm) >= 2:
            self.ncm[(fluxo, ncm[:2])]["valor"] += valor

    def to_json(self):
        def serial(dd):
            return {("|".join(k) if isinstance(k, tuple) else k):
                    {c: str(v) for c, v in vals.items()} if isinstance(vals, dict)
                    else str(vals) for k, vals in dd.items()}
        return {
            "meta": self.meta,
            "operacoes": serial(self.ops),
            "ncm2": serial(self.ncm),
            "apuracao": {k: str(v) for k, v in self.apuracao.items()},
            "creditos_por_natureza": {k: str(v) for k, v in self.cred_nat.items()},
            "servicos": {k: str(v) for k, v in self.servicos.items()},
            "ativo": {k: str(v) for k, v in self.ativo.items()},
            "inventario_h010": str(self.inventario),
            "icms_st_em_entradas": str(self.st_entradas),
        }


def detecta_tipo(campos):
    # EFD ICMS/IPI:        |0000|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|...
    # EFD Contribuições:   |0000|COD_VER|TIPO_ESCRIT|IND_SIT_ESP|NUM_REC|DT_INI|DT_FIN|NOME|CNPJ|...
    if (len(campos) > 4 and DATA_RE.match(campos[3] or "")
            and DATA_RE.match(campos[4] or "")):
        return "efd_icms_ipi"
    if (len(campos) > 6 and DATA_RE.match(campos[5] or "")
            and DATA_RE.match(campos[6] or "")):
        return "efd_contribuicoes"
    return "desconhecido"


def parse(caminho, ac: Acumulador):
    tipo = None
    doc_atual = {}  # contexto C100/A100/D100 corrente
    with open(caminho, encoding="latin-1", errors="replace") as fh:
        for linha in fh:
            linha = linha.rstrip("\r\n")
            if not linha.startswith("|"):
                continue
            c = linha.split("|")[1:-1]  # remove bordas vazias
            if not c:
                continue
            reg = c[0]
            if reg == "0000":
                tipo = detecta_tipo(c)
                if tipo == "efd_icms_ipi":
                    ac.meta["arquivos"].append({
                        "arquivo": caminho, "tipo": tipo, "dt_ini": c[3],
                        "dt_fin": c[4], "nome": c[5], "cnpj": c[6]})
                elif tipo == "efd_contribuicoes":
                    ac.meta["arquivos"].append({
                        "arquivo": caminho, "tipo": tipo, "dt_ini": c[5],
                        "dt_fin": c[6], "nome": c[7], "cnpj": c[8],
                        "ind_ativ": c[13] if len(c) > 13 else ""})
                else:
                    ac.meta["arquivos"].append({"arquivo": caminho,
                                                "tipo": "desconhecido"})
            elif reg == "0200" and len(c) >= 8:
                ac.itens[c[1]] = (c[6], c[7])
            elif reg == "C100" and len(c) >= 12:
                doc_atual = {"ind_oper": c[1], "cod_sit": c[5]}
            elif reg == "C170" and len(c) >= 24:
                if doc_atual.get("cod_sit") in ("02", "03", "04", "05"):
                    continue  # cancelado/denegado
                fluxo = "entrada" if doc_atual.get("ind_oper") == "0" else "saida"
                ti, ncm = ac.itens.get(c[2], (None, None))
                pis = dec(c[29]) if len(c) > 29 else Decimal(0)
                cof = dec(c[35]) if len(c) > 35 else Decimal(0)
                ac.op(tipo, fluxo, c[10], ti, dec(c[6]), dec(c[7]), dec(c[14]),
                      dec(c[17]), dec(c[23]) if len(c) > 23 else Decimal(0),
                      pis, cof, ncm)
            elif reg == "C190" and len(c) >= 11 and tipo == "efd_icms_ipi":
                fluxo = "entrada" if c[2][0] in "123" else "saida"
                # usar C190 apenas para saídas (nas entradas o C170 é obrigatório
                # e usá-lo nos dois causaria dupla contagem)
                if fluxo == "saida":
                    ac.op(tipo, fluxo, c[2], None, dec(c[4]), Decimal(0),
                          dec(c[6]), dec(c[8]), dec(c[10]))
            elif reg in ("C181", "C185") and len(c) >= 10:
                # consolidação de vendas (EFD Contribuições) — registrar só no C181
                if reg == "C181":
                    ac.op(tipo, "saida", c[2], None, dec(c[3]), dec(c[4]))
            elif reg in ("C191", "C195") and len(c) >= 12:
                if reg == "C191":
                    ac.op(tipo, "entrada", c[3], None, dec(c[4]), dec(c[5]))
                    if c[6]:
                        ac.cred_nat[f"NAT_{c[6]}"] += dec(c[7])
            elif reg == "A100" and len(c) >= 21:
                fluxo = "tomado" if c[1] == "0" else "prestado"
                ac.servicos[f"{fluxo}_valor"] += dec(c[11])
                ac.servicos[f"{fluxo}_iss"] += dec(c[20])
                ac.servicos[f"{fluxo}_pis"] += dec(c[15])
                ac.servicos[f"{fluxo}_cofins"] += dec(c[17])
            elif reg == "F100" and len(c) >= 14:
                if c[1] == "0":
                    ac.servicos["f100_aquisicoes"] += dec(c[5])
                elif c[1] == "1":
                    ac.servicos["f100_receitas"] += dec(c[5])
            elif reg == "F120" and len(c) >= 15:
                ac.ativo["f120_encargo_mes"] += dec(c[5])
                ac.ativo["f120_cred_pis"] += dec(c[10])
                ac.ativo["f120_cred_cofins"] += dec(c[14])
            elif reg == "F130" and len(c) >= 18:
                ac.ativo["f130_aquisicao"] += dec(c[6])
                ac.ativo["f130_cred_pis"] += dec(c[13])
                ac.ativo["f130_cred_cofins"] += dec(c[17])
            elif reg in ("D101", "D105") and len(c) >= 8:
                ac.servicos[f"frete_cred_{'pis' if reg == 'D101' else 'cofins'}"] += dec(c[7])
                ac.servicos["frete_base"] += dec(c[5])
            elif reg == "M100" and len(c) >= 14:
                ac.apuracao["pis_cred_descontado"] += dec(c[13])
            elif reg == "M500" and len(c) >= 14:
                ac.apuracao["cofins_cred_descontado"] += dec(c[13])
            elif reg == "M105" and len(c) >= 7:
                ac.cred_nat[f"M105_NAT_{c[1]}"] += dec(c[6])
            elif reg == "M505" and len(c) >= 7:
                ac.cred_nat[f"M505_NAT_{c[1]}"] += dec(c[6])
            elif reg == "M200" and len(c) >= 13:
                ac.apuracao["pis_a_recolher"] += dec(c[12])
            elif reg == "M600" and len(c) >= 13:
                ac.apuracao["cofins_a_recolher"] += dec(c[12])
            elif reg == "E110" and len(c) >= 15:
                ac.apuracao["icms_debitos"] += dec(c[1])
                ac.apuracao["icms_creditos"] += dec(c[5])
                ac.apuracao["icms_a_recolher"] += dec(c[12])
                ac.apuracao["icms_saldo_credor"] += dec(c[13])
            elif reg == "E210" and len(c) >= 14:
                ac.apuracao["icms_st_retencao"] += dec(c[7])
                ac.apuracao["icms_st_a_recolher"] += dec(c[12])
            elif reg == "E520" and len(c) >= 9:
                ac.apuracao["ipi_a_recolher"] += dec(c[8] if len(c) > 8 else "0")
            elif reg == "H010" and len(c) >= 6:
                ac.inventario += dec(c[5])
            elif reg == "G125" and len(c) >= 10:
                ac.ativo["g125_parcela_icms_48avos"] += dec(c[9])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_out = "parsed.json"
    if "--json" in sys.argv:
        json_out = sys.argv[sys.argv.index("--json") + 1]
        args = [a for a in args if a != json_out]
    if not args:
        sys.exit(__doc__)
    ac = Acumulador()
    for caminho in args:
        parse(caminho, ac)
    out = ac.to_json()
    with open(json_out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    # resumo no stdout
    print(f"Arquivos: {[m.get('tipo') for m in out['meta']['arquivos']]}")
    tot = defaultdict(Decimal)
    for k, v in ac.ops.items():
        tot[(k[0], k[1], k[2])] += v["valor"]
    for (fonte, fluxo, cls), v in sorted(tot.items()):
        print(f"  {fonte:20} {fluxo:8} {cls:28} R$ {v:,.2f}")
    for k, v in sorted(ac.apuracao.items()):
        print(f"  apuração {k:24} R$ {v:,.2f}")
    print(f"JSON: {json_out}")


if __name__ == "__main__":
    main()
