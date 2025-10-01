from database_manager import DatabaseManager
import getpass
import sys
from enum import Enum

# Classe Enum para os status do pedido, como você definiu.
class StatusPedido(Enum):
    PENDENTE = 'Pendente'
    EM_PREPARACAO = 'Em Preparação'
    EM_TRANSITO = 'Em Trânsito'
    ENTREGUE = 'Entregue'
    CANCELADO = 'Cancelado'

# --- Funções de Fluxo (Cadastro, Login, Painéis) ---

def cadastrar_cliente(db):
    """Função para guiar o cadastro de um novo cliente."""
    print("\n--- Cadastro de Novo Cliente ---")
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
            print("\n❌ Falha ao cadastrar cliente.")
    except (KeyboardInterrupt, EOFError):
        print("\nCadastro cancelado.")

def cadastrar_restaurante(db):
    """Função para guiar o cadastro completo de um novo restaurante."""
    print("\n--- Cadastro de Novo Restaurante (Parte 1: Dados Básicos) ---")
    try:
        usuario = input("Digite um nome de usuário para o restaurante: ")
        email = input("Digite o email de contato: ")
        senha = getpass.getpass("Digite uma senha: ")
        nome = input("Digite o nome do restaurante: ")
        telefone = input("Digite o telefone do restaurante: ")
        tipo_culinaria = input("Digite o tipo de culinária: ")

        while True:
            try:
                taxa_entrega = float(input("Digite a taxa de entrega (ex: 5.50): "))
                break
            except ValueError:
                print("Valor inválido. Use ponto como separador decimal.")
        tempo_estimado = input("Digite o tempo de entrega estimado (ex: 30-40 min): ")
        
        print("\n--- (Parte 2: Endereço) ---")
        endereco = {
            "rua": input("Rua: "), "num": input("Número: "), "bairro": input("Bairro: "),
            "cidade": input("Cidade: "), "estado": input("Estado (UF): "), "cep": input("CEP: ")
        }

        print("\nCadastrando restaurante...")
        restaurante_id = db.create_restaurant(usuario, email, senha, nome, telefone, tipo_culinaria, endereco, taxa_entrega, tempo_estimado)

        if restaurante_id:
            print(f"\n✅ Restaurante '{nome}' cadastrado com sucesso! ID: {restaurante_id}")
            add_schedules_flow(db, restaurante_id)
            add_menu_flow(db, restaurante_id)
        else:
            print("\n❌ Falha ao cadastrar restaurante.")
    except (KeyboardInterrupt, EOFError):
        print("\nCadastro cancelado.")

def add_schedules_flow(db, restaurante_id):
    """Fluxo interativo para adicionar horários de funcionamento."""
    print("\n--- (Parte 3: Horários de Funcionamento) ---")
    while True:
        dia = input("Digite o dia da semana (ex: Segunda, Terça) ou 'sair' para terminar: ")
        if dia.lower() == 'sair':
            break
        abertura = input(f"Horário de abertura na(o) {dia} (HH:MM:SS): ")
        fechamento = input(f"Horário de fechamento na(o) {dia} (HH:MM:SS): ")
        db.add_schedule(restaurante_id, dia, abertura, fechamento)
        print(f"Horário de {dia} adicionado!")

