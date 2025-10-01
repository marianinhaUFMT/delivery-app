DROP DATABASE IF EXISTS gerenciador_restaurantes;

CREATE DATABASE gerenciador_restaurantes;
USE gerenciador_restaurantes;

-- tabela usuario
CREATE TABLE IF NOT EXISTS usuario (
	usuario_id INT AUTO_INCREMENT,
	usuario VARCHAR(100) UNIQUE NOT NULL,
	email VARCHAR(100) UNIQUE NOT NULL,
	senha VARCHAR(100) NOT NULL,
	is_restaurante BOOLEAN NOT NULL DEFAULT FALSE,
	PRIMARY KEY (usuario_id)
	
);

-- tabela cliente
CREATE TABLE IF NOT EXISTS cliente (
    cliente_id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE, -- vincula ao login
    nome_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE
);

-- tabela enderecos_entrega (lista de enderecos por cliente)
CREATE TABLE IF NOT EXISTS enderecos_entrega (
    endereco_id INT AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    rua VARCHAR(100) NOT NULL,
    num VARCHAR(10) NOT NULL,
    bairro VARCHAR(100) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    estado VARCHAR(100) NOT NULL,
    cep VARCHAR(10) NOT NULL,
    PRIMARY KEY (endereco_id),
    FOREIGN KEY (cliente_id) REFERENCES cliente(cliente_id) ON DELETE CASCADE
);

-- tabela enderecos_restaurante (lista de enderecos por restaurante)
CREATE TABLE IF NOT EXISTS enderecos_restaurante (
    id_end_rest INT AUTO_INCREMENT,
    rua VARCHAR(100) NOT NULL,
    num VARCHAR(10) NOT NULL,
    bairro VARCHAR(100) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    estado VARCHAR(100) NOT NULL,
    cep VARCHAR(10) NOT NULL,
    PRIMARY KEY (id_end_rest)
);

-- tabela restaurante
CREATE TABLE IF NOT EXISTS restaurante (
    id_restaurante INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE, -- vincula ao login
    id_end_rest INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    tipo_culinaria VARCHAR(100) NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (id_end_rest) REFERENCES enderecos_restaurante(id_end_rest) ON DELETE CASCADE
);

-- tabela horarios_funcionamento_restaurante
CREATE TABLE IF NOT EXISTS horarios_funcionamento_restaurante(
    horario_funcionamento_id INT AUTO_INCREMENT,
    dia_semana ENUM('Domingo','Segunda','Terça','Quarta','Quinta','Sexta','Sábado') NOT NULL,
    horario_abertura TIME,
    horario_fechamento TIME,
    id_restaurante INT NOT NULL,
	PRIMARY KEY(horario_funcionamento_id),
    UNIQUE KEY(id_restaurante, dia_semana),
	FOREIGN KEY(id_restaurante) REFERENCES restaurante(id_restaurante) ON DELETE CASCADE
);

-- tabela avaliacoes_restaurante
CREATE TABLE IF NOT EXISTS avaliacoes_restaurante (
    id_avaliacao INT AUTO_INCREMENT,
    id_restaurante INT NOT NULL,
    id_cliente INT NOT NULL,
    nota INT CHECK (nota BETWEEN 0 AND 5),
    feedback VARCHAR(255),
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_avaliacao),
    FOREIGN KEY (id_restaurante) REFERENCES restaurante(id_restaurante) ON DELETE CASCADE,
    FOREIGN KEY (id_cliente) REFERENCES cliente(cliente_id) ON DELETE CASCADE
);

-- tabela categoria pratos
CREATE TABLE IF NOT EXISTS categoria_pratos (
    categoria_id INT AUTO_INCREMENT,
    id_restaurante INT NOT NULL,
    nome_categoria VARCHAR(100) NOT NULL,
    PRIMARY KEY (categoria_id),
    UNIQUE KEY (id_restaurante, nome_categoria),
    FOREIGN KEY (id_restaurante) REFERENCES restaurante(id_restaurante) ON DELETE CASCADE
);

-- tabela pratos
CREATE TABLE IF NOT EXISTS pratos (
    id_prato INT AUTO_INCREMENT,
    categoria_id INT NOT NULL,
    nome_prato VARCHAR(100) NOT NULL,
    descricao VARCHAR(255),
    preco DECIMAL(10, 2) NOT NULL,
    status_disp BOOLEAN DEFAULT TRUE, -- true = disponivel, false = indisponivel
    PRIMARY KEY (id_prato),
    FOREIGN KEY (categoria_id) REFERENCES categoria_pratos(categoria_id) ON DELETE CASCADE
);

-- tabela forma_pagamento
CREATE TABLE IF NOT EXISTS forma_pagamento (
    id_forma_pagamento INT AUTO_INCREMENT,
    descricao VARCHAR(100) NOT NULL,
    PRIMARY KEY (id_forma_pagamento)
);

