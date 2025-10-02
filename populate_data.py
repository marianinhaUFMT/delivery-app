import mysql.connector
import sys

class DatabaseManager:
    """
    Gerencia a conexão e a população de dados no banco de dados.
    """
    def __init__(self):
        self.connection = None
        self.cursor = None
        try:
            # Conecta ao banco de dados usando o arquivo de configuração
            self.connection = mysql.connector.connect(option_files="my.cnf")
            self.cursor = self.connection.cursor()
            print("Conexão com o banco de dados bem-sucedida.")
            print(f'ID da conexão: {self.connection.connection_id}')
        except mysql.connector.Error as e:
            print(f"Erro ao conectar com o MySQL: {e}")
            sys.exit(1)

    def populate_clients(self, clients_data):
        """
        Popula a tabela de clientes a partir de uma lista de dicionários.
        """
        print("\n--- Populando Clientes ---")
        try:
            with self.connection.cursor() as cursor:
                for client in clients_data:
                    # 1. Inserir na tabela de usuários
                    sql_usuario = "INSERT INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, FALSE)"
                    val_usuario = (client['usuario'], client['email'], client['senha'])
                    cursor.execute(sql_usuario, val_usuario)
                    usuario_id = cursor.lastrowid

                    # 2. Inserir na tabela de clientes
                    sql_cliente = "INSERT INTO cliente (usuario_id, nome_completo, email, telefone, cpf) VALUES (%s, %s, %s, %s, %s)"
                    val_cliente = (usuario_id, client['nome_completo'], client['email'], client['telefone'], client['cpf'])
                    cursor.execute(sql_cliente, val_cliente)
                    print(f"Cliente '{client['nome_completo']}' inserido com sucesso.")
                
                self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao popular clientes: {e}")
            self.connection.rollback()

    def populate_restaurants_complete(self, restaurants_data):
        """
        Popula a tabela de restaurantes e suas tabelas relacionadas (endereço, horários, cardápio).
        """
        print("\n--- Populando Restaurantes e Cardápios ---")
        try:
            with self.connection.cursor() as cursor:
                for rest in restaurants_data:
                    # 1. Inserir na tabela de usuários
                    sql_usuario = "INSERT INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, TRUE)"
                    val_usuario = (rest['usuario'], rest['email'], rest['senha'])
                    cursor.execute(sql_usuario, val_usuario)
                    usuario_id = cursor.lastrowid

                    # 2. Inserir endereço do restaurante
                    sql_endereco = "INSERT INTO enderecos_restaurante (rua, num, bairro, cidade, estado, cep) VALUES (%s, %s, %s, %s, %s, %s)"
                    val_endereco = (rest['endereco']['rua'], rest['endereco']['num'], rest['endereco']['bairro'], rest['endereco']['cidade'], rest['endereco']['estado'], rest['endereco']['cep'])
                    cursor.execute(sql_endereco, val_endereco)
                    id_end_rest = cursor.lastrowid

                    # 3. Inserir na tabela de restaurante
                    sql_restaurante = "INSERT INTO restaurante (usuario_id, id_end_rest, nome, telefone, tipo_culinaria) VALUES (%s, %s, %s, %s, %s)"
                    val_restaurante = (usuario_id, id_end_rest, rest['nome'], rest['telefone'], rest['tipo_culinaria'])
                    cursor.execute(sql_restaurante, val_restaurante)
                    restaurante_id = cursor.lastrowid
                    print(f"\nRestaurante '{rest['nome']}' inserido com sucesso (ID: {restaurante_id}).")

                    # 4. Inserir horários de funcionamento
                    sql_horario = "INSERT INTO horarios_funcionamento_restaurante (id_restaurante, dia_semana, horario_abertura, horario_fechamento) VALUES (%s, %s, %s, %s)"
                    for horario in rest['horarios']:
                        val_horario = (restaurante_id, horario['dia_semana'], horario['abertura'], horario['fechamento'])
                        cursor.execute(sql_horario, val_horario)
                    print(f"-> Horários de funcionamento de '{rest['nome']}' inseridos.")

                    # 5. Inserir cardápio (categorias e pratos)
                    for categoria in rest['cardapio']:
                        sql_categoria = "INSERT INTO categoria_pratos (id_restaurante, nome_categoria) VALUES (%s, %s)"
                        cursor.execute(sql_categoria, (restaurante_id, categoria['nome_categoria']))
                        categoria_id = cursor.lastrowid
                        
                        sql_prato = "INSERT INTO pratos (categoria_id, nome_prato, descricao, preco) VALUES (%s, %s, %s, %s)"
                        for prato in categoria['pratos']:
                            val_prato = (categoria_id, prato['nome'], prato['descricao'], prato['preco'])
                            cursor.execute(sql_prato, val_prato)
                    print(f"-> Cardápio de '{rest['nome']}' inserido.")
                
                self.connection.commit()

        except mysql.connector.Error as e:
            print(f"Erro ao popular restaurantes: {e}")
            self.connection.rollback()

    def populate_payment_methods(self):
        """
        Adiciona as formas de pagamento padrão na tabela.
        """
        print("\n--- Populando Formas de Pagamento ---")
        try:
            with self.connection.cursor() as cursor:
                payment_methods = [('Dinheiro',), ('Pix',), ('Cartão de Crédito',), ('Cartão de Débito',)]
                query = "INSERT IGNORE INTO forma_pagamento (descricao) VALUES (%s)"
                cursor.executemany(query, payment_methods)
                self.connection.commit()
                print("Formas de pagamento populadas com sucesso.")
        except mysql.connector.Error as e:
            print(f"Erro ao popular formas de pagamento: {e}")
            self.connection.rollback()

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("\nConexão com o banco de dados fechada.")

    def __del__(self):
        self.close()