def add_menu_flow(db, restaurante_id):
    """
    Fluxo interativo aprimorado para adicionar itens ao cardápio,
    permitindo selecionar categorias existentes ou criar novas.
    """
    while True:
        print("\n--- Adicionar Itens ao Cardápio ---")
        
        categories = db.get_restaurant_categories(restaurante_id)
        print("Escolha uma categoria para adicionar pratos ou crie uma nova:")
        
        if categories:
            for i, category in enumerate(categories):
                print(f"  {i+1} - {category['nome_categoria']}")
        
        print("\n  [N] - Criar Nova Categoria")
        print("  [S] - Sair e voltar ao menu anterior")
        
        choice = input("Sua opção: ").lower()

        categoria_id = None
        nome_categoria = ""

        if choice == 's':
            break
        elif choice == 'n':
            nome_categoria = input("Digite o nome da nova categoria: ")
            if nome_categoria:
                categoria_id = db.add_dish_category(restaurante_id, nome_categoria)
                if not categoria_id:
                    print("❌ Erro ao criar categoria (talvez já exista uma com esse nome).")
                    input("Pressione Enter para continuar...")
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

        if categoria_id:
            print(f"\n-- Adicionando pratos à categoria '{nome_categoria}' --")
            while True:
                nome_prato = input("  - Nome do prato (ou 'voltar' para o menu de categorias): ")
                if nome_prato.lower() == 'voltar':
                    break
                
                descricao = input("    > Descrição do prato: ")
                while True:
                    try:
                        preco = float(input("    > Preço (ex: 29.90): "))
                        break
                    except ValueError:
                        print("    > Preço inválido. Use ponto como separador decimal.")
                
                db.add_dish(categoria_id, nome_prato, descricao, preco)
                print(f"    ✅ Prato '{nome_prato}' adicionado com sucesso!")


def do_login(db):
    """Função para o fluxo de login."""
    print("\n--- Login ---")
    try:
        usuario = input("Usuário: ")
        senha = getpass.getpass("Senha: ")
        user_data = db.login_user(usuario, senha)
        if user_data:
            print("\n✅ Login bem-sucedido!")
            if user_data['is_restaurante']:
                show_restaurant_panel(db, user_data)
            else:
                show_client_panel(db, user_data)
        else:
            print("\n❌ Usuário ou senha incorretos.")
    except (KeyboardInterrupt, EOFError):
        print("\nLogin cancelado.")


def address_selection_flow(db, cliente_id):
    """Permite que o cliente selecione um endereço existente ou adicione um novo."""
    print("\n--- (Etapa 3: Endereço de Entrega) ---")
    
    while True:
        addresses = db.get_client_addresses(cliente_id)
        if addresses:
            print("Selecione um endereço de entrega:")
            for i, addr in enumerate(addresses):
                print(f"  {i+1} - {addr['rua']}, {addr['num']} - {addr['bairro']}")
            print(f"  {len(addresses) + 1} - Adicionar novo endereço")
            prompt = "Sua opção: "
            choice_offset = 0
        else:
            print("Você não tem endereços cadastrados. Vamos adicionar um.")
            prompt = "Pressione Enter para continuar ou 'cancelar' para sair: "
            choice_offset = 1 
        
        try:
            user_input = input(prompt)
            if user_input.lower() == 'cancelar':
                return None

            if not addresses:
                choice = 1
            else:
                choice = int(user_input)

            if 1 <= choice <= len(addresses):
                return addresses[choice - 1]['endereco_id']
            elif choice == len(addresses) + 1 or choice_offset == 1:
                print("\n-- Novo Endereço --")
                rua = input("Rua: ")
                num = input("Número: ")
                bairro = input("Bairro: ")
                cidade = input("Cidade: ")
                estado = input("Estado (UF): ")
                cep = input("CEP: ")
                
                new_addr_id = db.add_client_address(cliente_id, rua, num, bairro, cidade, estado, cep)
                if new_addr_id:
                    print("Endereço adicionado com sucesso!")
                else:
                    print("Falha ao adicionar endereço.")
                    return None
            else:
                print("Seleção inválida.")
        except (ValueError, IndexError):
            print("Seleção inválida.")

def payment_selection_flow(db):
    """Permite que o cliente selecione uma forma de pagamento."""
    print("\n--- (Etapa 4: Forma de Pagamento) ---")
    payment_methods = db.get_payment_methods()
    if not payment_methods:
        print("Nenhuma forma de pagamento disponível.")
        return None
        
    print("Selecione a forma de pagamento:")
    for i, method in enumerate(payment_methods):
        print(f"  {i+1} - {method['formaPag']}")
        
    try:
        choice = int(input("Sua opção: "))
        if 1 <= choice <= len(payment_methods):
            return payment_methods[choice - 1]['id_forma_pagamento']
        else:
            print("Seleção inválida.")
            return None
    except (ValueError, IndexError):
        print("Seleção inválida.")
        return None
    
