import flet as ft
import json
import os
from datetime import datetime
import sqlite3

# Arquivos
USUARIOS_FILE = "usuarios.json"
DB_FILE = "usuarios.db"

# Verifica se o arquivo de usuários existe, senão cria um vazio
if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, "w") as f:
        json.dump({}, f)

# Cria a tabela de usuários no banco de dados se não existir
def criar_tabela_usuarios():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        senha TEXT
    )
    """)
    conn.commit()
    conn.close()

# Cria a tabela de movimentações no banco de dados se não existir
def criar_tabela_movimentacoes():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material TEXT,
        tipo TEXT,
        quantidade INTEGER,
        data TEXT,
        colaborador TEXT,
        lote TEXT,
        status TEXT,
        pagador TEXT,
        recebedor TEXT
    )
    """)
    conn.commit()
    conn.close()

# Função para adicionar movimentação no banco de dados
def adicionar_movimentacao_bd(material, tipo, quantidade, data, colaborador, lote):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO movimentacoes (material, tipo, quantidade, data, colaborador, lote, status) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (material, tipo, quantidade, data, colaborador, lote, "Pendente de Pagamento"))
    conn.commit()
    conn.close()

# Função para carregar as movimentações
def carregar_movimentacoes():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movimentacoes")
    movimentacoes = cursor.fetchall()
    conn.close()
    return movimentacoes

# Função para carregar usuários
def carregar_usuarios():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, senha FROM usuarios")
    usuarios = {usuario: senha for usuario, senha in cursor.fetchall()}
    conn.close()
    return usuarios

# Função para salvar usuários no banco de dados
def salvar_usuarios(usuarios):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for usuario, senha in usuarios.items():
        cursor.execute("INSERT OR REPLACE INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha))
    conn.commit()
    conn.close()

# Função para atualizar a tabela
def atualizar_tabela(page, tabela):
    tabela.rows.clear()
    movimentacoes = carregar_movimentacoes()
    for mov in movimentacoes:
        status = ft.Text(mov[7], color="green" if mov[7] == "Recebido" else "red")
        tabela.rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(mov[1])),  # material
            ft.DataCell(ft.Text(mov[2])),  # tipo
            ft.DataCell(ft.Text(str(mov[3]))),  # quantidade
            ft.DataCell(ft.Text(mov[4])),  # data
            ft.DataCell(ft.Text(mov[5])),  # colaborador
            ft.DataCell(ft.Text(mov[6])),  # lote
            ft.DataCell(status),
            ft.DataCell(ft.IconButton(ft.icons.CHECK, on_click=lambda e, idx=mov[0]: abrir_popup_pagador(e, page, idx, tabela))),
            ft.DataCell(ft.IconButton(ft.icons.PERSON, on_click=lambda e, idx=mov[0]: abrir_popup_recebedor(e, page, idx, tabela) if mov[7] == "Pago" else None))
        ]))
    page.update()

# Função para limpar os campos
def limpar_campos(material, tipo, quantidade, data, colaborador, lote, page):
    material.value = ""
    quantidade.value = ""
    data.value = datetime.now().strftime('%d/%m/%Y')
    lote.value = ""
    colaborador.value = None
    tipo.value = None
    page.update()

# Função para adicionar movimentação
def adicionar_movimentacao(e, page, material, tipo, quantidade, data, colaborador, lote, tabela):
    adicionar_movimentacao_bd(material.value, tipo.value, int(quantidade.value), data.value, colaborador.value, lote.value)
    atualizar_tabela(page, tabela)
    limpar_campos(material, tipo, quantidade, data, colaborador, lote, page)

