# Security_Tedas

Protótipos para apoiar a implementação de medidas de segurança para a equipe de desenvolvimento.

## Configuração do Ambiente Virtual e Execução do Projeto

Siga os passos abaixo para criar um ambiente virtual, instalar as dependências e executar o projeto.

### 1. Criação do Ambiente Virtual
1. **Crie o ambiente virtual:**
   ```bash
   python -m venv venv
   ```
2. **Ative o ambiente virtual:**
   - No Windows:
     ```bash
     venv\Scripts\activate
     ```
   - No macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
3. **Verifique se o ambiente virtual está ativo:**
   ```bash
   which python
   ```
   O caminho deve apontar para a pasta `venv`.

### 2. Instalação das Dependências
1. **Instale as dependências do projeto:**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Execução do Projeto
1. **Inicie o servidor Flask:**
   ```bash
   python app.py
   ```
2. **Acesse a aplicação:**
   No navegador, acesse:
   ```
   http://127.0.0.1:5000
   ```

   Exemplos de teste:
   - **Login:**
     ```bash
     curl -X POST -u alice:senha_alice http://127.0.0.1:5000/login
     ```
   - **Acesso à rota pública:**
     ```bash
     curl http://127.0.0.1:5000/public
     ```
   - **Acesso à rota de usuário:**
     ```bash
     curl -H "Authorization: <TOKEN>" http://127.0.0.1:5000/user
     ```
   - **Acesso à rota de admin:**
     ```bash
     curl -H "Authorization: <TOKEN>" http://127.0.0.1:5000/admin
     ```

### 4. Desativar o Ambiente Virtual (Opcional)
Quando terminar de trabalhar no projeto, você pode desativar o ambiente virtual:
```bash
deactivate
```

Agora seu projeto está configurado e pronto para rodar! Se precisar de mais alguma coisa, é só pedir. 🚀

