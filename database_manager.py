# -*- coding: utf-8 -*-
"""
Módulo responsável por toda a interação com o banco de dados MySQL.

Esta classe encapsula a lógica de conexão, execução de queries e
gerenciamento de transações para a aplicação de delivery. É implementada
como um gerenciador de contexto para garantir o fechamento seguro da conexão.

Uso recomendado:
    with DatabaseManager() as db:
        clientes = db.get_all_clients()
"""

import mysql.connector
from mysql.connector import MySQLConnection, Error
import sys
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """Gerencia a conexão e as operações com o banco de dados."""

    def __init__(self, config_file: str = "my.cnf"):
        """
        Inicializa o gerenciador e estabelece a conexão com o banco de dados.

        Args:
            config_file (str): Caminho para o arquivo de configuração da conexão.
        """
        self.connection: Optional[MySQLConnection] = None
        try:
            self.connection = mysql.connector.connect(option_files=config_file)
            print(f"✅ Conexão MySQL aberta com sucesso! ID: {self.connection.connection_id}")
        except Error as e:
            print(f"❌ Erro fatal ao conectar ao MySQL: {e}", file=sys.stderr)
            sys.exit(1)

    def __enter__(self):
        """Permite que a classe seja usada em um bloco 'with'."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Garante que a conexão seja fechada ao sair do bloco 'with'."""
        self.close()

    def close(self):
        """Fecha a conexão com o banco de dados, se estiver ativa."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("ℹ️ Conexão MySQL fechada.")

    # -------------------- LOGIN E CONSULTAS GERAIS --------------------

    def login_user(self, usuario: str, senha: str) -> Optional[Dict[str, Any]]:
        """
        Verifica as credenciais do usuário e retorna seus dados básicos.

        Args:
            usuario (str): Nome de usuário para login.
            senha (str): Senha do usuário.

        Returns:
            Optional[Dict[str, Any]]: Um dicionário com os IDs do usuário, cliente e/ou restaurante
                                      se o login for bem-sucedido, caso contrário None.
        """
        query = """
            SELECT u.usuario_id, u.senha, u.is_restaurante, c.cliente_id, r.id_restaurante
            FROM usuario AS u
            LEFT JOIN cliente AS c ON u.usuario_id = c.usuario_id
            LEFT JOIN restaurante AS r ON u.usuario_id = r.usuario_id
            WHERE u.usuario = %s
        """
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (usuario,))
                user_data = cursor.fetchone()
                
                # Simples verificação de senha (em um projeto real, use hash de senha)
                if user_data and user_data['senha'] == senha:
                    return {
                        'usuario_id': user_data['usuario_id'],
                        'is_restaurante': user_data['is_restaurante'],
                        'cliente_id': user_data['cliente_id'],
                        'restaurante_id': user_data['id_restaurante']
                    }
                return None
        except Error as e:
            print(f"Erro durante o login: {e}")
            return None

    # -------------------- CLIENTE --------------------

    def create_client(self, usuario: str, email: str, senha: str, nome_completo: str, telefone: str, cpf: str) -> Optional[int]:
        """
        Cria um novo usuário e um novo cliente no banco de dados.

        Args:
            (Vários): Dados do cliente a ser criado.

        Returns:
            Optional[int]: O ID do novo cliente ou None em caso de erro ou se o usuário já existir.
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT IGNORE INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, FALSE)",
                    (usuario, email, senha)
                )
                usuario_id = cursor.lastrowid
                
                if usuario_id == 0: # INSERT IGNORE não inseriu nada
                    print(f"Usuário '{usuario}' ou email '{email}' já existe.")
                    return None

                cursor.execute(
                    "INSERT INTO cliente (usuario_id, nome_completo, email, telefone, cpf) VALUES (%s, %s, %s, %s, %s)",
                    (usuario_id, nome_completo, email, telefone, cpf)
                )
                cliente_id = cursor.lastrowid
                self.connection.commit()
                return cliente_id
        except Error as e:
            print(f"Erro ao criar cliente: {e}")
            self.connection.rollback()
            return None

    def add_client_address(self, cliente_id: int, rua: str, num: str, bairro: str, cidade: str, estado: str, cep: str) -> Optional[int]:
        """
        Adiciona um novo endereço de entrega para um cliente.

        Returns:
            Optional[int]: O ID do novo endereço ou None em caso de erro.
        """
        sql = """
            INSERT INTO enderecos_entrega (cliente_id, rua, num, bairro, cidade, estado, cep) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (cliente_id, rua, num, bairro, cidade, estado, cep))
                self.connection.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"Erro ao adicionar endereço: {e}")
            self.connection.rollback()
            return None

    def get_client_addresses(self, cliente_id: int) -> List[Dict[str, Any]]:
        """Busca todos os endereços de um cliente."""
        sql = "SELECT endereco_id, rua, num, bairro FROM enderecos_entrega WHERE cliente_id = %s"
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(sql, (cliente_id,))
                return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar endereços: {e}")
            return []

    # -------------------- RESTAURANTE --------------------

    def create_restaurant(self, usuario: str, email: str, senha: str, nome: str, telefone: str, tipo_culinaria: str,
                          endereco: Dict, taxa_entrega: float, tempo_estimado: str) -> Optional[int]:
        """
        Cria um novo usuário, endereço e restaurante no banco de dados.

        Returns:
            Optional[int]: O ID do novo restaurante ou None em caso de erro.
        """
        try:
            with self.connection.cursor() as cursor:
                # 1. Cria o usuário
                cursor.execute(
                    "INSERT IGNORE INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, TRUE)",
                    (usuario, email, senha)
                )
                usuario_id = cursor.lastrowid
                if usuario_id == 0:
                    print(f"Usuário '{usuario}' ou email '{email}' já existe.")
                    self.connection.rollback()
                    return None

                # 2. Cria o endereço do restaurante
                cursor.execute(
                    "INSERT INTO enderecos_restaurante (rua, num, bairro, cidade, estado, cep) VALUES (%s, %s, %s, %s, %s, %s)",
                    (endereco['rua'], endereco['num'], endereco['bairro'], endereco['cidade'], endereco['estado'], endereco['cep'])
                )
                id_end_rest = cursor.lastrowid
                
                # 3. Cria o restaurante
                sql_rest = """
                    INSERT INTO restaurante (usuario_id, id_end_rest, nome, telefone, tipo_culinaria, taxa_entrega, tempo_entrega_estimado) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_rest, (usuario_id, id_end_rest, nome, telefone, tipo_culinaria, taxa_entrega, tempo_estimado))
                restaurante_id = cursor.lastrowid
                
                self.connection.commit()
                return restaurante_id
        except Error as e:
            print(f"Erro ao criar restaurante: {e}")
            self.connection.rollback()
            return None

    def get_all_restaurants(self) -> List[Dict[str, Any]]:
        """Busca uma lista com os dados principais de todos os restaurantes."""
        sql = "SELECT id_restaurante, nome, tipo_culinaria, taxa_entrega, tempo_entrega_estimado FROM restaurante"
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(sql)
                return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar restaurantes: {e}")
            return []

    # -------------------- HORÁRIOS --------------------

    def add_schedule(self, id_restaurante: int, dia_semana: str, horario_abertura: str, horario_fechamento: str) -> None:
        """Adiciona um horário de funcionamento para um restaurante."""
        sql = """
            INSERT IGNORE INTO horarios_funcionamento_restaurante 
            (id_restaurante, dia_semana, horario_abertura, horario_fechamento) VALUES (%s, %s, %s, %s)
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (id_restaurante, dia_semana, horario_abertura, horario_fechamento))
                self.connection.commit()
        except Error as e:
            print(f"Erro ao adicionar horário: {e}")
            self.connection.rollback()

    # -------------------- CARDÁPIO (MENU) --------------------

    def add_dish_category(self, id_restaurante: int, nome_categoria: str) -> Optional[int]:
        """Adiciona uma nova categoria de pratos para um restaurante."""
        sql = "INSERT INTO categoria_pratos (id_restaurante, nome_categoria) VALUES (%s, %s)"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (id_restaurante, nome_categoria))
                self.connection.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"Erro ao adicionar categoria de prato: {e}")
            self.connection.rollback()
            return None

    def get_restaurant_categories(self, id_restaurante: int) -> List[Dict[str, Any]]:
        """Busca todas as categorias de pratos de um restaurante."""
        sql = "SELECT categoria_id, nome_categoria FROM categoria_pratos WHERE id_restaurante = %s"
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(sql, (id_restaurante,))
                return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar categorias: {e}")
            return []

    def add_dish(self, categoria_id: int, nome_prato: str, descricao: str, preco: float) -> Optional[int]:
        """Adiciona um novo prato a uma categoria."""
        sql = "INSERT INTO pratos (categoria_id, nome_prato, descricao, preco) VALUES (%s, %s, %s, %s)"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (categoria_id, nome_prato, descricao, preco))
                self.connection.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"Erro ao adicionar prato: {e}")
            self.connection.rollback()
            return None

    def get_restaurant_menu(self, id_restaurante: int) -> Dict[str, List[Dict]]:
        """Busca o cardápio de um restaurante, organizado por categoria."""
        query = """
            SELECT cp.nome_categoria, p.id_prato, p.nome_prato, p.descricao, p.preco, p.status_disp
            FROM pratos AS p
            JOIN categoria_pratos AS cp ON p.categoria_id = cp.categoria_id
            WHERE cp.id_restaurante = %s
            ORDER BY cp.nome_categoria, p.nome_prato;
        """
        menu = {}
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (id_restaurante,))
                for item in cursor.fetchall():
                    categoria = item['nome_categoria']
                    if categoria not in menu:
                        menu[categoria] = []
                    menu[categoria].append(item)
            return menu
        except Error as e:
            print(f"Erro ao buscar o cardápio: {e}")
            return {}

    def get_dish_details(self, id_prato: int) -> Optional[Dict[str, Any]]:
        """Busca os detalhes de um prato específico."""
        sql = "SELECT id_prato, nome_prato, descricao, preco, status_disp FROM pratos WHERE id_prato = %s"
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(sql, (id_prato,))
                return cursor.fetchone()
        except Error as e:
            print(f"Erro ao buscar detalhes do prato: {e}")
            return None

    def edit_dish(self, id_prato: int, nome: str, descricao: str, preco: float) -> bool:
        """Atualiza nome, descrição e preço de um prato."""
        sql = "UPDATE pratos SET nome_prato = %s, descricao = %s, preco = %s WHERE id_prato = %s"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (nome, descricao, preco, id_prato))
                self.connection.commit()
                return True
        except Error as e:
            print(f"Erro ao editar o prato: {e}")
            self.connection.rollback()
            return False

    def update_dish_availability(self, id_prato: int, is_available: bool) -> bool:
        """Altera o status de disponibilidade (status_disp) de um prato."""
        sql = "UPDATE pratos SET status_disp = %s WHERE id_prato = %s"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (is_available, id_prato))
                self.connection.commit()
                return True
        except Error as e:
            print(f"Erro ao alterar disponibilidade do prato: {e}")
            self.connection.rollback()
            return False

    # -------------------- PEDIDOS (ORDERS) --------------------

    def create_order(self, id_cliente: int, id_restaurante: int, id_forma_pagamento: int, endereco_id: int, taxa_entrega: float) -> Optional[int]:
        """Cria um novo registro de pedido na tabela."""
        sql = """
            INSERT INTO pedido (id_cliente, id_restaurante, id_forma_pagamento, endereco_id, valor_total) 
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            with self.connection.cursor() as cursor:
                # O valor inicial do pedido é apenas a taxa de entrega. Os itens somarão a este valor.
                cursor.execute(sql, (id_cliente, id_restaurante, id_forma_pagamento, endereco_id, taxa_entrega))
                self.connection.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"Erro ao criar pedido: {e}")
            self.connection.rollback()
            return None

    def add_order_item(self, id_pedido: int, id_prato: int, qtd: int, preco_item: float, observacoes: str) -> None:
        """Adiciona um item a um pedido existente e atualiza o valor total do pedido."""
        sql_item = "INSERT INTO item_pedido (id_pedido, id_prato, qtd, preco_item, observacoes) VALUES (%s, %s, %s, %s, %s)"
        sql_update_total = "UPDATE pedido SET valor_total = valor_total + %s WHERE id_pedido = %s"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql_item, (id_pedido, id_prato, qtd, preco_item, observacoes))
                
                valor_total_itens = qtd * preco_item
                cursor.execute(sql_update_total, (valor_total_itens, id_pedido))
                
                self.connection.commit()
        except Error as e:
            print(f"Erro ao adicionar item de pedido: {e}")
            self.connection.rollback()

    def update_order_status(self, id_pedido: int, status: str) -> None:
        """Atualiza o status de um pedido."""
        sql = "UPDATE pedido SET status_pedido = %s WHERE id_pedido = %s"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (status, id_pedido))
                self.connection.commit()
        except Error as e:
            print(f"Erro ao atualizar status do pedido: {e}")
            self.connection.rollback()

    def get_orders_for_restaurant(self, id_restaurante: int) -> List[Dict[str, Any]]:
        """Busca todos os pedidos recebidos por um restaurante."""
        query = """
            SELECT p.id_pedido, p.dataHora, p.status_pedido, p.valor_total, c.nome_completo 
            FROM pedido AS p
            JOIN cliente AS c ON p.id_cliente = c.cliente_id
            WHERE p.id_restaurante = %s 
            ORDER BY p.dataHora DESC;
        """
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (id_restaurante,))
                return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar pedidos do restaurante: {e}")
            return []

    def get_orders_for_client(self, id_cliente: int) -> List[Dict[str, Any]]:
        """Busca o histórico de pedidos de um cliente."""
        query = """
            SELECT p.id_pedido, p.dataHora, p.status_pedido, p.valor_total, r.nome as nome_restaurante 
            FROM pedido AS p
            JOIN restaurante AS r ON p.id_restaurante = r.id_restaurante
            WHERE p.id_cliente = %s 
            ORDER BY p.dataHora DESC;
        """
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (id_cliente,))
                return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar pedidos do cliente: {e}")
            return []

    # -------------------- OUTROS --------------------

    def get_payment_methods(self) -> List[Dict[str, Any]]:
        """Busca todas as formas de pagamento disponíveis."""
        sql = "SELECT id_forma_pagamento, descricao AS formaPag FROM forma_pagamento"
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(sql)
                return cursor.fetchall()
        except Error as e:
            print(f"Erro ao buscar formas de pagamento: {e}")
            return []

    def evaluate_restaurant(self, id_restaurante: int, id_cliente: int, nota: int, feedback: str) -> None:
        """Registra uma avaliação de um cliente para um restaurante."""
        sql = "INSERT INTO avaliacoes_restaurante (id_restaurante, id_cliente, nota, feedback) VALUES (%s, %s, %s, %s)"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (id_restaurante, id_cliente, nota, feedback))
                self.connection.commit()
        except Error as e:
            print(f"Erro ao registrar avaliação: {e}")
            self.connection.rollback()