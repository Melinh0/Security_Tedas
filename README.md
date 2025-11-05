# Security TEDAS - API de Gerenciamento de Exames de Tomografia

## 📋 Descrição do Projeto

API Django REST Framework para gerenciamento seguro de usuários, pacientes e exames de tomografia. Sistema com autenticação JWT, controle de acesso baseado em roles (RBAC), criptografia de dados sensíveis e upload seguro de arquivos DICOM.

## 🏗️ Estrutura do Projeto

```
Security_Tedas/
├── 📁 security_api/                 # Configurações principais
│   ├── settings.py                  # Configurações Django e REST Framework
│   ├── urls.py                      # Rotas principais e documentação
│   ├── middleware.py               # Middleware de segurança
│   ├── asgi.py                     # Configuração ASGI
│   └── wsgi.py                     # Configuração WSGI
├── 📁 accounts/                     # App de autenticação e usuários
│   ├── models.py                   # Modelo ProfissionalSaude
│   ├── views.py                    # Views de autenticação
│   ├── urls.py                     # Rotas de login/usuários
│   ├── serializers.py              # Serializers para API
│   ├── admin.py                    # Configuração admin
│   ├── permissions.py              # Permissões personalizadas
│   ├── forms.py                    # Formulários Django
│   └── apps.py                     # Configuração do app
├── 📁 patients/                     # App de gerenciamento de pacientes
│   ├── models.py                   # Modelo Paciente
│   ├── views.py                    # Views para CRUD
│   ├── urls.py                     # Rotas de pacientes
│   ├── serializers.py              # Serializers da API
│   ├── admin.py                    # Interface admin
│   └── apps.py                     # Configuração do app
├── 📁 exams/                        # App de gerenciamento de exames
│   ├── models.py                   # Modelo FatiaTomografia
│   ├── views.py                    # Views para upload/download
│   ├── urls.py                     # Rotas de exames
│   ├── serializers.py              # Serializers
│   ├── utils.py                    # Utilitários para processamento
│   ├── admin.py                    # Admin interface
│   └── apps.py                     # Configuração do app
├── 📁 audit/                        # App de registros de auditoria
│   ├── models.py                   # Modelo RegistroAuditoria
│   ├── views.py                    # Views de logs
│   ├── urls.py                     # Rotas de auditoria
│   ├── serializers.py              # Serializers
│   ├── admin.py                    # Interface admin
│   └── apps.py                     # Configuração do app
├── 📁 core/                         # Utilitários e funcionalidades centrais
│   ├── models.py                   # Modelos base
│   ├── views.py                    # Views base
│   ├── utils.py                    # Utilitários gerais
│   ├── permissions.py              # Permissões base
│   ├── admin.py                    # Admin base
│   └── apps.py                     # Configuração do app
├── 📜 manage.py                     # Script de gerenciamento Django
├── 🐳 docker-compose.yml           # Configuração Docker Compose
├── 🐳 Dockerfile                   # Build da imagem Docker
├── 📜 entrypoint.sh                # Script de inicialização
├── 📜 requirements.txt             # Dependências Python
└── 📜 README.md                    # Este arquivo
```

## 🚀 Pré-requisitos

