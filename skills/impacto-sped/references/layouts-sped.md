# Layouts SPED — registros usados na simulação

Conferidos com os Guias Práticos oficiais (EFD Contribuições v1.35; EFD ICMS/IPI v3.2.2, leiaute 020/2026). Convenção: arquivo texto, um registro por linha, campos entre pipes `|REG|c2|...|`. Blocos abrem com X001 e fecham com X990; arquivo termina em `|9999|n|`.

**Importante**: até 06/2026 as EFDs **não têm campos IBS/CBS** (a apuração dos novos tributos será assistida, a partir dos DF-e; regimes específicos vão para a DeRE). Monitorar o portal SPED para mudanças de leiaute.

## 1. EFD Contribuições (PIS/COFINS)

### 0000 (14 campos)
`REG|COD_VER|TIPO_ESCRIT|IND_SIT_ESP|NUM_REC_ANTERIOR|DT_INI|DT_FIN|NOME|CNPJ|UF|COD_MUN|SUFRAMA|IND_NAT_PJ|IND_ATIV`
(IND_ATIV: 0=industrial, 1=serviços, 2=comércio, 3=financeira, 4=imobiliária, 9=outros)

### 0200 — itens (12 campos)
`REG|COD_ITEM|DESCR_ITEM|COD_BARRA|COD_ANT_ITEM|UNID_INV|TIPO_ITEM|COD_NCM|EX_IPI|COD_GEN|COD_LST|ALIQ_ICMS`
TIPO_ITEM: **00**=revenda, **01**=matéria-prima, 02=embalagem, 03=em processo, 04=acabado, 05=subproduto, 06=intermediário, **07=uso e consumo**, **08=ativo imobilizado**, 09=serviços, 10=outros insumos, 99=outras.

### A100 — documento de serviço (21 campos)
`REG|IND_OPER|IND_EMIT|COD_PART|COD_SIT|SER|SUB|NUM_DOC|CHV_NFSE|DT_DOC|DT_EXE_SERV|VL_DOC|IND_PGTO|VL_DESC|VL_BC_PIS|VL_PIS|VL_BC_COFINS|VL_COFINS|VL_PIS_RET|VL_COFINS_RET|VL_ISS`
IND_OPER: **0=serviço contratado (aquisição), 1=serviço prestado (receita)**.

### A170 — item do serviço (18 campos)
`REG|NUM_ITEM|COD_ITEM|DESCR_COMPL|VL_ITEM|VL_DESC|NAT_BC_CRED|IND_ORIG_CRED|CST_PIS|VL_BC_PIS|ALIQ_PIS|VL_PIS|CST_COFINS|VL_BC_COFINS|ALIQ_COFINS|VL_COFINS|COD_CTA|COD_CCUS`

### C100 — NF-e (29 campos, igual nas duas EFDs)
`REG|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|CHV_NFE|DT_DOC|DT_E_S|VL_DOC|IND_PGTO|VL_DESC|VL_ABAT_NT|VL_MERC|IND_FRT|VL_FRT|VL_SEG|VL_OUT_DA|VL_BC_ICMS|VL_ICMS|VL_BC_ICMS_ST|VL_ICMS_ST|VL_IPI|VL_PIS|VL_COFINS|VL_PIS_ST|VL_COFINS_ST`

### C170 — itens (37 campos na Contribuições; 38 na ICMS/IPI com VL_ABAT_NT no fim)
`REG|NUM_ITEM|COD_ITEM|DESCR_COMPL|QTD|UNID|VL_ITEM|VL_DESC|IND_MOV|CST_ICMS|CFOP|COD_NAT|VL_BC_ICMS|ALIQ_ICMS|VL_ICMS|VL_BC_ICMS_ST|ALIQ_ST|VL_ICMS_ST|IND_APUR|CST_IPI|COD_ENQ|VL_BC_IPI|ALIQ_IPI|VL_IPI|CST_PIS|VL_BC_PIS|ALIQ_PIS|QUANT_BC_PIS|ALIQ_PIS_QUANT|VL_PIS|CST_COFINS|VL_BC_COFINS|ALIQ_COFINS|QUANT_BC_COFINS|ALIQ_COFINS_QUANT|VL_COFINS|COD_CTA[|VL_ABAT_NT]`

