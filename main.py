"""
Módulo principal para a execução do aplicativo de delivery.
Gerencia o fluxo de interação do usuário, desde o login e cadastro
até a criação de pedidos e gerenciamento por parte dos restaurantes.
"""

import getpass
import sys
from database_manager import DatabaseManager

# ==============================================================================
# --- CONSTANTES ---
# Usar constantes para comandos do usuário evita erros de digitação e
# torna o código mais legível.
# ==============================================================================
SAIR_COMMAND = 'sair'
VOLTAR_COMMAND = 'voltar'
CONFIRM_COMMAND = 's'
NEW_CATEGORY_COMMAND = 'n'


# ==============================================================================
# --- FUNÇÕES AUXILIARES (HELPERS) ---
# Funções pequenas e reutilizáveis para tarefas comuns.
# ==============================================================================

def _print_header(title: str):
    """Imprime um cabeçalho formatado para organizar a interface do usuário."""
    print(f"\n--- {title.upper()} ---")


def _get_validated_input(prompt: str, type_cast=str, error_message="Entrada inválida."):
    """
    Solicita uma entrada do usuário e a valida, repetindo até receber um valor válido.

    Args:
        prompt (str): A mensagem a ser exibida para o usuário.
        type_cast (type, optional): O tipo para o qual a entrada deve ser convertida (ex: int, float).
                                    Padrão é str.
        error_message (str, optional): A mensagem de erro a ser exibida.

    Returns:
        O valor inserido pelo usuário, convertido para o tipo especificado.
    """
    while True:
        try:
            value = input(prompt)
            return type_cast(value)
        except ValueError:
            print(f"❌ {error_message} Tente novamente.")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada pelo usuário.")
            return None


def _confirm_action(prompt: str) -> bool:
    """
    Pede uma confirmação (s/n) ao usuário.

    Args:
        prompt (str): A pergunta a ser feita.

    Returns:
        bool: True se o usuário confirmar, False caso contrário.
    """
    choice = input(prompt).lower()
    return choice == CONFIRM_COMMAND


# ==============================================================================
# --- FLUXOS DE CADASTRO E LOGIN ---
# ==============================================================================

def cadastrar_cliente(db: DatabaseManager):
    """Guia o usuário através do processo de cadastro de um novo cliente."""
    _print_header("Cadastro de Novo Cliente")
    try:
        usuario = input("Digite um nome de usuário: ")
        email = input("Digite seu email: ")
        senha = getpass.getpass("Digite sua senha: ")
        nome_completo = input("Digite seu nome completo: ")
        telefone = input("Digite seu telefone: ")
        cpf = input("Digite seu CPF: ")

        print("\nCadastrando cliente...")
        cliente_id = db.create_client(usuario, email, senha, nome_completo, telefone, cpf)

        if cliente_id:
            print(f"\n✅ Cliente '{nome_completo}' cadastrado com sucesso! ID: {cliente_id}")
        else:
            print("\n❌ Falha ao cadastrar cliente. Verifique se os dados já existem.")
    except (KeyboardInterrupt, EOFError):
        print("\nCadastro cancelado.")


def cadastrar_restaurante(db: DatabaseManager):
    """Guia o usuário através do processo completo de cadastro de um restaurante."""
    try:
        _print_header("Cadastro de Restaurante (Parte 1: Dados Básicos)")
        usuario = input("Digite um nome de usuário para o restaurante: ")
        email = input("Digite o email de contato: ")
        senha = getpass.getpass("Digite uma senha: ")
        nome = input("Digite o nome do restaurante: ")
        telefone = input("Digite o telefone do restaurante: ")
        tipo_culinaria = input("Digite o tipo de culinária: ")
        taxa_entrega = _get_validated_input(
            "Digite a taxa de entrega (ex: 5.50): ", float, "Valor inválido. Use ponto decimal."
        )
        if taxa_entrega is None: return
        tempo_estimado = input("Digite o tempo de entrega estimado (ex: 30-40 min): ")

        _print_header("Cadastro de Restaurante (Parte 2: Endereço)")
        endereco = {
            "rua": input("Rua: "), "num": input("Número: "), "bairro": input("Bairro: "),
            "cidade": input("Cidade: "), "estado": input("Estado (UF): "), "cep": input("CEP: ")
        }

        print("\nCadastrando restaurante...")
        restaurante_id = db.create_restaurant(
            usuario, email, senha, nome, telefone, tipo_culinaria, endereco, taxa_entrega, tempo_estimado
        )

        if restaurante_id:
            print(f"\n✅ Restaurante '{nome}' cadastrado com sucesso! ID: {restaurante_id}")
            # Após o cadastro básico, inicia os fluxos para adicionar detalhes
            add_schedules_flow(db, restaurante_id)
            add_menu_flow(db, restaurante_id)
        else:
            print("\n❌ Falha ao cadastrar restaurante.")
    except (KeyboardInterrupt, EOFError):
        print("\nCadastro cancelado.")


