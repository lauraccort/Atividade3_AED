import sys

def novo_kadane():
    return {"fim_soma" : 0, "fim_ini": 0, "mi" : 0, "mj" : 0, "ms" : 0}

def atualizar_kadane(kadane, k, L):
    if k > 1 and kadane["fim_soma"] >= 0:
        kadane["fim_soma"] += L
    else:
        kadane["fim_soma"] = L
        kadane["fim_ini"] = k

    s, i = kadane["fim_soma"], kadane["fim_ini"]
    if (k == 1 or s > kadane["ms"] or (s == kadane["ms"] and (i, k) < (kadane["mi"], kadane["mj"]))):
        kadane["mi"], kadane["mj"], kadane["ms"] = i, k, s

def melhor(kadane):
    return f"{kadane["mi"]} {kadane["mj"]} {kadane["ms"]}"

def atualizar_pilha(pilha, soma, k, L):
    if L > 0:
        pilha.append([k, L])
        soma += L
    elif L < 0:
        d = -L
        while d > 0 and pilha:
            j, r = pilha[-1]
            if r > d:
                pilha[-1][1] = r - d
                soma -= d
                d = 0
            else:
                pilha.pop()
                soma -= r
                d -= r
    return soma

def prosperidade(pilha, soma):
    if not pilha:
        return "0"
    b = pilha[0][0]
    i, r = pilha[-1]

    return f"{len(pilha)} {b} {soma} {i} {r}"

def main():
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
    pos += 3*m

    kadane = novo_kadane()
    pilha = []
    soma_pilha = 0
    saida = []

    k = 1                            # período 1: logo após o setup
    atualizar_kadane(kadane, k, total)
    soma_pilha = atualizar_pilha(pilha, soma_pilha, k, total)

    P = int(tokens[pos])
    pos += 1
    for _ in range(P):          # um lote por período (2 até P+1)
        q = int(tokens[pos])
        pos += 1
        for _ in range(q):      # as q operações do lote
            op = tokens[pos]
            pos += 1
            # aqui entra o tratamento de cada operação

            if op == "INSERIR":
                ident, x, y, lucro, r = (int(t) for t in tokens[pos:pos + 5])
                pos += 5 + 3 * r          
                lucros[ident] = lucro
                total += lucro

            elif op == "LUCRO":
                ident, lucro = int(tokens[pos]), int(tokens[pos+1])
                pos += 2
                total += lucro - lucros[ident]
                lucros[ident] = lucro

            elif op == "MELHOR":
                saida.append(melhor(kadane))

            elif op == "PROSPERIDADE":
                saida.append(prosperidade(pilha, soma_pilha))

        k += 1                      
        atualizar_kadane(kadane, k, total)
        soma_pilha = atualizar_pilha(pilha, soma_pilha, k, total)

    if saida:
        print("\n".join(saida))
        
if __name__ == "__main__":
    main()