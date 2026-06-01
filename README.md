# Sistema de Apoio à Decisão em Saúde Indígena (Dengue)

## Objetivo
Este projeto é um serviço de backend completo em Python, projetado para gerar propostas estruturadas de intervenção em saúde pública para Distritos Sanitários Especiais Indígenas (DSEI), com foco principal na prevenção e combate à dengue.

O sistema utiliza Inteligência Artificial (Google Gemini) em conjunto com Geração Aumentada por Recuperação (RAG) para combinar dados estruturados de indicadores reais (água, saneamento, epidemiologia, governança) com evidências técnicas extraídas de PDFs.

## Casos de Uso
1. **Geração de Proposta de Intervenção Baseada em Dados:** Permite a geração de propostas técnicas robustas a partir dos indicadores de saúde e vulnerabilidade do DSEI.
2. **Integração via API:** Pode ser consumido por um frontend ou outro serviço, funcionando como o cérebro analítico.
3. **Consulta de Evidências Técnicas em PDFs:** Usa RAG para buscar informações e guias técnicos de PDFs oficiais, contextualizando os dados de campo.
4. **Tratamento Resiliente de Dados Faltantes:** Identifica "sem informação" e lacunas, gerando ações de "validação local" em vez de assumir fatos não comprovados.
5. **Teste e Homologação com Mock:** Permite a operação em modo *mock* local para testes e desenvolvimento sem depender da API externa real.

## Arquitetura
O sistema não possui frontend. É uma API RESTful construída em **FastAPI**, exposta primariamente no padrão JSON. O fluxo de solicitação e resposta segue o padrão:
1. Recebe parâmetros (`dsei`, `data_init`, `data_end`).
2. Coleta dados estruturados através de uma API externa (ou *Mock*).
3. Interpreta as colunas usando um catálogo determinístico via Pydantic (`field_catalog.py`), filtrando incertezas antes do LLM.
4. Categoriza os dados (riscos diretos de dengue, infraestrutura e governança).
5. Recupera fragmentos de documentos (PDFs) no Vector Store local (ChromaDB).
6. Monta o contexto combinado e chama a API do Google Gemini.
7. Valida a resposta do Gemini em tempo real usando o Pydantic para garantir integridade do JSON, retentando automaticamente em caso de anomalia.
8. Retorna JSON completo e tipado ao serviço requisitante.

## Como a Interpretação via Pydantic Funciona
O `src/field_catalog.py` contém uma lista extensa de chaves de API mapeadas com seus graus de prioridade, agrupamento e risco associado à dengue. O `src/field_interpreter.py` nivela (flattens) o JSON bruto da API externa, buscando *match* com o catálogo. Com isso:
* Variáveis como `exist_estrut_perc_ald_sem_estrutura` são interpretadas determinísticamente.
* Porcentagens como "87%" são transformadas no float `87.0`.
* Campos não mapeados são isolados em `unmapped_fields`.
* Somente as interpretações exatas são passadas ao Gemini, evitando que a IA alucine o significado de uma coluna obscura.

## Adicionando PDFs
* Coloque arquivos `.pdf` (guias de MS, artigos, cartilhas) em `data/pdfs/`.
* O sistema extrairá o texto através do PyMuPDF (com fallback para o pdfplumber/OCR).
* Execute o comando de reindexação (`python cli.py --reindex` ou rota da API) para atualizar o banco vetorial e disponibilizar essas evidências ao Gemini.

## Configuração do .env
Crie um `.env` a partir do `.env.example`:
```ini
GEMINI_API_KEY=sua_chave_gemini_aqui
API_URL=https://painel-dengue-aldeias-indigenas-production.up.railway.app/api/dashboard
API_METHOD=GET
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
CHROMA_PERSIST_DIR=storage/chroma
PDF_DIR=data/pdfs
MOCK_API=false
MOCK_API_RESPONSE_PATH=data/mock/api_response_example.json
REINDEX_ON_STARTUP=false
ADMIN_TOKEN=super_secreto_token_admin
API_TIMEOUT_SECONDS=60
CORS_ORIGINS=*
```

## Como Executar Localmente
Com o Python 3.11+ instalado:
```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Testando com Mock API
Com a aplicação em execução:
```bash
curl -X POST http://localhost:8000/generate-intervention \
-H "Content-Type: application/json" \
-d '{
"dsei": "YANOMAMI",
"data_init": "2024-01-01",
"data_end": "2024-01-31",
"use_mock": true
}'
```

## Testando com API Real
```bash
curl -X POST http://localhost:8000/generate-intervention \
-H "Content-Type: application/json" \
-d '{
"dsei": "BAHIA",
"data_init": "2024-01-01",
"data_end": "2024-01-31",
"use_mock": false
}'
```

## Como Recriar o Índice RAG (Vector Store)
Por CLI:
```bash
python cli.py --reindex
```
Por API:
```bash
curl -X POST http://localhost:8000/admin/reindex \
-H "Authorization: Bearer troque_este_token"
```

## CLI (Linha de Comando)
O CLI permite operações em lote ou debugging rápido sem levantar o servidor Uvicorn.
* Rodar com Mock e salvar resultado:
  `python cli.py --dsei "YANOMAMI" --data-init "2024-01-01" --data-end "2024-01-31" --mock --output output.json`
* Rodar com API real:
  `python cli.py --dsei "BAHIA" --data-init "2024-01-01" --data-end "2024-01-31"`

## Deploy no Railway
1. Conecte seu repositório no Railway.
2. O Railway detectará automaticamente o arquivo `railway.json` e o `Dockerfile`.
3. Certifique-se de configurar as Variavéis de Ambiente (`GEMINI_API_KEY`, `API_URL`, etc) no painel do Railway.
4. O `Dockerfile` fornece os artefatos de sistema (Poppler utils) para extração limpa de PDFs. O Railway alocará o `PORT` e iniciará o Uvicorn corretamente.

## Limitações Conhecidas
* O diretório `storage/chroma` é persistido localmente e na conteinerização é descartado a cada restart se você não configurar persistência em disco. Configure `REINDEX_ON_STARTUP=true` ou reindexe via POST na inicialização.
* Fallback de OCR básico existe mas imagens muito degradadas podem ser puladas.
* O Gemini pode apresentar instabilidade se o JSON exigido for incompatível, embora o fallback/retry reduza drasticamente esse risco.
