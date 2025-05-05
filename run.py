# run.py

from app import create_app, db

app = create_app()  # Criar o aplicativo

if __name__ == "__main__":
    with app.app_context():  # Garantir que o contexto da aplicação é criado
        db.create_all()  # Criar todas as tabelas no banco de dados, se necessário
    app.run(debug=True)  # Rodar a aplicação
