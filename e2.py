"""
Algoritmos e Estruturas de Dados
Rede de distribuição - Entregável 2: fechamento e proximidade
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
from math import isqrt

def novo_heap():
    """
    (a) Recebe: nada.
    (b) 
    (c) O(1).
    """
    return {"ids": [], "chaves": [], "pos": {}}

def heap_subir(heap, i):
    """
    (a) Recebe: heap e i, índice válido; o heap vale em todo ponto 
    exceto, talvez, entre i e seu pai.
    (b) Sobe o elemento de i até restaurar a propriedade de heap, atualizando
        pos a cada movimento. Modifica o heap.
    (c) O(log n): no máximo a altura do heap, O(1) por nível.
    """
    ids, chaves, pos = heap["ids"], heap["chaves"], heap["pos"]
    ident, chave = ids[i], chaves[i]
    while i > 0:
        pai = (i - 1) // 2
        if chaves[pai] <= chave:
            break
        ids[i], chaves[i] = ids[pai], chaves[pai]   
        pos[ids[i]] = i
        i = pai
    ids[i], chaves[i] = ident, chave
    pos[ident] = i

def heap_descer(heap, i):
    """
    (a) Recebe: heap e i, índice válido; o heap vale em todo ponto exceto,
        talvez, entre i e seus filhos.
    (b) Desce o elemento de i, trocando com o menor filho, até restaurar a
        propriedade de heap, atualizando pos. Modifica o heap.
    (c) O(log n): no máximo a altura do heap, O(1) por nível.
    """
    ids, chaves, pos = heap["ids"], heap["chaves"], heap["pos"]
    tam = len(ids)
    ident, chave = ids[i], chaves[i]
    while True:
        filho = 2 * i + 1
        if filho >= tam:
            break
        if filho + 1 < tam and chaves[filho + 1] < chaves[filho]:
            filho += 1                                
        if chaves[filho] >= chave:
            break
        ids[i], chaves[i] = ids[filho], chaves[filho]  
        pos[ids[i]] = i
        i = filho
    ids[i], chaves[i] = ident, chave
    pos[ident] = i

def heap_inserir(heap, ident, chave):
    """
    (a) Recebe: heap, id que ainda não está no heap e chave.
    (b) Coloca o elemento no fim e o sobe. Modifica o heap.
    (c) O(log n): append O(1) amortizado e um heap_subir.
    """
    heap["ids"].append(ident)
    heap["chaves"].append(chave)
    heap["pos"][ident] = len(heap["ids"]) - 1
    heap_subir(heap, len(heap["ids"]) - 1)

def heap_alterar(heap, ident, chave):
    """
    (a) Recebe: heap, id presente no heap e uma nova chave.
    (b) Troca a chave e reposiciona: sobe se diminuiu, desce se aumentou.
        Modifica o heap.
    (c) O(log n): busca em pos O(1) esperado e um heap_subir ou heap_descer.
    """
    i = heap["pos"][ident]
    antiga = heap["chaves"][i]
    heap["chaves"][i] = chave
    if chave < antiga:
        heap_subir(heap, i)
    elif chave > antiga:
        heap_descer(heap, i)

def heap_remover(heap, ident):
    """
    (a) Recebe: heap e id presente no heap.
    (b) Remove o elemento: o último ocupa o lugar dele e é reposicionado
        (sobe ou desce). Modifica o heap.
    (c) O(log n): pop O(1) e um heap_subir ou heap_descer.
    """
    ids, chaves, pos = heap["ids"], heap["chaves"], heap["pos"]
    i = pos.pop(ident)
    ultimo_id = ids.pop()
    ultima_chave = chaves.pop()
    if i == len(ids):                 
        return
    ids[i], chaves[i] = ultimo_id, ultima_chave
    pos[ultimo_id] = i
    if i > 0 and chaves[(i - 1) // 2] > ultima_chave:
        heap_subir(heap, i)
    else:
        heap_descer(heap, i)

def nova_rede():
    """
    (a) Recebe: nada.
    (b) Devolve uma rede vazia, um dicionário com os campos:
        - lucros (dicionário id : lucro) e coords (dicionário id : (x, y)) dos vivos;
        - fila (heap de novo_heap): um elemento por vivo, chave = lucro;
        - total (int): soma dos lucros dos vivos;
        - par_cache (str ou None): resposta do PAR para os vivos atuais, ou
          None se precisa ser recalculada.
        Invariantes entre as operações:
        - lucros, coords e fila têm exatamente os mesmos ids, e a chave de
          cada id na fila é lucros[id];
        - total == soma de lucros.values();
        - par_cache, se não for None, é a resposta correta para os vivos
          atuais (inserir ou remover zera; mudar lucro não afeta).
    (c) O(1).
    """
    return {"lucros": {}, "coords": {}, "fila": novo_heap(),
            "total": 0, "par_cache": None}

def inserir_deposito(rede, ident, x, y, lucro):
    """
    (a) Recebe: rede, id novo (nunca usado), coordenadas x, y e lucro.
    (b) Cria o depósito vivo em lucros, coords e fila, soma o lucro ao total e
        invalida par_cache. Modifica a rede.
    (c) O(log n): inserções em dict O(1) esperado e heap_inserir O(log n).
    """
    rede["lucros"][ident] = lucro
    rede["coords"][ident] = (x, y)
    heap_inserir(rede["fila"], ident, lucro)
    rede["total"] += lucro
    rede["par_cache"] = None

def mudar_lucro(rede, ident, lucro):
    """
    (a) Recebe: rede, ident (depósito vivo) e o novo lucro.
    (b) Ajusta o total pela diferença, grava o novo lucro e reposiciona o
        depósito na fila, as coordenadas não mudam.
    (c) O(log n): acesso ao dict O(1) esperado e heap_alterar O(log n).
    """
    rede["total"] += lucro - rede["lucros"][ident]
    rede["lucros"][ident] = lucro
    heap_alterar(rede["fila"], ident, lucro)

def remover_deposito(rede, ident):
    """
    (a) Recebe: rede e ident (depósito vivo).
    (b) Função única de remoção: tira o depósito de fila, lucros e coords,
        desconta o lucro do total e invalida par_cache. Modifica a rede.
    (c) O(log n): heap_remover O(log n) e remoções em dict O(1) esperado.
    """
    heap_remover(rede["fila"], ident)
    rede["total"] -= rede["lucros"].pop(ident)
    del rede["coords"][ident]
    rede["par_cache"] = None

def remover_abaixo(rede, T):
    """
    (a) Recebe: rede e a tolerância mínima de lucro (T).
    (b) Fecha todos os vivos com lucro estritamente menor que T. 
    Devolve quantos foram removidos e modifica a rede.
    (c) O((k+1) log n), com k removidos: cada remoção custa O(log n) e o
        teste do topo é O(1); os demais vivos não são examinados.
    """
    fila = rede["fila"]
    removidos = 0
    while fila["ids"] and fila["chaves"][0] < T:
        remover_deposito(rede, fila["ids"][0])
        removidos += 1
    return removidos

def par_rec(pts, lo, hi):
    """
    (a) Recebe: pts, lista de tuplas (x, y, id) com pts[lo:hi] ordenado por
        x (empates por y); lo e hi com hi - lo >= 2. 
    (b) Devolve (d2, a, b): o menor quadrado de distância entre dois pontos
        de pts[lo:hi] e os ids desses pontos. Ao terminar, pts[lo:hi] fica
        ordenado por y (modifica pts nesse trecho).
        Divide ao meio por índice (não por valor de x, que pode repetir),
        resolve as metades e depois procura, na faixa vertical em torno da
        divisória com (x - xm)^2 < d2, pares que cruzam as metades.
    (c) O(m log m), m = hi - lo: T(m) = 2T(m/2) + O(m). O passo O(m) é a
        junção das metades por y (sorted reconhece as duas sequências já
        ordenadas e só as intercala), a montagem da faixa e sua varredura,
        em que cada ponto é comparado com O(1) vizinhos (no máximo 7: num
        retângulo d x 2d cabem poucos pontos a distância >= d entre si).
        Espaço adicional O(m); profundidade da recursão O(log m).
    """
    if hi - lo <= 3:                                  
        melhor_par = None
        for i in range(lo, hi):
            xi, yi, ai = pts[i]
            for j in range(i + 1, hi):
                xj, yj, aj = pts[j]
                d2 = (xi - xj) ** 2 + (yi - yj) ** 2
                if melhor_par is None or d2 < melhor_par[0]:
                    melhor_par = (d2, ai, aj)
        pts[lo:hi] = sorted(pts[lo:hi], key=lambda p: p[1])
        return melhor_par

    meio = (lo + hi) // 2
    xm = pts[meio][0]               
    esq = par_rec(pts, lo, meio)
    dir_ = par_rec(pts, meio, hi)
    melhor_par = esq if esq[0] <= dir_[0] else dir_

    pts[lo:hi] = sorted(pts[lo:hi], key=lambda p: p[1])   # junção por y
    d2_min = melhor_par[0]
    faixa = [p for p in pts[lo:hi] if (p[0] - xm) ** 2 < d2_min]
    for i in range(len(faixa)):
        xi, yi, ai = faixa[i]
        for j in range(i + 1, len(faixa)):
            xj, yj, aj = faixa[j]
            dy = yj - yi
            if dy * dy >= d2_min:   
                break
            d2 = (xi - xj) ** 2 + dy * dy
            if d2 < d2_min:
                d2_min = d2
                melhor_par = (d2, ai, aj)
    return melhor_par

def par(rede):
    """
    (a) Recebe: rede, com pelo menos dois vivos de coordenadas distintas.
    (b) Devolve "a b d": ids a < b do par mais próximo e a distância
        arredondada para cima, em aritmética inteira (menor t com
        t*t >= d2). Usa par_cache se válido; senão ordena os pontos por x,
        chama par_rec e guarda a resposta em par_cache.
    (c) O(n log n) sem cache (ordenação + par_rec); O(1) com cache.
        Espaço adicional O(n) para a lista de pontos, descartada ao final.
    """
    if rede["par_cache"] is None:
        pts = sorted((x, y, ident) for ident, (x, y) in rede["coords"].items())
        d2, a, b = par_rec(pts, 0, len(pts))
        if a > b:
            a, b = b, a
        t = isqrt(d2)              
        if t * t < d2:              
            t += 1
        rede["par_cache"] = f"{a} {b} {t}"
    return rede["par_cache"]

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

            elif op == "REMOVER":

            elif op == "PAR":
                

        k += 1                      
        atualizar_kadane(kadane, k, total)
        soma_pilha = atualizar_pilha(pilha, soma_pilha, k, total)

    if saida:
        print("\n".join(saida))
        
if __name__ == "__main__":
    main()