-- tabela pedido
CREATE TABLE IF NOT EXISTS pedido (
    id_pedido INT AUTO_INCREMENT,
    id_cliente INT NOT NULL,
    id_restaurante INT NOT NULL,
    id_forma_pagamento INT NOT NULL,
    endereco_id INT NOT NULL,        -- A coluna que faltava
    dataHora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_pedido ENUM('Pendente', 'Em Preparação', 'Em Trânsito', 'Entregue', 'Cancelado') DEFAULT 'Pendente',
    valor_total DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (id_pedido),
    FOREIGN KEY (id_cliente) REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    FOREIGN KEY (id_restaurante) REFERENCES restaurante(id_restaurante) ON DELETE CASCADE,
    FOREIGN KEY (id_forma_pagamento) REFERENCES forma_pagamento(id_forma_pagamento),
    FOREIGN KEY (endereco_id) REFERENCES enderecos_entrega(endereco_id) ON DELETE RESTRICT -- A chave estrangeira que faltava
);

-- tabela item_pedido
CREATE TABLE IF NOT EXISTS item_pedido (
    id_pedido INT NOT NULL,
    id_prato INT NOT NULL,
    qtd INT NOT NULL CHECK (qtd > 0),
    preco_item DECIMAL(10, 2) NOT NULL,
    observacoes VARCHAR(255),
    PRIMARY KEY (id_pedido, id_prato),
    FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido) ON DELETE CASCADE,
    FOREIGN KEY (id_prato) REFERENCES pratos(id_prato) ON DELETE RESTRICT
);

-- tabela produtos
CREATE TABLE IF NOT EXISTS produtos(
	produto_id INT AUTO_INCREMENT,
    estoque INT NOT NULL CHECK (estoque >= 0),
    nome_produto VARCHAR(64),
    PRIMARY KEY(produto_id)
);

-- atualiza valor total automaticamente ao inserir item no pedido
CREATE TRIGGER trg_valor_total
AFTER INSERT ON item_pedido
FOR EACH ROW
BEGIN
    UPDATE pedido
    SET valor_total = valor_total + (NEW.qtd * NEW.preco_item)
    WHERE id_pedido = NEW.id_pedido;
END;

-- funcao calcular nota media restaurante
CREATE FUNCTION fn_media_avaliacao(rest_id INT)
RETURNS DECIMAL(3,2)
DETERMINISTIC
BEGIN
    DECLARE media DECIMAL(3,2);
    SELECT AVG(nota) INTO media
    FROM avaliacoes_restaurante
    WHERE id_restaurante = rest_id;
    RETURN IFNULL(media, 0);
END;

-- funcao calcular total pedidos restaurante
CREATE FUNCTION fn_valor_pedido(pedido_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT SUM(qtd * preco_item) INTO total
    FROM item_pedido
    WHERE id_pedido = pedido_id;
    RETURN IFNULL(total, 0);
END;

-- criar pedido completo
CREATE PROCEDURE sp_criar_pedido(
    IN p_cliente_id INT,
    IN p_restaurante_id INT
)
BEGIN
    INSERT INTO pedido (id_cliente, id_restaurante, valor_total)
    VALUES (p_cliente_id, p_restaurante_id, 0);
END;

-- alterar status pedido
CREATE PROCEDURE sp_alterar_status(
    IN p_pedido_id INT,
    IN p_status ENUM('Pendente','Em Preparação','Em Trânsito','Entregue','Cancelado')
)
BEGIN
    UPDATE pedido
    SET status_pedido = p_status
    WHERE id_pedido = p_pedido_id;
END;
 -- registrar avaliacao
 CREATE PROCEDURE sp_avaliar_restaurante(
    IN p_restaurante_id INT,
    IN p_cliente_id INT,
    IN p_nota INT,
    IN p_feedback VARCHAR(255)
)
BEGIN
    INSERT INTO avaliacoes_restaurante(id_restaurante, id_cliente, nota, feedback)
    VALUES (p_restaurante_id, p_cliente_id, p_nota, p_feedback);
END;

# Alterações futuras: adicionar taxa de entrega e tempo estimado de entrega na tabela restaurante
ALTER TABLE restaurante 
ADD COLUMN taxa_entrega DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
ADD COLUMN tempo_entrega_estimado VARCHAR(50);

--SELECT usuario_id, is_restaurante FROM usuario WHERE usuario = 'rest1';

-- Substitua '5' pelo ID que você encontrou
--SELECT * FROM restaurante WHERE usuario_id = 2;

ALTER TABLE pedido
ADD COLUMN foi_avaliado BOOLEAN NOT NULL DEFAULT FALSE;

-- 1. Adiciona a coluna para ligar a avaliação ao pedido
ALTER TABLE avaliacoes_restaurante ADD COLUMN id_pedido INT NULL AFTER id_cliente;

-- 2. Faz a coluna de data e hora ser preenchida automaticamente
ALTER TABLE avaliacoes_restaurante MODIFY COLUMN data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;