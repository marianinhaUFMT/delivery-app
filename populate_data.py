import mysql.connector
import sys

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        try:
            self.connection = mysql.connector.connect(option_files="my.cnf")
            self.cursor = self.connection.cursor()
            print("arquivo de configuração único")
            print(f'ID da conexão con: {self.connection.connection_id}')
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL Database: {e}")
            sys.exit(1)

    def populate_clients(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, FALSE)", ("client1", "client1@email.com", "password1"))
                usuario_id = cursor.lastrowid
                cursor.execute("INSERT INTO cliente (usuario_id, nome_completo, email, telefone, cpf) VALUES (%s, %s, %s, %s, %s)", 
                             (usuario_id, "Client One", "client1@email.com", "123456789", "12345678901"))
                self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Error populating clients: {e}")
            self.connection.rollback()

    def populate_restaurants(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, TRUE)", ("rest1", "rest1@email.com", "password1"))
                usuario_id = cursor.lastrowid
                cursor.execute("INSERT INTO enderecos_restaurante (rua, num, bairro, cidade, estado, cep) VALUES (%s, %s, %s, %s, %s, %s)", 
                             ("Rua Exemplo", "123", "Centro", "São Paulo", "SP", "01000-000"))
                id_end_rest = cursor.lastrowid
                cursor.execute("INSERT INTO restaurante (usuario_id, id_end_rest, nome, telefone, tipo_culinaria) VALUES (%s, %s, %s, %s, %s)", 
                             (usuario_id, id_end_rest, "Restaurant One", "987654321", "Italian"))
                self.connection.commit()
                cursor.execute("SELECT LAST_INSERT_ID()")
                return cursor.fetchone()[0]
        except mysql.connector.Error as e:
            print(f"Error populating restaurants: {e}")
            self.connection.rollback()
            return None

    def populate_schedules(self, rest_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO horarios_funcionamento_restaurante (id_restaurante, dia_semana, horario_abertura, horario_fechamento) VALUES (%s, %s, %s, %s)", 
                             (rest_id, "Segunda", "09:00:00", "21:00:00"))
                self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Error populating schedules: {e}")
            self.connection.rollback()

    def populate_menu(self, rest_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO categoria_pratos (id_restaurante, nome_categoria) VALUES (%s, 'Pratos Principais')", (rest_id,))
                cursor.execute("SELECT LAST_INSERT_ID()")
                categoria_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO pratos (categoria_id, nome_prato, descricao, preco) VALUES (%s, 'Pizza Margherita', 'Pizza com queijo e manjericão', 25.50)", (categoria_id,))
                self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Error populating menu: {e}")
            self.connection.rollback()

    def populate_payment_methods(self):
        """Adiciona as formas de pagamento padrão na tabela."""
        try:
            with self.connection.cursor() as cursor:
                # Usamos INSERT IGNORE para não dar erro se os dados já existirem
                payment_methods = [('Dinheiro',), ('Pix',), ('Cartão de Crédito',), ('Cartão de Débito',)]
                query = "INSERT IGNORE INTO forma_pagamento (descricao) VALUES (%s)"
                cursor.executemany(query, payment_methods)
                self.connection.commit()
                print("Formas de pagamento populadas com sucesso.")
        except mysql.connector.Error as e:
            print(f"Erro ao popular formas de pagamento: {e}")
            self.connection.rollback()

    def close(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    def __del__(self):
        self.close()

if __name__ == "__main__":
    db = DatabaseManager()
    try:
        # Adicione a nova chamada aqui
        db.populate_payment_methods()

        db.populate_clients()
        rest_id = db.populate_restaurants()
        if rest_id:
            db.populate_schedules(rest_id)
            db.populate_menu(rest_id)
    finally:
        db.close()