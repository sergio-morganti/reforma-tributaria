---
name: impacto-sped
description: >-
  Estima o impacto da reforma tributária (IBS/CBS, EC 132/2023, LC 214/2025) a partir de
  arquivos SPED: recebe EFD Contribuições, EFD ICMS/IPI e ECF/ECD, calcula a carga tributária
  atual vs. pós-reforma ano a ano (2026-2033), a apropriação de créditos (inclusive itens hoje
  sem crédito, como uso e consumo, serviços e ativo imobilizado), e o efeito em preço, margem,
  custos e cadeia de suprimentos. Use SEMPRE que o usuário enviar arquivos SPED/EFD (.txt) ou
  pedir para: simular impacto da reforma tributária, estimar carga IBS/CBS, comparar carga
  atual vs nova, analisar apropriação de créditos na reforma, calcular efeito em preço ou
  margem da reforma, analisar EFD Contribuições ou EFD ICMS/IPI, ou perguntar "quanto minha
  empresa vai pagar com a reforma?", "qual o impacto do IBS/CBS no meu negócio?".
---

# Impacto da Reforma Tributária via SPED

Receber arquivos SPED (EFD Contribuições e/ou EFD ICMS/IPI; ECF/ECD opcionais para margem), reconstruir a carga tributária atual, simular débitos e créditos de IBS/CBS e quantificar impacto em carga, créditos, preço, margem, custos e suprimentos na grade de transição 2026-2033.

## Fluxo de trabalho

### 1. Entender o pedido e os arquivos

Perguntar (se não estiver claro): setor/atividade da empresa, regime (Lucro Real/Presumido — a EFD revela), se os NCMs dos produtos têm tratamento favorecido (saúde, alimentos, agro, cesta básica), e qual cenário de alíquota usar. Defaults documentados: alíquota de referência 28% (cenários 26,5% e 28,55% como sensibilidade).

### 2. Parsear os arquivos

```bash
python <skill-dir>/scripts/sped_parser.py arquivo1.txt arquivo2.txt --json parsed.json
```

O parser detecta automaticamente o tipo (EFD Contribuições × EFD ICMS/IPI), agrega operações por CFOP×CST, extrai apurações (M200/M600, E110/E210), créditos por natureza (M105/M505), ativo (F120/F130), serviços (bloco A) e classifica cada operação (revenda, insumo, uso e consumo, ativo, energia, frete, serviço tomado, venda, exportação, devolução, transferência...). Ler `references/layouts-sped.md` se precisar interpretar registros além dos cobertos.

Arquivos grandes: o parser processa em streaming; não tente ler o .txt inteiro no contexto.

### 3. Simular o impacto

```bash
python <skill-dir>/scripts/simula_impacto.py parsed.json --aliquota 28 --json impacto.json
```

Parâmetros opcionais: `--reducao "NCM_PREFIXO=0.6,..."` (reduções por NCM), `--simples-share 0.15` (fração das compras de fornecedores do Simples), `--passthrough 0.5`. O script aplica a metodologia de `references/metodologia.md`:

- **Débito novo** = Σ receitas tributáveis (excluídas exportações, devoluções, transferências, remessas) × t_ref × (1 − redução do item).
- **Crédito novo** = base ampla: TODAS as entradas de contribuintes regulares (inclusive uso e consumo, serviços, energia, frete, ativo com crédito imediato), ajustada pelo regime do fornecedor.
- **Baseline** = ICMS a recolher (E110) + ICMS-ST (E210) + IPI + PIS/COFINS (M200/M600) + ISS estimado do bloco A.
- Grade 2026-2033 com a convivência dos dois sistemas (ICMS/ISS 90/80/70/60% em 2029-2032).

### 4. Interpretar e complementar com julgamento

O número do script é o esqueleto. Agregar análise qualitativa obrigatória:

- **Créditos que nascem com a reforma**: quantificar (o script separa) uso e consumo (CFOP x556), serviços tomados (bloco A), energia/telecom administrativas, ativo imobilizado (crédito imediato vs. 1/48 do CIAP e F120/F130), mercadorias com ICMS-ST embutido (x403/x411). Este é frequentemente o maior achado.
- **Fornecedores do Simples**: crédito limitado ao cobrado no regime único (ou cheio se o fornecedor optar pelo "híbrido") — recomendar renegociação/qualificação da base de fornecedores quando a fração for relevante.
- **Fim da ST**: efeito de capital de giro e precificação no varejo.
- **Split payment**: efeito caixa (recolhimento na liquidação) — relevante para quem hoje financia capital de giro com o tributo.
- **Margem**: se houver ECF/ECD, usar a DRE (L300/P150 ou I155) para traduzir ΔCarga e ΔCusto em pontos de margem. IBS/CBS são "por fora" — não transitam pela DRE como ICMS/PIS/COFINS hoje; a receita líquida comparável muda.
- **Sensibilidade**: sempre apresentar pelo menos 2 cenários de alíquota e o break-even de repasse de preço.

### 5. Entregar o relatório

Estrutura (markdown; gerar PDF/XLSX se o usuário pedir — usar as skills de documento do ambiente):

```markdown
# Impacto da Reforma Tributária — <empresa> | período analisado
## Sumário executivo (ΔCarga em R$ e %, 3 achados principais)
## Carga atual (baseline por tributo)
## Simulação IBS/CBS (débitos, créditos, alíquota efetiva)
## Créditos: o que muda (tabela categoria a categoria, hoje vs. reforma)
## Impacto em preço e margem (break-even, cenários de repasse)
## Suprimentos (fornecedores Simples, ST, renegociações recomendadas)
## Trajetória 2026-2033 (tabela ano a ano)
## Premissas e limitações
```

**Sempre** listar as premissas (alíquota usada, classificação NCM→redução adotada, share Simples) e o caráter de estimativa — o resultado depende da Resolução do Senado que fixará a alíquota e da tabela cClassTrib aplicável a cada produto.

## Limites

- EFD Contribuições e EFD ICMS/IPI **não têm campos IBS/CBS** (estratégia oficial: apuração assistida via DF-e). A simulação cruza dados atuais com regras novas — é estimativa, não apuração.
- Registro 0150 não traz o regime do fornecedor; sem enriquecimento externo, o share do Simples é premissa.
- Para precisão por produto, seria preciso mapear NCM→cClassTrib item a item (tabela oficial no Portal NF-e); o script aceita reduções por prefixo de NCM como aproximação.
