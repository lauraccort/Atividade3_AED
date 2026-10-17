import sys
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

    periodos = []
    periodos.append(total)

    P = int(tokens[pos])
    pos += 1
    for _ in range(P):          # um lote por período (2 até P+1)
        q = int(tokens[pos])
        pos += 1
        for _ in range(q):      # as q operações do lote
            op = tokens[pos]
            pos += 1
            # aqui entra o tratamento de cada operação
        periodos.append(total)  # fim do lote: registra L_k

    if op == " INSERIR":
        ident, x, y, lucro, r = (int(t) for t in tokens[pos:pos + 5])
        pos += 5 + 3 * r          
        lucros[ident] = lucro
        total += lucro

    elif op == "LUCRO":
        ident, lucro = int(tokens[pos]), int(tokens[pos+1])
        pos += 2
        total += lucro - lucros[ident]
        lucros[ident] = lucro
        
if __name__ == "__main__":
    main()