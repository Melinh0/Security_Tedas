# SecurityAPI

API Gateway segura construída com **Django Rest Framework** e **PostgreSQL**, com RBAC, autenticação JWT, criptografia de dados pessoais (PII) em repouso, auditoria e containerização com Docker.

## Stack

- Python 3.12 + Django 6.1 + Django REST Framework
- PostgreSQL 16 (produção/Docker) · SQLite (desenvolvimento local)
- JWT (simplejwt) com rotação e blacklist de refresh tokens
- Redis para rate limiting distribuído
- Nginx com TLS/HTTPS como reverse proxy
- Docker + Docker Compose

## Funcionalidades de segurança

| Área | Implementação |
|------|---------------|
| RBAC | Perfis `admin`, `user` e `public` com permissões por endpoint (`api/permissions.py`) |
| JWT | Access token de 30 min, refresh de 7 dias com rotação e blacklist (logout revoga o token) |
| Criptografia de PII | Username, email e role cifrados com Fernet (AES-128-CBC + HMAC); lookup por blind index HMAC-SHA256 (`api/encryption.py`) |
| OWASP – validação de entrada | Serializadores DRF validam todos os campos; senhas passam pelos validadores do Django; registro não permite auto-promoção a `admin` |
| OWASP – rate limiting | DRF throttling: login 5/min, registro 3/min, refresh 10/min, reveal 10/min + limite global por IP/usuário; Redis no Docker |
| OWASP – sanitização de upload | Endpoint de avatar valida formato real da imagem (Pillow), limita tamanho/dimensões, re-serializa a imagem e usa nome aleatório (`api/upload.py`) |
| TLS/HTTPS | Config Django para HTTPS obrigatório (HSTS, cookies secure) + Nginx com TLS 1.2/1.3 e redirect HTTP→HTTPS |
| Security headers | CSP, X-Frame-Options DENY, nosniff, Referrer-Policy, Permissions-Policy (`config/middleware.py`) |
| Audit logs | Middleware registra todo acesso à API; eventos explícitos de login (sucesso/falha), registro, logout, criação de usuário, upload e **revelação de PII** (`api/audit.py`) |
| Conta de usuário | Backend de autenticação próprio com comparação em tempo constante para usernames cifrados |

## Requisitos

- Python 3.12+
- Docker + Docker Compose (apenas para subir com PostgreSQL/Redis/Nginx)

## Execução local (desenvolvimento)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
python manage.py generate_encryption_key   # cole o resultado em ENCRYPTION_KEY
```

Prepare o banco e inicie:

```bash
python manage.py migrate
python manage.py runserver
```

Sem `DATABASE_URL` o projeto usa SQLite local (só para desenvolvimento).

## Execução com Docker (PostgreSQL + TLS)

1. Preencha o `.env` (copie do `.env.example`): `DJANGO_SECRET_KEY`, `ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `ALLOWED_HOSTS`.
2. Gere os certificados TLS auto-assinados (Linux/macOS com OpenSSL; no Windows use o WSL ou o Git Bash):

```bash
sh scripts/generate-certs.sh
```

3. Suba a stack:

```bash
docker compose up -d --build
```

4. Acesse:

- `https://localhost/api/docs/` — documentação Swagger
- `https://localhost/admin/` — painel Django
- `http://localhost` redireciona automaticamente para HTTPS

### Políticas de acesso do Docker

- Container da aplicação roda com usuário **não-root** e `cap_drop: ALL`
- Banco e Redis em rede interna (`backend: internal: true`), sem portas expostas ao host
- Tráfego externo só passa pelo Nginx (TLS), que aplica rate limit adicional por IP
- Segredos vêm do `.env` (nunca entram na imagem; `.dockerignore` bloqueia `.env` e chaves)
- Logs de auditoria vão para o banco + stdout do container (rotacionáveis via driver de logging)

## Criptografia dos registros (chave em posse do admin)

Username, email e role são gravados **cifrados** no banco. A chave Fernet (`ENCRYPTION_KEY`) fica apenas no `.env` do admin — quem não tem a chave não lê os dados.

```bash
# gerar nova chave (guarde como segredo)
python manage.py generate_encryption_key

# criar admin com PII cifrada
python manage.py create_admin --username yagoadmin --password SuaSenhaForte123

# admin: descriptografar os dados de um usuário
python manage.py decrypt_user --username yagoadmin
python manage.py decrypt_user --username yagoadmin --field email
```

Via API, o admin também pode consultar dados decifrados em `GET /api/users/<id>/reveal/` — cada consulta é registrada no audit log (`REVEAL_PII`).

**Importante:** sem a `ENCRYPTION_KEY` os dados pessoais são irrecuperáveis. Guarde-a fora do repositório e faça backup seguro.

## Endpoints

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| POST | `/api/auth/register/` | Cadastra usuário (perfis `user`/`public`) | Público · 3/min |
| POST | `/api/auth/login/` | Retorna tokens JWT | Público · 5/min |
| POST | `/api/auth/refresh/` | Rotaciona o refresh token | Público · 10/min |
| POST | `/api/auth/logout/` | Revoga o refresh token | Autenticado |
| GET | `/api/users/` | Lista usuários (dados decifrados) | `admin` |
| POST | `/api/users/` | Cria usuário (inclusive `admin`) | `admin` |
| GET | `/api/users/<id>/reveal/` | Revela PII de um usuário (auditado) | `admin` · 10/min |
| GET | `/api/public/` | Lista usuários com perfil `public` | Autenticado |
| GET | `/api/visible-users/` | Lista usuários que não são `admin` | `admin`, `user` |
| GET | `/api/me/` | Dados do próprio usuário | Autenticado |
| PATCH | `/api/me/` | Atualiza o próprio email | Autenticado |
| GET | `/api/audit-logs/` | Logs de auditoria (filtros `action`, `user_id`) | `admin` |
| POST | `/api/upload/avatar/` | Upload de avatar sanitizado · 10/min | Autenticado |
| GET | `/api/docs/` | Documentação Swagger | — |
| GET | `/api/schema/` | Esquema OpenAPI | — |

### Exemplo de uso

```bash
# registrar
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "joao", "password": "SenhaForte123", "role": "user"}'

# logar
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "joao", "password": "SenhaForte123"}'

# usar o token
curl http://127.0.0.1:8000/api/me/ \
  -H "Authorization: Bearer <access_token>"
```

## Testes

```bash
python manage.py test api
```

17 testes cobrindo: criptografia em repouso, login com username cifrado, RBAC por perfil, audit logs (inclusive `REVEAL_PII` e `LOGIN_FAILED`), rate limiting no login e sanitização de upload.

## Estrutura do projeto

```
├── config/            # settings, urls, middlewares (headers de segurança)
├── api/
│   ├── encryption.py  # Fernet + blind index (HMAC)
│   ├── backends.py    # autenticação com username cifrado
│   ├── permissions.py # RBAC
│   ├── audit.py       # gravação de eventos de auditoria
│   ├── middleware.py  # auditoria de todo acesso à API
│   ├── upload.py      # sanitização de imagens
│   └── management/    # generate_encryption_key, decrypt_user, create_admin
├── nginx/nginx.conf   # TLS, HSTS, rate limit por IP
├── scripts/           # geração de certificados
├── docker-compose.yml # db + redis + web + nginx (redes segmentadas)
└── Dockerfile         # imagem non-root
```
