# database_manager.py
import mysql.connector
import sys

class DatabaseManager:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(option_files="my.cnf")
            self.cursor = self.connection.cursor()
            print(f"Conexão MySQL aberta com sucesso! ID: {self.connection.connection_id}")
        except mysql.connector.Error as e:
            print(f"Erro ao conectar ao MySQL: {e}")
            sys.exit(1)

    # -------------------- CLIENTE --------------------
    def create_client(self, usuario, email, senha, nome_completo, telefone, cpf):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT IGNORE INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, FALSE)",
                (usuario, email, senha)
            )
            usuario_id = cursor.lastrowid
            cursor.execute(
                "INSERT IGNORE INTO cliente (usuario_id, nome_completo, email, telefone, cpf) VALUES (%s, %s, %s, %s, %s)",
                (usuario_id, nome_completo, email, telefone, cpf)
            )
            self.connection.commit()
            return usuario_id
        except mysql.connector.Error as e:
            print(f"Erro ao criar cliente: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    # -------------------- RESTAURANTE --------------------
    def create_restaurant(self, usuario, email, senha, nome, telefone, tipo_culinaria, endereco):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT IGNORE INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, TRUE)",
                (usuario, email, senha)
            )
            usuario_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO enderecos_restaurante (rua, num, bairro, cidade, estado, cep) VALUES (%s, %s, %s, %s, %s, %s)",
                (endereco['rua'], endereco['num'], endereco['bairro'], endereco['cidade'], endereco['estado'], endereco['cep'])
            )
            id_end_rest = cursor.lastrowid
            cursor.execute(
                "INSERT INTO restaurante (usuario_id, id_end_rest, nome, telefone, tipo_culinaria) VALUES (%s, %s, %s, %s, %s)",
                (usuario_id, id_end_rest, nome, telefone, tipo_culinaria)
            )
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            print(f"Erro ao criar restaurante: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    # -------------------- HORÁRIOS --------------------
    def add_schedule(self, id_restaurante, dia_semana, horario_abertura, horario_fechamento):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT IGNORE INTO horarios_funcionamento_restaurante (id_restaurante, dia_semana, horario_abertura, horario_fechamento) VALUES (%s, %s, %s, %s)",
                (id_restaurante, dia_semana, horario_abertura, horario_fechamento)
            )
            self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar horário: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    # -------------------- PEDIDOS --------------------
    def create_order(self, id_cliente, id_restaurante):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO pedido (id_cliente, id_restaurante, status, forma_pagamento, valor_total) VALUES (%s, %s, %s, %s, %s)",
                (id_cliente, id_restaurante, "Em Preparação", "Dinheiro", 0)
            )
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            print(f"Erro ao criar pedido: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def add_order_item(self, id_pedido, id_prato, qtd, preco_item, observacoes):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO item_pedido (id_pedido, id_prato, qtd, preco_item, observacoes) VALUES (%s, %s, %s, %s, %s)",
                (id_pedido, id_prato, qtd, preco_item, observacoes)
            )
            # Atualiza valor_total do pedido
            cursor.execute(
                "UPDATE pedido SET valor_total = valor_total + %s WHERE id_pedido = %s",
                (qtd * preco_item, id_pedido)
            )
            self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar item de pedido: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def update_order_status(self, id_pedido, status):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "UPDATE pedido SET status = %s WHERE id_pedido = %s",
                (status, id_pedido)
            )
            self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao atualizar status do pedido: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    # -------------------- AVALIAÇÃO --------------------
    def evaluate_restaurant(self, id_restaurante, id_cliente, nota, feedback):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO avaliacao (id_restaurante, id_cliente, nota, feedback) VALUES (%s, %s, %s, %s)",
                (id_restaurante, id_cliente, nota, feedback)
            )
            self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao avaliar restaurante: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    # -------------------- FECHAR CONEXÃO --------------------
    def close(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    def __del__(self):
        self.close()


# -------------------- TESTE --------------------
if __name__ == "__main__":
    db = DatabaseManager()
    try:
        # Cria cliente
        cliente_id = db.create_client("client1", "client1@email.com", "pass123", "Alice Silva", "11987654321", "12345678901")
        # Cria restaurante
        rest_id = db.create_restaurant("rest1", "rest1@email.com", "pass456", "Pizzaria Bella", "1133334444", "Italiana",
                                       {"rua": "Av. Paulista", "num": "1000", "bairro": "Bela Vista", "cidade": "São Paulo", "estado": "SP", "cep": "01310-000"})
        if rest_id:
            # Adiciona horários
            db.add_schedule(rest_id, "Segunda", "09:00:00", "22:00:00")
            # Cria pedido
            pedido_id = db.create_order(cliente_id, rest_id)
            # Adiciona item de pedido
            db.add_order_item(pedido_id, 1, 2, 25.50, "Sem cebola")
            # Atualiza status do pedido
            db.update_order_status(pedido_id, "Em Trânsito")
            # Avalia restaurante
            db.evaluate_restaurant(rest_id, cliente_id, 5, "Excelente!")
    finally:
        db.close()
