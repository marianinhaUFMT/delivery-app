
"""
Módulo para gerenciamento da conexão e operações com o banco de dados MySQL.

Esta classe encapsula a lógica de conexão, execução de queries e
gerenciamento de transações, além de fornecer métodos para popular
o banco de dados com dados iniciais de teste.

A classe é implementada como um gerenciador de contexto para garantir
que a conexão seja fechada de forma segura e automática.

Exemplo de uso:
    with DatabaseManager() as db:
        restaurante_id = db.create_restaurant(...)
"""

import mysql.connector
from mysql.connector import MySQLConnection, Error
import sys
from typing import Optional

class DatabaseManager:
    """
    Gerencia a conexão e as transações com o banco de dados MySQL.
    """

    def __init__(self, config_file: str = "my.cnf"):
        """
        Inicializa o gerenciador e estabelece a conexão com o banco de dados.

        Args:
            config_file (str): O caminho para o arquivo de configuração da conexão.
        """
        self.connection: Optional[MySQLConnection] = None
        try:
            # A conexão é estabelecida usando um arquivo de configuração externo
            # para não expor credenciais no código.
            self.connection = mysql.connector.connect(option_files=config_file)
            print("✅ Conexão com o banco de dados estabelecida com sucesso.")
            print(f"   ID da Conexão: {self.connection.connection_id}")
        except Error as e:
            print(f"❌ Erro fatal ao conectar com o MySQL: {e}", file=sys.stderr)
            # Se a conexão falhar, o programa não pode continuar.
            sys.exit(1)

    def __enter__(self):
        """
        Método de entrada para o gerenciador de contexto. Retorna a própria instância.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Método de saída do gerenciador de contexto. Garante que a conexão seja fechada.
        """
        self.close()

    def close(self):
        """
        Fecha a conexão com o banco de dados de forma segura.
        """
        if self.connection and self.connection.is_connected():
            print("\nℹ️ Fechando conexão com o banco de dados...")
            self.connection.close()
            print("✅ Conexão fechada.")

    def populate_clients(self) -> None:
        """
        Popula a tabela de clientes com um usuário de exemplo.
        A transação é controlada com commit() em caso de sucesso e rollback() em caso de erro.
        """
        print("   -> Populando clientes...")
        try:
            # Criar um cursor novo para cada operação é a melhor prática.
            with self.connection.cursor() as cursor:
                # 1. Insere na tabela 'usuario'
                sql_usuario = "INSERT INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, FALSE)"
                cursor.execute(sql_usuario, ("client1", "client1@email.com", "password123"))
                usuario_id = cursor.lastrowid # Maneira correta de obter o último ID inserido

                # 2. Insere na tabela 'cliente' usando o ID do usuário
                sql_cliente = "INSERT INTO cliente (usuario_id, nome_completo, email, telefone, cpf) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_cliente, (usuario_id, "Cliente Exemplo Um", "client1@email.com", "999998888", "12345678901"))
                
                self.connection.commit()
                print("      Cliente de exemplo inserido com sucesso.")
        except Error as e:
            print(f"      ❌ Erro ao popular clientes: {e}")
            self.connection.rollback()

    def populate_restaurants(self) -> Optional[int]:
        """
        Popula as tabelas de restaurante e endereço com um exemplo.

        Returns:
            Optional[int]: O ID do restaurante inserido, ou None em caso de falha.
        """
        print("   -> Populando restaurantes...")
        try:
            with self.connection.cursor() as cursor:
                # 1. Insere usuário do tipo restaurante
                sql_usuario = "INSERT INTO usuario (usuario, email, senha, is_restaurante) VALUES (%s, %s, %s, TRUE)"
                cursor.execute(sql_usuario, ("restaurante_bom", "contato@restaurante.com", "senha123"))
                usuario_id = cursor.lastrowid

                # 2. Insere o endereço do restaurante
                sql_endereco = "INSERT INTO enderecos_restaurante (rua, num, bairro, cidade, estado, cep) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql_endereco, ("Avenida Principal", "100", "Centro", "Goiânia", "GO", "74000-000"))
                id_end_rest = cursor.lastrowid

                # 3. Insere o restaurante, ligando usuário e endereço
                sql_restaurante = "INSERT INTO restaurante (usuario_id, id_end_rest, nome, telefone, tipo_culinaria) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_restaurante, (usuario_id, id_end_rest, "Sabor da Terra", "62988887777", "Comida Goiana"))
                restaurante_id = cursor.lastrowid
                
                self.connection.commit()
                print(f"      Restaurante de exemplo (ID: {restaurante_id}) inserido com sucesso.")
                return restaurante_id
        except Error as e:
            print(f"      ❌ Erro ao popular restaurantes: {e}")
            self.connection.rollback()
            return None

    def populate_schedules(self, rest_id: int) -> None:
        """
        Popula a tabela de horários de funcionamento para um restaurante específico.

        Args:
            rest_id (int): O ID do restaurante para o qual o horário será adicionado.
        """
        print(f"   -> Populando horários para o restaurante ID {rest_id}...")
        try:
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO horarios_funcionamento_restaurante (id_restaurante, dia_semana, horario_abertura, horario_fechamento) VALUES (%s, %s, %s, %s)"
                horarios = [
                    (rest_id, "Segunda", "11:00:00", "22:00:00"),
                    (rest_id, "Terça", "11:00:00", "22:00:00"),
                    (rest_id, "Quarta", "11:00:00", "22:00:00"),
                ]
                cursor.executemany(sql, horarios)
                self.connection.commit()
                print("      Horários de exemplo inseridos com sucesso.")
        except Error as e:
            print(f"      ❌ Erro ao popular horários: {e}")
            self.connection.rollback()

    def populate_menu(self, rest_id: int) -> None:
        """
        Popula o cardápio com uma categoria e um prato de exemplo para um restaurante.

        Args:
            rest_id (int): O ID do restaurante.
        """
        print(f"   -> Populando cardápio para o restaurante ID {rest_id}...")
        try:
            with self.connection.cursor() as cursor:
                # 1. Insere a categoria
                sql_categoria = "INSERT INTO categoria_pratos (id_restaurante, nome_categoria) VALUES (%s, %s)"
                cursor.execute(sql_categoria, (rest_id, 'Pratos Principais'))
                categoria_id = cursor.lastrowid

                # 2. Insere um prato nessa categoria
                sql_prato = "INSERT INTO pratos (categoria_id, nome_prato, descricao, preco) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql_prato, (categoria_id, 'Pamonha Frita', 'Deliciosa pamonha salgada frita na hora', 15.50))
                
                self.connection.commit()
                print("      Cardápio de exemplo inserido com sucesso.")
        except Error as e:
            print(f"      ❌ Erro ao popular cardápio: {e}")
            self.connection.rollback()

    def populate_payment_methods(self) -> None:
        """
        Adiciona as formas de pagamento padrão na tabela `forma_pagamento`.
        Usa 'INSERT IGNORE' para evitar erros caso os dados já existam,
        tornando a operação idempotente (pode ser executada várias vezes sem problemas).
        """
        print("   -> Populando formas de pagamento...")
        try:
            with self.connection.cursor() as cursor:
                payment_methods = [
                    ('Dinheiro',), ('Pix',), ('Cartão de Crédito',), ('Cartão de Débito',)
                ]
                # 'INSERT IGNORE' é útil para dados estáticos como este
                query = "INSERT IGNORE INTO forma_pagamento (descricao) VALUES (%s)"
                cursor.executemany(query, payment_methods)
                self.connection.commit()
                print("      Formas de pagamento populadas com sucesso.")
        except Error as e:
            print(f"      ❌ Erro ao popular formas de pagamento: {e}")
            self.connection.rollback()


def _populate_initial_data(db: DatabaseManager) -> None:
    """
    Executa a sequência de funções para popular o banco de dados com dados iniciais.

    Args:
        db (DatabaseManager): Uma instância do gerenciador de banco de dados.
    """
    print("\nIniciando a população do banco de dados com dados de exemplo...")
    db.populate_payment_methods()
    db.populate_clients()
    
    rest_id = db.populate_restaurants()
    if rest_id:
        db.populate_schedules(rest_id)
        db.populate_menu(rest_id)
    print("\n✨ População do banco de dados concluída.")


# Ponto de entrada do script:
# Este bloco só será executado quando o arquivo for chamado diretamente.
if __name__ == "__main__":
    # A sintaxe 'with' garante que a conexão será criada e, ao final,
    # o método close() será chamado automaticamente.
    with DatabaseManager() as db_manager:
        _populate_initial_data(db_manager)