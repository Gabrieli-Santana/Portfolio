import sqlite3
from datetime import datetime


def criar_tabela():
    """Cria a tabela de gastos se não existir"""
    conn = sqlite3.connect('gastos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gastos
                 (id INTEGER PRIMARY KEY, data TEXT, categoria TEXT, valor REAL, descricao TEXT)''')
    conn.commit()
    conn.close()
    print("✅ Tabela 'gastos' criada/verificada com sucesso!")


def adicionar_gasto():
    """Adiciona um novo gasto ao banco de dados"""
    print("\n➕ ADICIONAR NOVO GASTO")

    data = input("Data (DD/MM/AAAA) ou Enter para hoje: ").strip()
    if not data:
        data = datetime.now().strftime("%d/%m/%Y")

    categoria = input("Categoria (alimentacao, transporte, lazer, etc): ").strip()
    valor = float(input("Valor: R$ "))
    descricao = input("Descrição: ").strip()

    conn = sqlite3.connect('gastos.db')
    c = conn.cursor()
    c.execute('''INSERT INTO gastos (data, categoria, valor, descricao) VALUES (?, ?, ?, ?)''', (data, categoria, valor, descricao))
    conn.commit()
    conn.close()
    print("✅ Gasto adicionado com sucesso!")


def listar_gastos():
    """Lista todos os gastos cadastrados"""
    print("\n📋 LISTA DE GASTOS")

    conn = sqlite3.connect('gastos.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM gastos ORDER BY data DESC''')
    gastos = c.fetchall()
    conn.close()

    if not gastos:
        print("Nenhum gasto cadastrado.")
        return

    total = 0
    print("-" * 60)
    print(f"{'ID':<3} {'Data':<12} {'Categoria':<15} {'Valor':<10} {'Descrição'}")
    print("-" * 60)

    for gasto in gastos:
        id_gasto, data, categoria, valor, descricao = gasto
        total += valor
        print(f"{id_gasto:<3} {data:<12} {categoria:<15} R$ {valor:<7.2f} {descricao}")

    print("-" * 60)
    print(f"TOTAL: R$ {total:.2f}")


def resumir_por_categoria():
    """Mostra resumo dos gastos por categoria"""
    print("\n📊 RESUMO POR CATEGORIA")

    conn = sqlite3.connect('gastos.db')
    c = conn.cursor()
    c.execute('''SELECT categoria, SUM(valor) as total
                 FROM gastos
                 GROUP BY categoria
                 ORDER BY total DESC''')
    categorias = c.fetchall()
    conn.close()

    if not categorias:
        print("Nenhum gasto para resumir.")
        return

    total_geral = 0
    print("-" * 30)
    print(f"{'Categoria':<15} {'Total'}")
    print("-" * 30)

    for categoria, total in categorias:
        total_geral += total
        print(f"{categoria:<15} R$ {total:.2f}")

    print("-" * 30)
    print(f"{'TOTAL GERAL':<15} R$ {total_geral:.2f}")


def menu_principal():
    """Menu interativo do sistema"""
    while True:
        print("\n" + "=" * 40)
        print("💰 GERENCIADOR DE GASTOS PESSOAIS")
        print("=" * 40)
        print("1. Adicionar gasto")
        print("2. Listar todos os gastos")
        print("3. Resumo por categoria")
        print("4. Sair")
        print("-" * 40)

        opcao = input("Escolha uma opção (1-4): ").strip()

        if opcao == "1":
            adicionar_gasto()
        elif opcao == "2":
            listar_gastos()
        elif opcao == "3":
            resumir_por_categoria()
        elif opcao == "4":
            print("👋 Saindo do sistema...")
            break
        else:
            print("❌ Opção inválida! Tente novamente.")


# Execução principal
if __name__ == "__main__":
    criar_tabela()  # Garante que a tabela existe
    menu_principal()