#!/usr/bin/env python3
"""Validador de NF-e/NFC-e — recalcula tributos (ICMS, IPI, PIS, COFINS, IS,
IBS/CBS da NT 2025.002-RTC), confere totais e reporta retenções.

Uso:
  python valida_nfe.py nota.xml [outra.xml ... | diretorio/] [--json saida.json]

Saída: relatório no stdout (ERRO/ALERTA/INFO) e, com --json, estrutura completa.
Tolerância de arredondamento: R$ 0,01 por item/total (half-up por item).
Biblioteca padrão apenas (xml.etree).
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from decimal import ROUND_HALF_UP, Decimal

NS = {"n": "http://www.portalfiscal.inf.br/nfe"}
TOL = Decimal("0.01")
OBRIGATORIO_IBSCBS = "2026-08-03"   # RV UB12-10 em produção (NT 2025.002 v1.40)
VALOR_JURIDICO = "2026-01-01"
ALIQ_TESTE = {"2026": {"ibs": Decimal("0.1"), "cbs": Decimal("0.9")}}


def d(node, path=None, default=None):
    """Extrai Decimal de um campo (ou None)."""
    el = node.find(path, NS) if path else node
    if el is None or el.text is None:
        return default
    try:
        return Decimal(el.text)
    except Exception:
        return default


def t(node, path):
    el = node.find(path, NS)
    return el.text if el is not None and el.text else None


def r2(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Achados(list):
    def add(self, sev, onde, msg, declarado=None, esperado=None):
        item = {"severidade": sev, "onde": onde, "mensagem": msg}
        if declarado is not None:
            item["declarado"] = str(declarado)
        if esperado is not None:
            item["esperado"] = str(esperado)
        self.append(item)

    def cmp(self, onde, campo, declarado, esperado):
        if declarado is None or esperado is None:
            return
        if abs(declarado - r2(esperado)) > TOL:
            self.add("ERRO", onde, f"{campo} divergente", declarado, r2(esperado))


def valida_icms(det, n, a):
    icms = det.find("n:imposto/n:ICMS", NS)
    if icms is None:
        return {}
    g = list(icms)[0] if len(icms) else None
    if g is None:
        return {}
    tag = g.tag.split("}")[1]
    cst = t(g, "n:CST") or t(g, "n:CSOSN")
    vbc, p, v = d(g, "n:vBC"), d(g, "n:pICMS"), d(g, "n:vICMS")
    if vbc is not None and p is not None and v is not None:
        a.cmp(f"item {n} ICMS", "vICMS", v, vbc * p / 100)
    # ST
    vbcst, pst, vst = d(g, "n:vBCST"), d(g, "n:pICMSST"), d(g, "n:vICMSST")
    if vbcst is not None and pst is not None and vst is not None:
        proprio = v or Decimal(0)
        a.cmp(f"item {n} ICMS-ST", "vICMSST", vst, vbcst * pst / 100 - proprio)
    vfcp = d(g, "n:vFCP")
    if vfcp is not None and d(g, "n:vBCFCP") is not None and d(g, "n:pFCP") is not None:
        a.cmp(f"item {n} FCP", "vFCP", vfcp, d(g, "n:vBCFCP") * d(g, "n:pFCP") / 100)
    return {"grupo": tag, "cst": cst, "vBC": vbc, "vICMS": v, "vICMSST": vst}


def valida_ipi(det, n, a):
    ipi = det.find("n:imposto/n:IPI/n:IPITrib", NS)
    if ipi is None:
        return {}
    vbc, p, v = d(ipi, "n:vBC"), d(ipi, "n:pIPI"), d(ipi, "n:vIPI")
    q, vu = d(ipi, "n:qUnid"), d(ipi, "n:vUnid")
    if v is not None:
        if vbc is not None and p is not None:
            a.cmp(f"item {n} IPI", "vIPI", v, vbc * p / 100)
        elif q is not None and vu is not None:
            a.cmp(f"item {n} IPI", "vIPI", v, q * vu)
    return {"vIPI": v}


def valida_pis_cofins(det, n, a, qual):
    g = det.find(f"n:imposto/n:{qual}", NS)
    if g is None:
        return {}
    sub = list(g)[0] if len(g) else None
    if sub is None:
        return {}
    cst = t(sub, "n:CST")
    v = d(sub, f"n:v{qual}")
    vbc, p = d(sub, "n:vBC"), d(sub, f"n:p{qual}")
    q, al = d(sub, "n:qBCProd"), d(sub, "n:vAliqProd")
    if v is not None:
        if vbc is not None and p is not None:
            a.cmp(f"item {n} {qual}", f"v{qual}", v, vbc * p / 100)
        elif q is not None and al is not None:
            a.cmp(f"item {n} {qual}", f"v{qual}", v, q * al)
    return {"cst": cst, f"v{qual}": v}


def aliq_efetiva(g_ente, p_tag):
    """Retorna (aliquota_nominal, aliquota_efetiva esperada, pAliqEfet declarada)."""
    p = d(g_ente, f"n:{p_tag}")
    gred = g_ente.find("n:gRed", NS)
    if gred is not None:
        pred = d(gred, "n:pRedAliq", Decimal(0))
        pefet_decl = d(gred, "n:pAliqEfet")
        pefet_esp = p * (1 - pred / 100) if p is not None else None
        return p, pefet_esp, pefet_decl
    return p, p, None


def valida_ibscbs(det, n, a, ano, dhemi):
    g = det.find("n:imposto/n:IBSCBS", NS)
    if g is None:
        return None
    cst, cclass = t(g, "n:CST"), t(g, "n:cClassTrib")
    res = {"CST": cst, "cClassTrib": cclass}
    exige = {"510": "gDif", "550": "gTribRegular", "620": "gIBSCBSMono",
             "800": "gTransfCred"}
    gn = g.find("n:gIBSCBS", NS)
    mono = g.find("n:gIBSCBSMono", NS)
    transf = g.find("n:gTransfCred", NS)
    if cst in exige:
        alvo = exige[cst]
        achou = (mono is not None if alvo == "gIBSCBSMono" else
                 transf is not None if alvo == "gTransfCred" else
                 gn is not None and any(e.find(f"n:{alvo}", NS) is not None
                                        for e in (gn.find("n:gIBSUF", NS),
                                                  gn.find("n:gIBSMun", NS),
                                                  gn.find("n:gCBS", NS)) if e is not None)
                 or (gn is not None and gn.find(f"n:{alvo}", NS) is not None))
        if not achou:
            a.add("ERRO", f"item {n} IBSCBS", f"CST {cst} exige grupo {alvo} ausente")
    if cst in ("200", "210") and gn is not None:
        tem_red = any(e is not None and e.find("n:gRed", NS) is not None
                      for e in (gn.find("n:gIBSUF", NS), gn.find("n:gIBSMun", NS),
                                gn.find("n:gCBS", NS)))
        if not tem_red:
            a.add("ERRO", f"item {n} IBSCBS", f"CST {cst} exige gRed ausente")
    if gn is not None:
        vbc = d(gn, "n:vBC")
        res["vBC"] = vbc
        soma_ibs = Decimal(0)
        for ente, ptag, vtag in (("gIBSUF", "pIBSUF", "vIBSUF"),
                                 ("gIBSMun", "pIBSMun", "vIBSMun"),
                                 ("gCBS", "pCBS", "vCBS")):
            ge = gn.find(f"n:{ente}", NS)
            if ge is None:
                continue
            p, pefet_esp, pefet_decl = aliq_efetiva(ge, ptag)
            v = d(ge, f"n:{vtag}")
            res[vtag] = v
            if pefet_decl is not None and pefet_esp is not None:
                a.cmp(f"item {n} {ente}", "pAliqEfet", pefet_decl, pefet_esp)
            aliq = pefet_decl if pefet_decl is not None else pefet_esp
            if vbc is not None and aliq is not None and v is not None:
                a.cmp(f"item {n} {ente}", vtag, v, vbc * aliq / 100)
            if v is not None and vtag in ("vIBSUF", "vIBSMun"):
                soma_ibs += v
            # alíquotas do ano-teste
            if ano in ALIQ_TESTE and p is not None:
                ref = ALIQ_TESTE[ano]["cbs"] if ente == "gCBS" else None
                if ente == "gIBSUF" and p != ALIQ_TESTE[ano]["ibs"]:
                    a.add("ALERTA", f"item {n} {ente}",
                          f"pIBSUF={p}% difere da alíquota-teste {ALIQ_TESTE[ano]['ibs']}% de {ano}")
                if ente == "gCBS" and ref is not None and p != ref:
                    a.add("ALERTA", f"item {n} {ente}",
                          f"pCBS={p}% difere da alíquota-teste {ref}% de {ano}")
        vibs = d(gn, "n:vIBS")
        res["vIBS"] = vibs
        if vibs is not None:
            a.cmp(f"item {n} IBSCBS", "vIBS (= vIBSUF+vIBSMun)", vibs, soma_ibs)
        # plausibilidade da base (sem IPI/ICMS na transição)
        prod = det.find("n:prod", NS)
        op = ((d(prod, "n:vProd") or Decimal(0)) + (d(prod, "n:vFrete") or Decimal(0))
              + (d(prod, "n:vSeg") or Decimal(0)) + (d(prod, "n:vOutro") or Decimal(0))
              - (d(prod, "n:vDesc") or Decimal(0)))
        if vbc is not None and vbc > op + TOL:
            a.add("ALERTA", f"item {n} IBSCBS",
                  "vBC maior que valor da operação — verificar inclusão indevida de "
                  "IPI/ICMS na base (na transição ficam fora, art. 12 §2º LC 214)",
                  vbc, r2(op))
    if mono is not None:
        gp = mono.find("n:gMonoPadrao", NS)
        if gp is not None:
            q = d(gp, "n:qBCMono")
            for ad, vv in (("adRemIBS", "vIBSMono"), ("adRemCBS", "vCBSMono")):
                if q is not None and d(gp, f"n:{ad}") is not None and d(gp, f"n:{vv}") is not None:
                    a.cmp(f"item {n} monofasia", vv, d(gp, f"n:{vv}"), q * d(gp, f"n:{ad}"))
    return res


def soma_itens(itens, chave):
    return sum((i.get(chave) or Decimal(0)) for i in itens)


def valida_totais(inf, itens, a):
    tot = inf.find("n:total/n:ICMSTot", NS)
    if tot is not None:
        for campo, chave in (("vICMS", "vICMS"), ("vIPI", "vIPI"),
                             ("vPIS", "vPIS"), ("vCOFINS", "vCOFINS")):
            vt = d(tot, f"n:{campo}")
            if vt is not None:
                a.cmp("totais ICMSTot", campo, vt, soma_itens(itens, chave))
    ibst = inf.find("n:total/n:IBSCBSTot", NS)
    if ibst is not None:
        mapa = (("n:vBCIBSCBS", "vBC"), ("n:gIBS/n:vIBS", "vIBS"),
                ("n:gIBS/n:gIBSUF/n:vIBSUF", "vIBSUF"),
                ("n:gIBS/n:gIBSMun/n:vIBSMun", "vIBSMun"),
                ("n:gCBS/n:vCBS", "vCBS"))
        for path, chave in mapa:
            vt = d(ibst, path)
            if vt is not None:
                a.cmp("totais IBSCBSTot", path.split("n:")[-1], vt,
                      soma_itens(itens, chave))


def retencoes(inf):
    ret = inf.find("n:total/n:retTrib", NS)
    if ret is None:
        return {}
    campos = ["vRetPIS", "vRetCOFINS", "vRetCSLL", "vBCIRRF", "vIRRF",
              "vBCRetPrev", "vRetPrev"]
    return {c: str(d(ret, f"n:{c}")) for c in campos if d(ret, f"n:{c}") is not None}


def valida_arquivo(caminho):
    a = Achados()
    tree = ET.parse(caminho)
    root = tree.getroot()
    inf = root.find(".//n:NFe/n:infNFe", NS) or root.find("n:infNFe", NS)
    if inf is None:
        a.add("ERRO", "arquivo", "infNFe não encontrado — XML não parece NF-e/NFC-e")
        return {"arquivo": caminho, "achados": a}
    ide = inf.find("n:ide", NS)
    dhemi = (t(ide, "n:dhEmi") or t(ide, "n:dEmi") or "")[:10]
    ano = dhemi[:4]
    chave = inf.get("Id", "")[3:]
    crt = t(inf, "n:emit/n:CRT")
    itens, tem_ibscbs = [], False
    for det in inf.findall("n:det", NS):
        n = det.get("nItem")
        item = {"nItem": n}
        item.update({"vICMS": valida_icms(det, n, a).get("vICMS"),
                     "vIPI": valida_ipi(det, n, a).get("vIPI"),
                     "vPIS": valida_pis_cofins(det, n, a, "PIS").get("vPIS"),
                     "vCOFINS": valida_pis_cofins(det, n, a, "COFINS").get("vCOFINS")})
        ib = valida_ibscbs(det, n, a, ano, dhemi)
        if ib:
            tem_ibscbs = True
            item.update({k: ib.get(k) for k in
                         ("vBC", "vIBS", "vIBSUF", "vIBSMun", "vCBS", "CST",
                          "cClassTrib")})
        itens.append(item)
    if not tem_ibscbs and crt == "3":
        if dhemi >= OBRIGATORIO_IBSCBS:
            a.add("ERRO", "nota", f"Grupo IBSCBS ausente — obrigatório por RV desde "
                  f"{OBRIGATORIO_IBSCBS} (NT 2025.002, UB12-10)")
        elif dhemi >= VALOR_JURIDICO:
            a.add("ALERTA", "nota", "Grupo IBSCBS ausente — obrigação legal desde "
                  "01/01/2026 (período educativo sem penalidade até 03/08/2026)")
    valida_totais(inf, itens, a)
    ret = retencoes(inf)
    erros = sum(1 for x in a if x["severidade"] == "ERRO")
    alertas = sum(1 for x in a if x["severidade"] == "ALERTA")
    status = ("REPROVADA" if erros else
              "APROVADA COM ALERTAS" if alertas else "APROVADA")
    return {"arquivo": os.path.basename(caminho), "chave": chave, "dhEmi": dhemi,
            "CRT": crt, "emitente": t(inf, "n:emit/n:xNome"),
            "destinatario": t(inf, "n:dest/n:xNome"), "status": status,
            "erros": erros, "alertas": alertas, "retencoes_destacadas": ret,
            "achados": list(a)}


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    json_out = None
    if "--json" in sys.argv:
        json_out = sys.argv[sys.argv.index("--json") + 1]
    arquivos = []
    for a in args:
        if a == json_out:
            continue
        if os.path.isdir(a):
            arquivos += [os.path.join(a, f) for f in sorted(os.listdir(a))
                         if f.lower().endswith(".xml")]
        else:
            arquivos.append(a)
    if not arquivos:
        sys.exit(__doc__)
    resultados = []
    for arq in arquivos:
        try:
            r = valida_arquivo(arq)
        except ET.ParseError as e:
            r = {"arquivo": arq, "status": "ERRO DE PARSE", "achados":
                 [{"severidade": "ERRO", "onde": "arquivo", "mensagem": str(e)}]}
        resultados.append(r)
        print(f"\n=== {r.get('arquivo')} — {r.get('status')} "
              f"({r.get('erros', '?')} erros, {r.get('alertas', '?')} alertas) ===")
        print(f"Chave: {r.get('chave', '')} | Emissão: {r.get('dhEmi', '')} | "
              f"CRT: {r.get('CRT', '')}")
        if r.get("retencoes_destacadas"):
            print(f"Retenções destacadas: {r['retencoes_destacadas']}")
        for f in r["achados"]:
            extra = ""
            if "declarado" in f:
                extra = f" [declarado={f['declarado']} esperado={f.get('esperado')}]"
            print(f"  {f['severidade']:6} {f['onde']}: {f['mensagem']}{extra}")
        if not r["achados"]:
            print("  Nenhuma divergência encontrada.")
    if json_out:
        def enc(o):
            return str(o) if isinstance(o, Decimal) else o
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(resultados, fh, ensure_ascii=False, indent=2, default=enc)
        print(f"\nJSON: {json_out}")


if __name__ == "__main__":
    main()
