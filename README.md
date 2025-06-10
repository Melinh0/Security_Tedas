# Security API - Documentação

Esta API fornece autenticação e gerenciamento de usuários com dois tipos de perfis: **admin** e **user**.
Implementa JWT para autenticação e Flask-Mail para recuperação de senha.

---

## ✅ Pré-requisitos

* Python 3.7+
* pip (gerenciador de pacotes Python)
* Serviço de email (Gmail usado por padrão)

---

## ⚙️ Configuração do Ambiente

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 2. Crie um ambiente virtual

```bash
python3 -m venv venv
```

### 3. Ative o ambiente virtual

Linux/macOS:

```bash
source venv/bin/activate
```

Windows (PowerShell):

```bash
.\venv\Scripts\activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

**`requirements.txt` deve conter:**

```
Flask
Flask-JWT-Extended
Flask-SQLAlchemy
Flask-Mail
Flasgger
python-dotenv
```

---

## 🔐 Configuração

### 1. Configuração do Banco de Dados

Por padrão, usa SQLite (cria `app.db` automaticamente).

Para usar outro banco, edite `app/config.py`:

```python
SQLALCHEMY_DATABASE_URI = "postgresql://user:password@localhost/dbname"
```

---

## ▶️ Executando a API

```bash
python run.py
```

A API estará disponível em:
[http://localhost:5000](http://localhost:5000)

---

## 📚 Documentação da API (Swagger)

Acesse:
[http://localhost:5000/apidocs](http://localhost:5000/apidocs)

---

## 👤 Usuários Padrão

Criados na inicialização:

**Admin**

* Username: admin
* Password: admin
* Email: [admin@example.com](mailto:admin@example.com)

**User**

* Username: user
* Password: user
* Email: [user@example.com](mailto:user@example.com)

---

## 🔗 Endpoints Principais

### 🔒 Autenticação

* `POST /login` – Login (admin ou user)
* `POST /forgot-password` – Solicita recuperação de senha
* `POST /reset-password` – Redefinir senha com token

### 👑 Administradores (token admin)

* `GET /admins` – Lista todos admins
* `POST /admins` – Cria novo admin
* `PUT /admins/me` – Atualiza o próprio admin

### 👥 Usuários

* `GET /users` (admin) – Lista usuários
* `POST /users` (admin) – Cria usuário
* `PUT /users/me` (user/admin) – Atualiza o próprio usuário

---

## 🧪 Testando a API

### 1. Login (obter token)

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin", "password":"admin"}'
```

### 2. Criar novo usuário (como admin)

```bash
curl -X POST http://localhost:5000/users \
  -H "Authorization: Bearer <SEU_TOKEN_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"username":"novo_user", "password":"senha123", "email":"novo@exemplo.com"}'
```

### 3. Atualizar próprio perfil (como user)

```bash
curl -X PUT http://localhost:5000/users/me \
  -H "Authorization: Bearer <TOKEN_DO_USER>" \
  -H "Content-Type: application/json" \
  -d '{"email":"novo_email@exemplo.com"}'
```

---

## 🔁 Fluxo de Recuperação de Senha

1. `POST /forgot-password` com o email
2. Usuário recebe um email com token
3. `POST /reset-password` com:

   * Email
   * Token recebido
   * Nova senha

---

## 📁 Estrutura de Arquivos

```
app/
├── controllers/
│   └── admin.controller.py
├── models/
│   └── admin.py
├── utils/
│   └── decorators.py
├── swagger/
    └── admin_swagger.yaml
├── routes.py
├── __init__.py
├── config.py

run.py
requirements.txt
venv
```

---

## ❗ Solução de Problemas Comuns

**Erro ao enviar email:**

* Verifique as credenciais no `venv`
* Verifique configurações de segurança do Gmail

Para debug:

```python
# app/config.py
MAIL_SUPPRESS_SEND = False
MAIL_DEBUG = True
```

**Erros de banco de dados:**

* Delete `app.db`
* Reinicie a aplicação

**Erros de autenticação:**

* Confirme se o token está no header:
  `Authorization: Bearer <token>`
* Tokens expiram após 1 hora (padrão)

---

## 🤝 Contribuição

1. Faça um fork
2. Crie uma branch:

```bash
git checkout -b feature/minha-feature
```

3. Faça commit:

```bash
git commit -am 'Add minha feature'
```

4. Envie para o GitHub:

```bash
git push origin feature/minha-feature
```

5. Abra um Pull Request

---
