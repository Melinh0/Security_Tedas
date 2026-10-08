# SecurityAPI

API REST desenvolvida em Flask com autenticação JWT, controle de perfis (roles) e documentação automática via Swagger (Flasgger).

## Requisitos

- Python 3.8 ou superior

## Instalação

Crie um ambiente virtual e instale as dependências:

```bash
python -m venv venv
```

Ative o ambiente virtual:

```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Execução

```bash
python run.py
```

A API ficará disponível em `http://127.0.0.1:5000`.

## Documentação (Swagger)

Com a API executando, acesse:

```
http://127.0.0.1:5000/apidocs/
```

## Endpoints

| Método | Rota                 | Descrição                                  | Acesso         |
|--------|----------------------|--------------------------------------------|----------------|
| POST   | `/auth/register`     | Cadastra um novo usuário                   | Público        |
| POST   | `/auth/login`        | Autentica e retorna o token JWT            | Público        |
| GET    | `/auth/protected`    | Exemplo de rota protegida                  | Autenticado    |
| GET    | `/api/users`         | Lista todos os usuários                    | `admin`        |
| GET    | `/api/public`        | Lista usuários com perfil `public`         | Autenticado    |
| GET    | `/api/visible-users` | Lista usuários que não são `admin`         | `admin`, `user`|

## Exemplo de uso

1. Cadastre um usuário:

```bash
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "yago", "password": "admin", "role": "admin"}'
```

2. Faça login para obter o token:

```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "yago", "password": "admin"}'
```

3. Use o token para acessar rotas protegidas:

```bash
curl http://127.0.0.1:5000/api/users \
  -H "Authorization: Bearer <access_token>"
```

## Usuário padrão

Ao iniciar, a API cria automaticamente o usuário `yago` com a senha `admin` caso ainda não exista.
