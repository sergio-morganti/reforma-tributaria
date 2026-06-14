# Layout NF-e/NFC-e — Grupos IBS/CBS/IS (NT 2025.002-RTC)

Conferido contra a NT 2025.002-RTC **v1.50 (03/06/2026)** e o XSD `DFeTiposBasicos_v1.00`. A NT e as tabelas oficiais são vinculantes; em divergência, prevalece o Portal NF-e (https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=).

## 1. Cronograma de obrigatoriedade (CRT 3 — Regime Normal)

| Marco | Produção |
|---|---|
| 06/10/2025 | Campos implantados; preenchimento facultativo, sem valor jurídico |
| 01/01/2026 | Obrigatório pela legislação, **com valor jurídico**; RVs aplicadas se preenchido |
| **03/08/2026** | **Preenchimento obrigatório por regra de validação (RV UB12-10)** — rejeição se ausente |
| 03/11/2026 | Novo layout de monofasia de combustíveis (v1.50) em produção |

Simples Nacional (CRT 1/2) e MEI (CRT 4): IBS/CBS só a partir de 2027 (art. 348 LC 214/25). Alíquotas 2026: **IBS 0,1% (estadual; municipal 0%) + CBS 0,9%** (arts. 343-348).

## 2. Grupo UB12 `<IBSCBS>` (por item, dentro de det/imposto)

```
IBSCBS
├── CST          (N3 — tabela CST IBS/CBS, §4)
├── cClassTrib   (N6 — tabela cClassTrib, §5)
├── indDoacao    (opc)
├── (choice) gIBSCBS | gIBSCBSMono | gTransfCred (CST 800: vIBS, vCBS)
└── gCredPresIBSZFM (opc: tpCredPresIBSZFM 0-4, vCredPresIBSZFM)
```

### gIBSCBS — tributação padrão

| Tag | Descrição |
|---|---|
| `vBC` | Base única para IBS-UF, IBS-Mun e CBS |
| `gIBSUF/pIBSUF`, `vIBSUF` | Alíquota e valor IBS estadual |
| `gIBSMun/pIBSMun`, `vIBSMun` | Alíquota e valor IBS municipal |
| `vIBS` | = vIBSUF + vIBSMun (− vCredPres quando IndDeduzCredPres=1) |
| `gCBS/pCBS`, `vCBS` | Alíquota e valor CBS |
| `gDif/pDif`, `vDif` (em cada ente) | Diferimento — exigido por CST 510 |
| `gDevTrib/vDevTrib` | Devolução de tributo (cashback na NF, art. 118) |
| `gRed/pRedAliq`, `pAliqEfet` | Redução de alíquota — exigido por CST 200/210 |
| `gTribRegular` | Como seria a tributação regular (CST 550): CSTReg, cClassTribReg, pAliqEfetReg*, vTribReg* |
| `gIBSCredPres`/`gCBSCredPres` | Crédito presumido: cCredPres, pCredPres, vCredPres ou vCredPresCondSus |
| `gTribCompraGov` | Compras governamentais: alíquotas/valores sem o redutor (art. 473) |
| `gCBS/gALCZFMCBS` | ZFM/ALC alíquota zero CBS (v1.40): tpALCZFMCBS, nProcSuframa, pAliqEfetRegCBS, vTribRegCBS |

### gIBSCBSMono — monofasia de combustíveis (layout vigente até 03/11/2026)

`gMonoPadrao` (qBCMono, adRemIBS, adRemCBS, vIBSMono, vCBSMono), `gMonoReten` (retenção do biocombustível a misturar, art. 178), `gMonoRet` (retido anteriormente), `gMonoDif`, `vTotIBSMonoItem`, `vTotCBSMonoItem`. A partir da v1.50: separação ad rem × ad valorem por tributo (gIBSMonoAdRem/AdValorem, gCBSMonoAdRem/AdValorem, gpBioDiferenca — cClassTrib 620004/620005).

## 3. Fórmulas de cálculo (RVs centrais)

