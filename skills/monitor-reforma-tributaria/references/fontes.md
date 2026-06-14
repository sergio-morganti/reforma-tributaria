# Fontes de monitoramento — Reforma Tributária do Consumo

Verificadas em 09/06/2026. Coluna "Acesso" indica a estratégia: **fetch** = HTML estático, web_fetch funciona; **JS** = renderização client-side, usar WebSearch ou navegador; **API** = endpoint estruturado, preferir sempre.

## Fontes oficiais (normas)

| Fonte | URL | O que monitorar | Acesso |
|---|---|---|---|
| Portal Reforma Tributária — MF | https://www.gov.br/fazenda/pt-br/acesso-a-informacao/acoes-e-programas/reforma-tributaria | Hub oficial: leis, regulamentos, notícias | fetch |
| Notícias MF (reforma) | https://www.gov.br/fazenda/pt-br/acesso-a-informacao/acoes-e-programas/reforma-tributaria/na-midia/noticiass/noticias e https://www.gov.br/fazenda/pt-br/assuntos/noticias/2026 | Anúncios de decretos, atos conjuntos, split payment | fetch |
| RFB — Serviços Reforma Tributária | https://www.gov.br/receitafederal/pt-br/servicos/reforma-tributaria | Piloto CBS, NFS-e, calculadora RTC | fetch |
| RFB — Formulários reforma | https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/formularios/reforma-tributaria | Leiautes DeRE etc. | fetch |
| RFB — Normas (SIJUT) | https://normasinternet2.receita.fazenda.gov.br/ | INs, Portarias, Atos Conjuntos RFB/CGIBS | JS |
| DOU — leitura do dia | https://www.in.gov.br/leiturajornal?data=DD-MM-AAAA&secao=do1 | Decretos, atos, resoluções (buscar: "Ato Conjunto RFB/CGIBS", CGIBS, "Imposto sobre Bens e Serviços", CBS, "split payment", "Imposto Seletivo") | fetch (a busca do site é JS; a leitura do jornal por data funciona) |
| Planalto — textos consolidados | https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm e .../lcp227.htm | Alterações no texto, vetos | fetch (latin-1) |
| CGIBS | http://www.cgibs.gov.br/ | Resoluções do Comitê Gestor (PDFs em /upload/arquivos/AAAAMM/) | homepage JS; PDFs são links diretos |
| Câmara — API Dados Abertos | https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PLP&ano=2026 (e idProposicao=2438459 p/ PLP 108) | Novos PLPs (IS, ajustes LC 214), vetos | API JSON |
| Senado — Dados Abertos | https://legis.senado.leg.br/dadosabertos/materia/pesquisa/lista?sigla=PLP | Resolução do Senado (alíquota de referência!), PLPs | API XML |
| Portal NF-e — Informes | https://www.nfe.fazenda.gov.br/portal/informe.aspx?ehCTG=false | Novas NTs (RTC = NT 2025.002) e Informes Técnicos | fetch |
| Portal NF-e — lista de NTs | https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY= | Versões de NTs | fetch |
| Portal NF-e — tabelas (Diversos) | https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=/NJarYc9nus= | cClassTrib, cCredPres, alíquotas CBS | fetch |
| Portal SPED | http://sped.rfb.gov.br/ (destaques: /destaques/show/7) | Leiautes EFD/ECD/ECF, DeRE, apuração assistida | fetch |
| Portal NFS-e nacional | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc | NTs SE/CGNFS-e, anexos RTC | fetch |
| Agência Câmara / Agência Senado | https://www.camara.leg.br/temas/reforma-tributaria e https://www12.senado.leg.br/noticias | Tramitações, factual | fetch |

## Fontes secundárias (análise — rotular como interpretação)

| Fonte | URL | Observações |
|---|---|---|
| JOTA — Tributos | https://www.jota.info/tributos | Cobertura diária especializada |
| Valor Econômico | https://valor.globo.com/tudo-sobre/reforma-tributaria/ | Paywall — usar manchetes/WebSearch |
| PwC Brasil | https://www.pwc.com.br/pt/servicos/reforma-tributaria.html | Hub + alertas |
| KPMG Brasil | https://kpmg.com/br/pt/home/insights/2023/12/reforma-tributaria.html | Análises LC 214/227 |
| Deloitte / EY Brasil | https://www.deloitte.com/br/pt/services/tax.html e https://www.ey.com/pt_br/insights/tax | Tax alerts (JS pesado — preferir WebSearch site:) |
| Migalhas / Conjur | https://www.migalhas.com.br / https://www.conjur.com.br | Sempre conferir contra fonte oficial |

## Dicas operacionais

- As APIs da Câmara/Senado + páginas estáticas cobrem ~90% do monitoramento sem JS.
- Para big four e portais com paywall, usar `WebSearch` com `site:dominio reforma tributária` e a data.
- URLs do Portal NF-e com `exibirArquivo.aspx?conteudo=...` são estáveis por documento — boas para o log de estado.
- Slugs de notícia do gov.br mudam; identificar itens por título+data, não só por URL.