def place_order_flow(db, client_user_data):
    """Orquestra o fluxo completo de um cliente fazendo um pedido."""
    print("\n--- Fazer um Pedido (Etapa 1: Escolha o Restaurante) ---")
    restaurants = db.get_all_restaurants()
    if not restaurants:
        print("Nenhum restaurante cadastrado.")
        return

    for i, r in enumerate(restaurants):
        print(f"  {i+1} - {r['nome']} ({r['tipo_culinaria']}) | Taxa: R$ {r['taxa_entrega']:.2f} | Tempo: {r['tempo_entrega_estimado']}")

    try:
        choice = int(input("Digite o número do restaurante: "))
        if not (1 <= choice <= len(restaurants)):
            print("Seleção inválida.")
            return
        selected_restaurant = restaurants[choice - 1]
    except (ValueError, IndexError):
        print("Seleção inválida.")
        return

    print(f"\n--- (Etapa 2: Monte seu Carrinho no {selected_restaurant['nome']}) ---")
    menu = db.get_restaurant_menu(selected_restaurant['id_restaurante'])
    if not menu:
        print("Este restaurante não possui um cardápio disponível.")
        return
        
    cart = []
    menu_items_list = []
    item_number = 1
    for category, dishes in menu.items():
        print(f"\n-- {category} --")
        for dish in dishes:
            if dish['status_disp']:
                print(f"  {item_number} - {dish['nome_prato']} - R$ {dish['preco']:.2f}")
                print(f"      ({dish['descricao']})")
                menu_items_list.append(dish)
                item_number += 1
    
    while True:
        try:
            dish_choice = input("\nDigite o número do prato para adicionar (ou 'fim' para fechar o carrinho): ")
            if dish_choice.lower() == 'fim':
                break
            
            dish_index = int(dish_choice) - 1
            if not (0 <= dish_index < len(menu_items_list)):
                print("Número de prato inválido.")
                continue
                
            selected_dish = menu_items_list[dish_index]
            
            qty = int(input(f"Quantidade de '{selected_dish['nome_prato']}': "))
            obs = input("Observações (opcional): ")
            
            cart.append({'dish': selected_dish, 'quantity': qty, 'observations': obs})
            print(f"'{selected_dish['nome_prato']}' adicionado ao carrinho!")

        except ValueError:
            print("Entrada inválida. Por favor, digite um número.")

    if not cart:
        print("Carrinho vazio. Pedido cancelado.")
        return
    
    selected_address_id = address_selection_flow(db, client_user_data['cliente_id'])
    if not selected_address_id:
        print("Endereço não selecionado. Pedido cancelado.")
        return

    selected_payment_id = payment_selection_flow(db)
    if not selected_payment_id:
        print("Forma de pagamento não selecionada. Pedido cancelado.")
        return
        
    print("\n--- (Etapa Final: Confirme seu Pedido) ---")
    subtotal_price = 0
    for item in cart:
        item_total = item['dish']['preco'] * item['quantity']
        print(f"  - {item['quantity']}x {item['dish']['nome_prato']} @ R$ {item['dish']['preco']:.2f} cada = R$ {item_total:.2f}")
        if item['observations']:
            print(f"    Obs: {item['observations']}")
        subtotal_price += item_total
    
    taxa_entrega = selected_restaurant['taxa_entrega']
    total_price = subtotal_price + taxa_entrega
    
    print("---------------------------------")
    print(f"  Subtotal dos Itens: R$ {subtotal_price:.2f}")
    print(f"  Taxa de Entrega:    R$ {taxa_entrega:.2f}")
    print(f"  VALOR TOTAL:        R$ {total_price:.2f}")
    
    confirm = input("Tudo certo? Enviar pedido? (s/n): ")
    if confirm.lower() == 's':
        pedido_id = db.create_order(
            client_user_data['cliente_id'], 
            selected_restaurant['id_restaurante'],
            selected_payment_id,
            selected_address_id,
            taxa_entrega
        )
        
        if pedido_id:
            for item in cart:
                db.add_order_item(
                    pedido_id, 
                    item['dish']['id_prato'], 
                    item['quantity'], 
                    item['dish']['preco'], 
                    item['observations']
                )
            # Ao criar o pedido, o status inicial é 'Pendente'
            db.update_order_status(pedido_id, StatusPedido.PENDENTE.value)
            print(f"\n✅ Pedido enviado com sucesso! O ID do seu pedido é: {pedido_id}")
        else:
            print("\n❌ Ocorreu um erro ao criar seu pedido. Tente novamente.")
    else:
        print("Pedido cancelado.")

