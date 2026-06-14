---
name: valida-nfe
description: >-
  Valida XML de NF-e/NFC-e: recalcula todos os tributos (ICMS, IPI, PIS, COFINS, Imposto
  Seletivo e IBS/CBS conforme NT 2025.002-RTC da reforma tributária), confere se os campos e
  totais estão calculados corretamente e identifica as retenções aplicáveis (IRRF, CSRF
  PIS/COFINS/CSLL, INSS, ISS). Use SEMPRE que o usuário enviar um XML de nota fiscal ou pedir
  para: validar uma NF-e/NFC-e, conferir cálculo de impostos de uma nota, checar se IBS/CBS
  estão corretos, auditar destaque de tributos, verificar retenções de uma nota fiscal, ou
  perguntar "essa nota está certa?", "os impostos desta NF batem?". Também acionar para
  validação em lote de vários XMLs.
---

# Validação de NF-e (campos, cálculos e retenções)

Receber um ou mais XMLs de NF-e (modelo 55) / NFC-e (65), recalcular cada tributo a partir das bases e alíquotas declaradas, comparar com os valores destacados e reportar divergências, além de apontar as retenções que deveriam (ou não) incidir.

## Fluxo de trabalho

### 1. Rodar o validador determinístico

```bash
python <skill-dir>/scripts/valida_nfe.py caminho/para/nota.xml --json saida.json
```

O script aceita `nfeProc` ou `NFe` como raiz, valida item a item (ICMS, IPI, PIS, COFINS, IS, grupo IBSCBS) e o batimento dos totais (`ICMSTot`, `IBSCBSTot`, `ISTot`), e imprime um relatório com severidades (ERRO/ALERTA/INFO). Para lote, passar vários arquivos ou um diretório.

### 2. Analisar o resultado com julgamento

O script verifica aritmética e consistência estrutural. Em cima disso, avaliar o que exige conhecimento tributário (ler `references/layout-nfe-rtc.md` e `references/tributos-e-retencoes.md` conforme a necessidade):

- **Coerência CST × cClassTrib × grupos**: CST 510 exige `gDif`; 550 exige `gTribRegular`; 620 exige `gIBSCBSMono`; 800 exige `gTransfCred`; CST 200/210 exigem `gRed` com `pAliqEfet = pIBS × (1 − pRedAliq/100)`. A tabela cClassTrib oficial (Portal NF-e > Documentos > Diversos) é vinculante — em caso de dúvida sobre um código, buscar a planilha.
- **Alíquotas 2026**: IBS 0,1% (estadual; municipal 0%) e CBS 0,9% no ano-teste. Alíquotas diferentes disso em 2026 são alerta (exceto reduções/monofasia). pIBSUF+pIBSMun e pCBS devem refletir o cClassTrib (reduções de 30%/60%, alíquota zero da cesta básica etc.).
- **Base de cálculo IBS/CBS**: "por fora" — vBC = valor da operação (vProd + frete + seguro + outras despesas − descontos incondicionais), **excluindo** o próprio IBS/CBS, o IPI e, na transição, o ICMS/ISS destacados. O IS integra a BC quando não recuperável. Divergência aqui é o erro mais comum.
- **Retenções**: o XML traz o grupo `retTrib` (total). Verificar se a natureza da operação (serviços profissionais, cessão de mão de obra, limpeza/vigilância) exigiria IRRF/CSRF/INSS e se os valores conferem com as bases (ver tabela na referência). Lembrar: **IBS/CBS não têm retenção na fonte** — o mecanismo é o split payment; CSRF morre com PIS/COFINS em 2027.
- **Cronograma**: notas emitidas a partir de 03/08/2026 (regime normal) sem grupo IBSCBS = ERRO (RV UB12-10); antes disso, ausência = ALERTA (obrigação legal desde 01/01/2026, sem penalidade no período educativo).

### 3. Produzir o relatório

Estrutura do relatório ao usuário (e em arquivo quando solicitado):

```markdown
# Validação NF-e <chave> — <emitente> → <destinatário>
## Resumo
(aprovada / aprovada com alertas / reprovada — nº de erros e alertas)
## Divergências de cálculo
(por item e tributo: declarado vs. recalculado, diferença, causa provável)
## Conformidade reforma tributária (IBS/CBS/IS)
(presença e coerência do grupo IBSCBS, CST × cClassTrib, alíquotas do ano)
## Retenções
(o que incide na operação, o que foi destacado, o que falta/sobra)
## Observações
```

Sempre indicar a **causa provável** de cada divergência (ex.: "vBC do IBS inclui o IPI — na transição o IPI não compõe a base"), não apenas o delta. Arredondamento: tolerância de R$ 0,01 por item (half-up); acima disso é divergência real.

## Limites

- O script não substitui a validação do autorizador SEFAZ (schemas XSD e ~200 RVs da NT). Ele cobre aritmética, batimento de totais e as regras estruturais principais.
- Tabelas oficiais (cClassTrib, alíquotas CBS, cCredPres) evoluem — para códigos desconhecidos, consultar o Portal NF-e antes de afirmar erro.
- NFS-e nacional (DPS) tem layout próprio; o validador cobre NF-e/NFC-e. Para NFS-e, analisar manualmente com a seção 7 de `references/layout-nfe-rtc.md`.