- `vBC` = vProd + frete + seguro + outras despesas − descontos incondicionais, **excluídos**: o próprio IBS/CBS (por fora), o IPI e — na transição — o ICMS/ISS destacados (art. 12 §2º LC 214/25). O IS integra a BC quando não recuperável.
- `pAliqEfet = pIBSUF × (1 − pRedAliq/100)` (idem Mun/CBS); em compra governamental aplica-se também `pRedutor`.
- `vIBSUF = vBC × pAliqEfet_UF/100`; `vIBSMun = vBC × pAliqEfet_Mun/100`; `vCBS = vBC × pAliqEfet_CBS/100`.
- `vIBS = vIBSUF + vIBSMun`.
- `vDif = vBC × pAliq × pDif/100`; `vCredPres = base × pCredPres/100`.
- Monofasia: `vIBSMono = qBCMono × adRemIBS`; `vCBSMono = qBCMono × adRemCBS`.
- Arredondamento: 2 casas, half-up, **por item**; totais = soma dos itens já arredondados.
- A obrigatoriedade/vedação de cada subgrupo é dirigida pelos indicadores da tabela cClassTrib (`ind_gDif`, `ind_gRed`, `ind_gTribRegular`, `ind_gIBSCBSMono`, `IndDeduzCredPres` etc.) — validação dinâmica tabela × XML.

## 4. CST do IBS/CBS

| CST | Significado | Exige |
|---|---|---|
| 000 | Tributação integral | gIBSCBS |
| 010/011 | Alíquotas uniformes (/reduzidas) | gIBSCBS |
| 200 | Alíquota reduzida | gRed |
| 210 | Redução com redutor de BC | gRed |
| 220/221 | Alíquota fixa (/proporcional) | gIBSCBS |
| 400 | Isenção | — |
| 410 | Imunidade/não incidência | — |
| 510 | Diferimento | gDif |
| 550 | Suspensão | gTribRegular |
| 620 | Monofasia | gIBSCBSMono |
| 800 | Transferência de crédito | gTransfCred |
| 810 | Ajustes (notas de débito/crédito) | — |
| 820 | Regime específico (declaração) | — |
| 830 | Exclusão de BC | — |

## 5. cClassTrib

Código de 6 dígitos; cada um aponta para um dispositivo da LC 214/2025 (000001 = tributação integral; 200xxx = reduções 30%/60%; 410xxx = imunidades; 620xxx = monofasia). A planilha oficial (Portal NF-e > Documentos > Diversos, versão 15/04/2026) vincula cClassTrib → CST permitido → grupos exigidos → % de redução. Tabelas irmãs: cCredPres (15/12/2025) e Alíquotas CBS (12/05/2026, IT 2026.002).

## 6. Totais e outros campos novos

```
total/ISTot/vIS = Σ vIS itens
total/IBSCBSTot
 ├── vBCIBSCBS = Σ vBC
 ├── gIBS { gIBSUF{vDif,vDevTrib,vIBSUF}, gIBSMun{...,vIBSMun}, vIBS, vCredPres, vCredPresCondSus }
 ├── gCBS { vDif, vDevTrib, vCBS, vCredPres, vCredPresCondSus }
 └── gMono { vIBSMono, vCBSMono, vIBSMonoReten, vCBSMonoReten, vIBSMonoRet, vCBSMonoRet }
```

- Cada total = soma aritmética dos itens; divergência → rejeição (RVs W59f/W59g).
- **vNF**: com grupo VB (`vItem`), `vNF = Σ vItem` (RV W07-10/v1.40). IBS/CBS são "por fora" — não somam ao vNF; o IS compõe conforme o item.
- `finNFe` ganhou **5=Nota de crédito, 6=Nota de débito** (tpNFCredito/tpNFDebito); `cMunFGIBS` (B12a); `gCompraGov` (tpEnteGov, pRedutor, tpOperGov); `gPagAntecipado`; grupo VC `DFeReferenciado` (devoluções referenciam item a item — RV VC02-14, produção 01/09/2026).
- Eventos novos (apropriação de crédito, imobilização, consumo pessoal, perecimento etc.) e código de status com 4 dígitos.

## 7. NFS-e nacional (DPS) — visão rápida

Layout RTC em produção desde 05/01/2026 (NT SE/CGNFS-e 004 v2.00; mais recente NT 009 — Anexo VI v1.04.00). O prestador envia a DPS; **IBS/CBS são calculados pelo ambiente nacional** e devolvidos na NFS-e. Grupos: `trib/tribMun` (ISSQN, tpRetISSQN), `trib/tribFed` (piscofins, vRetCP, vRetIRRF, vRetCSLL), novo grupo `IBSCBS` (CST, cClassTrib, cIndOp — Anexo VII). Correlação Item LC 116 × NBS × cClassTrib: Anexo VIII. Docs: https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc
