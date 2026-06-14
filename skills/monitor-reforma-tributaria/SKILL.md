---
name: monitor-reforma-tributaria
description: >-
  Monitora normas e atualizações da Reforma Tributária do Consumo brasileira (EC 132/2023,
  IBS/CBS/IS, LC 214/2025, LC 227/2026) em fontes oficiais e secundárias e gera resumo
  executivo em PDF quando há novidade. Use SEMPRE que o usuário pedir para: verificar
  atualizações/novidades da reforma tributária, acompanhar normas do IBS/CBS/Imposto Seletivo,
  checar novas Notas Técnicas da NF-e ou do SPED, monitorar o CGIBS/Comitê Gestor, split
  payment, regulamentação da CBS/IBS, alíquota de referência, ou gerar o resumo diário/semanal
  da reforma. Também acionar quando uma tarefa agendada pedir o monitoramento diário, ou quando
  o usuário perguntar "saiu algo novo da reforma?", "teve atualização do IBS/CBS?", "novidades
  tributárias de hoje".
---

# Monitor da Reforma Tributária

Verificar fontes oficiais e secundárias em busca de novidades da Reforma Tributária do Consumo (IBS/CBS/IS), comparar com o que já foi reportado e produzir um resumo executivo em PDF **apenas quando houver atualização relevante**.

## Fluxo de trabalho

### 1. Determinar a janela de verificação

- Se o usuário (ou a tarefa agendada) indicar um período, use-o.
- Caso contrário, procure o arquivo de estado `reforma-monitor-state.json` na pasta de trabalho (outputs). Se existir, a janela vai de `ultima_verificacao` até agora.
- Sem estado e sem período: assuma os últimos 2 dias úteis e diga isso no resumo.

### 2. Varrer as fontes

Ler `references/fontes.md` para a lista completa de fontes, URLs exatas e estratégia de acesso (quais são HTML estático fetchável, quais exigem navegação, quais têm API JSON/XML).

Ordem de varredura recomendada (do mais normativo ao interpretativo):

1. **Notícias do Ministério da Fazenda** (reforma tributária) e da RFB — anúncios de decretos, atos conjuntos RFB/CGIBS, regulamentos.
2. **DOU** via leitura do dia (`https://www.in.gov.br/leiturajornal?data=DD-MM-AAAA&secao=do1`) buscando termos: "Ato Conjunto RFB/CGIBS", "CGIBS", "Imposto sobre Bens e Serviços", "CBS", "split payment", "Imposto Seletivo".
3. **Portal NF-e** — página de informes (novas NTs e Informes Técnicos, tabelas cClassTrib/alíquotas) e **Portal SPED** — destaques (novos leiautes, DeRE, apuração assistida).
4. **CGIBS** (resoluções) e **Câmara/Senado** via APIs de dados abertos — novos PLPs, apreciação de vetos da LC 227/2026, Resolução do Senado fixando alíquotas de referência.
5. **Fontes secundárias** (JOTA, Valor, Agência Câmara/Senado, big four) — interpretação e tendências; sempre rotular como "análise/notícia", nunca como norma.

Use WebSearch complementarmente (ex.: `"reforma tributária" IBS CBS <mês/ano>`) para capturar o que a varredura direta perder. Se um fetch retornar página vazia/JS, não insista — use busca ou as ferramentas de navegador se disponíveis.

**Pontos quentes a vigiar em 2026** (atualizar esta lista conforme evoluir): Resolução do Senado da alíquota de referência da CBS 2027 (cálculo TCU); lei ordinária das alíquotas do Imposto Seletivo; apreciação dos vetos à LC 227/2026; 01/08/2026 = início da obrigatoriedade dos campos IBS/CBS nos DF-e; atos do cronograma do split payment; novas versões da NT 2025.002-RTC (v1.50 em 03/06/2026) e da tabela cClassTrib; instalação plena do CGIBS.

### 3. Filtrar o que é novidade

Comparar contra `reforma-monitor-state.json` (lista de itens já reportados, identificados por URL ou título+data). Um item é novidade se: foi publicado dentro da janela E não consta do estado. Em caso de dúvida (data ausente), incluir com ressalva.

**Se não houver nenhuma novidade**: NÃO gerar PDF. Atualizar o estado com a data da verificação e responder em uma linha: "Verificado em DD/MM — sem atualizações da reforma tributária desde a última checagem."

### 4. Gerar o resumo em PDF

Quando houver novidade, escrever um markdown com esta estrutura e converter para PDF:

```markdown
# Reforma Tributária — Resumo de atualizações | DD/MM/AAAA

## Destaques
(2-4 bullets com o que realmente importa e por quê)

## Normas e atos oficiais
(por item: o que é, número/data do ato, o que muda na prática, prazo/vigência, link)

## Documentos técnicos (NF-e, NFS-e, SPED)
(novas NTs, ITs, tabelas, leiautes — e impacto para quem emite documentos fiscais)

## Tramitação legislativa
(movimentos em PLPs, vetos, resoluções do Senado)

## Notícias e análises
(fontes secundárias, rotuladas como interpretação)

## Próximos marcos
(prazos e datas a vigiar — manter sempre os 3-5 mais próximos)
```

Regras de escrita: para cada item, explicar **o que muda na prática** para uma empresa (não só ementa); sempre citar a fonte com URL; distinguir norma vigente de proposta/minuta; datas no formato DD/MM/AAAA. Público: tributaristas e executivos — denso, sem juridiquês desnecessário.

Converter com o script incluído (não requer dependências além de `reportlab` — instalar com `pip install reportlab --break-system-packages` se faltar):

```bash
python <skill-dir>/scripts/gera_pdf.py resumo.md reforma-tributaria-AAAA-MM-DD.pdf
```

Salvar o PDF na pasta de outputs e apresentá-lo ao usuário (present_files). Se o ambiente tiver uma skill de PDF mais completa, pode usá-la em vez do script.

### 5. Atualizar o estado

Gravar/atualizar `reforma-monitor-state.json` na pasta de outputs:

```json
{
  "ultima_verificacao": "2026-06-09T07:00:00-03:00",
  "itens_reportados": [
    {"data": "2026-06-03", "titulo": "Ato Conjunto RFB/CGIBS nº 2/2026 — split payment", "url": "https://..."}
  ]
}
```

Manter apenas os últimos 90 dias de itens para o arquivo não crescer indefinidamente.

## Contexto mínimo da reforma (para interpretar o que encontrar)

- **Arquitetura**: IBS (estados/municípios, gerido pelo CGIBS) + CBS (federal) + Imposto Seletivo. Lei geral: LC 214/2025. Comitê Gestor: LC 227/2026. Regulamentos: Decreto 12.955/2026 (CBS) e Resolução CGIBS 6/2026 (IBS).
- **Transição**: 2026 = ano-teste (CBS 0,9% + IBS 0,1%, dispensa de recolhimento para quem destaca nos DF-e); 2027 = CBS plena, PIS/COFINS extintos, IS entra, IPI zerado (exceto ZFM); 2029-2032 = ICMS/ISS caem 90/80/70/60%; 2033 = regime integral.
- **Alíquota de referência**: estimativa corrente ~28% (trava de 26,5% na revisão do art. 475 da LC 214). Número definitivo da CBS 2027 sairá por Resolução do Senado em 2026.
- **Split payment**: base normativa criada nos regulamentos; documentação técnica da Plataforma Pública publicada em 06/2026 (Ato Conjunto RFB/CGIBS 2/2026); implementação escalonada e opcional.

Se algo encontrado contradisser este contexto, a fonte nova prevalece — e isso é, por si, um destaque do resumo.
