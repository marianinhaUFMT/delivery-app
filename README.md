# Sistema de Delivery - Laboratório de Banco de Dados

## Descrição do Projeto

A plataforma simula um serviço de delivery de comida, permitindo que usuários se cadastrem como **clientes** ou **restaurantes**.

  * **Clientes** podem navegar pelos restaurantes disponíveis, visualizar seus cardápios, montar um carrinho, fazer pedidos e acompanhar o status da entrega.
  * **Restaurantes** possuem um painel administrativo para gerenciar seus dados, cardápio, horários de funcionamento, receber e atualizar o status dos pedidos em tempo real.

-----

## Funcionalidades Principais

### Para Clientes

  * Cadastro e Login de usuário.
  * Visualização da lista de restaurantes, com indicador de "Aberto" ou "Fechado".
  * Navegação pelo cardápio completo dos restaurantes.
  * Sistema de carrinho de compras funcional, permitindo adicionar, remover e atualizar itens.
  * Gerenciamento de múltiplos endereços de entrega.
  * Finalização de pedido com seleção de endereço e forma de pagamento.
  * Acompanhamento do status do pedido (`Pendente`, `Em Preparação`, etc.).
  * Sistema de avaliação do pedido após a entrega.

### Para Restaurantes

  * Cadastro e Login com perfil de restaurante.
  * Painel administrativo para gerenciamento.
  * Recebimento de novos pedidos em tempo real.
  * Atualização do status dos pedidos, notificando o cliente.
  * Gerenciamento completo do cardápio: criação de categorias e adição/edição/remoção de pratos.
  * Edição das informações do restaurante (nome, telefone, taxa de entrega, etc.).
  * Definição e edição dos horários de funcionamento para cada dia da semana.
  * Visualização das avaliações recebidas dos clientes.

-----

## Tecnologias Utilizadas

  * **Backend:**
      * **Python 3:** Linguagem de programação principal.
      * **Flask:** Micro-framework web para a criação das rotas e lógica da aplicação.
      * **Flask-SocketIO:** Para comunicação bidirecional em tempo real entre cliente e servidor.
  * **Frontend:**
      * **HTML5:** Estrutura das páginas.
      * **CSS3:** Estilização e design.
      * **JavaScript:** Interatividade e comunicação com o WebSocket.
  * **Banco de Dados:**
      * **MySQL:** Sistema de gerenciamento de banco de dados relacional.
      * **Railway:** Plataforma de nuvem para hospedagem do banco de dados MySQL.

-----

## Como Executar o Projeto

Siga os passos abaixo para configurar e rodar a aplicação em seu ambiente local.

### 1\. Pré-requisitos

  * Python 3.x instalado.
  * Dependências (estão abaixo).

2.  **Crie e ative um ambiente virtual:**

    ```bash
    # Para Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    A aplicação precisa de bibliotecas como `Flask`, `Flask-SocketIO`, `mysql-connector-python`, entre outras. Instale elas com os seguintes comandos:

    ```bash
    pip install Flask
    pip install Flask-SocketIO
    pip install mysql-connector-python
    pip install pytz
    pip install eventlet
    ```

4.  **Configure a Conexão com o Banco de Dados:**
    A aplicação se conecta a um banco de dados MySQL hospedado no site Railway. No nosso caso, já está configurado com as credenciais corretas para o banco em nuvem no arquivo `my.cnf`

### 2\. Executando a Aplicação

Com o ambiente configurado, inicie o servidor Flask:

```bash
python3 app.py
```

Abra seu navegador e acesse [http://127.0.0.1:5000](http://127.0.0.1:5000) para ver a aplicação funcionando.

-----

## Autores

  * Mariana
  * Anna Bheatryz
