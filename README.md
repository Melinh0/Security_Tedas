# Security TEDAS 

## Descrição do Projeto
Esta API fornece um sistema seguro para gerenciamento de usuários, pacientes e exames de tomografia, com controle de acesso baseado em roles e criptografia de dados sensíveis.

## Pré-requisitos
- Docker
- Docker Compose

## Passo a Passo para Execução com Docker

### 1. Clone o repositório
```bash
git clone https://github.com/Melinh0/Security_Tedas.git
cd Security_Tedas
```

### 2. Execute o docker-compose para construir e iniciar os containers
```bash
sudo docker-compose up --build
```

### 3. Aguarde a inicialização
Aguarde até que os containers estejam rodando. Você verá mensagens indicando que:
- O banco de dados PostgreSQL está pronto
- As migrações do Django foram aplicadas
- O servidor está ouvindo na porta 8000

### 4. Acesse a documentação interativa (Swagger)
Abra seu navegador e acesse:
```
http://localhost:8000/swagger/
```

### 5. Acesse o painel administrativo (Opcional)
Para acessar o painel administrativo do Django:
```
http://localhost:8000/admin/
```

Credenciais padrão do admin:
- Usuário: `admin`
- Senha: `admin`

## Estrutura de Containers
O docker-compose cria dois serviços:
1. **db**: Banco de dados PostgreSQL na porta 5434
2. **web**: Aplicação Django na porta 8000

## Comandos Úteis

### Parar os containers
```bash
sudo docker-compose down
```

### Executar em segundo plano
```bash
sudo docker-compose up -d
```

### Ver logs
```bash
sudo docker-compose logs -f
```

### Executar comandos no container
```bash
sudo docker-compose exec web python manage.py createsuperuser
```

## Solução de Problemas Comuns

### Porta já em uso
Se as portas 8000 ou 5434 estiverem em uso, altere as configurações no arquivo `docker-compose.yml`.

### Erro de permissão
Se encontrar problemas de permissão com o Docker, execute:
```bash
sudo chmod 666 /var/run/docker.sock
```

### Reconstruir containers
Se houver problemas com dependências, reconstrua os containers:
```bash
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up
```

## Variáveis de Ambiente
O projeto utiliza as seguintes variáveis de ambiente configuradas no docker-compose.yml:
- `DB_NAME`: Nome do banco de dados
- `DB_USER`: Usuário do banco de dados
- `DB_PASSWORD`: Senha do banco de dados
- `DB_HOST`: Host do banco de dados
- `DB_PORT`: Porta do banco de dados
- `SECRET_KEY`: Chave secreta do Django
- `DEBUG`: Modo debug (True/False)

## Funcionalidades da API
- Autenticação JWT
- Gerenciamento de usuários com diferentes roles (admin, profissional de saúde, pesquisador)
- CRUD de pacientes
- Upload e gestão de exames de tomografia
- Sistema de auditoria e logs
- Recuperação segura de senha

Para mais detalhes sobre os endpoints disponíveis, consulte a documentação Swagger em http://localhost:8000/swagger/