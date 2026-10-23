"""
Rede de distribuição - Entregável 1: histórico de períodos
Algoritmos e Estruturas de Dados - BCC - 2026.2

Estruturas de dados:
- lucros (dict id -> lucro): tabela hash da biblioteca. Os ids chegam a 10^9,
  então um vetor indexado por id é inviável; com no máximo 5000 vivos, a tabela
  dá busca/inserção/atualização em O(1) esperado (lista seria O(n) por busca;
  árvore balanceada, O(log n) sem precisarmos de ordem).
- total (int): soma dos lucros dos vivos, mantida incrementalmente, então L_k
  é lido em O(1) sem varrer os depósitos.
- kadane (dict com 5 campos): estado do Kadane online; MELHOR em O(1) sem
  reexaminar o histórico.
- pilha (list de pares [j, r]) + soma_pilha: pilha de prosperidade; append/pop
  no fim da list em O(1) amortizado; PROSPERIDADE em O(1).

Notação: n = depósitos vivos, P = períodos registrados, h = altura da pilha.
"""
import sys


def novo_kadane():
    """
    (a) Recebe: nada.
    (b) Devolve o estado inicial do Kadane online, um dict com os campos:
        - fim_soma, fim_ini: soma e início do melhor intervalo que termina no
          último período registrado (empate: menor início);
        - mi, mj, ms: melhor intervalo global [mi, mj] e sua soma ms
          (empate: menor i, depois menor j).
        Invariante: após registrar o período k, [mi, mj] é o melhor intervalo
        de 1..k e ms >= fim_soma.
    (c) O(1).
    """
    return {"fim_soma": 0, "fim_ini": 0, "mi": 0, "mj": 0, "ms": 0}


def atualizar_kadane(kadane, k, L):
    """
    (a) Recebe: kadane (estado de novo_kadane), k (período recém-registrado,
        k >= 1, chamado em ordem 1, 2, 3, ...) e L (= L_k).
    (b) Atualiza o melhor intervalo que termina em k e o melhor global.
        Estende com soma anterior >= 0 (e não > 0) para preservar o menor
        início em caso de empate. Não devolve nada.
    (c) O(1): poucas comparações e atribuições.
    """
    if k > 1 and kadane["fim_soma"] >= 0:
        kadane["fim_soma"] += L
    else:
        kadane["fim_soma"] = L
        kadane["fim_ini"] = k

    s, i = kadane["fim_soma"], kadane["fim_ini"]
    if (k == 1 or s > kadane["ms"]
            or (s == kadane["ms"] and (i, k) < (kadane["mi"], kadane["mj"]))):
        kadane["mi"], kadane["mj"], kadane["ms"] = i, k, s


def melhor(kadane):
    """
    (a) Recebe: kadane, com pelo menos um período registrado.
    (b) Devolve a string "i j S" do melhor intervalo. Não modifica nada.
    (c) O(1): leitura do estado mantido.
    """
    return f"{kadane['mi']} {kadane['mj']} {kadane['ms']}"


def atualizar_pilha(pilha, soma, k, L):
    """
    (a) Recebe: pilha (lista de pares [j, r], base em pilha[0], topo em
        pilha[-1]), soma (soma atual dos resíduos), k (período recém-registrado)
        e L (= L_k).
        Invariantes da pilha: todo r > 0; os j crescem da base ao topo;
        soma == soma dos r; se não vazia com base b, soma == L_b + ... + L_k.
    (b) Aplica a regra da pilha de prosperidade para L_k e devolve a nova
        soma. Modifica a pilha.
    (c) O(1) amortizado: cada elemento é empilhado uma vez e desempilhado no
        máximo uma vez, então o while não custa mais que os pushes anteriores.
    """
    if L > 0:
        pilha.append([k, L])
        soma += L
    elif L < 0:
        d = -L
        while d > 0 and pilha:
            j, r = pilha[-1]
            if r > d:                 # topo absorve o prejuízo todo
                pilha[-1][1] = r - d  # mantém o j original
                soma -= d
                d = 0
            else:                     # r <= d: topo consumido (inclusive exato)
                pilha.pop()
                soma -= r
                d -= r
        # se a pilha esvaziou e sobrou d, a sobra é descartada
    return soma                       # L == 0: nada muda


def prosperidade(pilha, soma):
    """
    (a) Recebe: a pilha e a soma dos resíduos.
    (b) Devolve "0" se a pilha está vazia; senão "h b s i r" (altura, período
        da base, soma dos resíduos, período e resíduo do topo).
    (c) O(1): len, base e topo por índice, soma já mantida.
    """
    if not pilha:
        return "0"
    b = pilha[0][0]
    i, r = pilha[-1]
    return f"{len(pilha)} {b} {soma} {i} {r}"


def main():
    """
    Ponto de ancoragem.
    (a) Recebe: a entrada padrão no formato do enunciado.
    (b) Lê setup, rotas (descartadas) e lotes; executa INSERIR, LUCRO, MELHOR
        e PROSPERIDADE e registra cada período ao fim do seu lote. Escreve uma
        linha por MELHOR/PROSPERIDADE na saída padrão.
    (c) O(tamanho da entrada): cada operação custa O(1) esperado/amortizado.
        Espaço: O(n + tamanho da entrada).
    """
    tokens = sys.stdin.read().split()
    n, m, T = int(tokens[0]), int(tokens[1]), int(tokens[2])
    pos = 3

    lucros = {}
    total = 0
    for _ in range(n):
        ident, x, y, lucro = (int(t) for t in tokens[pos:pos + 4])
        lucros[ident] = lucro
        total += lucro
        pos += 4
    pos += 3 * m                     # rotas: lidas e descartadas no E1

    kadane = novo_kadane()
    pilha = []
    soma_pilha = 0
    saida = []

    k = 1                            # período 1: logo após o setup
    atualizar_kadane(kadane, k, total)
    soma_pilha = atualizar_pilha(pilha, soma_pilha, k, total)

    P = int(tokens[pos])
    pos += 1
    for _ in range(P):               # um lote por período (2 até P+1)
        q = int(tokens[pos])
        pos += 1
        for _ in range(q):           # as q operações do lote
            op = tokens[pos]
            pos += 1
            if op == "INSERIR":
                ident, x, y, lucro, r = (int(t) for t in tokens[pos:pos + 5])
                pos += 5 + 3 * r     # pula as r rotas (não contam em q)
                lucros[ident] = lucro
                total += lucro
            elif op == "LUCRO":
                ident, lucro = int(tokens[pos]), int(tokens[pos + 1])
                pos += 2
                total += lucro - lucros[ident]  # ajusta pela diferença...
                lucros[ident] = lucro           # ...e só depois sobrescreve

            elif op == "MELHOR":
                saida.append(melhor(kadane))

            elif op == "PROSPERIDADE":
                saida.append(prosperidade(pilha, soma_pilha))

            elif op == "DIST":       # não aparece no E1; só consome o argumento
                pos += 1
            # PAR e REMOVER não aparecem no E1 e não têm argumentos

        k += 1                       # fim do lote: registra L_k
        atualizar_kadane(kadane, k, total)
        soma_pilha = atualizar_pilha(pilha, soma_pilha, k, total)

    if saida:
        print("\n".join(saida))

if __name__ == "__main__":
    main()
