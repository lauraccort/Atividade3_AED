"""
Entregável 3 - Rede de distribuição: rede de rotas
Laura da Costa Corte Cordeiro e Ana Helena de Souza Macedo
Algoritmos e Estruturas de Dados - BCC - 2026.2

Estruturas de dados:
- rede (dict com os campos lucros, coords, fila, saida, entrada, total,
  par_cache): agrupa tudo o que muda quando um depósito entra ou sai, para que
  uma única função (remover_deposito) mantenha todas as partes consistentes.
- lucros e coords (dict id -> lucro, dict id -> (x, y)): tabelas hash da
  biblioteca. Os ids chegam a 10^9, então um vetor indexado por id é inviável;
  com no máximo 5000 vivos, busca/inserção/remoção custam O(1) esperado.
- fila (heap mínimo indexado, implementado aqui com listas e um dict pos):
  fila de prioridade com alteração de chave. Uma instância com chave = lucro
  serve ao REMOVER; o DIST cria outra instância, com chave = distância, para o
  Dijkstra (mesmas funções, instâncias separadas).
- saida e entrada (grafo dirigido em listas de adjacência esparsas):
  saida[u] é um dict v -> custo das rotas u -> v; entrada[v] é um set dos u
  com rota u -> v. O grafo é esparso (m <= 5n no setup, r <= 20 por
  INSERIR): uma matriz teria 25 milhões de células e listar vizinhos custaria
  O(n). O conjunto de entrada permite apagar as rotas que chegam a um
  depósito removido sem varrer o grafo todo.
- total (int): soma dos lucros dos vivos, mantida incrementalmente; L_k é
  lido em O(1).
- par_cache (str ou None): último resultado do PAR, reutilizado enquanto o
  conjunto de vivos não muda (permitido pela seção 1.6). Nenhuma estrutura
  guarda distâncias entre pares.
- kadane (dict) e pilha (list de pares [j, r]) + soma_pilha: histórico do E1;
  MELHOR e PROSPERIDADE em O(1).

Notação: n = depósitos vivos, m = rotas vivas, P = períodos registrados,
h = altura da pilha, k = depósitos removidos por uma chamada de REMOVER,
g(x) = grau de x (rotas que saem de x mais rotas que chegam a x).
"""
import sys
from math import isqrt


# --------------------------------------------------------------------------
# Fila de prioridade: heap mínimo indexado (sem classes)
# --------------------------------------------------------------------------

def novo_heap():
    """
    (a) Recebe: nada.
    (b) Devolve um heap vazio, um dict com os campos:
        - ids (list): ids na ordem do heap (ids[0] é o topo);
        - chaves (list): chaves[i] é a chave de ids[i];
        - pos (dict id -> índice): pos[id] é a posição de id em ids.
        Invariantes entre as operações:
        - len(ids) == len(chaves) == len(pos) e pos[ids[i]] == i para todo i;
        - propriedade de heap: chaves[(i-1)//2] <= chaves[i] para todo i > 0.
        O pos é o que permite alterar a chave de um id qualquer: um heap
        comum não saberia onde o elemento está.
    (c) O(1).
    """
    return {"ids": [], "chaves": [], "pos": {}}