def do_login(db: DatabaseManager):
    """
    Executa o fluxo de login para um usuário (cliente ou restaurante).
    Redireciona para o painel apropriado em caso de sucesso.
    """
    _print_header("Login")
    try:
        usuario = input("Usuário: ")
        senha = getpass.getpass("Senha: ")
        user_data = db.login_user(usuario, senha)

        if user_data:
            print("\n✅ Login bem-sucedido!")
            if user_data.get('is_restaurante'):
                show_restaurant_panel(db, user_data)
            else:
                show_client_panel(db, user_data)
        else:
            print("\n❌ Usuário ou senha incorretos.")
    except (KeyboardInterrupt, EOFError):
        print("\nLogin cancelado.")


# ==============================================================================
# --- PAINEL DO CLIENTE E FLUXOS RELACIONADOS ---
# ==============================================================================

def show_client_panel(db: DatabaseManager, user_data: dict):
    """
    Exibe o painel de opções para clientes logados.

    Args:
        db (DatabaseManager): Instância do gerenciador de banco de dados.
        user_data (dict): Dicionário contendo os dados do cliente logado.
    """
    cliente_id = user_data.get('cliente_id')
    if not cliente_id:
        print("Erro: Não foi possível identificar o cliente associado a este usuário.")
        return

    while True:
        _print_header(f"ÁREA DO CLIENTE (ID: {cliente_id})")
        print("  1 - Fazer um Pedido")
        print("  2 - Ver Meus Pedidos")
        print("  3 - Logout")

        choice = input("Sua opção: ")
        if choice == '1':
            place_order_flow(db, user_data)
        elif choice == '2':
            view_orders_flow_client(db, cliente_id)
        elif choice == '3':
            break
        else:
            print("Opção inválida.")
        input("\nPressione Enter para continuar...")


def place_order_flow(db: DatabaseManager, client_user_data: dict):
    """
    Orquestra o fluxo completo de um cliente fazendo um pedido,
    desde a escolha do restaurante até a confirmação final.

    Args:
        db (DatabaseManager): Instância do gerenciador de banco de dados.
        client_user_data (dict): Dicionário com os dados do cliente.
    """
    # Etapa 1: Selecionar o restaurante
    selected_restaurant = _select_restaurant_for_order(db)
    if not selected_restaurant:
        return

    # Etapa 2: Montar o carrinho de compras
    cart = _build_order_cart(db, selected_restaurant['id_restaurante'])
    if not cart:
        print("Carrinho vazio. Pedido cancelado.")
        return

    # Etapa 3: Selecionar endereço de entrega
    cliente_id = client_user_data['cliente_id']
    selected_address_id = address_selection_flow(db, cliente_id)
    if not selected_address_id:
        print("Endereço não selecionado. Pedido cancelado.")
        return

    # Etapa 4: Selecionar forma de pagamento
    selected_payment_id = payment_selection_flow(db)
    if not selected_payment_id:
        print("Forma de pagamento não selecionada. Pedido cancelado.")
        return

    # Etapa 5: Revisar e confirmar o pedido
    _review_and_create_order(
        db, cliente_id, selected_restaurant, cart,
        selected_address_id, selected_payment_id
    )


def _select_restaurant_for_order(db: DatabaseManager) -> dict | None:
    """
    Lista os restaurantes e permite ao cliente escolher um.

    Returns:
        dict | None: Dicionário com os dados do restaurante escolhido ou None se cancelado.
    """
    _print_header("Fazer Pedido (Etapa 1: Escolha o Restaurante)")
    restaurants = db.get_all_restaurants()
    if not restaurants:
        print("Nenhum restaurante cadastrado no momento.")
        return None

    for i, r in enumerate(restaurants):
        print(f"  {i+1} - {r['nome']} ({r['tipo_culinaria']}) | "
              f"Taxa: R$ {r['taxa_entrega']:.2f} | Tempo: {r['tempo_entrega_estimado']}")

    prompt = "Digite o número do restaurante: "
    choice = _get_validated_input(prompt, int, "Por favor, digite um número.")
    if choice is None: return None

    if 1 <= choice <= len(restaurants):
        return restaurants[choice - 1]
    else:
        print("Seleção inválida.")
        return None