### Consolidações: C180/C181/C185 (vendas) e C190/C191/C195 (aquisições c/ crédito)
- C181/C185: `REG|CST|CFOP|VL_ITEM|VL_DESC|VL_BC|ALIQ|QUANT_BC|ALIQ_QUANT|VL|COD_CTA`
- C191/C195: `REG|CNPJ_CPF_PART|CST|CFOP|VL_ITEM|VL_DESC|NAT_BC_CRED|VL_BC|ALIQ|QUANT_BC|ALIQ_QUANT|VL|COD_CTA`

### D100/D101/D105 — fretes (CT-e)
D101/D105: `REG|IND_NAT_FRT|VL_ITEM|CST|NAT_BC_CRED|VL_BC|ALIQ|VL|COD_CTA` (D105=COFINS)

### F100 — demais operações (19 campos)
`REG|IND_OPER|COD_PART|COD_ITEM|DT_OPER|VL_OPER|CST_PIS|VL_BC_PIS|ALIQ_PIS|VL_PIS|CST_COFINS|VL_BC_COFINS|ALIQ_COFINS|VL_COFINS|NAT_BC_CRED|IND_ORIG_CRED|COD_CTA|COD_CCUS|DESC_DOC_OPER` (IND_OPER 0=aquisição c/ crédito, 1=receita)

### F120/F130 — crédito sobre ativo imobilizado
F120 (depreciação): `REG|NAT_BC_CRED|IDENT_BEM_IMOB|IND_ORIG_CRED|IND_UTIL_BEM_IMOB|VL_OPER_DEP|PARC_OPER_NAO_BC_CRED|CST_PIS|VL_BC_PIS|ALIQ_PIS|VL_PIS|CST_COFINS|VL_BC_COFINS|ALIQ_COFINS|VL_COFINS|COD_CTA|COD_CCUS|DESC_BEM_IMOB`
F130 (valor de aquisição): idem com `MES_OPER_AQUIS|VL_OPER_AQUIS|...|VL_BC_CRED|IND_NR_PARC` (1=integral, 2=1/12, 3=1/24, 4=1/48...). No IBS/CBS o crédito de CAPEX é **imediato** — comparar com este fluxo.

### Apuração: M100/M105 (créditos PIS), M200/M210 (contribuição PIS); M500/M505/M600/M610 = espelhos COFINS
- M200: `REG|VL_TOT_CONT_NC_PER|VL_TOT_CRED_DESC|VL_TOT_CRED_DESC_ANT|VL_TOT_CONT_NC_DEV|VL_RET_NC|VL_OUT_DED_NC|VL_CONT_NC_REC|VL_TOT_CONT_CUM_PER|VL_RET_CUM|VL_OUT_DED_CUM|VL_CONT_CUM_REC|VL_TOT_CONT_REC` (campo 13 = total a recolher)
- M105: `REG|NAT_BC_CRED|CST_PIS|VL_BC_PIS_TOT|VL_BC_PIS_CUM|VL_BC_PIS_NC|VL_BC_PIS|QUANT_BC_PIS_TOT|QUANT_BC_PIS|DESC_CRED`
- M100: campo 14 = VL_CRED_DESC (crédito utilizado no período).

### CST PIS/COFINS
01-09/49 = saídas (01 básica; 04 monofásica zero; 06 zero; 07 isenta; 08 sem incidência; 09 suspensão). **50-66 = entradas COM crédito** (50 recv. tributada MI; 52 exportação; 53/56 mistas; 60-66 presumido). **70-75 = entradas SEM crédito** (massa que tende a virar crédito no IBS/CBS, exceto uso pessoal — art. 57 LC 214).

