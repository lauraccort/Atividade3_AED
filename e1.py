"""
Algoritmos e Estruturas de Dados
Rede de distribuição - Entregável 1: histórico de períodos
Laura da Costa Corte Cordeiro e Ana Helena de Souza Macedo

Estruturas de dados usadas:
- lucros (dicionário id : lucro, biblioteca do Python, tabela hash): os ids
  chegam a 10^9, então um vetor indexado por id é inviável; com no máximo
  5000 depósitos vivos, a tabela dá busca, inserção e atualização em O(1)
  esperado.
  Invariante: contém os depósitos vivos e o lucro atual de cada.
- total (inteiro): soma dos lucros dos depósitos vivos, mantida
  atualizada por INSERIR (+= L) e LUCRO (+= novo - antigo), para que
  L_k seja lido em O(1) sem varrer os depósitos.
  Invariante: após cada operação, total == soma dos valores de lucros.
- kadane (dicionário): estado da soma máxima de subvetor consecutivo 
  (algoritmo de Kadane), atualizado a cada período, para que
  MELHOR seja respondido sem reexaminar o histórico.
  Invariantes: após registrar o período k: fim_soma é a maior soma de um
  intervalo que termina em k, e fim_ini é o menor início com essa soma;
  [mi, mj] é o melhor intervalo de 1 até k (empate: menor i, depois menor j)
  e ms é a sua soma.
- pilha (lista do Python usada como pilha, de pares [j, r]) e soma_pilha
  (inteiro): pilha de prosperidade; append e pop no fim da lista custam O(1)
  amortizado, e a soma dos resíduos é mantida junto, para que PROSPERIDADE
  seja respondida sem percorrer a pilha.
  Invariantes: todo resíduo r é > 0; os j crescem da base (pilha[0]) para o
  topo (pilha[-1]); soma_pilha == soma dos r; se a pilha não está vazia e b
  é o j da base, soma_pilha == L_b + ... + L_k.
- saida (lista de strings): respostas acumuladas e impressas de uma vez no
  final; append em O(1) amortizado.

Notações: n = depósitos vivos, P = períodos registrados, h = altura da pilha.
"""
import sys

def novo_kadane():
    """
    (a) Recebe: nada.
    (b) Devolve o estado inicial da soma máxima de subvetor consecutivo
        (algoritmo de Kadane), um dicionário com fim_soma e
        fim_ini (soma e início do melhor intervalo que termina no último
        período) e mi, mj, ms (melhor intervalo global [mi, mj] e sua soma).
    (c) O(1).
    """
    return {"fim_soma" : 0, "fim_ini": 0, "mi" : 0, "mj" : 0, "ms" : 0}

def atualizar_kadane(kadane, k, L):
    """
    (a) Recebe: kadane (criado por novo_kadane), k (período registrado, 
        chamado em ordem crescente e contínua a partir de 1) 
        e L (lucro L_k).
    (b) Atualiza o melhor intervalo que termina em k (estende se a soma
        anterior for >= 0, o que mantém o menor início no empate; senão
        recomeça em k) e o melhor intervalo global. Não devolve nada e
        modifica o kadane.
    (c) O(1): poucas operações e atribuições.
    """
    if k > 1 and kadane["fim_soma"] >= 0:
        kadane["fim_soma"] += L
    else:
        kadane["fim_soma"] = L
        kadane["fim_ini"] = k

    s, i = kadane["fim_soma"], kadane["fim_ini"]
    if (k == 1 or s > kadane["ms"] or (s == kadane["ms"] and (i, k) < (kadane["mi"], kadane["mj"]))):
        kadane["mi"], kadane["mj"], kadane["ms"] = i, k, s

def melhor(kadane):
    """
    (a) Recebe: kadane, com pelo menos um período registrado.
    (b) Devolve a string "i j S" do melhor intervalo de períodos já
        registrados. Não modifica nada.
    (c) O(1): só lê o estado mantido por atualizar_kadane.
    """
    return f"{kadane["mi"]} {kadane["mj"]} {kadane["ms"]}"

def atualizar_pilha(pilha, soma, k, L):
    """
    (a) Recebe: pilha (lista de pares [j, r], base em pilha[0], topo em
        pilha[-1], todo r > 0), soma (soma atual dos resíduos), k (período
        registrado) e L (lucro L_k).
    (b) Aplica a regra da pilha de prosperidade: L > 0 empilha (k, L);
        L = 0 não muda nada; L < 0 consome o prejuízo a partir do topo,
        reduzindo ou desempilhando elementos (a sobra é descartada).
        Devolve a nova soma dos resíduos; modifica a pilha.
    (c) O(1) amortizado: cada elemento é empilhado uma vez e desempilhado no
        máximo uma vez, então o while não custa mais que os pushes.
    """
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
    """
    (a) Recebe: a pilha de prosperidade e a soma dos seus resíduos.
    (b) Devolve "0" se a pilha estiver vazia; senão "h b s i r" (altura,
        período da base, soma dos resíduos, período e resíduo do topo).
        Não modifica nada.
    (c) O(1): len, base e topo por índice, soma já mantida.
    """
    if not pilha:
        return "0"
    b = pilha[0][0]
    i, r = pilha[-1]

    return f"{len(pilha)} {b} {soma} {i} {r}"

def main():
    """
    (a) Recebe: a entrada padrão conforme o enunciado.
    (b) Lê o setup inicial (rotas descartadas), executa INSERIR, LUCRO, MELHOR e
        PROSPERIDADE de cada lote e registra cada período ao fim do seu lote.
        Escreve uma linha por MELHOR e PROSPERIDADE na saída padrão.
    (c) Por comando: INSERIR e LUCRO O(1) esperado (dicionário); MELHOR e
        PROSPERIDADE O(1); registro de período O(1) amortizado. Total
        O(tamanho da entrada). Espaço: O(n + tamanho da entrada).
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
    pos += 3*m

    kadane = novo_kadane()
    pilha = []
    soma_pilha = 0
    saida = []

    k = 1                            
    atualizar_kadane(kadane, k, total)
    soma_pilha = atualizar_pilha(pilha, soma_pilha, k, total)

    P = int(tokens[pos])
    pos += 1
    for _ in range(P):          
        q = int(tokens[pos])
        pos += 1
        for _ in range(q):     
            op = tokens[pos]
            pos += 1

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