# --- Painéis Pós-Login ---

def show_restaurant_panel(db, user_data):
    """Mostra o painel de opções interativo para restaurantes logados."""
    id_restaurante = user_data['restaurante_id']
    if not id_restaurante:
        print("Erro: Não foi possível identificar o restaurante associado a este usuário.")
        return

    while True:
        print(f"\n>> PAINEL DO RESTAURANTE (ID: {id_restaurante}) <<")
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

def manage_menu_flow_restaurant(db, id_restaurante):
    """Menu principal para gerenciamento do cardápio."""
    while True:
        print("\n--- Gerenciar Cardápio ---")
        print("  1 - Listar todos os pratos")
        print("  2 - Adicionar novo prato")
        print("  3 - Editar um prato existente")
        print("  4 - Voltar ao painel principal")

        choice = input("Sua opção: ")
        if choice == '1':
            list_dishes_restaurant(db, id_restaurante)
        elif choice == '2':
            print("\n--- Adicionar Novos Itens ao Cardápio ---")
            add_menu_flow(db, id_restaurante)
        elif choice == '3':
            edit_dish_restaurant(db, id_restaurante)
        elif choice == '4':
            break
        else:
            print("Opção inválida.")
        input("\nPressione Enter para continuar...")

def list_dishes_restaurant(db, id_restaurante):
    """Exibe o cardápio completo do restaurante para o admin."""
    menu = db.get_full_restaurant_menu_for_admin(id_restaurante)
    if not menu:
        print("Seu restaurante ainda não possui um cardápio cadastrado.")
        return

    print("\n--- Seu Cardápio Atual (Visão do Administrador) ---")
    for category, dishes in menu.items():
        print(f"\n-- {category} --")
        for dish in dishes:
            disponibilidade = "Disponível" if dish['status_disp'] else "Indisponível"
            print(f"  ID: {dish['id_prato']} | {dish['nome_prato']} - R$ {dish['preco']:.2f} [{disponibilidade}]")
    return menu

def edit_dish_restaurant(db, id_restaurante):
    """Fluxo para editar um prato existente."""
    print("\n--- Editar Prato ---")
    menu = list_dishes_restaurant(db, id_restaurante)
    if not menu:
        return
    
    try:
        prato_id_str = input("\nDigite o ID do prato que deseja editar (ou 'voltar'): ")
        if prato_id_str.lower() == 'voltar':
            return
        prato_id = int(prato_id_str)
        
        dish_details = db.get_dish_details(prato_id)
        if not dish_details:
             print("ID de prato inválido.")
             return

        print(f"\nEditando '{dish_details['nome_prato']}': (Deixe em branco para manter o valor atual)")
        
        novo_nome = input(f"  - Nome [{dish_details['nome_prato']}]: ") or dish_details['nome_prato']
        nova_descricao = input(f"  - Descrição [{dish_details['descricao']}]: ") or dish_details['descricao']

        while True:
            try:
                novo_preco_str = input(f"  - Preço [{dish_details['preco']:.2f}]: ")
                novo_preco = float(novo_preco_str) if novo_preco_str else dish_details['preco']
                break
            except ValueError:
                print("    > Preço inválido. Use ponto como separador decimal.")

        while True:
            disponibilidade_atual = "Disponível" if dish_details['status_disp'] else "Indisponível"
            nova_disp_str = input(f"  - Disponibilidade [{disponibilidade_atual}]. Alterar para (d/i)?: ").lower()
            
            if not nova_disp_str:
                nova_disponibilidade = dish_details['status_disp']
                break
            if nova_disp_str in ['d', 'i']:
                nova_disponibilidade = (nova_disp_str == 'd')
                break
            else:
                print("    > Opção inválida. Digite 'd' para disponível ou 'i' para indisponível.")

        db.edit_dish(prato_id, novo_nome, nova_descricao, novo_preco)
        if nova_disponibilidade != dish_details['status_disp']:
            db.update_dish_availability(prato_id, nova_disponibilidade)
        
        print("\n✅ Prato atualizado com sucesso!")

    except ValueError:
        print("Entrada inválida. Por favor, digite um número de ID.")