def _build_order_cart(db: DatabaseManager, restaurant_id: int) -> list:
    """
    Exibe o cardápio e gerencia a adição de itens ao carrinho.

    Args:
        restaurant_id (int): O ID do restaurante escolhido.

    Returns:
        list: Uma lista de dicionários, onde cada um representa um item no carrinho.
    """
    _print_header(f"Monte seu Carrinho")
    menu = db.get_restaurant_menu(restaurant_id)
    if not menu:
        print("Este restaurante não possui um cardápio disponível.")
        return []

    cart = []
    menu_items_flat = []
    item_number = 1
    # Transforma o menu (dicionário de categorias) em uma lista plana de pratos
    for category, dishes in menu.items():
        print(f"\n-- {category} --")
        for dish in dishes:
            print(f"  {item_number} - {dish['nome_prato']} - R$ {dish['preco']:.2f}")
            print(f"      ({dish['descricao']})")
            menu_items_flat.append(dish)
            item_number += 1

    while True:
        prompt = f"\nDigite o número do prato para adicionar (ou '{SAIR_COMMAND}' para fechar): "
        user_input = input(prompt)
        if user_input.lower() == SAIR_COMMAND:
            break

        try:
            dish_index = int(user_input) - 1
            if not (0 <= dish_index < len(menu_items_flat)):
                print("Número de prato inválido.")
                continue

            selected_dish = menu_items_flat[dish_index]
            qty_prompt = f"Quantidade de '{selected_dish['nome_prato']}': "
            qty = _get_validated_input(qty_prompt, int, "Digite um número inteiro.")
            if qty is None: continue # Cancelado pelo usuário

            obs = input("Observações (opcional): ")

            cart.append({'dish': selected_dish, 'quantity': qty, 'observations': obs})
            print(f"✅ '{selected_dish['nome_prato']}' adicionado ao carrinho!")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número.")

    return cart


def _review_and_create_order(db, cliente_id, restaurant, cart, address_id, payment_id):
    """
    Exibe um resumo do pedido para confirmação e o cria no banco de dados.
    """
    _print_header("Etapa Final: Confirme seu Pedido")
    subtotal = sum(item['dish']['preco'] * item['quantity'] for item in cart)
    taxa_entrega = restaurant['taxa_entrega']
    total = subtotal + taxa_entrega

    for item in cart:
        item_total = item['dish']['preco'] * item['quantity']
        print(f"  - {item['quantity']}x {item['dish']['nome_prato']} @ R$ {item['dish']['preco']:.2f} = R$ {item_total:.2f}")
        if item['observations']:
            print(f"    Obs: {item['observations']}")

    print("---------------------------------")
    print(f"  Subtotal dos Itens: R$ {subtotal:.2f}")
    print(f"  Taxa de Entrega:    R$ {taxa_entrega:.2f}")
    print(f"  VALOR TOTAL:        R$ {total:.2f}")

    if _confirm_action("\nTudo certo? Enviar pedido? (s/n): "):
        pedido_id = db.create_order(
            cliente_id, restaurant['id_restaurante'], payment_id,
            address_id, taxa_entrega
        )
        if pedido_id:
            for item in cart:
                db.add_order_item(
                    pedido_id, item['dish']['id_prato'], item['quantity'],
                    item['dish']['preco'], item['observations']
                )
            print(f"\n✅ Pedido enviado com sucesso! O ID do seu pedido é: {pedido_id}")
        else:
            print("\n❌ Ocorreu um erro ao criar seu pedido. Tente novamente.")
    else:
        print("Pedido cancelado.")


def view_orders_flow_client(db: DatabaseManager, cliente_id: int):
    """
    Exibe o histórico de pedidos para um cliente.

    Args:
        cliente_id (int): O ID do cliente.
    """
    _print_header("Meus Pedidos")
    orders = db.get_orders_for_client(cliente_id)
    if not orders:
        print("Você ainda não fez nenhum pedido.")
        return

    for order in orders:
        print(f"  ID: {order['id_pedido']} | Data: {order['dataHora'].strftime('%d/%m/%Y %H:%M')}")
        print(f"  Restaurante: {order['nome_restaurante']} | Valor: R$ {order['valor_total']:.2f}")
        print(f"  Status: {order['status_pedido']}\n")


