# 🔧 Guia Completo de Manutenção — Busca de Especificações

> **Para quem é este guia?** Qualquer pessoa que precise manter, alterar ou instalar
> o sistema de busca de especificações técnicas, mesmo sem experiência com programação.

---

## 📋 Índice

1. [Instalação do zero (sem Python)](#1-instalação-do-zero)
2. [Estrutura dos arquivos](#2-estrutura-dos-arquivos)
3. [Como iniciar o app](#3-como-iniciar-o-app)
4. [Adicionar novo tipo de equipamento](#4-adicionar-novo-tipo-de-equipamento)
5. [Adicionar novo site de busca](#5-adicionar-novo-site-de-busca)
6. [Adicionar nova especificação técnica](#6-adicionar-nova-especificação-técnica)
7. [Filtrar resultados irrelevantes](#7-filtrar-resultados-irrelevantes)
8. [Trocar a chave da IA](#8-trocar-a-chave-da-ia)
9. [Problemas comuns e soluções](#9-problemas-comuns-e-soluções)

---

## 1. Instalação do zero

### 1.1 Instalar o Python

```
1. Abra o navegador e acesse: https://www.python.org/downloads/
2. Clique no botão amarelo "Download Python 3.x.x"
3. Execute o arquivo baixado
```

⚠️ **MUITO IMPORTANTE** — Na tela de instalação:

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   ☑  Install launcher for all users              │
│   ☑  Add Python to PATH    ◄── MARCAR ISSO!     │
│                                                  │
│   [ Install Now ]                                │
│                                                  │
└──────────────────────────────────────────────────┘
```

Se esquecer de marcar "Add Python to PATH", desinstale e instale de novo marcando.

### 1.2 Verificar se o Python foi instalado

```
1. Pressione  Windows + R
2. Digite:    cmd
3. Pressione  Enter
4. Na tela preta, digite:  python --version
5. Deve aparecer algo como: Python 3.12.x
```

Se aparecer erro, tente `py --version`. Se nenhum funcionar, reinstale o Python.

### 1.3 Instalar as dependências

```
1. Abra o Explorador de Arquivos
2. Navegue até a pasta:  C:\Users\SeuUsuario\Downloads
3. Clique na barra de endereço (onde mostra o caminho da pasta)
4. Digite:  cmd
5. Pressione Enter (abre um terminal nessa pasta)
6. Cole este comando e pressione Enter:
```

```
pip install requests beautifulsoup4 googlesearch-python selenium webdriver-manager openpyxl pdfplumber streamlit pandas python-dotenv groq
```

Aguarde terminar (pode levar 2-3 minutos). Quando aparecer o cursor piscando de novo, está pronto.

### 1.4 Configurar a chave da IA (opcional, mas recomendado)

```
1. Acesse: https://console.groq.com/keys
2. Crie uma conta gratuita (pode usar Google)
3. Clique em "Create API Key"
4. Copie a chave gerada (começa com gsk_...)
5. Na pasta Downloads, abra o arquivo .env com o Bloco de Notas
6. Encontre a linha GROQ_API_KEY= e cole a chave:
   GROQ_API_KEY=gsk_sua_chave_aqui
7. Salve e feche
```

> **Nota:** Se o arquivo `.env` não aparecer, pode ser que esteja oculto.
> No Explorador de Arquivos, clique em **Exibir** → marque **Itens ocultos**.

---

## 2. Estrutura dos arquivos

Todos os arquivos ficam na pasta `Downloads`:

```
Downloads/
│
├── freezer_specs_scraper.py    ◄── MOTOR DE BUSCA (scraping + regex)
│   │
│   ├── Lista de sites de busca
│   ├── Lista de equipamentos conhecidos
│   ├── Padrões regex para extrair specs
│   ├── Filtros de relevância
│   └── Lógica de busca (Google, HTML, PDF)
│
├── app_busca.py                ◄── INTERFACE WEB (Streamlit)
│   │
│   ├── Layout visual (métricas, tabelas)
│   ├── Integração com IA (Groq/Llama)
│   ├── Chat do assistente
│   └── Exportação CSV
│
├── .env                        ◄── CHAVES E CONFIGURAÇÕES
│   │
│   └── GROQ_API_KEY=gsk_...
│
└── GUIA_MANUTENCAO.md          ◄── ESTE ARQUIVO
```

---

## 3. Como iniciar o app

### Passo a passo visual:

```
1. Abra o Explorador de Arquivos
2. Vá até:  C:\Users\SeuUsuario\Downloads
3. Clique na barra de endereço
4. Digite:  cmd
5. Pressione Enter
6. No terminal, cole:

   py -m streamlit run app_busca.py --server.headless true --server.port 8501

7. Pressione Enter
8. Aguarde aparecer:

   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501

9. Abra o navegador e acesse: http://localhost:8501
```

### Para parar o app:
```
No terminal, pressione:  Ctrl + C
```

### Para acessar de outro computador na mesma rede:
```
No navegador do outro computador, acesse:
http://IP_DO_COMPUTADOR:8501

Para descobrir o IP, no terminal digite:  ipconfig
Procure "Endereço IPv4": geralmente começa com 192.168.x.x
```

---

## 4. Adicionar novo tipo de equipamento

> **Quando usar:** Quando quiser que o sistema reconheça um novo tipo
> de equipamento (ex: "liquidificador industrial", "câmara fria").

### Arquivo: `freezer_specs_scraper.py`

### O que procurar: `EQUIPMENT_CONTEXT_KEYWORDS`

```
1. Abra o arquivo  freezer_specs_scraper.py  com o Bloco de Notas
   (clique com botão direito → Abrir com → Bloco de Notas)

2. Pressione  Ctrl + F  (Localizar)

3. Digite:  EQUIPMENT_CONTEXT_KEYWORDS

4. Você vai encontrar algo assim:
```

**ANTES:**
```python
EQUIPMENT_CONTEXT_KEYWORDS = [
    "forno", "freezer", "geladeira", "refrigerador", "expositor",
    "ar condicionado", "ar-condicionado", "split", "coifa",
    "fritadeira", "cervejeira", "balcao", "vitrine",
]
```

**DEPOIS (exemplo: adicionar "liquidificador" e "câmara fria"):**
```python
EQUIPMENT_CONTEXT_KEYWORDS = [
    "forno", "freezer", "geladeira", "refrigerador", "expositor",
    "ar condicionado", "ar-condicionado", "split", "coifa",
    "fritadeira", "cervejeira", "balcao", "vitrine",
    "liquidificador", "câmara fria",
]
```

### ⚠️ Regras importantes:
```
✅  Sempre entre aspas:           "liquidificador"
✅  Sempre com vírgula no final:  "liquidificador",
✅  Sempre em minúsculo:          "câmara fria"  (não "Câmara Fria")
❌  Não apagar os existentes
❌  Não remover os colchetes [ ]
```

### Salvar:
```
Ctrl + S  →  Fechar o arquivo  →  O app atualiza sozinho
```

---

## 5. Adicionar novo site de busca

> **Quando usar:** Quando descobrir um site de varejo ou fabricante
> que tem boas especificações técnicas.

### Arquivo: `freezer_specs_scraper.py`

### 5A. Site de varejo (loja online)

### O que procurar: `RETAIL_SEARCH_URLS`

```
1. Abra  freezer_specs_scraper.py  com Bloco de Notas
2. Ctrl + F  →  RETAIL_SEARCH_URLS
3. Adicione uma nova linha:
```

**ANTES:**
```python
RETAIL_SEARCH_URLS = [
    ("Magazine Luiza", "https://www.magazineluiza.com.br/busca/{q}/"),
    ("Americanas", "https://www.americanas.com.br/busca/{q}"),
]
```

**DEPOIS (exemplo: adicionar Shopee):**
```python
RETAIL_SEARCH_URLS = [
    ("Magazine Luiza", "https://www.magazineluiza.com.br/busca/{q}/"),
    ("Americanas", "https://www.americanas.com.br/busca/{q}"),
    ("Shopee", "https://shopee.com.br/search?keyword={q}"),
]
```

### Como descobrir a URL de busca de um site:

```
1. Vá ao site (ex: shopee.com.br)
2. Pesquise qualquer coisa, tipo "freezer"
3. Olhe a barra de endereço:
   https://shopee.com.br/search?keyword=freezer
                                         ^^^^^^^
4. Substitua "freezer" por {q}:
   https://shopee.com.br/search?keyword={q}

5. Use esse formato na lista
```

### 5B. Site de fabricante

### O que procurar: `MANUFACTURER_DOMAINS`

```python
MANUFACTURER_DOMAINS = {
    "imbera": "https://www.imbera.com/br/busca?q={q}",
    "metalfrio": "https://www.metalfrio.com.br/busca?q={q}",
    "novamarca": "https://www.novamarca.com.br/produtos?busca={q}",  # ← novo
}
```

### ⚠️ Regras:
```
✅  O nome da marca em minúsculo:  "novamarca"
✅  A URL com {q} no lugar da busca
✅  Vírgula no final da linha
✅  Aspas em tudo
```

---

## 6. Adicionar nova especificação técnica

> **Quando usar:** Quando quiser extrair um dado novo dos sites,
> como Peso (kg), Dimensões, Nível de Ruído (dB), Capacidade (litros), etc.

⚠️ **Este é o procedimento mais complexo.** São 8 alterações em 2 arquivos.

### Exemplo completo: adicionar "Peso (kg)"

---

### ARQUIVO 1: `freezer_specs_scraper.py` (6 alterações)

---

### Alteração 1 de 8 — Adicionar campo no modelo de dados

```
Ctrl + F  →  class FreezerSpecs
```

**ANTES:**
```python
@dataclass
class FreezerSpecs:
    produto: str
    potencia_w: Optional[str] = None
    voltagem_v: Optional[str] = None
    consumo_kwh: Optional[str] = None
    btu: Optional[str] = None
    fase: Optional[str] = None
    fonte_potencia: Optional[str] = None
    fonte_voltagem: Optional[str] = None
    fonte_consumo: Optional[str] = None
    fonte_btu: Optional[str] = None
    fonte_fase: Optional[str] = None
```

**DEPOIS:**
```python
@dataclass
class FreezerSpecs:
    produto: str
    potencia_w: Optional[str] = None
    voltagem_v: Optional[str] = None
    consumo_kwh: Optional[str] = None
    btu: Optional[str] = None
    fase: Optional[str] = None
    peso_kg: Optional[str] = None          # ← NOVO
    fonte_potencia: Optional[str] = None
    fonte_voltagem: Optional[str] = None
    fonte_consumo: Optional[str] = None
    fonte_btu: Optional[str] = None
    fonte_fase: Optional[str] = None
    fonte_peso: Optional[str] = None       # ← NOVO
```

---

### Alteração 2 de 8 — Criar padrões regex

```
Ctrl + F  →  PHASE_PATTERNS
Adicione ABAIXO do bloco PHASE_PATTERNS:
```

```python
PESO_PATTERNS = [
    r"[Pp]eso\s*(?:l[ií]quido\s*)?(?:bruto\s*)?[:\-–]?\s*(\d+[\.,]?\d*)\s*[Kk][Gg]",
    r"[Ww]eight\s*[:\-–]?\s*(\d+[\.,]?\d*)\s*[Kk][Gg]",
    r"(\d+[\.,]?\d*)\s*[Kk][Gg]\b",
]
```

> **Como funciona o regex:** `(\d+[\.,]?\d*)` captura números como "45", "45.5", "45,5".
> O resto são as palavras ao redor: "Peso:", "Weight:", "kg", etc.
> Teste seus regex em: https://regex101.com (selecione Python)

---

### Alteração 3 de 8 — Criar função de busca

```
Ctrl + F  →  def find_phase
Adicione ACIMA dessa linha:
```

```python
def find_peso(text: str) -> Optional[str]:
    for pattern in PESO_PATTERNS:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).replace(",", ".")
            try:
                num = float(value)
                if 0.5 <= num <= 500:
                    return f"{value} kg"
            except ValueError:
                pass
    return None
```

> O `if 0.5 <= num <= 500` é um filtro: ignora valores absurdos
> (menos de 0.5 kg ou mais de 500 kg provavelmente não é um equipamento).
> Ajuste conforme necessário.

---

### Alteração 4 de 8 — Adicionar nos dicionários de resultado

Procure **TODOS** os trechos que tenham:

```python
result = {"potencia": None, "voltagem": None, "consumo": None, "btu": None, "fase": None}
```

E mude para:

```python
result = {"potencia": None, "voltagem": None, "consumo": None, "btu": None, "fase": None, "peso": None}
```

> **Quantos existem?** Use Ctrl + F para encontrar todos. Atualmente são 5:
> - `extract_specs_from_pdf`
> - `extract_from_json_ld`
> - `extract_from_spec_tables`
> - `extract_all_specs`
> - `extract_from_text`

E onde tem `find_phase(text)`, adicione abaixo:
```python
result["peso"] = find_peso(text)
```

---

### Alteração 5 de 8 — Adicionar detecção em tabelas HTML

```
Ctrl + F  →  _match_label_value
Dentro dessa função, adicione no final (antes do último return):
```

```python
    elif any(k in label for k in ("peso", "weight", "massa", "peso líquido", "peso bruto")):
        parsed = find_peso(value)
        if parsed and not result.get("peso"):
            result["peso"] = parsed
```

---

### Alteração 6 de 8 — Aplicar resultado encontrado

```
Ctrl + F  →  _apply_result
Adicione no final da função (antes do  return found):
```

```python
    if result.get("peso") and not specs.peso_kg:
        specs.peso_kg = result["peso"]
        specs.fonte_peso = url
        found.append(f"Peso={result['peso']}")
```

---

### ARQUIVO 2: `app_busca.py` (2 alterações)

---

### Alteração 7 de 8 — Adicionar coluna nas tabelas

```
Ctrl + F  →  display_cols
```

Em **TODOS** os `display_cols` (existem 2), adicione:

```python
"peso_kg": "Peso (kg)",
```

Exemplo:
```python
display_cols = {
    "produto": "Equipamento",
    "potencia_w": "Potencia (W)",
    "voltagem_v": "Voltagem (V)",
    "fase": "Fase",
    "consumo_kwh": "Consumo (kWh)",
    "btu": "BTU",
    "peso_kg": "Peso (kg)",          # ← NOVO
    "fonte_potencia": "Fonte Potencia",
    "fonte_voltagem": "Fonte Voltagem",
    "tempo_busca": "Tempo",
}
```

---

### Alteração 8 de 8 — Adicionar métrica visual

```
Ctrl + F  →  render_metric("BTU"
```

Adicione uma nova coluna. Onde tem:

```python
col1, col2, col3, col4, col5 = st.columns(5)
```

Mude para:

```python
col1, col2, col3, col4, col5, col6 = st.columns(6)
```

E adicione:

```python
with col6:
    render_metric("Peso (kg)", result.get("peso_kg"), result.get("fonte_peso"))
```

> **Atenção:** Existem 2 blocos de `render_metric` no arquivo. Altere os dois.

---

## 7. Filtrar resultados irrelevantes

> **Quando usar:** Quando uma busca traz resultados de carros, imóveis,
> ou qualquer coisa que não seja equipamento.

### Arquivo: `freezer_specs_scraper.py`

```
Ctrl + F  →  IRRELEVANT_KEYWORDS
```

Adicione palavras do assunto indesejado:

```python
IRRELEVANT_KEYWORDS = [
    "carro", "automóvel", "ferrari", "fiat",
    # ... existentes ...
    "palavra_nova",  # ← adicionar aqui
]
```

---

## 8. Trocar a chave da IA

```
1. Acesse:  https://console.groq.com/keys
2. Faça login (ou crie conta gratuita)
3. Clique em "Create API Key"
4. Copie a chave (começa com gsk_...)

5. Na pasta Downloads, abra o arquivo  .env  com Bloco de Notas
   (Se não aparecer: Explorador → Exibir → Itens ocultos)

6. Substitua a chave antiga:
   GROQ_API_KEY=gsk_nova_chave_aqui

7. Salve (Ctrl + S) e reinicie o app
```

---

## 9. Problemas comuns e soluções

### "python não é reconhecido como comando"

```
Causa:  Python não foi adicionado ao PATH durante instalação.
Solução: Desinstale o Python e instale novamente MARCANDO
         "Add Python to PATH" na primeira tela.
Alternativa: Tente usar  py  ao invés de  python
```

### "pip não é reconhecido"

```
Causa:  Mesmo problema do PATH.
Solução: Tente:  py -m pip install ...
         ao invés de:  pip install ...
```

### "ModuleNotFoundError: No module named 'streamlit'"

```
Causa:  As dependências não foram instaladas.
Solução: Abra o cmd na pasta Downloads e execute:

pip install requests beautifulsoup4 googlesearch-python selenium webdriver-manager openpyxl pdfplumber streamlit pandas python-dotenv groq
```

### "A porta 8501 já está em uso"

```
Causa:  O app já está rodando em outro terminal.
Solução:
  1. Abra o cmd
  2. Digite:  netstat -ano | findstr :8501
  3. Anote o número da última coluna (PID)
  4. Digite:  taskkill /PID numero_anotado /F
  5. Inicie o app novamente
```

### "O app não encontra nenhuma especificação"

```
Possíveis causas:
  1. Equipamento muito novo ou raro (poucos dados online)
  2. Nome digitado muito genérico (ex: "forno" sozinho)
  3. Internet lenta ou bloqueio de firewall

Soluções:
  - Tente com nome mais completo: "Forno Venancio FIRI100" ao invés de "Forno Roma"
  - Adicione mais sites de busca (seção 5)
  - Verifique se a IA está ativa (chave no .env)
```

### "O app mostra dados de carro/imóvel"

```
Causa:  O nome do equipamento é igual a um carro ou outro produto.
Solução:
  1. Adicione palavras do assunto errado em IRRELEVANT_KEYWORDS (seção 7)
  2. Clique em "Limpar cache de buscas" na barra lateral do app
  3. Busque novamente
```

### "Erro de sintaxe depois de editar o arquivo"

```
Causa:  Algo foi digitado errado no código Python.
Diagnóstico: O terminal mostra o número da linha com erro.

Erros comuns:
  - Esqueceu a vírgula:     "forno" "freezer"     ← faltou vírgula
  - Esqueceu as aspas:      forno,                 ← faltou aspas
  - Esqueceu o colchete:    "forno", "freezer"     ← faltou ]
  - Indentação errada:      o Python exige espaços alinhados

Solução: Compare com as linhas acima/abaixo e corrija o padrão.
         Em último caso, restaure o backup.
```

---

## 📞 Dicas finais

| Dica | Detalhe |
|------|---------|
| **Sempre faça backup** | Antes de editar, copie o arquivo (ex: `freezer_specs_scraper_backup.py`) |
| **Teste após alterar** | Busque um equipamento conhecido para validar |
| **Use Ctrl + Z** | Se errou no Bloco de Notas, desfaça antes de salvar |
| **Regex** | Teste padrões em https://regex101.com (selecione Python) |
| **O app atualiza sozinho** | Depois de salvar o arquivo, o Streamlit detecta e reinicia |

---

## 10. Deploy no Streamlit Cloud (app online)

> **Para que serve:** Colocar o app online em uma URL pública gratuita,
> acessível de qualquer navegador, sem instalar nada.

### 10.1 Criar conta no GitHub (só na primeira vez)

```
1. Abra o navegador
2. Acesse:  https://github.com/signup
3. Preencha: email, senha, nome de usuário
4. Confirme o email (link que chega no email)
5. Pronto — conta criada
```

### 10.2 Criar o repositório no GitHub

```
1. Acesse:  https://github.com/new
2. Preencha:
   - Repository name:  busca-especificacoes
   - Description:      Busca de especificações técnicas de equipamentos
   - Marque:           Public
   - NÃO marque:       "Add a README file"
   - NÃO marque:       "Add .gitignore"
3. Clique em  "Create repository"
4. Na página que abrir, copie o link HTTPS que aparece:
   Algo como:  https://github.com/SEU-USUARIO/busca-especificacoes.git
```

### 10.3 Enviar o código para o GitHub

```
1. Abra o Explorador de Arquivos
2. Vá até:  C:\Users\SeuUsuario\Downloads
3. Clique na barra de endereço, digite cmd, pressione Enter
4. Cole estes 2 comandos (um de cada vez):

   git remote add origin https://github.com/SEU-USUARIO/busca-especificacoes.git
   git push -u origin main

5. Se pedir login:
   - Uma janela do navegador vai abrir pedindo para autorizar o Git
   - Clique em "Authorize"
   - Volte ao terminal — o push continua automaticamente

6. Quando aparecer "main -> main", está pronto!
```

### 10.4 Publicar no Streamlit Cloud

```
1. Acesse:  https://share.streamlit.io
2. Clique em "Continue with GitHub"
3. Autorize o acesso
4. Clique em "New app" (botão azul)
5. Preencha:

   ┌──────────────────────────────────────────────────┐
   │  Repository:    SEU-USUARIO/busca-especificacoes  │
   │  Branch:        main                              │
   │  Main file:     app_busca.py                      │
   └──────────────────────────────────────────────────┘

6. Clique em "Advanced settings..."
7. Na aba "Secrets", cole:

   GROQ_API_KEY = "gsk_SUA_CHAVE_GROQ_AQUI"

   (Substitua pela sua chave real do Groq)

8. Clique em "Deploy!"
9. Aguarde 2-3 minutos — o app vai ficar disponível em:

   https://SEU-USUARIO-busca-especificacoes.streamlit.app

10. Compartilhe esse link com qualquer pessoa!
```

### 10.5 Atualizar o app online depois de alterar

Sempre que fizer alterações nos arquivos e quiser que o app online atualize:

```
1. Abra o cmd na pasta Downloads
2. Execute estes 3 comandos:

   git add app_busca.py freezer_specs_scraper.py
   git commit -m "Atualização do app"
   git push

3. O Streamlit Cloud detecta automaticamente e redesploya em 1-2 minutos.
```

### 10.6 Limitação importante

```
O Streamlit Cloud NÃO suporta Selenium (navegador automatizado).
Isso significa que sites que precisam de JavaScript para carregar
serão ignorados na versão online.

A maioria dos sites funciona normalmente (via requests direto).
Para a versão completa com Selenium, rode localmente (seção 3).
```
