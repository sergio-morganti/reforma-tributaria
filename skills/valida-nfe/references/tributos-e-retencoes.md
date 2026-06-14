# Tributos tradicionais e retenções — regras de validação (transição 2026-2032)

ICMS/ISS convivem com IBS/CBS até 2032; PIS/COFINS até 2026 (extintos em 2027, quando a CBS fica plena e o IPI é zerado exceto ZFM).

## 1. ICMS (grupo N, tag `ICMS__`)

- `orig` (0-8) + `CST` (00,02,10,15,20,30,40,41,50,51,53,60,61,70,90) ou `CSOSN` (101...900).
- **ICMS00**: `vICMS = vBC × pICMS/100`. Base "por dentro" (ICMS integra a própria base); inclui frete/seguro/outras despesas, exclui descontos incondicionais; IPI entra na BC quando destinatário é consumidor final/não contribuinte.
- **ICMS20**: `vBC = valor da operação × (1 − pRedBC/100)`.
- **ST (10/30/70/90)**: `vBCST = (operação + IPI + frete + despesas) × (1 + pMVAST/100)`; `vICMSST = vBCST × pICMSST/100 − vICMS próprio`. FCP: `vFCP = vBCFCP × pFCP/100`.
- **60/61**: retido anteriormente / monofásico (`adRemICMS`, `vICMSMonoRet`).
- **CSOSN 101**: `vCredICMSSN = vBC × pCredSN/100`.
- DIFAL (grupo ICMSUFDest): partilha vICMSUFDest/vICMSUFRemet + FCP UF destino.

## 2. IPI (grupo O)

CST 00/49/50/99 (saída), 01-05/51-55 (entrada). Ad valorem: `vIPI = vBC × pIPI/100`; específica: `vIPI = qUnid × vUnid`.

## 3. PIS (grupo Q) e COFINS (grupo S)

- CST 01/02: `vPIS = vBC × pPIS/100` (0,65% cumulativo / 1,65% não cumulativo); `vCOFINS = vBC × pCOFINS/100` (3% / 7,6%).
- CST 03: por quantidade (`qBCProd × vAliqProd`). CST 04-09: monofásico/zero/isento/suspensão.
- Base = receita da operação **excluído o ICMS destacado** (Lei 14.592/2023).
- Em 2026, valores de teste IBS/CBS recolhidos são compensáveis com PIS/COFINS.

## 4. Totais (grupo W `ICMSTot`)

Cada campo = Σ itens. Fórmula clássica: `vNF = vProd − vDesc − vICMSDeson + vST + vFCPST + vFrete + vSeg + vOutro + vII + vIPI + vIPIDevol` — modificada quando há grupo VB/IBSCBS (vNF = Σ vItem, RV W07-10).

## 5. Retenções — quadro de incidência

No XML: grupo `total/retTrib` → `vRetPIS, vRetCOFINS, vRetCSLL, vBCIRRF, vIRRF, vBCRetPrev, vRetPrev`.

| Retenção | Hipótese | Alíquota | Fundamento | Dispensas |
|---|---|---|---|---|
| **IRRF** | Serviços profissionais (lista do art. 714 RIR/2018), comissões | **1,5%** (1% p/ limpeza/conservação/segurança/locação de mão de obra, art. 716) | RIR/2018 arts. 714-718 | IR ≤ R$ 10 |
| **CSRF** (PIS 0,65% + COFINS 3% + CSLL 1%) | PJ paga PJ: serviços profissionais, limpeza, vigilância, locação de mão de obra, factoring | **4,65%** | Lei 10.833/2003 arts. 30-36 | Pagamento ≤ R$ 215,05; prestador no Simples |
| **INSS** | **Cessão de mão de obra/empreitada** (limpeza, vigilância, construção) | **11%** (3,5% se CPRB) +4% atividades especiais; deduções de material/equipamento previstas | Lei 8.212/91 art. 31; IN RFB 2110/2022 | — |
| **ISS retido** | Hipóteses do art. 6º LC 116/2003 (serviços devidos no local da prestação; lei municipal define responsável) | 2% a 5% (alíquota do município) | LC 116/2003 arts. 3º, 6º | — |
| **Órgãos públicos federais** | Pagamentos de bens/serviços | IR+CSLL+PIS+COFINS por natureza (tabela) | IN RFB 1234/2012 | — |

## 6. O que muda com a reforma

- **IBS/CBS não têm retenção na fonte.** O mecanismo de arrecadação assistida é o **split payment** (arts. 31-35 e 51-53 da LC 214/25), recolhimento na liquidação financeira — escalonado e opcional conforme regulamento (Decreto 12.955/2026); Plataforma Pública com manual técnico publicado em 06/2026.
- Exceções "tipo retenção" no layout: `gMonoReten` (combustíveis, art. 178) e compras governamentais (`pRedutor`/`gTribCompraGov`, arts. 471-473).
- **CSRF e retenções de PIS/COFINS desaparecem em 2027** com a extinção de PIS/COFINS. **IRRF e CSLL retidos continuam** (reforma da renda é trilha separada). **INSS 11% continua.** **ISS retido se extingue gradualmente** com o ISS (2029-2032).

## 7. Heurísticas de auditoria de retenção

1. Identificar a natureza da operação: CFOP de serviço, descrição dos itens, CNAE do emitente, `infCpl`.
2. Serviço profissional PJ→PJ sem `vRetPIS/vRetCOFINS/vRetCSLL` → alertar possível falta de CSRF (verificar se o prestador é Simples — dispensado).
3. Cessão de mão de obra (limpeza, vigilância, portaria, construção com empreitada) sem `vRetPrev` → alerta forte (INSS 11% é a retenção mais autuada).
4. `vIRRF` destacado: conferir 1,5% (ou 1%) sobre `vBCIRRF`; bases zeradas com valor destacado = erro.
5. Mercadoria pura (sem serviço) com retenções destacadas → alerta inverso (retenção indevida).