### NAT_BC_CRED (tabela 4.3.7)
01 revenda; 02 insumo-bem; 03 insumo-serviço; 04 energia; 05/06 aluguéis; 07 armazenagem/frete de venda; 08 leasing; 09/10/11 ativo (depreciação/aquisição/edificações); 12 devolução; 13 outras; 14 frete subcontratado; 15/16 imobiliária; 17 vales/uniformes; 18 estoque de abertura.

## 2. EFD ICMS/IPI

### 0000 (15 campos — distingue do Contribuições: DT_INI no campo 4)
`REG|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|CPF|UF|IE|COD_MUN|IM|SUFRAMA|IND_PERFIL|IND_ATIV`

### C190 — analítico por CST×CFOP×alíquota (o registro mais eficiente p/ simulação em massa)
`REG|CST_ICMS|CFOP|ALIQ_ICMS|VL_OPR|VL_BC_ICMS|VL_ICMS|VL_BC_ICMS_ST|VL_ICMS_ST|VL_RED_BC|VL_IPI|COD_OBS`

### E110 — apuração do ICMS próprio (15 campos)
`REG|VL_TOT_DEBITOS|VL_AJ_DEBITOS|VL_TOT_AJ_DEBITOS|VL_ESTORNOS_CRED|VL_TOT_CREDITOS|VL_AJ_CREDITOS|VL_TOT_AJ_CREDITOS|VL_ESTORNOS_DEB|VL_SLD_CREDOR_ANT|VL_SLD_APURADO|VL_TOT_DED|VL_ICMS_RECOLHER|VL_SLD_CREDOR_TRANSPORTAR|DEB_ESP`
(campo 13 = ICMS a recolher; campo 6 = créditos por entradas)

### E200/E210 — ICMS-ST por UF
E210 campo 13 = VL_ICMS_RECOL_ST; campo 8 = VL_RETENCAO_ST. **O IBS não tem ST** — todo esse fluxo vira débito-crédito normal.

### H005/H010 — inventário
H010: `REG|COD_ITEM|UNID|QTD|VL_UNIT|VL_ITEM|IND_PROP|COD_PART|TXT_COMPL|COD_CTA|VL_ITEM_IR` — estima estoque de créditos na transição e estoque sob ST.

### G125 — CIAP (ICMS de ativo em 1/48)
`REG|COD_IND_BEM|DT_MOV|TIPO_MOV|VL_IMOB_ICMS_OP|VL_IMOB_ICMS_ST|VL_IMOB_ICMS_FRT|VL_IMOB_ICMS_DIF|NUM_PARC|VL_PARC_PASS`

## 3. ECD/ECF — margem e DRE

- **ECD I155** (saldos por conta): `REG|COD_CTA|COD_CCUS|VL_SLD_INI|IND_DC_INI|VL_DEB|VL_CRED|VL_SLD_FIN|IND_DC_FIN`; plano em I050, de-para referencial em I051. Reconstruir DRE mensal pelas contas de resultado.
- **ECF L300** (DRE Lucro Real, por conta referencial RFB) e **P150** (DRE Lucro Presumido): receita bruta, deduções (tributos sobre venda), CMV, lucro bruto, despesas, resultado.
- Atenção: receita líquida atual já exclui ICMS/PIS/COFINS "por dentro"; IBS/CBS são "por fora" e não transitam pela DRE — ajustar a comparação de margem.

## 4. Downloads oficiais

- EFD ICMS/IPI (guia v3.2.2, leiaute 020): http://sped.rfb.gov.br/pasta/show/1573
- EFD Contribuições (guia v1.35): http://sped.rfb.gov.br/pasta/show/1989
- DeRE (regimes específicos — financeiro, saúde, prognósticos): http://sped.rfb.gov.br/projeto/show/2918
- ECD: http://sped.rfb.gov.br/projeto/show/273 · ECF: http://sped.rfb.gov.br/projeto/show/269