def address_selection_flow(db: DatabaseManager, cliente_id: int) -> int | None:
    """
    Permite ao cliente selecionar um endereço existente ou adicionar um novo.

    Returns:
        int | None: O ID do endereço selecionado ou None se a operação for cancelada.
    """
    _print_header("Etapa 3: Endereço de Entrega")
    while True:
        addresses = db.get_client_addresses(cliente_id)
        if addresses:
            print("Selecione um endereço de entrega:")
            for i, addr in enumerate(addresses):
                print(f"  {i+1} - {addr['rua']}, {addr['num']} - {addr['bairro']}")
            print(f"  {len(addresses) + 1} - Adicionar novo endereço")
            prompt = "Sua opção: "
            choice = _get_validated_input(prompt, int, "Seleção inválida.")
            if choice is None: return None

            if 1 <= choice <= len(addresses):
                return addresses[choice - 1]['endereco_id']
            elif choice == len(addresses) + 1:
                # Chama a função para adicionar e continua o loop
                _add_new_address(db, cliente_id)
            else:
                print("Seleção inválida.")
        else:
            print("Você não tem endereços cadastrados. Vamos adicionar um.")
            if _confirm_action("Pressione Enter para adicionar ou digite 'n' para cancelar: "):
                _add_new_address(db, cliente_id)
            else:
                return None


def _add_new_address(db: DatabaseManager, cliente_id: int):
    """Lida com a lógica de adicionar um novo endereço para o cliente."""
    _print_header("Novo Endereço")
    rua = input("Rua: ")
    num = input("Número: ")
    bairro = input("Bairro: ")
    cidade = input("Cidade: ")
    estado = input("Estado (UF): ")
    cep = input("CEP: ")

    new_addr_id = db.add_client_address(cliente_id, rua, num, bairro, cidade, estado, cep)
    if new_addr_id:
        print("✅ Endereço adicionado com sucesso!")
    else:
        print("❌ Falha ao adicionar endereço.")


def payment_selection_flow(db: DatabaseManager) -> int | None:
    """
    Exibe as formas de pagamento disponíveis e permite a seleção.

    Returns:
        int | None: O ID da forma de pagamento ou None se cancelado.
    """
    _print_header("Etapa 4: Forma de Pagamento")
    payment_methods = db.get_payment_methods()
    if not payment_methods:
        print("Nenhuma forma de pagamento disponível.")
        return None

    print("Selecione a forma de pagamento:")
    for i, method in enumerate(payment_methods):
        print(f"  {i+1} - {method['formaPag']}")

    choice = _get_validated_input("Sua opção: ", int, "Seleção inválida.")
    if choice is None: return None

    if 1 <= choice <= len(payment_methods):
        return payment_methods[choice - 1]['id_forma_pagamento']
    else:
        print("Seleção inválida.")
        return None


# ==============================================================================
# --- PAINEL DO RESTAURANTE E FLUXOS RELACIONADOS ---
# ==============================================================================

def show_restaurant_panel(db: DatabaseManager, user_data: dict):
    """
    Exibe o painel de opções para restaurantes logados.

    Args:
        db (DatabaseManager): Instância do gerenciador de banco de dados.
        user_data (dict): Dicionário contendo os dados do restaurante logado.
    """
    id_restaurante = user_data.get('restaurante_id')
    if not id_restaurante:
        print("Erro: Não foi possível identificar o restaurante associado a este usuário.")
        return

    while True:
        _print_header(f"PAINEL DO RESTAURANTE (ID: {id_restaurante})")
        print("  1 - Ver e Gerenciar Pedidos Recebidos")
        print("  2 - Gerenciar Cardápio")
        print("  3 - Logout")

        choice = input("Sua opção: ")
        if choice == '1':
            manage_orders_flow_restaurant(db, id_restaurante)
        elif choice == '2':
            manage_menu_flow_restaurant(db, id_restaurante)
        elif choice == '3':
            break
        else:
            print("Opção inválida.")


def manage_menu_flow_restaurant(db: DatabaseManager, id_restaurante: int):
    """Menu principal para o restaurante gerenciar seu cardápio."""
    while True:
        _print_header("Gerenciar Cardápio")
        print("  1 - Listar todos os pratos")
        print("  2 - Adicionar novo prato/categoria")
        print("  3 - Editar um prato existente")
        print("  4 - Voltar ao painel principal")

        choice = input("Sua opção: ")
        if choice == '1':
            list_dishes_restaurant(db, id_restaurante)
        elif choice == '2':
            add_menu_flow(db, id_restaurante)
        elif choice == '3':
            edit_dish_restaurant(db, id_restaurante)
        elif choice == '4':
            break
        else:
            print("Opção inválida.")
        input("\nPressione Enter para continuar...")


