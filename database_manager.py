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
            
            if usuario_id == 0:
                print(f"Usuário '{usuario}' ou email '{email}' já existe. Não é possível criar novo cliente.")
                return None

            cursor.execute(
                "INSERT IGNORE INTO cliente (usuario_id, nome_completo, email, telefone, cpf) VALUES (%s, %s, %s, %s, %s)",
                (usuario_id, nome_completo, email, telefone, cpf)
            )
            cliente_id = cursor.lastrowid
            self.connection.commit()
            return cliente_id
        except mysql.connector.Error as e:
            print(f"Erro ao criar cliente: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    # -------------------- RESTAURANTE --------------------
    def create_restaurant(self, usuario, email, senha, nome, telefone, tipo_culinaria, endereco, taxa_entrega, tempo_estimado):
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
                """INSERT INTO restaurante 
                (usuario_id, id_end_rest, nome, telefone, tipo_culinaria, taxa_entrega, tempo_entrega_estimado) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (usuario_id, id_end_rest, nome, telefone, tipo_culinaria, taxa_entrega, tempo_estimado)
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
    def create_order(self, id_cliente, id_restaurante, id_forma_pagamento, endereco_id, taxa_entrega):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO pedido 
                   (id_cliente, id_restaurante, id_forma_pagamento, endereco_id, valor_total) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (id_cliente, id_restaurante, id_forma_pagamento, endereco_id, taxa_entrega)
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
                "UPDATE pedido SET status_pedido = %s WHERE id_pedido = %s",
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
                "INSERT INTO avaliacoes_restaurante (id_restaurante, id_cliente, nota, feedback) VALUES (%s, %s, %s, %s)",
                (id_restaurante, id_cliente, nota, feedback)
            )
            self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao avaliar restaurante: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    # -------------------- LOGIN --------------------
    def login_user(self, usuario, senha):
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
                SELECT 
                    u.usuario_id, u.senha, u.is_restaurante, 
                    c.cliente_id, 
                    r.id_restaurante
                FROM usuario AS u
                LEFT JOIN cliente AS c ON u.usuario_id = c.usuario_id
                LEFT JOIN restaurante AS r ON u.usuario_id = r.usuario_id
                WHERE u.usuario = %s
            """
            cursor.execute(query, (usuario,))
            user_data = cursor.fetchone()
            
            if user_data and user_data['senha'] == senha:
                return {
                    'usuario_id': user_data['usuario_id'],
                    'is_restaurante': user_data['is_restaurante'],
                    'cliente_id': user_data['cliente_id'],
                    'restaurante_id': user_data['id_restaurante']
                }
            else:
                return None
        except mysql.connector.Error as e:
            print(f"Erro durante o login: {e}")
            return None
        finally:
            cursor.close()

    # -------------------- CARDÁPIO E CONSULTAS --------------------
    def add_dish_category(self, id_restaurante, nome_categoria):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO categoria_pratos (id_restaurante, nome_categoria) VALUES (%s, %s)",
                (id_restaurante, nome_categoria)
            )
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar categoria de prato: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def add_dish(self, categoria_id, nome_prato, descricao, preco):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO pratos (categoria_id, nome_prato, descricao, preco) VALUES (%s, %s, %s, %s)",
                (categoria_id, nome_prato, descricao, preco)
            )
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar prato: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def get_all_restaurants(self):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_restaurante, nome, tipo_culinaria, taxa_entrega, tempo_entrega_estimado FROM restaurante")
            restaurants = cursor.fetchall()
            return restaurants
        except mysql.connector.Error as e:
            print(f"Erro ao buscar restaurantes: {e}")
            return []
        finally:
            cursor.close()

    def get_restaurant_menu(self, id_restaurante):
        """Busca o cardápio completo de um restaurante, organizado por categoria."""
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Esta query busca todos os pratos e os ordena pela categoria
            query = """
                SELECT 
                    cp.nome_categoria,
                    p.id_prato,
                    p.nome_prato,
                    p.descricao,
                    p.preco,
                    p.status_disp -- ESTA É A LINHA QUE FALTAVA
                FROM pratos AS p
                JOIN categoria_pratos AS cp ON p.categoria_id = cp.categoria_id
                WHERE cp.id_restaurante = %s
                ORDER BY cp.nome_categoria, p.nome_prato;
            """
            cursor.execute(query, (id_restaurante,))
            menu_items = cursor.fetchall()
            
            # Organiza os pratos em um dicionário de categorias
            menu = {}
            for item in menu_items:
                categoria = item['nome_categoria']
                if categoria not in menu:
                    menu[categoria] = []
                menu[categoria].append(item)
            return menu
        except mysql.connector.Error as e:
            print(f"Erro ao buscar o cardápio: {e}")
            return {}
        finally:
            cursor.close()
    
    def get_orders_for_restaurant(self, id_restaurante):
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
                SELECT p.id_pedido, p.dataHora, p.status_pedido, p.valor_total, c.nome_completo 
                FROM pedido AS p
                JOIN cliente AS c ON p.id_cliente = c.cliente_id
                WHERE p.id_restaurante = %s 
                ORDER BY p.dataHora DESC;
            """
            cursor.execute(query, (id_restaurante,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar pedidos do restaurante: {e}")
            return []
        finally:
            cursor.close()

    def get_orders_for_client(self, id_cliente):
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
                SELECT p.id_pedido, p.dataHora, p.status_pedido, p.valor_total, r.nome as nome_restaurante 
                FROM pedido AS p
                JOIN restaurante AS r ON p.id_restaurante = r.id_restaurante
                WHERE p.id_cliente = %s 
                ORDER BY p.dataHora DESC;
            """
            cursor.execute(query, (id_cliente,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar pedidos do cliente: {e}")
            return []
        finally:
            cursor.close()

    def get_payment_methods(self):
        """Busca todas as formas de pagamento disponíveis."""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_forma_pagamento, descricao AS formaPag FROM forma_pagamento")
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar formas de pagamento: {e}")
            return []
        finally:
            cursor.close()

    def get_client_addresses(self, cliente_id):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT endereco_id, rua, num, bairro FROM enderecos_entrega WHERE cliente_id = %s", (cliente_id,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar endereços: {e}")
            return []
        finally:
            cursor.close()

    def add_client_address(self, cliente_id, rua, num, bairro, cidade, estado, cep):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO enderecos_entrega 
                    (cliente_id, rua, num, bairro, cidade, estado, cep) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (cliente_id, rua, num, bairro, cidade, estado, cep)
            )
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar endereço: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()
    def get_restaurant_categories(self, id_restaurante):
        """Busca todas as categorias de pratos de um restaurante."""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT categoria_id, nome_categoria FROM categoria_pratos WHERE id_restaurante = %s", (id_restaurante,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar categorias: {e}")
            return []
        finally:
            cursor.close()

    def get_dish_details(self, id_prato):
        """Busca os detalhes de um prato específico."""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_prato, nome_prato, descricao, preco, status_disp FROM pratos WHERE id_prato = %s", (id_prato,))
            return cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar detalhes do prato: {e}")
            return None
        finally:
            cursor.close()

    def edit_dish(self, id_prato, nome, descricao, preco):
        """Atualiza as informações de um prato existente."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "UPDATE pratos SET nome_prato = %s, descricao = %s, preco = %s WHERE id_prato = %s",
                (nome, descricao, preco, id_prato)
            )
            self.connection.commit()
            return True
        except mysql.connector.Error as e:
            print(f"Erro ao editar o prato: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def update_dish_availability(self, id_prato, is_available):
        """Altera o status de disponibilidade de um prato."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "UPDATE pratos SET status_disp = %s WHERE id_prato = %s",
                (is_available, id_prato)
            )
            self.connection.commit()
            return True
        except mysql.connector.Error as e:
            print(f"Erro ao alterar disponibilidade do prato: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    # -------------------- FECHAR CONEXÃO --------------------
    def close(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    def __del__(self):
        self.close()