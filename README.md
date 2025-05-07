  # Processador de Consultas SQL

  Este projeto implementa um processador de consultas SQL com interface gráfica interativa usando Streamlit. O projeto visa demonstrar os conceitos de processamento e otimização de consultas SQL estudados em bancos de dados.

  ## Funcionalidades

  1. **Parser SQL**: Analisa e valida consultas SQL
  2. **Conversão para Álgebra Relacional**: Transforma consultas SQL em expressões de álgebra relacional
  3. **Otimizador**: Implementa heurísticas para otimizar consultas
  4. **Grafo de Operadores**: Visualiza o plano de execução da consulta
  5. **Plano de Execução**: Mostra a ordem de execução das operações

  ## Heurísticas de Otimização Implementadas

  - Aplicação prioritária de operações que reduzem o tamanho dos resultados intermediários:
    - Operações de seleção (redução de tuplas)
    - Operações de projeção (redução de atributos)
  - Execução prioritária das operações de seleção e junção mais restritivas
  - Reordenação dos nós folha da árvore de consulta
  - Evitar operações de produto cartesiano quando possível

  ## Tecnologias Utilizadas

  - **Python**: Linguagem principal do projeto
  - **Streamlit**: Interface gráfica interativa
  - **NetworkX**: Geração e manipulação de grafos
  - **Matplotlib**: Visualização dos grafos
  - **sqlparse**: Parsing de consultas SQL

  ## Estrutura do Projeto

  ```
  app/
  │
  ├── main.py                  # Aplicação Streamlit principal
  ├── parser.py                # Módulo para parser SQL
  ├── relational_algebra.py    # Convertedor SQL para álgebra relacional
  ├── optimizer.py             # Otimizador baseado em heurísticas
  ├── graph_generator.py       # Gerador de grafo de operadores
  ├── execution_plan.py        # Gerador de plano de execução
  └── metadata.py              # Definição dos metadados das tabelas
  ```

  ## Como Executar

1. **Crie e ative um ambiente virtual (venv):**

   *No Windows:*
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

   *No Linux/MacOS:*
   ```
   python -m venv venv
   source venv/bin/activate
   ```

2. **Instale as dependências usando o requirements.txt:**
   ```
   pip install -r requirements.txt
   ```

   (Certifique-se de que o arquivo requirements.txt contém todas as dependências necessárias)

3. **Execute a aplicação:**
   ```
   streamlit run app/main.py
   ```

4. **Acesse a interface através do navegador (geralmente em http://localhost:8501)**

  ## Exemplos de Consultas

  O sistema vem com consultas de exemplo que podem ser carregadas diretamente na interface:

  - Consulta Simples: `SELECT Nome, Email FROM Cliente WHERE idCliente > 5`
  - Consulta com JOIN: `SELECT p.Nome, c.Descricao FROM Produto p JOIN Categoria c ON p.Categoria_idCategoria = c.idCategoria`
  - Consulta Complexa: `Select cliente.nome, pedido.idPedido, pedido.DataPedido, pedido.ValorTotalPedido from Cliente Join pedido on cliente.idcliente = pedido.Cliente_idCliente where cliente.TipoCliente_idTipoCliente = 1 and pedido.ValorTotalPedido = 0;`

  ## Mais exemplos de Querys

  - Consulta 1:
  ```
  Select cliente.nome, pedido.idPedido, pedido.DataPedido, pedido.ValorTotalPedido
  from Cliente Join pedido on cliente.idcliente = pedido.Cliente_idCliente
  where cliente.TipoCliente_idTipoCliente = 1 and pedido.ValorTotalPedido = 0;
  ```

  - Consulta 2:
  ```
  Select cliente.nome, pedido.idPedido, pedido.DataPedido, Status.descricao, pedido.ValorTotalPedido
  from Cliente Join pedido on cliente.idcliente = pedido.Cliente_idCliente
  Join Status on Status.idstatus = Pedido.status_idstatus
  where Status.descricao = 'Aberto' and cliente.TipoCliente_idTipoCliente = 1 and pedido.ValorTotalPedido = 0;
  ```

  - Consulta 3:
  ```
  Select cliente.nome, pedido.idPedido, pedido.DataPedido, Status.descricao, pedido.ValorTotalPedido, produto.QuantEstoque
  from Cliente Join pedido on cliente.idcliente = pedido.Cliente_idCliente
  Join Status on Status.idstatus = Pedido.status_idstatus
  Join pedido_has_produto on pedido.idPedido = pedido_has_produto.Pedido_idPedido
  Join produto on produto.idProduto = pedido_has_produto.Produto_idProduto
  where Status.descricao = 'Aberto' and cliente.TipoCliente_idTipoCliente = 1 and pedido.ValorTotalPedido = 0 and produto.QuantEstoque > 0;
  ```

  - Consulta 4:
  ```
  Select cliente.nome, tipocliente.descricao, pedido.idPedido, pedido.DataPedido, Status.descricao, pedido.ValorTotalPedido, categoria.descricao, produto.QuantEstoque
  from Cliente Join pedido on cliente.idcliente = pedido.Cliente_idCliente
  Join tipocliente on cliente.tipocliente_idtipocliente = tipocliente.idTipoCliente
  Join endereco on cliente.idcliente = endereco.Cliente_idCliente
  Join Status on Status.idstatus = Pedido.status_idstatus
  Join pedido_has_produto on pedido.idPedido = pedido_has_produto.Pedido_idPedido
  Join produto on produto.idProduto = pedido_has_produto.Produto_idProduto
  Join categoria on categoria.idcategoria = produto.Categoria_idCategoria
  where Status.descricao = 'Aberto' and cliente.email = 'Luffy@gmail.com' and pedido.ValorTotalPedido = 0 
  and produto.preco > 5000 and endereco.cidade = 'Gramado';
  ```

  ## Metadados do Banco

  O projeto utiliza um esquema de banco de dados predefinido com as seguintes tabelas:
  - Categoria
  - Produto
  - TipoCliente
  - Cliente
  - TipoEndereco
  - Endereco
  - Telefone
  - Status
  - Pedido
  - Pedido_has_Produto

  Os detalhes das colunas de cada tabela estão disponíveis na interface.