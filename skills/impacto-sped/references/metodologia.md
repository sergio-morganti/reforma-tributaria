# Metodologia de simulação de impacto IBS/CBS a partir do SPED

## 1. Parâmetros da transição (LC 214/2025 + EC 132/2023)

| Ano | IBS | CBS | Tributos antigos |
|---|---|---|---|
| 2026 | 0,1% (teste) | 0,9% (teste) | Todos vigentes; teste compensável com PIS/COFINS; dispensa de recolhimento p/ quem destaca |
| 2027-2028 | 0,1% | plena (referência − 0,1 p.p.) | PIS/COFINS extintos; IPI zerado (exceto ZFM); IS entra |
| 2029 | proporcional ↑ | plena | ICMS/ISS a 90% |
| 2030 | ↑ | plena | ICMS/ISS a 80% |
| 2031 | ↑ | plena | ICMS/ISS a 70% |
| 2032 | ↑ | plena | ICMS/ISS a 60% |
| 2033 | integral | integral | ICMS/ISS extintos |

- **Alíquota de referência somada (t_ref)**: estimativa corrente ~28% (MF 28,55% dez/2024; trava de 26,5% no art. 475). Parametrizar cenários: 26,5 / 28 / 28,55%. O valor definitivo da CBS 2027 sai por Resolução do Senado (cálculo TCU) em 2026.
- **Reduções por categoria** (aplicar via NCM/NBS → cClassTrib): 60% (saúde, medicamentos, educação, alimentos de consumo humano, agro e insumos, cultura); 30% (profissões intelectuais regulamentadas); zero (cesta básica Anexo I, hortifrúti/ovos, medicamentos listados); isenção (transporte público coletivo); regimes específicos com redutores próprios (imóveis −50%/−70%, bares/restaurantes/hotelaria −40%, financeiro, combustíveis monofásicos).
- **Crédito amplo** (arts. 47 e ss.): toda aquisição de contribuinte regular gera crédito, exceto **uso e consumo pessoal** (art. 57 — joias, bebidas, armas, benefícios a sócios/empregados). Ativo imobilizado: crédito **integral e imediato** (vs. 1/48 do CIAP e F120/F130 hoje). **Não há ST no IBS.**

## 2. Pipeline de cálculo

**Passo 1 — Classificar operações**: `classe = f(CFOP ⊕ TIPO_ITEM(0200) ⊕ CST_PIS/COFINS ⊕ CST_ICMS)`. Divergências (ex.: CFOP x102 com TIPO_ITEM 07) vão para fila de revisão.

**Passo 2 — Débito novo** (saídas 5xxx/6xxx, excluindo devoluções de compra x20x, transferências x15x, remessas x9xx sem transação; exportações 7xxx = imunes com crédito mantido):
```
Débito_novo = Σ (VL_ITEM − VL_DESC − devoluções de venda) × t_ref × (1 − red_item)
```
(IBS/CBS por fora: partir da receita líquida dos tributos por dentro.)

**Passo 3 — Baseline atual**:
```
Carga_atual = E110.13 (ICMS a recolher) + E210.13 (ICMS-ST) + IPI (E520)
            + M200.13 + M600.13 (PIS/COFINS a recolher) + ISS (bloco A receitas × alíquota)
```

**Passo 4 — Crédito novo** (entradas 1xxx/2xxx/3xxx — TODAS as classes + fretes D100 + serviços A100 IND_OPER=0 + energia C500 + F100 aquisições):
```
Crédito_novo = Σ VL_j × t_efetivo_fornecedor_j
  t_efetivo = t_ref × (1 − red_j)          fornecedor regime regular
            = IBS/CBS cobrado no Simples    fornecedor Simples "puro" (crédito limitado)
            = t_ref cheio                   Simples que optar pelo regime regular ("híbrido")
            = 0                             PF não contribuinte / MEI
```
**Quantificar separadamente os créditos que nascem com a reforma**: (a) uso e consumo — CFOP x556/x407/x557 + TIPO_ITEM 07 + CST 70-75; (b) serviços tomados (bloco A, F100); (c) energia/telecom administrativas; (d) ativo — diferença entre crédito imediato e fluxo F120/F130/G125; (e) frete sobre compras; (f) mercadorias com ICMS-ST embutido (x403/x411).