def heap_subir(heap, i):
    """
    (a) Recebe: heap e i, índice válido; o heap vale em todo ponto exceto,
        talvez, entre i e seu pai.
    (b) Sobe o elemento de i até restaurar a propriedade de heap, atualizando
        pos a cada movimento. Modifica o heap.
    (c) O(log t), t = tamanho do heap: no máximo a altura, O(1) por nível.
    """
    ids, chaves, pos = heap["ids"], heap["chaves"], heap["pos"]
    ident, chave = ids[i], chaves[i]
    while i > 0:
        pai = (i - 1) // 2
        if chaves[pai] <= chave:
            break
        ids[i], chaves[i] = ids[pai], chaves[pai]   # pai desce para i
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
    (c) O(log t), t = tamanho do heap: no máximo a altura, O(1) por nível.
    """
    ids, chaves, pos = heap["ids"], heap["chaves"], heap["pos"]
    tam = len(ids)
    ident, chave = ids[i], chaves[i]
    while True:
        filho = 2 * i + 1
        if filho >= tam:
            break
        if filho + 1 < tam and chaves[filho + 1] < chaves[filho]:
            filho += 1                                # menor dos dois filhos
        if chaves[filho] >= chave:
            break
        ids[i], chaves[i] = ids[filho], chaves[filho]  # filho sobe para i
        pos[ids[i]] = i
        i = filho
    ids[i], chaves[i] = ident, chave
    pos[ident] = i


def heap_inserir(heap, ident, chave):
    """
    (a) Recebe: heap, ident (id que ainda não está no heap) e chave.
    (b) Coloca o elemento no fim e o sobe. Modifica o heap.
    (c) O(log t): append O(1) amortizado e um heap_subir.
    """
    heap["ids"].append(ident)
    heap["chaves"].append(chave)
    heap["pos"][ident] = len(heap["ids"]) - 1
    heap_subir(heap, len(heap["ids"]) - 1)


def heap_alterar(heap, ident, chave):
    """
    (a) Recebe: heap, ident (id presente no heap) e a nova chave.
    (b) Troca a chave e reposiciona: sobe se diminuiu, desce se aumentou.
        Modifica o heap.
    (c) O(log t): busca em pos O(1) esperado e um heap_subir ou heap_descer.
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
    (a) Recebe: heap e ident (id presente no heap).
    (b) Remove o elemento: o último ocupa o lugar dele e é reposicionado
        (sobe ou desce). Modifica o heap.
    (c) O(log t): pop O(1) e um heap_subir ou heap_descer.
    """
    ids, chaves, pos = heap["ids"], heap["chaves"], heap["pos"]
    i = pos.pop(ident)
    ultimo_id = ids.pop()
    ultima_chave = chaves.pop()
    if i == len(ids):                 # o removido era o último: nada a mover
        return
    ids[i], chaves[i] = ultimo_id, ultima_chave
    pos[ultimo_id] = i
    if i > 0 and chaves[(i - 1) // 2] > ultima_chave:
        heap_subir(heap, i)
    else:
        heap_descer(heap, i)


def heap_extrair_min(heap):
    """
    (a) Recebe: heap não vazio.
    (b) Remove e devolve o par (chave, id) de menor chave. Modifica o heap.
    (c) O(log t): leitura do topo O(1) e um heap_remover.
    """
    chave, ident = heap["chaves"][0], heap["ids"][0]
    heap_remover(heap, ident)
    return chave, ident


# --------------------------------------------------------------------------
# Rede: registro dos depósitos e grafo de rotas (sem classes)
# --------------------------------------------------------------------------

def nova_rede():
    """
    (a) Recebe: nada.
    (b) Devolve a rede vazia, um dict com os campos:
        - lucros (dict id -> lucro) e coords (dict id -> (x, y)) dos vivos;
        - fila (heap de novo_heap): um elemento por vivo, chave = lucro;
        - saida (dict id -> dict v -> custo): rotas que saem de cada vivo;
        - entrada (dict id -> set de u): origens das rotas que chegam a cada
          vivo;
        - total (int): soma dos lucros dos vivos (inclusive os abaixo de T
          ainda não removidos);
        - par_cache (str ou None): resposta do PAR para os vivos atuais, ou
          None se precisa ser recalculada.
        Invariantes entre as operações:
        - lucros, coords, fila, saida e entrada têm exatamente os mesmos ids
          (os vivos), e a chave de cada id na fila é lucros[id];
        - v está em saida[u] se e somente se u está em entrada[v]; toda rota
          liga dois vivos;
        - total == soma de lucros.values();
        - par_cache, se não for None, é a resposta correta para os vivos
          atuais (inserir ou remover zera; mudar lucro não afeta).
    (c) O(1).
    """
    return {"lucros": {}, "coords": {}, "fila": novo_heap(),
            "saida": {}, "entrada": {}, "total": 0, "par_cache": None}


def inserir_deposito(rede, ident, x, y, lucro):
    """
    (a) Recebe: rede, ident (id novo, nunca usado), coordenadas x, y e lucro.
    (b) Cria o depósito vivo em lucros, coords e fila, cria o vértice sem
        rotas no grafo, soma o lucro ao total e invalida par_cache.
        Modifica a rede. As rotas são acrescentadas depois, por inserir_rota.
    (c) O(log n): inserções em dict O(1) esperado e heap_inserir O(log n).
    """
    rede["lucros"][ident] = lucro
    rede["coords"][ident] = (x, y)
    heap_inserir(rede["fila"], ident, lucro)
    rede["saida"][ident] = {}
    rede["entrada"][ident] = set()
    rede["total"] += lucro
    rede["par_cache"] = None


def inserir_rota(rede, u, v, c):
    """
    (a) Recebe: rede, u e v (depósitos vivos distintos, sem rota u -> v
        ainda) e c (custo inteiro positivo).
    (b) Acrescenta a rota dirigida u -> v com custo c, nos dois lados
        (saida[u] e entrada[v]), mantendo o invariante do grafo.
    (c) O(1) esperado: uma inserção em dict e uma em set.
    """
    rede["saida"][u][v] = c
    rede["entrada"][v].add(u)


def mudar_lucro(rede, ident, lucro):
    """
    (a) Recebe: rede, ident (depósito vivo) e o novo lucro (substitui o
        antigo; pode ser menor que T).
    (b) Ajusta o total pela diferença, grava o novo lucro e reposiciona o
        depósito na fila. Não mexe em par_cache nem no grafo.
    (c) O(log n): acesso ao dict O(1) esperado e heap_alterar O(log n).
    """
    rede["total"] += lucro - rede["lucros"][ident]
    rede["lucros"][ident] = lucro
    heap_alterar(rede["fila"], ident, lucro)


def remover_deposito(rede, ident):
    """
    (a) Recebe: rede e ident (depósito vivo).
    (b) Função única de remoção: tira o depósito da fila, de lucros e de
        coords, apaga todas as rotas que saem dele ou chegam a ele (nos dois
        lados do grafo) e o vértice, desconta o lucro do total e invalida
        par_cache. Modifica a rede.
    (c) O(log n + g(ident)) esperado: heap_remover O(log n); uma remoção
        O(1) esperado para cada rota que toca o depósito; o conjunto de
        entrada evita varrer o grafo para achar quem aponta para ele.
    """
    heap_remover(rede["fila"], ident)
    rede["total"] -= rede["lucros"].pop(ident)
    del rede["coords"][ident]

    saida, entrada = rede["saida"], rede["entrada"]
    for u in entrada.pop(ident):      # rotas u -> ident
        del saida[u][ident]
    for v in saida.pop(ident):        # rotas ident -> v
        entrada[v].discard(ident)

    rede["par_cache"] = None


def remover_abaixo(rede, T):
    """
    (a) Recebe: rede e T, a tolerância mínima de lucro (pode ser negativa).
    (b) Fecha todos os vivos com lucro estritamente menor que T: enquanto o
        topo da fila (menor lucro) for < T, remove-o com remover_deposito
        (que também apaga suas rotas). Devolve quantos foram removidos.
        Modifica a rede.
    (c) O(k log n + soma dos graus dos removidos), com k removidos: cada
        remoção custa O(log n + g); o teste do topo é O(1); os demais vivos
        não são examinados.
    """
    fila = rede["fila"]
    removidos = 0
    while fila["ids"] and fila["chaves"][0] < T:
        remover_deposito(rede, fila["ids"][0])
        removidos += 1
    return removidos


# --------------------------------------------------------------------------
# DIST: caminhos mínimos com Dijkstra
# --------------------------------------------------------------------------

def dist(rede, s):
    """
    (a) Recebe: rede e s (depósito vivo).
    (b) Calcula, com Dijkstra, o menor custo de s a cada vivo, seguindo a
        direção das rotas (saida). Devolve a linha de resposta: os custos
        para os demais vivos em ordem crescente de id, separados por espaço,
        com -1 para os inalcançáveis; string vazia se s é o único vivo.
        Usa uma instância nova do heap (chave = distância), separada da fila
        de lucros. Não modifica a rede.
        Corretude: os custos são positivos, então, quando u sai do heap com
        a menor distância provisória, nenhum caminho ainda não examinado
        pode melhorá-la (ele passaria por um vértice com distância >= a de u
        e só acrescentaria custo); por isso cada u é finalizado ao sair.
    (c) O((n + m) log n): cada vivo entra e sai do heap no máximo uma vez
        (O(log n) cada) e cada rota é relaxada uma vez, com no máximo uma
        alteração de chave O(log n). Mais O(n log n) para ordenar os ids da
        saída. Espaço adicional O(n) (distâncias e heap).
    """
    saida = rede["saida"]
    distancia = {s: 0}
    heap = novo_heap()
    heap_inserir(heap, s, 0)

    while heap["ids"]:
        d, u = heap_extrair_min(heap)   # d é final: custos positivos
        for v, c in saida[u].items():   # relaxa as rotas u -> v
            nd = d + c
            if v not in distancia:      # primeira vez que v é alcançado
                distancia[v] = nd
                heap_inserir(heap, v, nd)
            elif nd < distancia[v]:     # v ainda no heap: caminho melhor
                distancia[v] = nd
                heap_alterar(heap, v, nd)
            # se v já foi finalizado, nd >= distancia[v] e nada muda

    partes = []
    for ident in sorted(rede["lucros"]):
        if ident != s:
            partes.append(str(distancia.get(ident, -1)))
    return " ".join(partes)


# --------------------------------------------------------------------------
# PAR: par de pontos mais próximo por divisão e conquista (Entregável 2)
# --------------------------------------------------------------------------

def par_rec(pts, lo, hi):
    """
    (a) Recebe: pts, lista de tuplas (x, y, id) com pts[lo:hi] ordenado por
        x (empates por y); lo e hi com hi - lo >= 2. Coordenadas distintas.
    (b) Devolve (d2, a, b): o menor quadrado de distância entre dois pontos
        de pts[lo:hi] e os ids desses pontos. Ao terminar, pts[lo:hi] fica
        ordenado por y (modifica pts nesse trecho).
        Divide ao meio por índice (não por valor de x, que pode repetir),
        resolve as metades e depois procura, na faixa vertical em torno da
        divisória com (x - xm)^2 < d2, pares que cruzam as metades.
    (c) O(t log t), t = hi - lo: T(t) = 2T(t/2) + O(t). O passo O(t) é a
        junção das metades por y (sorted reconhece as duas sequências já
        ordenadas e só as intercala), a montagem da faixa e sua varredura,
        em que cada ponto é comparado com O(1) vizinhos (no máximo 7: num
        retângulo d x 2d cabem poucos pontos a distância >= d entre si).
        Espaço adicional O(t); profundidade da recursão O(log t).
    """
    if hi - lo <= 3:                                  # caso base: força bruta
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
    xm = pts[meio][0]               # lido antes de a recursão reordenar por y
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
            if dy * dy >= d2_min:   # mais acima na faixa só fica mais longe
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
        t = isqrt(d2)               # maior t com t*t <= d2
        if t * t < d2:              # d2 não é quadrado perfeito: arredonda
            t += 1
        rede["par_cache"] = f"{a} {b} {t}"
    return rede["par_cache"]


# --------------------------------------------------------------------------
# Histórico de períodos (Entregável 1)
# --------------------------------------------------------------------------

def novo_kadane():
    """
    (a) Recebe: nada.
    (b) Devolve o estado inicial do Kadane online, um dict com:
        - fim_soma, fim_ini: soma e início do melhor intervalo que termina no
          último período registrado (empate: menor início);
        - mi, mj, ms: melhor intervalo global [mi, mj] e sua soma ms.
        Invariante: após registrar o período k, [mi, mj] é o melhor
        intervalo de 1..k (empate: menor i, depois menor j).
    (c) O(1).
    """
    return {"fim_soma": 0, "fim_ini": 0, "mi": 0, "mj": 0, "ms": 0}


def atualizar_kadane(kadane, k, L):
    """
    (a) Recebe: kadane, k (período recém-registrado, em ordem 1, 2, ...) e
        L (= L_k).
    (b) Atualiza o melhor intervalo que termina em k (estende se a soma
        anterior for >= 0, o que mantém o menor início no empate) e o
        melhor global. Não devolve nada.
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
    (b) Devolve "i j S" do melhor intervalo. Não modifica nada.
    (c) O(1): leitura do estado mantido.
    """
    return f"{kadane['mi']} {kadane['mj']} {kadane['ms']}"


def atualizar_pilha(pilha, soma, k, L):
    """
    (a) Recebe: pilha (list de pares [j, r], base em pilha[0], topo em
        pilha[-1]; todo r > 0), soma (soma dos resíduos), k e L (= L_k).
    (b) Aplica a regra da pilha de prosperidade para L_k e devolve a nova
        soma. Modifica a pilha.
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
            if r > d:                 # topo absorve o prejuízo todo
                pilha[-1][1] = r - d  # mantém o j original
                soma -= d
                d = 0
            else:                     # r <= d: topo consumido
                pilha.pop()
                soma -= r
                d -= r
    return soma