- **Docker** ([Instalação](https://docs.docker.com/get-docker/))
- **Docker Compose** ([Instalação](https://docs.docker.com/compose/install/))
- **Git** ([Instalação](https://git-scm.com/downloads))

## 📥 Clonagem e Execução

```bash
# Clone o repositório
git clone <URL_DO_REPOSITORIO>
cd Security_Tedas

# Execute com Docker
sudo docker-compose up --build
```

**Aguarde a inicialização completa:** 
```
web_1  | Starting development server at http://0.0.0.0:8000/
```

## 🌐 Acesso à Aplicação

### 1. Documentação da API (Swagger)
```
http://localhost:8000/swagger/
```

### 2. Painel Administrativo
```
http://localhost:8000/admin/
```

## 👥 Usuários Pré-Cadastrados

| Usuário | Senha | Role | Permissões |
|---------|-------|------|------------|
| `admin` | `admin` | Administrador | Acesso completo |
| `researcher` | `researcher` | Pesquisador | Apenas exames segmentados |
| `doctor` | `doctor` | Profissional | Gerenciar pacientes/exames |

## 🔧 Módulos e Funcionalidades

### 🔐 Accounts - Autenticação & Usuários
- **models.py**: Modelo `ProfissionalSaude` com roles
- **views.py**: Autenticação JWT, gerenciamento de usuários
- **serializers.py**: Validação de dados de usuário
- **permissions.py**: Controle de acesso por role
- **Endpoints:**
  - `POST /api/auth/login/` - Login com JWT
  - `POST /api/auth/forgot-password/` - Recuperação de senha
  - `POST /api/auth/reset-password/` - Redefinir senha
  - `GET /api/profissionais/` - Listar profissionais

### 🏥 Patients - Gestão de Pacientes
- **models.py**: Modelo `Paciente` com dados criptografados
- **views.py**: CRUD completo de pacientes
- **serializers.py**: Serialização segura de dados sensíveis
- **Endpoints:**
  - `GET/POST /api/pacientes/` - Listar/criar pacientes
  - `GET/PUT/DELETE /api/pacientes/{id}/` - Operações específicas

### 📊 Exams - Gestão de Exames DICOM
- **models.py**: Modelo `FatiaTomografia` para upload de exames
- **views.py**: Upload, download e processamento de exames
- **utils.py**: Utilitários para processamento DICOM
- **Endpoints:**
  - `POST /api/fatias-tomografia/` - Upload de exames
  - `GET /api/fatias-tomografia/` - Listar exames
  - `GET /api/fatias-tomografia/{id}/download/` - Download seguro

### 📝 Audit - Auditoria e Logs
- **models.py**: Modelo `RegistroAuditoria` para logs
- **views.py**: Consulta de registros de auditoria
- **Endpoints:**
  - `GET /api/registros/` - Listar registros (apenas admin)

### ⚙️ Core - Funcionalidades Centrais
- **utils.py**: Utilitários gerais e helpers
- **permissions.py**: Permissões base reutilizáveis

## 🛡️ Funcionalidades de Segurança

- **🔐 Autenticação JWT** com tempo de expiração configurável
- **👥 RBAC (Role-Based Access Control)** com 3 níveis de acesso
- **🔒 Criptografia AES-256** para dados sensíveis (CPF, informações médicas)
- **📁 Validação de arquivos** por tipo MIME para arquivos DICOM
- **📊 Auditoria completa** de todas as operações do sistema
- **📧 Recuperação segura** de senha via token por email
- **🛡️ Headers de segurança** via middleware customizado

## 🔌 Testando a API

### 1. Autenticação
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: multipart/form-data" \
  -F "username=admin" \
  -F "password=admin"
```

### 2. Listar Pacientes
```bash
curl -X GET http://localhost:8000/api/pacientes/ \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

### 3. Upload de Exame DICOM
```bash
curl -X POST http://localhost:8000/api/fatias-tomografia/ \
  -H "Authorization: Bearer SEU_TOKEN_JWT" \
  -F "paciente_id=1" \
  -F "arquivo=@exame.dcm" \
  -F "descricao=Tomografia L3"
```

## 🛠️ Gerenciamento de Usuários

### Via Django Admin
1. Acesse `http://localhost:8000/admin/`
2. Login: `admin` / `admin`
3. Em **"Profissional saudes"** → **"ADICIONAR"**

### Campos obrigatórios:
- **Username** (único)
- **Senha** (mínimo 8 caracteres)
- **Email** válido
- **Nome completo**
- **CPF** (apenas números, criptografado automaticamente)
- **Papel** (Admin/Pesquisador/Profissional)

## 🐛 Solução de Problemas

### Portas Ocupadas
```bash
# Edite docker-compose.yml
ports:
  - "8001:8000"  # Use porta livre
```

### Reconstruir Containers
```bash
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up
```

### Ver Logs da Aplicação
```bash
sudo docker-compose logs -f web
```

## 🚪 Comandos Úteis

```bash
# Executar em segundo plano
sudo docker-compose up -d

# Parar containers
sudo docker-compose down

# Comandos Django no container
sudo docker-compose exec web python manage.py createsuperuser
sudo docker-compose exec web python manage.py showmigrations
```

## ⚙️ Configurações Técnicas

- **Banco de Dados**: PostgreSQL com migrações automáticas
- **Autenticação**: JWT + Basic Authentication
- **Upload**: Máximo 50MB, tipos MIME validados
- **Criptografia**: AES-256 para dados sensíveis
- **Email**: SMTP configurado para recuperação de senha

---