# Função de autenticação do pagador
def abrir_popup_pagador(e, page, index, tabela):
    def confirmar_pagador(e):
        usuarios = carregar_usuarios()
        pagador = campo_pagador.value
        senha_pagador = campo_senha_pagador.value

        if pagador in usuarios and usuarios[pagador] == senha_pagador:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE movimentacoes SET status = ?, pagador = ? WHERE id = ?", 
                           ("Pago", pagador, index))
            conn.commit()
            conn.close()
            
            atualizar_tabela(page, tabela)
            page.dialog.open = False
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuário ou senha incorretos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    campo_pagador = ft.TextField(label="Usuário (Quem paga)")
    campo_senha_pagador = ft.TextField(label="Senha", password=True)

    popup = ft.AlertDialog(
        title=ft.Text("Autenticação do Pagador"),
        content=ft.Column([campo_pagador, campo_senha_pagador]),
        actions=[ft.TextButton("Confirmar", on_click=confirmar_pagador)]
    )
    page.dialog = popup
    popup.open = True
    page.update()

# Função de autenticação do recebedor
def abrir_popup_recebedor(e, page, index, tabela):
    def confirmar_recebedor(e):
        usuarios = carregar_usuarios()
        recebedor = campo_recebedor.value
        senha_recebedor = campo_senha_recebedor.value

        if recebedor in usuarios and usuarios[recebedor] == senha_recebedor:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE movimentacoes SET status = ?, recebedor = ? WHERE id = ?", 
                           ("Recebido", recebedor, index))
            conn.commit()
            conn.close()
            
            atualizar_tabela(page, tabela)
            page.dialog.open = False
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuário ou senha incorretos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    campo_recebedor = ft.TextField(label="Usuário (Quem recebe)")
    campo_senha_recebedor = ft.TextField(label="Senha", password=True)

    popup = ft.AlertDialog(
        title=ft.Text("Autenticação do Recebedor"),
        content=ft.Column([campo_recebedor, campo_senha_recebedor]),
        actions=[ft.TextButton("Confirmar", on_click=confirmar_recebedor)]
    )
    page.dialog = popup
    popup.open = True
    page.update()

# Função principal para a página
def pagina_principal(page: ft.Page):
    page.clean()
    page.title = "Controle de Pagamentos"
    page.window_width = 900
    page.window_height = 700
    page.scroll = ft.ScrollMode.AUTO

    campo_material = ft.TextField(label="Material", width=200)
    dropdown_tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Solicitação"), ft.dropdown.Option("Entrada")], width=200)
    campo_quantidade = ft.TextField(label="Quantidade", width=150, keyboard_type="number")
    campo_data = ft.TextField(label="Data", width=150, value=datetime.now().strftime('%d/%m/%Y'))
    dropdown_colaborador = ft.Dropdown(label="Colaborador", options=[ft.dropdown.Option(nome) for nome in ["Clay", "Ricardo", "Helton", "Daltino", "Yeda", "Wellingson", "Lucas", "Samuel", "Adriano"]], width=200)
    campo_lote = ft.TextField(label="Lote", width=150)

    campo_pesquisa_lote = ft.TextField(label="Pesquisar por Lote", width=200)

    tabela = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Material")),
        ft.DataColumn(ft.Text("Tipo")),
        ft.DataColumn(ft.Text("Quantidade")),
        ft.DataColumn(ft.Text("Data")),
        ft.DataColumn(ft.Text("Colaborador")),
        ft.DataColumn(ft.Text("Lote")),
        ft.DataColumn(ft.Text("Status")),
        ft.DataColumn(ft.Text("Pagamento")),
        ft.DataColumn(ft.Text("Recebimento"))
    ])

    def filtrar_por_lote(e):
        filtro_lote = campo_pesquisa_lote.value
        atualizar_tabela(page, tabela)

    campo_pesquisa_lote.on_change = filtrar_por_lote

    botao_adicionar = ft.ElevatedButton(text="Adicionar", on_click=lambda e: adicionar_movimentacao(e, page, campo_material, dropdown_tipo, campo_quantidade, campo_data, dropdown_colaborador, campo_lote, tabela))

    page.add(
        ft.Column([
            campo_material, dropdown_tipo, campo_quantidade, campo_data, dropdown_colaborador, campo_lote, botao_adicionar, campo_pesquisa_lote, tabela
        ])
    )

    atualizar_tabela(page, tabela)

# Inicializa o app
ft.app(target=pagina_principal)