**Passo 5 — Crédito atual**: `E110.6 + M100.14 + M500.14 + créditos IPI`; abrir por NAT_BC_CRED (M105/M505) para mapear a migração categoria a categoria.

**Passo 6 — Efeitos**:
```
ΔCarga = (Débito_novo − Crédito_novo) − Carga_atual_líquida
ΔCusto_suprimentos = Σ compras × (t_recuperável_novo − t_recuperável_atual)
Preço break-even: manter margem unitária — comparar preço cheio atual com
  custo_novo_líquido_de_créditos + margem_alvo, acrescido de t_ref(1−red) por fora
Margem: aplicar ΔCarga/ΔCusto sobre a DRE (ECF L300/P150 ou ECD I155);
  IBS/CBS por fora → receita líquida comparável muda
Pass-through: B2B contribuinte → neutralidade tendencial; B2C/Simples → modelar 0-100%
Caixa: split payment (recolhe na liquidação) + prazos de ressarcimento — capital de giro
```

**Passo 7 — Grade 2026-2033**: 2026 (teste compensável) → 2027-28 (CBS plena, sem PIS/COFINS, ICMS/ISS no baseline) → 2029-32 (interpolar ICMS/ISS 90/80/70/60% + IBS crescente, dois motores de crédito convivendo) → 2033 (pleno).

**Insumos mínimos**: 12 meses de EFD Contribuições + EFD ICMS/IPI (todas as filiais), última ECF/ECD, regime tributário dos fornecedores (0150 não traz — enriquecer ou assumir premissa), mapeamento NCM→redução.

## 3. CFOPs para classificação automática

| Classe | CFOPs (x = 1/2/3 entrada; 5/6/7 saída) | Tratamento |
|---|---|---|
| Insumo industrialização | x101, x401, x111, x116, x120, x122 | crédito hoje e no IBS/CBS |
| Revenda | x102, x403 (ST), x113, x117, x118, 1409/2409 | crédito pleno |
| Ativo imobilizado | x551, x406, 1604, x552 | hoje 1/48 → IBS/CBS imediato |
| **Uso e consumo** | **x556, x407, x557** | **hoje sem crédito → IBS/CBS com crédito** |
| Energia/comunicação/transporte | x252-x258, x301-x306, x351-x356 | condicionado hoje → amplo |
| Devolução de venda (entrada) | x201, x202, x410, x411, x553 | abate débito |
| Devolução de compra (saída) | 5201/5202/6201/6202, 5410/5411/6410/6411 | abate crédito |
| Vendas | 5101/6101/7101, 5102/6102/7102, 5103-5106, 5109/5110, 5401/5403/5405, 5115-5117 | débito |
| Transferências | x151, x152, x408, x409, 5151/5152/6151/6152 | excluir (sem receita) |
| Remessas/retornos | x9xx (5901/5902/5915/5916/5904, 5949 caso a caso) | excluir |
| Serviço de transporte prestado | 5351-5360, 6351-6360 | débito |
| Importação | 3101, 3102, 3551, 3556, 3651... | IBS/CBS na importação com crédito |

**CFOP × futuro**: o cClassTrib substitui funcionalmente o CFOP para IBS/CBS (descontinuação discutida para 2027+, sem ato publicado até 06/2026). Classificar por CFOP hoje, prever migração para cClassTrib.

## 4. Metodologias de referência (validação cruzada)

- **CCiF/UFMG (Domingues & Cardoso, 2020)**: equilíbrio geral computável, alíquota neutra 26,35%; custo de insumos −8% a −12% por macrossetor — útil como sanity check setorial.
- **MF/SERT**: alíquota de referência por bases tributáveis potenciais (TRU) — fonte do ~28%.
- **Consultorias (microssimulação "digital twin fiscal")**: reprocessar DF-e + SPED item a item com regras da LC 214 — é exatamente o que esta skill faz; precisão depende do mapeamento NCM→cClassTrib e do regime dos fornecedores.
