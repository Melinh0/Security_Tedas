# Security TEDAS - API de Gerenciamento de Exames de Tomografia

## 📋 Descrição do Projeto

Esta é uma API Django REST Framework para gerenciamento seguro de usuários, pacientes e fatias de exames de tomografio da L3. O sistema inclui autenticação JWT, controle de acesso baseado em roles (RBAC), criptografia de dados sensíveis e upload seguro de arquivos DICOM.

## 🚀 Pré-requisitos

Antes de começar, certifique-se de ter instalado em sua máquina:
- **Docker** ([Instalação do Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** ([Instalação do Docker Compose](https://docs.docker.com/compose/install/))
- **Git** ([Instalação do Git](https://git-scm.com/downloads))

## 📥 Clonagem do Repositório

```bash
# Clone o repositório
git clone <URL_DO_REPOSITORIO>
cd Security_Tedas
```

## 🐳 Execução do Projeto com Docker

### Passo 1: Verifique se o Docker está rodando

```bash
# Verifique se o Docker está instalado e funcionando
docker --version
docker-compose --version

# Se não estiver instalado, siga os links de instalação acima
```

### Passo 2: Construa e execute os containers

```bash
# Execute o comando para construir as imagens e iniciar os containers
sudo docker-compose up --build
```

**O que este comando faz:**
- Baixa as imagens base (Python 3.12 e PostgreSQL 16)
- Instala todas as dependências do projeto
- Configura o banco de dados PostgreSQL
- Executa as migrações do Django
- Inicia o servidor Django na porta 8000

### Passo 3: Aguarde a inicialização completa

Você verá no terminal mensagens como:
```
db_1   | 2025-09-12 18:19:39.881 UTC [1] LOG:  database system is ready to accept connections
web_1  | Database started
web_1  | Operations to perform:
web_1  |   Apply all migrations: admin, api, auth, contenttypes, sessions
web_1  | Running migrations:
web_1  |   No migrations to apply.
web_1  | Watching for file changes with StatReloader
web_1  | Django version 5.2.3, using settings 'security_api.settings'
web_1  | Starting development server at http://0.0.0.0:8000/
```

**⚠️ Importante:** Aguarde até ver a mensagem "Starting development server at http://0.0.0.0:8000/" antes de prosseguir.

## 🌐 Acesso à Aplicação

### 1. Documentação Interativa da API (Swagger)
Abra seu navegador e acesse:
```
http://localhost:8000/swagger/
```

Aqui você pode:
- Visualizar todos os endpoints disponíveis
- Testar as rotas diretamente pela interface
- Ver exemplos de requisições e respostas

### 2. Painel Administrativo do Django
Acesse o admin em:
```
http://localhost:8000/admin/
```

## 👥 Usuários Pré-Cadastrados

O sistema cria automaticamente 3 usuários durante a migração:

| Usuário | Senha | Role | Descrição |
|---------|-------|------|-----------|
| `admin` | `admin` | Administrador | Acesso completo ao sistema |
| `researcher` | `researcher` | Pesquisador | Acesso apenas a exames segmentados |
| `doctor` | `doctor` | Profissional de Saúde | Pode gerenciar pacientes e exames |

## 🛠️ Criando um Novo Usuário via Django Admin

### Passo 1: Faça login no Django Admin
- Acesse: `http://localhost:8000/admin/`
- Use as credenciais: **usuário:** `admin`, **senha:** `admin`

### Passo 2: Navegue até a seção de usuários
- No menu lateral, clique em **"Profissional saudes"**
- Clique no botão **"ADICIONAR PROFISSIONAL SAUDE"** no canto superior direito

### Passo 3: Preencha os dados do usuário

**Campos obrigatórios:**
- **Nome de usuário:** Escolha um username único
- **Senha:** Digite uma senha forte (mínimo 8 caracteres)
- **Confirmação de senha:** Repita a senha
- **Endereço de email:** Email válido do usuário
- **Nome completo:** Nome completo do profissional
- **CPF:** Apenas números (será criptografado automaticamente)
- **Papel:** Escolha entre Admin, Pesquisador ou Profissional da Saúde

**Campos condicionais:**
- Se escolher "Profissional da Saúde", selecione o **Tipo profissional** (Médico, Nutricionista, etc.)

### Passo 4: Salve o usuário
- Clique em **"SALVAR"** para criar o usuário
- O novo usuário já estará disponível para login

## 🔌 Testando as Rotas da API

### 1. Autenticação (Login)

**Endpoint:** `POST /api/login/`

**Exemplo usando curl:**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: multipart/form-data" \
  -F "username=admin" \
  -F "password=admin"
```

**Resposta esperada:**
```json
{
  "access": "eyJhbGciOiJ...",
  "refresh": "eyJhbGciOiJ...",
  "role": "admin"
}
```

### 2. Listar Pacientes (Require Autenticação)

**Endpoint:** `GET /api/pacientes/`

**Exemplo usando curl:**
```bash
curl -X GET http://localhost:8000/api/pacientes/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 3. Criar um Novo Paciente

**Endpoint:** `POST /api/pacientes/`

**Exemplo usando curl:**
```bash
curl -X POST http://localhost:8000/api/pacientes/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: multipart/form-data" \
  -F "full_name=João Silva" \
  -F "birth_date=1980-05-15" \
  -F "medical_info=Histórico de saúde do paciente"
```

## 🐛 Solução de Problemas Comuns

### Problema 1: Portas já em uso
```bash
# Se a porta 8000 ou 5434 estiver em uso, altere no docker-compose.yml
# Edite o arquivo docker-compose.yml e modifique as portas:
ports:
  - "8001:8000"  # Mude a primeira porta (8001) para uma disponível
```

### Problema 2: Erro de permissão do Docker
```bash
# Adicione seu usuário ao grupo docker
sudo usermod -aG docker $USER

# Ou execute com sudo
sudo docker-compose up --build
```

### Problema 3: Reconstruir containers
```bash
# Pare os containers
sudo docker-compose down

# Reconstrua com cache limpo
sudo docker-compose build --no-cache

# Execute novamente
sudo docker-compose up
```

### Problema 4: Ver logs de erro
```bash
# Ver logs em tempo real
sudo docker-compose logs -f web

# Ver logs do banco de dados
sudo docker-compose logs -f db
```

## 📁 Estrutura do Projeto

```
Security_Tedas/
├── api/                 # Aplicação principal Django
├── security_api/        # Configurações do projeto
├── docker-compose.yml   # Configuração do Docker
├── Dockerfile          # Build da imagem Docker
├── entrypoint.sh       # Script de inicialização
├── requirements.txt    # Dependências Python
└── README.md          # Este arquivo
```

## 🛡️ Funcionalidades de Segurança

- **Autenticação JWT** com tokens de acesso e refresh
- **Criptografia** de dados sensíveis (CPF, informações médicas)
- **Controle de acesso** baseado em roles (RBAC)
- **Validação de arquivos** por tipo MIME
- **Registro de auditoria** de todas as ações
- **Upload seguro** de arquivos DICOM com criptografia

## 🚪 Comandos Úteis

### Executar em segundo plano
```bash
sudo docker-compose up -d
```

### Parar os containers
```bash
sudo docker-compose down
```

### Executar comandos Django no container
```bash
# Criar superusuário adicional
sudo docker-compose exec web python manage.py createsuperuser

# Ver migrações pendentes
sudo docker-compose exec web python manage.py showmigrations

# Coletar arquivos estáticos (se necessário)
sudo docker-compose exec web python manage.py collectstatic
```