if __name__ == "__main__":
    
    # --- DADOS PARA POPULAR ---

    clients_to_add = [
        {
            "usuario": "ana.silva", "email": "ana.silva@email.com", "senha": "senha123",
            "nome_completo": "Ana Silva", "telefone": "11987654321", "cpf": "11122233344"
        },
        {
            "usuario": "carlos.souza", "email": "carlos.souza@email.com", "senha": "senha456",
            "nome_completo": "Carlos Souza", "telefone": "21912345678", "cpf": "55566677788"
        }
    ]

    restaurants_to_add = [
        {
            "usuario": "bellanapoli", "email": "contato@bellanapoli.com", "senha": "pizzas",
            "nome": "Bella Napoli Pizzaria", "telefone": "1144556677", "tipo_culinaria": "Italiana",
            "endereco": {"rua": "Rua das Pizzas", "num": "10", "bairro": "Centro", "cidade": "São Paulo", "estado": "SP", "cep": "01001-000"},
            "horarios": [
                {"dia_semana": "Terça", "abertura": "18:00:00", "fechamento": "23:00:00"},
                {"dia_semana": "Quarta", "abertura": "18:00:00", "fechamento": "23:00:00"},
                {"dia_semana": "Quinta", "abertura": "18:00:00", "fechamento": "23:00:00"},
                {"dia_semana": "Sexta", "abertura": "18:00:00", "fechamento": "00:00:00"},
                {"dia_semana": "Sábado", "abertura": "18:00:00", "fechamento": "00:00:00"},
            ],
            "cardapio": [
                {
                    "nome_categoria": "Pizzas Tradicionais",
                    "pratos": [
                        {"nome": "Pizza Margherita", "descricao": "Molho de tomate, mussarela e manjericão fresco.", "preco": 35.50},
                        {"nome": "Pizza Calabresa", "descricao": "Molho de tomate, mussarela, calabresa e cebola.", "preco": 38.00},
                    ]
                },
                {
                    "nome_categoria": "Bebidas",
                    "pratos": [
                        {"nome": "Refrigerante Lata", "descricao": "Coca-cola, Guaraná ou Soda.", "preco": 6.00},
                        {"nome": "Água Mineral", "descricao": "Com ou sem gás.", "preco": 4.00},
                    ]
                }
            ]
        },
        {
            "usuario": "sushizen", "email": "contato@sushizen.jp", "senha": "sushi",
            "nome": "Sushi Zen", "telefone": "2188776655", "tipo_culinaria": "Japonesa",
            "endereco": {"rua": "Avenida Copacabana", "num": "500", "bairro": "Copacabana", "cidade": "Rio de Janeiro", "estado": "RJ", "cep": "22020-001"},
            "horarios": [
                {"dia_semana": "Quarta", "abertura": "19:00:00", "fechamento": "23:30:00"},
                {"dia_semana": "Quinta", "abertura": "19:00:00", "fechamento": "23:30:00"},
                {"dia_semana": "Sexta", "abertura": "19:00:00", "fechamento": "01:00:00"},
                {"dia_semana": "Sábado", "abertura": "19:00:00", "fechamento": "01:00:00"},
            ],
            "cardapio": [
                {
                    "nome_categoria": "Combinados",
                    "pratos": [
                        {"nome": "Combinado Zen (20 peças)", "descricao": "Seleção do chef com sashimis e sushis variados.", "preco": 85.00},
                        {"nome": "Combinado Salmão (15 peças)", "descricao": "Sashimi, niguiri e uramaki de salmão.", "preco": 70.00},
                    ]
                }
            ]
        },
        {
            "usuario": "burgerhouse", "email": "pedido@burgerhouse.com", "senha": "bacon",
            "nome": "Burger House", "telefone": "3199887766", "tipo_culinaria": "Hamburgueria",
            "endereco": {"rua": "Rua dos Hamburguers", "num": "123", "bairro": "Savassi", "cidade": "Belo Horizonte", "estado": "MG", "cep": "30112-021"},
            "horarios": [
                {"dia_semana": "Quarta", "abertura": "17:00:00", "fechamento": "23:00:00"},
                {"dia_semana": "Quinta", "abertura": "17:00:00", "fechamento": "23:00:00"},
                {"dia_semana": "Sexta", "abertura": "17:00:00", "fechamento": "02:00:00"},
            ],
            "cardapio": [
                {
                    "nome_categoria": "Burgers",
                    "pratos": [
                        {"nome": "Classic Burger", "descricao": "Pão, carne 180g, queijo cheddar, alface, tomate e picles.", "preco": 28.00},
                        {"nome": "Bacon Explosion", "descricao": "Pão, carne 180g, dobro de queijo, muito bacon e molho especial.", "preco": 34.00},
                    ]
                }
            ]
        },
        {
            "usuario": "cantinamineira", "email": "contato@cantinamineira.com.br", "senha": "paodequeijo",
            "nome": "Cantina Mineira", "telefone": "3133221144", "tipo_culinaria": "Brasileira (Mineira)",
            "endereco": {"rua": "Praça da Liberdade", "num": "470", "bairro": "Funcionários", "cidade": "Belo Horizonte", "estado": "MG", "cep": "30140-010"},
            "horarios": [
                {"dia_semana": "Segunda", "abertura": "11:30:00", "fechamento": "15:00:00"},
                {"dia_semana": "Terça", "abertura": "11:30:00", "fechamento": "15:00:00"},
                {"dia_semana": "Quarta", "abertura": "11:30:00", "fechamento": "15:00:00"},
                {"dia_semana": "Quinta", "abertura": "11:30:00", "fechamento": "15:00:00"},
                {"dia_semana": "Sexta", "abertura": "11:30:00", "fechamento": "15:00:00"},
            ],
            "cardapio": [
                {
                    "nome_categoria": "Pratos Executivos",
                    "pratos": [
                        {"nome": "Feijão Tropeiro", "descricao": "Acompanha arroz, couve e bisteca de porco.", "preco": 45.00},
                        {"nome": "Frango com Quiabo", "descricao": "Acompanha angu e arroz branco.", "preco": 42.00},
                    ]
                }
            ]
        }
    ]

    # --- EXECUÇÃO ---
    
    db = DatabaseManager()
    try:
        # Popula as formas de pagamento
        db.populate_payment_methods()

        # Popula os clientes
        db.populate_clients(clients_to_add)
        
        # Popula os restaurantes com todos os dados relacionados
        db.populate_restaurants_complete(restaurants_to_add)

    finally:
        db.close()