def prosperidade(pilha, soma):
    """
    (a) Recebe: a pilha e a soma dos resíduos.
    (b) Devolve "0" se a pilha está vazia; senão "h b s i r".
    (c) O(1): len, base e topo por índice, soma já mantida.
    """
    if not pilha:
        return "0"
    b = pilha[0][0]
    i, r = pilha[-1]
    return f"{len(pilha)} {b} {soma} {i} {r}"


# --------------------------------------------------------------------------
# Ponto de ancoragem
# --------------------------------------------------------------------------

def main():
    """
    (a) Recebe: a entrada padrão no formato do enunciado.
    (b) Lê o setup (depósitos e depois rotas, agora guardadas no grafo),
        executa os lotes e registra cada período ao fim do seu lote. Escreve
        uma linha por DIST, PAR, REMOVER, MELHOR e PROSPERIDADE na saída
        padrão, na ordem de execução.
    (c) Por comando (n = vivos, m = rotas vivas no momento):
        - INSERIR: inserir_deposito O(log n) + r inserir_rota O(1) esperado;
        - LUCRO: mudar_lucro, O(log n);
        - REMOVER: remover_abaixo, O(k log n + graus dos removidos);
        - DIST: dist, O((n + m) log n);
        - PAR: par, O(n log n), ou O(1) se os vivos não mudaram;
        - MELHOR, PROSPERIDADE: O(1);
        - registro de cada período: O(1) amortizado.
        Espaço: O(n + m + tamanho da entrada).
    """
    tokens = sys.stdin.read().split()
    n, m, T = int(tokens[0]), int(tokens[1]), int(tokens[2])
    pos = 3

    rede = nova_rede()
    for _ in range(n):              # todos os vértices antes das rotas
        ident, x, y, lucro = (int(t) for t in tokens[pos:pos + 4])
        inserir_deposito(rede, ident, x, y, lucro)
        pos += 4
    for _ in range(m):              # rotas do setup: agora são usadas
        u, v, c = int(tokens[pos]), int(tokens[pos + 1]), int(tokens[pos + 2])
        inserir_rota(rede, u, v, c)
        pos += 3

    kadane = novo_kadane()
    pilha = []
    soma_pilha = 0
    saida = []

    k = 1                           # período 1: logo após o setup
    atualizar_kadane(kadane, k, rede["total"])
    soma_pilha = atualizar_pilha(pilha, soma_pilha, k, rede["total"])

    P = int(tokens[pos])
    pos += 1
    for _ in range(P):              # um lote por período (2 até P+1)
        q = int(tokens[pos])
        pos += 1
        for _ in range(q):
            op = tokens[pos]
            pos += 1

            if op == "INSERIR":
                ident, x, y, lucro, r = (int(t) for t in tokens[pos:pos + 5])
                pos += 5
                inserir_deposito(rede, ident, x, y, lucro)
                for _ in range(r):  # as r rotas não contam em q
                    u, v, c = (int(tokens[pos]), int(tokens[pos + 1]),
                               int(tokens[pos + 2]))
                    inserir_rota(rede, u, v, c)
                    pos += 3

            elif op == "LUCRO":
                ident, lucro = int(tokens[pos]), int(tokens[pos + 1])
                pos += 2
                mudar_lucro(rede, ident, lucro)

            elif op == "REMOVER":
                saida.append(str(remover_abaixo(rede, T)))

            elif op == "DIST":
                s = int(tokens[pos])
                pos += 1
                saida.append(dist(rede, s))

            elif op == "PAR":
                saida.append(par(rede))

            elif op == "MELHOR":
                saida.append(melhor(kadane))

            elif op == "PROSPERIDADE":
                saida.append(prosperidade(pilha, soma_pilha))

        k += 1                      # fim do lote: registra L_k
        atualizar_kadane(kadane, k, rede["total"])
        soma_pilha = atualizar_pilha(pilha, soma_pilha, k, rede["total"])

    if saida:
        sys.stdout.write("\n".join(saida) + "\n")


if __name__ == "__main__":
    main()
