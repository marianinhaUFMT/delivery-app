import mysql.connector
import sys

class DatabaseManager:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(option_files="my.cnf")
            # MODIFICADO: Removido self.cursor daqui, pois cada função gerenciará o seu.
            print(f"Conexão MySQL aberta com sucesso! ID: {self.connection.connection_id}")
        except mysql.connector.Error as e:
            print(f"Erro ao conectar ao MySQL: {e}")
            sys.exit(1)

    # -------------------- CLIENTE --------------------
    # MODIFICADO: Aplicado o 'with' statement e hashing de senha
    def create_client(self, usuario, email, senha, nome_completo, telefone, cpf):
        try:
            with self.connection.cursor() as cursor:
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

    # -------------------- RESTAURANTE --------------------
    # MODIFICADO: Aplicado o 'with' statement e hashing de senha
    def create_restaurant(self, usuario, email, senha, nome, telefone, tipo_culinaria, endereco, taxa_entrega, tempo_estimado):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT IGNORE INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, TRUE)",
                    (usuario, email, senha)
                )
                usuario_id = cursor.lastrowid

                if usuario_id == 0:
                    print(f"Usuário '{usuario}' ou email '{email}' já existe. Não é possível criar novo restaurante.")
                    self.connection.rollback() # Garante que nada seja salvo se o usuário já existir
                    return None

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

    # -------------------- HORÁRIOS --------------------
    # MODIFICADO: Aplicado o 'with' statement
    def add_schedule(self, id_restaurante, dia_semana, horario_abertura, horario_fechamento):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT IGNORE INTO horarios_funcionamento_restaurante (id_restaurante, dia_semana, horario_abertura, horario_fechamento) VALUES (%s, %s, %s, %s)",
                    (id_restaurante, dia_semana, horario_abertura, horario_fechamento)
                )
                self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar horário: {e}")
            self.connection.rollback()

    # -------------------- PEDIDOS --------------------
    # MODIFICADO: Aplicado o 'with' statement
    def create_order(self, id_cliente, id_restaurante, id_forma_pagamento, endereco_id, taxa_entrega):
        try:
            with self.connection.cursor() as cursor:
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

    # MODIFICADO: Aplicado o 'with' statement
    def add_order_item(self, id_pedido, id_prato, qtd, preco_item, observacoes):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO item_pedido (id_pedido, id_prato, qtd, preco_item, observacoes) VALUES (%s, %s, %s, %s, %s)",
                    (id_pedido, id_prato, qtd, preco_item, observacoes)
                )
                self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar item de pedido: {e}")
            self.connection.rollback()

    # MODIFICADO: Aplicado o 'with' statement
    def update_order_status(self, id_pedido, status):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE pedido SET status_pedido = %s WHERE id_pedido = %s",
                    (status, id_pedido)
                )
                self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao atualizar status do pedido: {e}")
            self.connection.rollback()


    # -------------------- AVALIAÇÃO --------------------
    # MODIFICADO: Aplicado o 'with' statement
    def add_review(self, pedido_id, restaurante_id, cliente_id, nota, feedback):
        """Salva uma nova avaliação no banco de dados."""
        try:
            with self.connection.cursor() as cursor:
                # Esta query agora está correta para sua nova estrutura de tabela
                query = """
                    INSERT INTO avaliacoes_restaurante (id_pedido, id_restaurante, id_cliente, nota, feedback)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (pedido_id, restaurante_id, cliente_id, nota, feedback))
                self.connection.commit()
                return cursor.lastrowid
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar avaliação: {e}")
            self.connection.rollback()
            return None

    def mark_order_as_reviewed(self, pedido_id):
        """Marca um pedido como avaliado para evitar duplicatas."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("UPDATE pedido SET foi_avaliado = TRUE WHERE id_pedido = %s", (pedido_id,))
                self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Erro ao marcar pedido como avaliado: {e}")
            self.connection.rollback()

    def get_reviews_for_restaurant(self, restaurante_id):
        """Busca todas as avaliações de um restaurante."""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = """
                    SELECT ar.nota, ar.feedback, c.nome_completo 
                    FROM avaliacoes_restaurante AS ar
                    JOIN cliente AS c ON ar.id_cliente = c.cliente_id
                    WHERE ar.id_restaurante = %s
                    ORDER BY ar.id_avaliacao DESC
                """
                cursor.execute(query, (restaurante_id,))
                return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar avaliações: {e}")
            return []

    # -------------------- LOGIN --------------------
    # MODIFICADO: Aplicado o 'with' statement e hashing de senha
    def login_user(self, usuario, senha):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = """
                    SELECT u.usuario_id, u.senha, u.is_restaurante, c.cliente_id, r.id_restaurante
                    FROM usuario AS u
                    LEFT JOIN cliente AS c ON u.usuario_id = c.usuario_id
                    LEFT JOIN restaurante AS r ON u.usuario_id = r.usuario_id
                    WHERE u.usuario = %s
                """
                cursor.execute(query, (usuario,))
                user_data = cursor.fetchone()
                
                if user_data:
                    if user_data['senha'] == senha:
                        return {
                            'usuario_id': user_data['usuario_id'],
                            'is_restaurante': user_data['is_restaurante'],
                            'cliente_id': user_data['cliente_id'],
                            'restaurante_id': user_data['id_restaurante']
                        }
                return None
        except mysql.connector.Error as e:
            print(f"Erro durante o login: {e}")
            return None

    # -------------------- CARDÁPIO E CONSULTAS --------------------
    # MODIFICADO: Aplicado o 'with' statement
    def add_dish_category(self, id_restaurante, nome_categoria):
        try:
            with self.connection.cursor() as cursor:
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

    # MODIFICADO: Aplicado o 'with' statement
    def add_dish(self, categoria_id, nome_prato, descricao, preco):
        try:
            with self.connection.cursor() as cursor:
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

    # MODIFICADO: Aplicado o 'with' statement
    def get_all_restaurants(self):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id_restaurante, nome, tipo_culinaria, taxa_entrega, tempo_entrega_estimado FROM restaurante")
                return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar restaurantes: {e}")
            return []

    # MODIFICADO: Aplicado o 'with' statement
    def get_restaurant_menu(self, id_restaurante):
        """Busca o cardápio de um restaurante PARA O CLIENTE, trazendo apenas pratos disponíveis."""
        menu = {}
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = """
                    SELECT cp.nome_categoria, p.id_prato, p.nome_prato, p.descricao, p.preco, p.status_disp
                    FROM pratos AS p
                    JOIN categoria_pratos AS cp ON p.categoria_id = cp.categoria_id
                    WHERE cp.id_restaurante = %s AND p.status_disp = TRUE
                    ORDER BY cp.nome_categoria, p.nome_prato;
                """
                cursor.execute(query, (id_restaurante,))
                menu_items = cursor.fetchall()
                
                for item in menu_items:
                    categoria = item['nome_categoria']
                    if categoria not in menu:
                        menu[categoria] = []
                    menu[categoria].append(item)
                return menu
        except mysql.connector.Error as e:
            print(f"Erro ao buscar o cardápio: {e}")
            return {}

    # NOVO MÉTODO: Para o painel de gerenciamento do restaurante
    def get_full_restaurant_menu_for_admin(self, id_restaurante):
        """Busca o cardápio completo de um restaurante PARA O ADMIN, incluindo pratos indisponíveis."""
        menu = {}
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = """
                    SELECT cp.nome_categoria, p.id_prato, p.nome_prato, p.descricao, p.preco, p.status_disp
                    FROM pratos AS p
                    JOIN categoria_pratos AS cp ON p.categoria_id = cp.categoria_id
                    WHERE cp.id_restaurante = %s
                    ORDER BY cp.nome_categoria, p.nome_prato;
                """
                cursor.execute(query, (id_restaurante,))
                menu_items = cursor.fetchall()

                for item in menu_items:
                    categoria = item['nome_categoria']
                    if categoria not in menu:
                        menu[categoria] = []
                    menu[categoria].append(item)
                return menu
        except mysql.connector.Error as e:
            print(f"Erro ao buscar o cardápio completo para o admin: {e}")
            return {}

    # MODIFICADO: Aplicado o 'with' statement
    def get_orders_for_restaurant(self, id_restaurante):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = """
                    SELECT p.id_pedido, p.dataHora, p.status_pedido, p.valor_total, c.nome_completo 
                    FROM pedido AS p JOIN cliente AS c ON p.id_cliente = c.cliente_id
                    WHERE p.id_restaurante = %s 
                    ORDER BY p.dataHora DESC;
                """
                cursor.execute(query, (id_restaurante,))
                return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar pedidos do restaurante: {e}")
            return []

    def get_orders_for_client(self, id_cliente):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                # MODIFICADO: Adicionado 'p.id_restaurante' à consulta
                query = """
                    SELECT p.id_pedido, p.dataHora, p.status_pedido, p.valor_total, 
                        p.foi_avaliado, r.nome as nome_restaurante, p.id_restaurante
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

    # MODIFICADO: Aplicado o 'with' statement
    def get_payment_methods(self):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id_forma_pagamento, descricao AS formaPag FROM forma_pagamento")
                return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar formas de pagamento: {e}")
            return []

    # MODIFICADO: Aplicado o 'with' statement
    def get_client_addresses(self, cliente_id):
        """Busca todos os endereços de um cliente."""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                # MODIFICADO: Adicionado cidade, estado e cep à consulta
                query = """
                    SELECT endereco_id, rua, num, bairro, cep 
                    FROM enderecos_entrega 
                    WHERE cliente_id = %s
                """
                cursor.execute(query, (cliente_id,))
                return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar endereços: {e}")
            return []
        
    
    def get_address_details(self, endereco_id):
        """Busca os detalhes de um endereço específico."""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM enderecos_entrega WHERE endereco_id = %s", (endereco_id,))
                return cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar detalhes do endereço: {e}")
            return None

    def update_client_address(self, endereco_id, endereco):
        """Atualiza um endereço de entrega existente."""
        try:
            with self.connection.cursor() as cursor:
                query = """
                    UPDATE enderecos_entrega SET rua=%s, num=%s, bairro=%s, cidade=%s, estado=%s, cep=%s
                    WHERE endereco_id = %s
                """
                cursor.execute(query, (endereco['rua'], endereco['num'], endereco['bairro'], 
                                       endereco['cidade'], endereco['estado'], endereco['cep'], endereco_id))
                self.connection.commit()
                return True
        except mysql.connector.Error as e:
            print(f"Erro ao atualizar endereço do cliente: {e}")
            self.connection.rollback()
            return False

    def delete_client_address(self, endereco_id):
        """Exclui um endereço de entrega."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM enderecos_entrega WHERE endereco_id = %s", (endereco_id,))
                self.connection.commit()
                return True
        except mysql.connector.Error as e:
            print(f"Erro ao excluir endereço: {e}")
            self.connection.rollback()
            return False

    # MODIFICADO: Aplicado o 'with' statement
    def add_client_address(self, cliente_id, rua, num, bairro, cidade, estado, cep):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO enderecos_entrega (cliente_id, rua, num, bairro, cidade, estado, cep) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (cliente_id, rua, num, bairro, cidade, estado, cep)
                )
                self.connection.commit()
                return cursor.lastrowid
        except mysql.connector.Error as e:
            print(f"Erro ao adicionar endereço: {e}")
            self.connection.rollback()
            return None

    # MODIFICADO: Aplicado o 'with' statement
    def get_restaurant_categories(self, id_restaurante):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT categoria_id, nome_categoria FROM categoria_pratos WHERE id_restaurante = %s", (id_restaurante,))
                return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar categorias: {e}")
            return []

    # MODIFICADO: Aplicado o 'with' statement
    def get_dish_details(self, id_prato):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                # MODIFICADO: Adicionado 'categoria_id' à consulta
                query = "SELECT id_prato, nome_prato, descricao, preco, status_disp, categoria_id FROM pratos WHERE id_prato = %s"
                cursor.execute(query, (id_prato,))
                return cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar detalhes do prato: {e}")
            return None

    # MODIFICADO: Aplicado o 'with' statement
    def edit_dish(self, id_prato, nome, descricao, preco, categoria_id): # MODIFICADO: adicionado categoria_id
        """Atualiza as informações de um prato existente, incluindo a categoria."""
        try:
            with self.connection.cursor() as cursor:
                # MODIFICADO: adicionado categoria_id ao UPDATE
                query = """
                    UPDATE pratos 
                    SET nome_prato = %s, descricao = %s, preco = %s, categoria_id = %s 
                    WHERE id_prato = %s
                """
                cursor.execute(query, (nome, descricao, preco, categoria_id, id_prato))
                self.connection.commit()
                return True
        except mysql.connector.Error as e:
            print(f"Erro ao editar o prato: {e}")
            self.connection.rollback()
            return False

    # MODIFICADO: Aplicado o 'with' statement
    def update_dish_availability(self, id_prato, is_available):
        try:
            with self.connection.cursor() as cursor:
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
    def get_restaurant_details(self, restaurante_id):
        """Busca todos os detalhes de um restaurante, incluindo o endereço."""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = """
                    SELECT r.*, e.rua, e.num, e.bairro, e.cidade, e.estado, e.cep
                    FROM restaurante AS r
                    JOIN enderecos_restaurante AS e ON r.id_end_rest = e.id_end_rest
                    WHERE r.id_restaurante = %s
                """
                cursor.execute(query, (restaurante_id,))
                return cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"Erro ao buscar detalhes do restaurante: {e}")
            return None

    def update_restaurant_details(self, restaurante_id, nome, telefone, tipo_culinaria, taxa_entrega, tempo_estimado):
        """Atualiza os dados principais de um restaurante."""
        try:
            with self.connection.cursor() as cursor:
                query = """
                    UPDATE restaurante SET nome=%s, telefone=%s, tipo_culinaria=%s, 
                                           taxa_entrega=%s, tempo_entrega_estimado=%s
                    WHERE id_restaurante = %s
                """
                cursor.execute(query, (nome, telefone, tipo_culinaria, taxa_entrega, tempo_estimado, restaurante_id))
                self.connection.commit()
                return True
        except mysql.connector.Error as e:
            print(f"Erro ao atualizar detalhes do restaurante: {e}")
            self.connection.rollback()
            return False

    def update_restaurant_address(self, id_end_rest, endereco):
        """Atualiza o endereço de um restaurante."""
        try:
            with self.connection.cursor() as cursor:
                query = """
                    UPDATE enderecos_restaurante SET rua=%s, num=%s, bairro=%s, cidade=%s, estado=%s, cep=%s
                    WHERE id_end_rest = %s
                """
                cursor.execute(query, (endereco['rua'], endereco['num'], endereco['bairro'], 
                                       endereco['cidade'], endereco['estado'], endereco['cep'], id_end_rest))
                self.connection.commit()
                return True
        except mysql.connector.Error as e:
            print(f"Erro ao atualizar endereço do restaurante: {e}")
            self.connection.rollback()
            return False

    # -------------------- FECHAR CONEXÃO --------------------
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexão com o banco de dados fechada.")

    def __del__(self):
        self.close()