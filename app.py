from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, join_room, leave_room # MODIFICADO
from database_manager import DatabaseManager
from enum import Enum
import os

class StatusPedido(Enum):
    PENDENTE = 'Pendente'
    EM_PREPARACAO = 'Em Preparação'
    EM_TRANSITO = 'Em Trânsito'
    ENTREGUE = 'Entregue'
    CANCELADO = 'Cancelado'

app = Flask(__name__)
app.secret_key = os.urandom(24)
db = DatabaseManager()

# INICIALIZAÇÃO DO SOCKET.IO
socketio = SocketIO(app)

# --- ROTAS DE AUTENTICAÇÃO E CADASTRO ---

@app.route("/")
def index():
    if 'user_id' in session:
        if session.get('is_restaurante'):
            return redirect(url_for('painel_restaurante'))
        else:
            return redirect(url_for('painel_cliente'))
    return redirect(url_for('login'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['password']
        user_data = db.login_user(usuario, senha)
        
        if user_data:
            session['user_id'] = user_data['usuario_id']
            session['is_restaurante'] = user_data.get('is_restaurante', False)
            flash('Login bem-sucedido!', 'success')
            
            if session['is_restaurante']:
                if 'restaurante_id' in user_data and user_data['restaurante_id'] is not None:
                    session['restaurante_id'] = user_data['restaurante_id']
                    session['cliente_id'] = None
                    return redirect(url_for('painel_restaurante'))
                else:
                    flash('Erro: Conta de restaurante inválida. Contate o suporte.', 'danger')
                    return redirect(url_for('login'))
            else:
                if 'cliente_id' in user_data and user_data['cliente_id'] is not None:
                    session['cliente_id'] = user_data['cliente_id']
                    session['restaurante_id'] = None
                    return redirect(url_for('painel_cliente'))
                else:
                    flash('Erro: Conta de cliente inválida. Contate o suporte.', 'danger')
                    return redirect(url_for('login'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route("/pre_cadastro")
def pre_cadastro():
    return render_template('pre_cadastro.html')

@app.route("/cadastro_cliente", methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        # Coleta dados do formulário
        usuario = request.form['usuario']
        nome_completo = request.form['nome_completo']
        email = request.form['email']
        telefone = request.form['telefone']
        cpf = request.form['cpf']
        senha = request.form['senha']
        
        cliente_id = db.create_client(usuario, email, senha, nome_completo, telefone, cpf)
        
        if cliente_id:
            flash('Cadastro realizado com sucesso! Faça seu login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Usuário ou email já existem. Tente novamente.', 'danger')
            return redirect(url_for('cadastro_cliente'))
            
    return render_template('cadastro_cliente.html')

# Em app.py

@app.route("/cadastro_restaurante", methods=['GET', 'POST'])
def cadastro_restaurante():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        senha = request.form['senha']
        nome = request.form['nome']
        telefone = request.form['telefone']
        tipo_culinaria = request.form['tipo_culinaria']
        taxa_entrega = request.form['taxa_entrega']
        tempo_estimado = request.form['tempo_estimado']
        
        endereco = {
            "rua": request.form['rua'], "num": request.form['num'], "bairro": request.form['bairro'],
            "cidade": request.form['cidade'], "estado": request.form['estado'], "cep": request.form['cep']
        }

        # A função create_restaurant precisa retornar mais detalhes para o login automático
        # VAMOS PRECISAR ALTERAR ELA TAMBÉM (ver próximo passo)
        novo_restaurante_data = db.create_restaurant(
            usuario, email, senha, nome, telefone, tipo_culinaria,
            endereco, taxa_entrega, tempo_estimado
        )
        
        if novo_restaurante_data:
            # --- LÓGICA DE LOGIN AUTOMÁTICO ADICIONADA ---
            session['user_id'] = novo_restaurante_data['usuario_id']
            session['is_restaurante'] = True
            session['restaurante_id'] = novo_restaurante_data['restaurante_id']
            session['cliente_id'] = None
            
            flash('Restaurante cadastrado com sucesso! Agora, por favor, configure seus horários de funcionamento.', 'success')
            
            # --- REDIRECIONAMENTO INTELIGENTE ---
            return redirect(url_for('restaurante_horarios'))
        else:
            flash('Erro ao cadastrar restaurante. O nome de usuário ou email podem já estar em uso.', 'danger')
            return redirect(url_for('cadastro_restaurante'))
            
    return render_template('cadastro_restaurante.html')


# --- ROTAS DO CLIENTE E CARDÁPIO ---
@app.route("/painel_cliente")
def painel_cliente():
    if 'user_id' not in session or session.get('is_restaurante'):
        flash('Faça login para continuar.', 'danger')
        return redirect(url_for('login'))
    restaurantes = db.get_all_restaurants()
    return render_template('painel_cliente.html', restaurantes=restaurantes)

@app.route('/meus_pedidos')
def meus_pedidos():
    # Verifica se o usuário é um cliente logado
    if 'user_id' not in session or session.get('is_restaurante'):
        flash('Faça login como cliente para ver seus pedidos.', 'danger')
        return redirect(url_for('login'))

    # Pega o id do cliente da sessão
    cliente_id = session['cliente_id']
    
    # Usa a função que já existe no database_manager para buscar os pedidos
    pedidos = db.get_orders_for_client(cliente_id)

    # Renderiza a nova página, passando a lista de pedidos para ela
    return render_template('meus_pedidos.html', pedidos=pedidos)

# ROTA PARA A PÁGINA DE AVALIAÇÃO
# app.py

@app.route('/avaliar_pedido/<int:pedido_id>', methods=['GET', 'POST'])
def avaliar_pedido(pedido_id):
    if 'user_id' not in session or session.get('is_restaurante'):
        return redirect(url_for('login'))

    cliente_id = session['cliente_id']
    pedidos_cliente = db.get_orders_for_client(cliente_id)
    pedido_info = next((p for p in pedidos_cliente if p['id_pedido'] == pedido_id), None)

    if not pedido_info or pedido_info['status_pedido'] != 'Entregue' or pedido_info['foi_avaliado']:
        flash('Este pedido não pode ser avaliado.', 'danger')
        return redirect(url_for('meus_pedidos'))

    if request.method == 'POST':
        nota = request.form.get('nota')
        feedback = request.form.get('feedback')
        
        # Primeiro, precisamos garantir que o id_restaurante está vindo da consulta
        # Verifique se a sua função get_orders_for_client está selecionando p.id_restaurante
        if 'id_restaurante' not in pedido_info:
             flash('Erro: Não foi possível identificar o restaurante. Contate o suporte.', 'danger')
             return redirect(url_for('meus_pedidos'))
        
        restaurante_id = pedido_info['id_restaurante']
        
        # --- CORREÇÃO APLICADA AQUI ---
        db.add_review(pedido_id, restaurante_id, cliente_id, nota, feedback)
        
        # Marca o pedido como avaliado
        db.mark_order_as_reviewed(pedido_id)
        
        flash('Obrigado pela sua avaliação!', 'success')
        return redirect(url_for('meus_pedidos'))

    return render_template('avaliar_pedido.html', pedido=pedido_info)

# ROTA PARA O RESTAURANTE VER AS AVALIAÇÕES
@app.route("/painel_restaurante/avaliacoes")
def restaurante_avaliacoes():
    if 'user_id' not in session or not session.get('is_restaurante'):
        return redirect(url_for('login'))
    
    id_restaurante = session['restaurante_id']
    avaliacoes = db.get_reviews_for_restaurant(id_restaurante)
    return render_template('restaurante_avaliacoes.html', avaliacoes=avaliacoes)

@app.route('/meus_enderecos')
def meus_enderecos():
    if 'user_id' not in session or session.get('is_restaurante'):
        flash('Faça login como cliente para continuar.', 'danger')
        return redirect(url_for('login'))

    cliente_id = session['cliente_id']
    enderecos = db.get_client_addresses(cliente_id)
    return render_template('meus_enderecos.html', enderecos=enderecos)

# Em app.py, substitua a função menu_restaurante
@app.route("/restaurante/<int:restaurante_id>")
def menu_restaurante(restaurante_id):
    if 'user_id' not in session or session.get('is_restaurante'):
        flash('Faça login para continuar.', 'danger')
        return redirect(url_for('login'))

    # Usamos get_restaurant_details para pegar as infos e verificamos o status separadamente
    restaurante_info = db.get_restaurant_details(restaurante_id)

    if not restaurante_info:
        return "Restaurante não encontrado", 404
        
    # Verifica se está aberto
    restaurante_esta_aberto = db.is_restaurant_open(restaurante_id)

    menu = db.get_restaurant_menu(restaurante_id)
    
    # Passa a informação 'aberto' para o template
    return render_template('menu_restaurante.html', menu=menu, restaurante=restaurante_info, aberto=restaurante_esta_aberto)

# Em app.py

@app.route("/painel_restaurante/horarios", methods=['GET', 'POST'])
def restaurante_horarios():
    if 'user_id' not in session or not session.get('is_restaurante'):
        return redirect(url_for('login'))

    id_restaurante = session['restaurante_id']
    
    if request.method == 'POST':
        horarios = {}
        dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        for dia in dias_semana:
            # Verifica se o dia foi "ativado" pelo checkbox
            if f"ativo_{dia}" in request.form:
                abertura = request.form.get(f"abertura_{dia}")
                fechamento = request.form.get(f"fechamento_{dia}")
                horarios[dia] = {'abertura': abertura, 'fechamento': fechamento}
            else:
                 # Se o dia não está ativo, envia horários vazios para apagar do banco
                horarios[dia] = {'abertura': None, 'fechamento': None}
        
        if db.update_schedule(id_restaurante, horarios):
            flash('Horários atualizados com sucesso!', 'success')
        else:
            flash('Erro ao atualizar os horários.', 'danger')
        
        return redirect(url_for('restaurante_horarios'))

    # Se for GET, busca os horários existentes para preencher o formulário
    horarios_atuais_lista = db.get_restaurant_schedule(id_restaurante)
    # Converte a lista para um dicionário para fácil acesso no template
    horarios_atuais = {h['dia_semana']: h for h in horarios_atuais_lista}
    
    dias_semana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']

    return render_template('restaurante_horarios.html', horarios=horarios_atuais, dias_semana=dias_semana)


# --- ROTAS DO CARRINHO E CHECKOUT ---
@app.route('/carrinho/adicionar', methods=['POST'])
def adicionar_ao_carrinho():
    if 'user_id' not in session or session.get('is_restaurante'):
        return redirect(url_for('login'))

    prato_id = request.form.get('prato_id')
    restaurante_id = int(request.form.get('restaurante_id'))

    # --- VERIFICAÇÃO ADICIONADA ---
    if not db.is_restaurant_open(restaurante_id):
        flash('Desculpe, este restaurante está fechado e não está aceitando pedidos no momento.', 'danger')
        return redirect(url_for('menu_restaurante', restaurante_id=restaurante_id))
    # --- FIM DA VERIFICAÇÃO ---

    if 'cart' not in session:
        session['cart'] = {'items': {}, 'restaurante_id': None, 'taxa_entrega': 0.0}

    if session['cart']['restaurante_id'] and session['cart']['restaurante_id'] != restaurante_id:
        flash('Você só pode adicionar itens de um restaurante por vez! Esvazie seu carrinho para continuar.', 'danger')
        return redirect(url_for('menu_restaurante', restaurante_id=restaurante_id))

    prato_details = db.get_dish_details(prato_id)
    if not prato_details:
        return "Prato não encontrado", 404

    cart_items = session['cart']['items']
    if prato_id in cart_items:
        cart_items[prato_id]['quantidade'] += 1
    else:
        cart_items[prato_id] = {
            'nome': prato_details['nome_prato'],
            'preco': float(prato_details['preco']),
            'quantidade': 1
        }
    
    if not session['cart']['restaurante_id']:
        restaurantes = db.get_all_restaurants()
        restaurante_info = next((r for r in restaurantes if r['id_restaurante'] == restaurante_id), None)
        if restaurante_info:
            session['cart']['restaurante_id'] = restaurante_id
            session['cart']['taxa_entrega'] = float(restaurante_info['taxa_entrega'])

    session.modified = True
    flash(f"'{prato_details['nome_prato']}' foi adicionado ao seu carrinho!", 'success')
    return redirect(request.referrer)

@app.route('/carrinho')
def ver_carrinho():
    if 'user_id' not in session or session.get('is_restaurante'):
        return redirect(url_for('login'))

    cart = session.get('cart', {'items': {}})
    subtotal = sum(item['preco'] * item['quantidade'] for item in cart.get('items', {}).values())
    taxa_entrega = cart.get('taxa_entrega', 0.0)
    total = subtotal + taxa_entrega
    
    return render_template('carrinho.html', cart=cart, subtotal=subtotal, total=total, taxa_entrega=taxa_entrega)

@app.route('/carrinho/remover/<prato_id>')
def remover_item_carrinho(prato_id):
    if 'cart' in session and prato_id in session['cart']['items']:
        session['cart']['items'].pop(prato_id)
        if not session['cart']['items']:
            session.pop('cart')
        session.modified = True
        flash('Item removido do carrinho.', 'info')
    return redirect(url_for('ver_carrinho'))

@app.route('/carrinho/atualizar', methods=['POST'])
def atualizar_carrinho():
    prato_id = request.form.get('prato_id')
    quantidade = int(request.form.get('quantidade', 1))

    if 'cart' in session and prato_id in session['cart']['items']:
        if quantidade > 0:
            session['cart']['items'][prato_id]['quantidade'] = quantidade
        else:
            session['cart']['items'].pop(prato_id)
        
        if not session['cart']['items']:
            session.pop('cart')
        session.modified = True
    return redirect(url_for('ver_carrinho'))
    
# app.py

@app.route('/checkout')
def checkout():
    if 'user_id' not in session or not session.get('cart'):
        return redirect(url_for('painel_cliente'))
        
    cliente_id = session['cliente_id']
    enderecos = db.get_client_addresses(cliente_id)
    formas_pagamento = db.get_payment_methods()
    
    cart = session.get('cart', {'items': {}})
    subtotal = sum(item['preco'] * item['quantidade'] for item in cart.get('items', {}).values())
    taxa_entrega = cart.get('taxa_entrega', 0.0)
    total = subtotal + taxa_entrega
    
    # MODIFICADO: Adicionado 'taxa_entrega=taxa_entrega' à lista de argumentos
    return render_template('checkout.html', 
                           cart=cart, 
                           subtotal=subtotal, 
                           total=total, 
                           taxa_entrega=taxa_entrega,  # <-- A variável que faltava
                           enderecos=enderecos, 
                           formas_pagamento=formas_pagamento)

@app.route('/adicionar_endereco', methods=['GET', 'POST'])
def adicionar_endereco():
    if 'user_id' not in session or session.get('is_restaurante'):
        flash('Faça login como cliente para continuar.', 'danger')
        return redirect(url_for('login'))

    cliente_id = session['cliente_id']
    # Pega o parâmetro 'origem' para saber para onde voltar
    origem = request.args.get('origem', 'painel_cliente') 

    if request.method == 'POST':
        rua = request.form['rua']
        num = request.form['num']
        bairro = request.form['bairro']
        cidade = request.form['cidade']
        estado = request.form['estado']
        cep = request.form['cep']

        endereco_id = db.add_client_address(cliente_id, rua, num, bairro, cidade, estado, cep)

        if endereco_id:
            flash('Endereço cadastrado com sucesso!', 'success')
            # Volta para a página de onde o usuário veio
            return redirect(url_for(origem))
        else:
            flash('Erro ao cadastrar endereço. Tente novamente.', 'danger')

    return render_template('adicionar_endereco.html', origem=origem)

@app.route('/editar_endereco/<int:endereco_id>', methods=['GET', 'POST'])
def editar_endereco(endereco_id):
    if 'user_id' not in session or session.get('is_restaurante'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        endereco = {
            "rua": request.form['rua'], "num": request.form['num'], "bairro": request.form['bairro'],
            "cidade": request.form['cidade'], "estado": request.form['estado'], "cep": request.form['cep']
        }
        if db.update_client_address(endereco_id, endereco):
            flash('Endereço atualizado com sucesso!', 'success')
        else:
            flash('Erro ao atualizar o endereço.', 'danger')
        return redirect(url_for('meus_enderecos'))

    # Se for GET, busca os dados e exibe o formulário
    endereco = db.get_address_details(endereco_id)
    if not endereco:
        return "Endereço não encontrado", 404
    
    return render_template('editar_endereco.html', endereco=endereco)


@app.route('/excluir_endereco/<int:endereco_id>')
def excluir_endereco(endereco_id):
    if 'user_id' not in session or session.get('is_restaurante'):
        return redirect(url_for('login'))
        
    if db.delete_client_address(endereco_id):
        flash('Endereço excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir o endereço.', 'danger')
        
    return redirect(url_for('meus_enderecos'))


@app.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    if 'user_id' not in session or not session.get('cart'):
        return redirect(url_for('login'))
        
    endereco_id = request.form.get('endereco_id')
    pagamento_id = request.form.get('pagamento_id')
    
    if not endereco_id or not pagamento_id:
        flash('Por favor, selecione um endereço e uma forma de pagamento.', 'danger')
        return redirect(url_for('checkout'))

    cart = session.get('cart')
    cliente_id = session.get('cliente_id')
    restaurante_id = cart['restaurante_id']
    taxa_entrega = cart['taxa_entrega']
    
    pedido_id = db.create_order(cliente_id, restaurante_id, pagamento_id, endereco_id, taxa_entrega)
    
    if pedido_id:
        for prato_id, item_details in cart['items'].items():
            db.add_order_item(
                pedido_id, prato_id, item_details['quantidade'],
                item_details['preco'], ""
            )
        db.update_order_status(pedido_id, StatusPedido.PENDENTE.value)
        
        # --- PARTE MODIFICADA ---
        # Após salvar, busca os dados completos do novo pedido
        pedidos_restaurante = db.get_orders_for_restaurant(restaurante_id)
        novo_pedido_info = next((p for p in pedidos_restaurante if p['id_pedido'] == pedido_id), None)
        if novo_pedido_info:
            # Emite o evento 'novo_pedido' apenas para a "sala" do restaurante específico
            socketio.emit('novo_pedido', novo_pedido_info, room=f'restaurante_{restaurante_id}')
        # --- FIM DA MODIFICAÇÃO ---

        session.pop('cart', None)
        return redirect(url_for('pedido_confirmado', pedido_id=pedido_id))
    else:
        flash('Ocorreu um erro ao processar seu pedido. Tente novamente.', 'danger')
        return redirect(url_for('checkout'))

@app.route('/pedido_confirmado/<int:pedido_id>')
def pedido_confirmado(pedido_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('pedido_confirmado.html', pedido_id=pedido_id)


# --- ROTAS DO PAINEL DO RESTAURANTE ---

@app.route("/painel_restaurante")
def painel_restaurante():
    if 'user_id' not in session or not session.get('is_restaurante'):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('login'))

    id_restaurante = session['restaurante_id']
    pedidos = db.get_orders_for_restaurant(id_restaurante)
    
    return render_template('painel_restaurante.html', pedidos=pedidos, statuses=StatusPedido)

@app.route("/painel_restaurante/cardapio")
def restaurante_cardapio():
    if 'user_id' not in session or not session.get('is_restaurante'):
        return redirect(url_for('login'))
    
    id_restaurante = session['restaurante_id']
    menu = db.get_full_restaurant_menu_for_admin(id_restaurante)
    return render_template('restaurante_cardapio.html', menu=menu)

@app.route("/painel_restaurante/categoria/adicionar", methods=['POST'])
def adicionar_categoria():
    if 'user_id' not in session or not session.get('is_restaurante'):
        return redirect(url_for('login'))

    id_restaurante = session['restaurante_id']
    nome_categoria = request.form.get('nome_categoria')

    if nome_categoria:
        # Chama a função que já existe no database_manager
        db.add_dish_category(id_restaurante, nome_categoria)
        flash(f"Categoria '{nome_categoria}' adicionada com sucesso!", 'success')
    else:
        flash('O nome da categoria não pode ser vazio.', 'danger')

    # Redireciona de volta para a página do cardápio para ver a nova categoria
    return redirect(url_for('restaurante_cardapio'))


@app.route("/painel_restaurante/prato/adicionar", methods=['GET', 'POST'])
def adicionar_prato():
    if 'user_id' not in session or not session.get('is_restaurante'):
        return redirect(url_for('login'))

    id_restaurante = session['restaurante_id']
    if request.method == 'POST':
        categoria_id = request.form.get('categoria_id')
        nome_prato = request.form.get('nome_prato')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco')
        
        db.add_dish(categoria_id, nome_prato, descricao, preco)
        flash('Prato adicionado com sucesso!', 'success')
        return redirect(url_for('restaurante_cardapio'))

    categorias = db.get_restaurant_categories(id_restaurante)
    return render_template('restaurante_form_prato.html', categorias=categorias)


@app.route("/painel_restaurante/prato/editar/<int:prato_id>", methods=['GET', 'POST'])
def editar_prato(prato_id):
    if 'user_id' not in session or not session.get('is_restaurante'):
        return redirect(url_for('login'))

    id_restaurante = session['restaurante_id']
    
    if request.method == 'POST':
        nome = request.form.get('nome_prato')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco')
        categoria_id = request.form.get('categoria_id')
        status = bool(int(request.form.get('status_disp')))

        db.edit_dish(prato_id, nome, descricao, preco, categoria_id)
        db.update_dish_availability(prato_id, status)
        
        # --- PARTE MODIFICADA ---
        # Avisa todos que estão vendo o cardápio sobre a mudança de disponibilidade
        update_data = {'prato_id': prato_id, 'status_disp': status}
        socketio.emit('cardapio_atualizado', update_data, room=f'menu_restaurante_{id_restaurante}')
        # --- FIM DA MODIFICAÇÃO ---

        flash('Prato atualizado com sucesso!', 'success')
        return redirect(url_for('restaurante_cardapio'))

    prato = db.get_dish_details(prato_id)
    if not prato:
        return "Prato não encontrado", 404
        
    categorias = db.get_restaurant_categories(id_restaurante)
    return render_template('restaurante_form_prato.html', prato=prato, categorias=categorias)

@app.route("/painel_restaurante/endereco", methods=['GET', 'POST'])
def restaurante_endereco():
    if 'user_id' not in session or not session.get('is_restaurante'):
        return redirect(url_for('login'))

    id_restaurante = session['restaurante_id']
    restaurante = db.get_restaurant_details(id_restaurante)
    
    if request.method == 'POST':
        db.update_restaurant_details(
            id_restaurante,
            request.form['nome'], request.form['telefone'], request.form['tipo_culinaria'],
            request.form['taxa_entrega'], request.form['tempo_estimado']
        )
        endereco = { "rua": request.form['rua'], "num": request.form['num'], "bairro": request.form['bairro'],
                     "cidade": request.form['cidade'], "estado": request.form['estado'], "cep": request.form['cep'] }
        db.update_restaurant_address(restaurante['id_end_rest'], endereco)
        
        flash('Dados atualizados com sucesso!', 'success')
        return redirect(url_for('painel_restaurante'))

    return render_template('restaurante_endereco.html', restaurante=restaurante)

@app.route("/pedido/atualizar_status/<int:pedido_id>", methods=['POST'])
def atualizar_status_pedido(pedido_id):
    if 'user_id' not in session or not session.get('is_restaurante'):
        return redirect(url_for('login'))

    novo_status = request.form.get('status')
    if novo_status:
        db.update_order_status(pedido_id, novo_status)
        flash(f'Status do pedido #{pedido_id} atualizado para "{novo_status}"!', 'success')

        # --- PARTE MODIFICADA ---
        # Avisa o cliente sobre a mudança de status
        pedido_details = db.get_order_details(pedido_id)
        if pedido_details and pedido_details.get('id_cliente'):
            id_cliente = pedido_details['id_cliente']
            dados_update = {'pedido_id': pedido_id, 'novo_status': novo_status}
            # Emite o evento 'status_atualizado' para a sala privada do cliente
            socketio.emit('status_atualizado', dados_update, room=f'cliente_{id_cliente}')
        # --- FIM DA MODIFICAÇÃO ---
            
    return redirect(url_for('painel_restaurante'))

# --- LÓGICA DO WEBSOCKET ---

@socketio.on('connect')
def handle_connect():
    """Executado quando um navegador se conecta. Coloca o usuário em sua sala privada."""
    if 'user_id' not in session:
        return

    if session.get('is_restaurante'):
        restaurante_id = session.get('restaurante_id')
        if restaurante_id:
            join_room(f'restaurante_{restaurante_id}')
            print(f"Restaurante {restaurante_id} entrou na sua sala privada.")
    else:
        cliente_id = session.get('cliente_id')
        if cliente_id:
            join_room(f'cliente_{cliente_id}')
            print(f"Cliente {cliente_id} entrou na sua sala privada.")

@socketio.on('join_menu_room')
def handle_join_menu_room(data):
    """Executado quando um cliente abre a página de um cardápio."""
    restaurante_id = data.get('restaurante_id')
    if restaurante_id:
        join_room(f'menu_restaurante_{restaurante_id}')
        print(f"Um usuário entrou na sala do cardápio do restaurante {restaurante_id}.")

@socketio.on('leave_menu_room')
def handle_leave_menu_room(data):
    """Executado quando um cliente sai da página de um cardápio."""
    restaurante_id = data.get('restaurante_id')
    if restaurante_id:
        leave_room(f'menu_restaurante_{restaurante_id}')
        print(f"Um usuário saiu da sala do cardápio do restaurante {restaurante_id}.")


if __name__ == '__main__':
    socketio.run(app, debug=True)