def add_schedules_flow(db: DatabaseManager, restaurante_id: int):
    """Fluxo interativo para adicionar horários de funcionamento."""
    _print_header("Parte 3: Horários de Funcionamento")
    while True:
        dia = input(f"Digite o dia da semana (ex: Segunda) ou '{SAIR_COMMAND}' para terminar: ")
        if dia.lower() == SAIR_COMMAND:
            break
        abertura = input(f"Horário de abertura na(o) {dia} (HH:MM): ")
        fechamento = input(f"Horário de fechamento na(o) {dia} (HH:MM): ")
        db.add_schedule(restaurante_id, dia, abertura, fechamento)
        print(f"Horário de {dia} adicionado!")


def add_menu_flow(db: DatabaseManager, restaurante_id: int):
    """
    Fluxo interativo para adicionar itens ao cardápio, permitindo
    criar ou selecionar categorias.
    """
    while True:
        _print_header("Adicionar Itens ao Cardápio")
        categories = db.get_restaurant_categories(restaurante_id)

        print("Escolha uma categoria para adicionar pratos:")
        if categories:
            for i, category in enumerate(categories):
                print(f"  {i+1} - {category['nome_categoria']}")

        print(f"\n  [{NEW_CATEGORY_COMMAND.upper()}] - Criar Nova Categoria")
        print(f"  [{SAIR_COMMAND.upper()[0]}] - Sair e voltar")

        choice = input("Sua opção: ").lower()
        categoria_id = None
        nome_categoria = ""

        if choice == SAIR_COMMAND[0]:
            break
        elif choice == NEW_CATEGORY_COMMAND:
            nome_categoria = input("Digite o nome da nova categoria: ")
            if nome_categoria:
                categoria_id = db.add_dish_category(restaurante_id, nome_categoria)
                if not categoria_id:
                    print("❌ Erro ao criar categoria (talvez já exista uma com esse nome).")
                    continue
            else:
                print("Nome da categoria não pode ser vazio.")
                continue
        else:
            try:
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(categories):
                    categoria_id = categories[choice_index]['categoria_id']
                    nome_categoria = categories[choice_index]['nome_categoria']
                else:
                    print("Opção inválida.")
                    continue
            except ValueError:
                print("Opção inválida.")
                continue

        # Se uma categoria foi selecionada ou criada com sucesso, adiciona pratos
        if categoria_id:
            _add_dishes_to_category_flow(db, categoria_id, nome_categoria)


def _add_dishes_to_category_flow(db: DatabaseManager, categoria_id: int, nome_categoria: str):
    """Fluxo para adicionar múltiplos pratos a uma categoria específica."""
    _print_header(f"Adicionando pratos à categoria '{nome_categoria}'")
    while True:
        nome_prato = input(f"  - Nome do prato (ou '{VOLTAR_COMMAND}' para o menu de categorias): ")
        if nome_prato.lower() == VOLTAR_COMMAND:
            break

        descricao = input("    > Descrição do prato: ")
        preco = _get_validated_input("    > Preço (ex: 29.90): ", float, "Preço inválido.")
        if preco is None: continue # Usuário cancelou

        db.add_dish(categoria_id, nome_prato, descricao, preco)
        print(f"    ✅ Prato '{nome_prato}' adicionado com sucesso!")


def list_dishes_restaurant(db: DatabaseManager, id_restaurante: int):
    """Exibe o cardápio completo do restaurante para o administrador."""
    _print_header("Seu Cardápio Atual")
    menu = db.get_restaurant_menu(id_restaurante)
    if not menu:
        print("Seu restaurante ainda não possui um cardápio cadastrado.")
        return

    for category, dishes in menu.items():
        print(f"\n-- {category} --")
        for dish in dishes:
            disponibilidade = "Disponível" if dish['status_disp'] else "Indisponível"
            print(f"  ID: {dish['id_prato']} | {dish['nome_prato']} - R$ {dish['preco']:.2f} [{disponibilidade}]")


