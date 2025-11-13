X = "X"
O = "O"
VAZIO = ""

tabuleiro = [VAZIO, VAZIO, VAZIO,
             VAZIO, VAZIO, VAZIO,
             VAZIO, VAZIO, VAZIO]

jogada = 0
jogo_valido = True
vencedor = False

jogador1 = input("Escolha X ou O: ").upper()
if jogador1 == X:
    jogador2 = O
else:
    jogador2 = X


def mostrar_tabuleiro():
    for i in range(0, 9, 3):
        print(f"{i} | {i + 1} | {i + 2}      {tabuleiro[i]} | {tabuleiro[i + 1]} | {tabuleiro[i + 2]}")


mostrar_tabuleiro()

while jogo_valido:
    jogada += 1
    casa = int(input("Escolha onde jogar (0-8): "))

    if jogada % 2 == 1:        tabuleiro[casa] = jogador1
    else:
        tabuleiro[casa] = jogador2

    mostrar_tabuleiro()

    # Verificar vitória - HORIZONTAL
    for i in range(0, 9, 3):
        if tabuleiro[i] == tabuleiro[i + 1] == tabuleiro[i + 2] != VAZIO:
            vencedor = tabuleiro[i]
            break

    # Verificar vitória - VERTICAL
    if not vencedor:
        for i in range(3):
            if tabuleiro[i] == tabuleiro[i + 3] == tabuleiro[i + 6] != VAZIO:
                vencedor = tabuleiro[i]
                break

    # Verificar vitória - DIAGONAL
    if not vencedor:
        if tabuleiro[0] == tabuleiro[4] == tabuleiro[8] != VAZIO:
            vencedor = tabuleiro[0]
        elif tabuleiro[2] == tabuleiro[4] == tabuleiro[6] != VAZIO:
            vencedor = tabuleiro[2]

    # Verificar se há vencedor ou empate
    if vencedor:
        jogo_valido = False
        print(f"Vencedor: {vencedor}")
    elif VAZIO not in tabuleiro:
        jogo_valido = False
        print("Jogo empatou: Deu velha!")