def manage_orders_flow_restaurant(db, id_restaurante):
    """Fluxo para o restaurante ver e atualizar o status dos pedidos."""
    orders = db.get_orders_for_restaurant(id_restaurante)
    if not orders:
        print("\nNenhum pedido recebido ainda.")
        return

    print("\n--- Pedidos Recebidos ---")
    order_ids = []
    for order in orders:
        order_ids.append(order['id_pedido'])
        print(f"  ID: {order['id_pedido']} | Data: {order['dataHora'].strftime('%d/%m/%Y %H:%M')}")
        print(f"  Cliente: {order['nome_completo']} | Valor: R$ {order['valor_total']:.2f}")
        print(f"  Status Atual: {order['status_pedido']}\n")

    try:
        pedido_id_str = input("Digite o ID do pedido para alterar o status (ou 'voltar'): ")
        if pedido_id_str.lower() == 'voltar':
            return
            
        pedido_id = int(pedido_id_str)
        if pedido_id not in order_ids:
            print("ID de pedido inválido ou não pertence a este restaurante.")
            return

        print("\nSelecione o novo status:")
        statuses = [s.value for s in StatusPedido]
        for i, status in enumerate(statuses):
            print(f"  {i+1} - {status}")
        
        status_choice = int(input("Sua opção: "))
        if 1 <= status_choice <= len(statuses):
            novo_status = statuses[status_choice - 1]
            db.update_order_status(pedido_id, novo_status)
            print(f"\n✅ Status do pedido {pedido_id} atualizado para '{novo_status}'.")
        else:
            print("Opção de status inválida.")

    except ValueError:
        print("Entrada inválida. Por favor, digite um número.")

def show_client_panel(db, user_data):
    """Mostra o painel de opções interativo para clientes logados."""
    id_cliente = user_data['cliente_id']
    if not id_cliente:
        print("Erro: Não foi possível identificar o cliente associado a este usuário.")
        return

    while True:
        print(f"\n>> ÁREA DO CLIENTE (ID de Cliente: {id_cliente}) <<")
        print("  1 - Fazer um Pedido")
        print("  2 - Ver Meus Pedidos")
        print("  3 - Logout")
        
        choice = input("Sua opção: ")
        if choice == '1':
            place_order_flow(db, user_data)
        elif choice == '2':
            view_orders_flow_client(db, id_cliente)
        elif choice == '3':
            break
        else:
            print("Opção inválida.")
        input("\nPressione Enter para continuar...")

def view_orders_flow_client(db, id_cliente):
    """Fluxo para o cliente visualizar seu histórico de pedidos."""
    orders = db.get_orders_for_client(id_cliente)
    if not orders:
        print("\nVocê ainda não fez nenhum pedido.")
        return

    print("\n--- Meus Pedidos ---")
    for order in orders:
        print(f"  ID: {order['id_pedido']} | Data: {order['dataHora'].strftime('%d/%m/%Y %H:%M')}")
        print(f"  Restaurante: {order['nome_restaurante']} | Valor: R$ {order['valor_total']:.2f}")
        print(f"  Status: {order['status_pedido']}\n")

# --- Função Principal ---

def main():
    """Função principal que exibe o menu e gerencia o fluxo do aplicativo."""
    db = None
    try:
        db = DatabaseManager()
    except Exception as e:
        print(f"Erro crítico ao conectar ao banco de dados: {e}", file=sys.stderr)
        sys.exit(1)
        
    try:
        while True:
            print("\n===== BEM-VINDO AO APP DE DELIVERY =====")
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
        if db:
            db.close()

if __name__ == "__main__":
    main()