def edit_dish_restaurant(db: DatabaseManager, id_restaurante: int):
    """Fluxo para editar os detalhes de um prato existente."""
    _print_header("Editar Prato")
    list_dishes_restaurant(db, id_restaurante) # Mostra os pratos primeiro

    prato_id = _get_validated_input("\nDigite o ID do prato que deseja editar: ", int)
    if prato_id is None: return

    dish_details = db.get_dish_details(prato_id)
    if not dish_details: # Adicionar verificação se prato pertence ao restaurante seria ideal
        print("ID de prato inválido.")
        return

    print(f"\nEditando '{dish_details['nome_prato']}': (Deixe em branco para manter o valor atual)")

    # Coleta os novos dados
    novo_nome = input(f"  - Nome atual: {dish_details['nome_prato']}. Novo nome: ") or dish_details['nome_prato']
    nova_descricao = input(f"  - Descrição atual: {dish_details['descricao']}. Nova descrição: ") or dish_details['descricao']
    novo_preco_str = input(f"  - Preço atual: {dish_details['preco']}. Novo preço: ")
    novo_preco = float(novo_preco_str) if novo_preco_str else dish_details['preco']

    # Edita disponibilidade
    disp_atual = "Disponível" if dish_details['status_disp'] else "Indisponível"
    nova_disp_input = input(f"  - Disponibilidade: {disp_atual}. Alterar para (d/i)?: ").lower()
    if nova_disp_input in ['d', 'i']:
        nova_disponibilidade = (nova_disp_input == 'd')
        db.update_dish_availability(prato_id, nova_disponibilidade)
    
    # Envia atualizações para o banco de dados
    db.edit_dish(prato_id, novo_nome, nova_descricao, novo_preco)
    print("\n✅ Prato atualizado com sucesso!")


def manage_orders_flow_restaurant(db: DatabaseManager, id_restaurante: int):
    """Fluxo para o restaurante visualizar e atualizar o status dos pedidos."""
    _print_header("Pedidos Recebidos")
    orders = db.get_orders_for_restaurant(id_restaurante)
    if not orders:
        print("Nenhum pedido recebido ainda.")
        return

    order_ids = [order['id_pedido'] for order in orders]
    for order in orders:
        print(f"  ID: {order['id_pedido']} | Data: {order['dataHora'].strftime('%d/%m/%Y %H:%M')}")
        print(f"  Cliente: {order['nome_completo']} | Valor: R$ {order['valor_total']:.2f}")
        print(f"  Status Atual: {order['status_pedido']}\n")

    prompt = f"Digite o ID do pedido para alterar o status (ou '{VOLTAR_COMMAND}'): "
    pedido_id_str = input(prompt)
    if pedido_id_str.lower() == VOLTAR_COMMAND:
        return

    try:
        pedido_id = int(pedido_id_str)
        if pedido_id not in order_ids:
            print("ID de pedido inválido ou não pertence a este restaurante.")
            return

        _print_header("Selecione o Novo Status")
        statuses = ['Pendente', 'Em Preparação', 'Em Trânsito', 'Entregue', 'Cancelado']
        for i, status in enumerate(statuses):
            print(f"  {i+1} - {status}")

        status_choice = _get_validated_input("Sua opção: ", int)
        if status_choice and 1 <= status_choice <= len(statuses):
            novo_status = statuses[status_choice - 1]
            db.update_order_status(pedido_id, novo_status)
            print(f"\n✅ Status do pedido {pedido_id} atualizado para '{novo_status}'.")
        else:
            print("Opção de status inválida.")

    except ValueError:
        print("Entrada inválida. Por favor, digite um número.")


# ==============================================================================
# --- FUNÇÃO PRINCIPAL ---
# ==============================================================================

def main():
    """
    Função principal que inicializa a conexão com o banco de dados e
    exibe o menu principal, gerenciando o fluxo do aplicativo.
    """
    try:
        db = DatabaseManager()
    except Exception as e:
        print(f"Erro crítico ao conectar ao banco de dados: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        while True:
            _print_header("Bem-vindo ao App de Delivery")
            print("  1 - Login")
            print("  2 - Cadastrar novo Cliente")
            print("  3 - Cadastrar novo Restaurante")
            print("  4 - Sair")

            escolha = input("Digite o número da sua opção: ")

            if escolha == '1':
                do_login(db)
            elif escolha == '2':
                cadastrar_cliente(db)
            elif escolha == '3':
                cadastrar_restaurante(db)
            elif escolha == '4':
                print("\nAté logo!")
                break
            else:
                print("\nOpção inválida!")

    except (KeyboardInterrupt, EOFError):
        print("\n\nSaindo do programa.")
    finally:
        print("Fechando conexão com o banco de dados.")
        db.close()


if __name__ == "__main__":
    main()