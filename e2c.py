"""
Rede de distribuição - Entregável 2: fechamento e proximidade
Nome: Ana Helena de Souza Macedo
Algoritmos e Estruturas de Dados - BCC - 2026.2

Estruturas de dados:
- Rede.reg (dict id -> [x, y, lucro]): tabela hash da biblioteca. Os ids chegam
  a 10^9, então um vetor indexado por id é inviável; com no máximo 5000 vivos,
  busca/inserção/remoção em O(1) esperado. Agora guarda também as coordenadas,
  necessárias ao PAR.
- FilaPrioridade (implementada aqui): min-heap binário indexado, com chave =
  lucro e um dict pos (id -> índice no heap). O pos permite alterar a chave ou
  remover um depósito qualquer por id em O(log n), e o REMOVER só olha o topo:
  custa O(log n) por depósito removido, em vez de varrer todos os vivos.
- Rede.total (int): soma dos lucros dos vivos, mantida incrementalmente, então
  L_k é lido em O(1) sem varrer os depósitos (agora também descontada nas
  remoções).
- kadane (dict com 5 campos): estado do Kadane online (E1); MELHOR em O(1).
- pilha (list de pares [j, r]) + soma_pilha: pilha de prosperidade (E1);
  append/pop no fim da list em O(1) amortizado; PROSPERIDADE em O(1).
- Rede.par_cache (str ou None): último resultado do PAR, reutilizado enquanto
  o conjunto de depósitos vivos não muda (permitido pela seção 1.6). O PAR
  monta, a cada consulta, uma lista de pontos ordenada por x e a descarta ao
  final: nenhuma estrutura guarda distâncias entre pares.

Notação: n = depósitos vivos, P = períodos registrados, h = altura da pilha,
k = depósitos removidos por uma chamada de REMOVER.
"""
import sys
from math import isqrt
from operator import itemgetter


class FilaPrioridade:
    """
    Min-heap binário indexado: fila de prioridade com alteração de chave.

    Campos:
    - ids (list): ids dos depósitos, na ordem do heap (ids[0] é o topo);
    - chaves (list): chaves[i] é o lucro do depósito ids[i];
    - pos (dict): pos[id] é o índice de id em ids.
    Invariantes entre as operações:
    - len(ids) == len(chaves) == len(pos);
    - pos[ids[i]] == i para todo i;
    - propriedade de heap: chaves[(i-1)//2] <= chaves[i] para todo i > 0.
    Escolhida porque o enunciado exige alterar o lucro de um depósito e achar
    os de lucro abaixo de T sem examinar todos; um heap comum não localizaria
    o depósito a alterar, e o pos resolve isso.
    Espaço: O(n).
    """

    def __init__(self):
        """
        (a) Recebe: nada.
        (b) Cria a fila vazia (ids, chaves e pos vazios).
        (c) O(1).
        """
        self.ids = []
        self.chaves = []
        self.pos = {}

    def __len__(self):
        """
        (a) Recebe: nada.
        (b) Devolve a quantidade de elementos da fila. Não modifica nada.
        (c) O(1).
        """
        return len(self.ids)

    def _subir(self, i):
        """
        (a) Recebe: i, índice válido, tal que o heap vale em todos os pontos
            exceto, possivelmente, entre i e seu pai.
        (b) Sobe o elemento de i até restaurar a propriedade de heap,
            atualizando pos. Modifica ids, chaves e pos.
        (c) O(log n): a altura do heap é log n e cada passo é O(1).
        """
        ids, chaves, pos = self.ids, self.chaves, self.pos
        ident, chave = ids[i], chaves[i]
        while i > 0:
            pai = (i - 1) >> 1
            if chaves[pai] <= chave:
                break
            ids[i], chaves[i] = ids[pai], chaves[pai]
            pos[ids[i]] = i
            i = pai
        ids[i], chaves[i] = ident, chave
        pos[ident] = i

    def _descer(self, i):
        """
        (a) Recebe: i, índice válido, tal que o heap vale em todos os pontos
            exceto, possivelmente, entre i e seus filhos.
        (b) Desce o elemento de i até restaurar a propriedade de heap,
            atualizando pos. Modifica ids, chaves e pos.
        (c) O(log n): a altura do heap é log n e cada passo é O(1).
        """
        ids, chaves, pos = self.ids, self.chaves, self.pos
        n = len(ids)
        ident, chave = ids[i], chaves[i]
        while True:
            filho = 2 * i + 1
            if filho >= n:
                break
            if filho + 1 < n and chaves[filho + 1] < chaves[filho]:
                filho += 1
            if chaves[filho] >= chave:
                break
            ids[i], chaves[i] = ids[filho], chaves[filho]
            pos[ids[i]] = i
            i = filho
        ids[i], chaves[i] = ident, chave
        pos[ident] = i

    def inserir(self, ident, chave):
        """
        (a) Recebe: ident (id que ainda não está na fila) e chave (lucro).
        (b) Insere o elemento no fim e o sobe. Modifica a fila.
        (c) O(log n): um append O(1) esperado e um _subir de O(log n).
        """
        self.ids.append(ident)
        self.chaves.append(chave)
        self.pos[ident] = len(self.ids) - 1
        self._subir(len(self.ids) - 1)

    def alterar(self, ident, chave):
        """
        (a) Recebe: ident (id presente na fila) e a nova chave.
        (b) Troca a chave e restaura o heap: sobe se diminuiu, desce se
            aumentou, nada se ficou igual. Modifica a fila.
        (c) O(log n): busca em pos O(1) esperado e um _subir ou _descer.
        """
        i = self.pos[ident]
        antiga = self.chaves[i]
        self.chaves[i] = chave
        if chave < antiga:
            self._subir(i)
        elif chave > antiga:
            self._descer(i)

    def remover(self, ident):
        """
        (a) Recebe: ident (id presente na fila).
        (b) Remove esse elemento: coloca o último no seu lugar e o reposiciona
            (sobe ou desce). Modifica a fila.
        (c) O(log n): busca em pos O(1) esperado e um _subir ou _descer.
        """
        i = self.pos.pop(ident)
        ultimo_id = self.ids.pop()
        ultima_chave = self.chaves.pop()
        if i == len(self.ids):          # o removido era o último elemento
            return
        self.ids[i] = ultimo_id
        self.chaves[i] = ultima_chave
        self.pos[ultimo_id] = i
        if i > 0 and self.chaves[(i - 1) >> 1] > ultima_chave:
            self._subir(i)
        else:
            self._descer(i)

    def topo(self):
        """
        (a) Recebe: nada. Pré-condição: a fila não está vazia.
        (b) Devolve o par (chave, id) do elemento de menor chave. Não modifica
            nada.
        (c) O(1): leitura do índice 0.
        """
        return self.chaves[0], self.ids[0]


def _par_rec(pts, lo, hi):
    """
    (a) Recebe: pts, lista de tuplas (x, y, id) ordenada por (x, y) em todo o
        intervalo; lo e hi, com hi - lo >= 2, delimitando pts[lo:hi].
        Coordenadas distintas entre si.
    (b) Devolve (d2, a, b): o menor quadrado de distância entre dois pontos de
        pts[lo:hi] e os ids desses pontos. Ao terminar, pts[lo:hi] está
        ordenado por y (modifica pts nesse intervalo). Divisão e conquista:
        resolve as duas metades, e depois procura, na faixa vertical de largura
        menor que d em torno da divisória, pares que cruzam as metades.
    (c) O(m log m) no pior caso, com m = hi - lo: T(m) = 2T(m/2) + O(m). O
        passo O(m) é a junção por y (sorted() sobre duas sequências já
        ordenadas por y reconhece as duas corridas e faz uma junção linear),
        a montagem da faixa e a varredura dela, em que cada ponto é comparado
        com O(1) vizinhos (no máximo 7: em um retângulo d x 2d cabem poucos
        pontos a distância >= d entre si). Espaço adicional O(m) e pilha de
        recursão O(log m).
    """
    if hi - lo <= 3:
        melhor = None
        for i in range(lo, hi):
            xi, yi, ai = pts[i]
            for j in range(i + 1, hi):
                xj, yj, aj = pts[j]
                d2 = (xi - xj) ** 2 + (yi - yj) ** 2
                if melhor is None or d2 < melhor[0]:
                    melhor = (d2, ai, aj)
        pts[lo:hi] = sorted(pts[lo:hi], key=itemgetter(1))
        return melhor

    meio = (lo + hi) // 2
    xm = pts[meio][0]               # lido antes de a recursão reordenar por y
    esq = _par_rec(pts, lo, meio)
    dir_ = _par_rec(pts, meio, hi)
    melhor = esq if esq[0] <= dir_[0] else dir_

    pts[lo:hi] = sorted(pts[lo:hi], key=itemgetter(1))      # junção por y
    faixa = [p for p in pts[lo:hi] if (p[0] - xm) ** 2 < melhor[0]]
    for i in range(len(faixa)):
        xi, yi, ai = faixa[i]
        for j in range(i + 1, len(faixa)):
            xj, yj, aj = faixa[j]
            dy = yj - yi
            if dy * dy >= melhor[0]:
                break
            d2 = (xi - xj) ** 2 + dy * dy
            if d2 < melhor[0]:
                melhor = (d2, ai, aj)
    return melhor


class Rede:
    """
    A rede de depósitos vivos.

    Campos:
    - reg (dict): reg[id] = [x, y, lucro] de cada depósito vivo;
    - fila (FilaPrioridade): um elemento por depósito vivo, com chave = lucro;
    - total (int): soma dos lucros dos depósitos vivos (inclusive os abaixo da
      tolerância ainda não removidos);
    - par_cache (str ou None): resposta "a b d" do PAR para o conjunto atual de
      vivos, ou None se ela precisa ser recalculada.
    Invariantes entre as operações:
    - o conjunto de ids de fila é igual ao de reg, e a chave de cada id na fila
      é reg[id][2];
    - total == soma de reg[id][2] sobre todos os vivos;
    - par_cache, se não for None, é a resposta correta para os vivos atuais
      (qualquer inserção ou remoção o zera; mudar lucro não o afeta, pois as
      coordenadas não mudam).
    Espaço: O(n).
    """

    def __init__(self):
        """
        (a) Recebe: nada.
        (b) Cria a rede vazia: reg e fila vazios, total 0 e par_cache None.
        (c) O(1).
        """
        self.reg = {}
        self.fila = FilaPrioridade()
        self.total = 0
        self.par_cache = None

    def inserir_deposito(self, ident, x, y, lucro):
        """
        (a) Recebe: ident (id novo, nunca usado), x e y (coordenadas) e lucro.
        (b) Cria o depósito vivo: registra em reg e em fila, soma o lucro ao
            total e invalida par_cache. Modifica esses campos.
        (c) O(log n): inserção em dict O(1) esperado e _subir do heap.
        """
        self.reg[ident] = [x, y, lucro]
        self.fila.inserir(ident, lucro)
        self.total += lucro
        self.par_cache = None

    def mudar_lucro(self, ident, lucro):
        """
        (a) Recebe: ident (depósito vivo) e o novo lucro (substitui o antigo).
        (b) Ajusta total pela diferença, grava o lucro em reg e reposiciona o
            depósito na fila. Não mexe em par_cache (coordenadas iguais).
        (c) O(log n): acesso ao dict O(1) esperado e alteração de chave no heap.
        """
        dep = self.reg[ident]
        self.total += lucro - dep[2]
        dep[2] = lucro
        self.fila.alterar(ident, lucro)

    def remover_deposito(self, ident):
        """
        (a) Recebe: ident (depósito vivo).
        (b) Fecha o depósito: tira de fila e de reg, desconta o lucro do total
            e invalida par_cache. Modifica esses campos. O Entregável 3 vai
            acrescentar aqui a remoção das rotas que tocam o depósito.
        (c) O(log n): remoção por id no heap e no dict O(1) esperado.
        """
        self.fila.remover(ident)
        lucro = self.reg.pop(ident)[2]
        self.total -= lucro
        self.par_cache = None

    def remover_abaixo(self, T):
        """
        (a) Recebe: T, a tolerância mínima de lucro (pode ser negativa).
        (b) Fecha todos os depósitos vivos de lucro estritamente menor que T:
            enquanto o topo do heap tem lucro < T, remove-o. Devolve a
            quantidade de depósitos removidos. Modifica a rede.
        (c) O((k+1) log n), com k removidos: um teste do topo mais um
            remover_deposito O(log n) por removido; não varre os vivos.
        """
        removidos = 0
        while len(self.fila) > 0 and self.fila.topo()[0] < T:
            self.remover_deposito(self.fila.topo()[1])
            removidos += 1
        return removidos

    def par(self):
        """
        (a) Recebe: nada. Pré-condição: pelo menos dois depósitos vivos, com
            coordenadas distintas.
        (b) Devolve a string "a b d": ids a < b do par mais próximo e a
            distância euclidiana entre eles arredondada para cima, calculada
            em inteiros (menor t com t*t >= d2). Se par_cache é válido, devolve
            o resultado guardado; senão ordena os pontos por x, chama
            _par_rec e guarda o resultado em par_cache.
        (c) O(n log n) com cache inválido (ordenação O(n log n) mais _par_rec
            O(n log n)); O(1) com cache válido. Espaço adicional O(n).
        """
        if self.par_cache is None:
            pts = sorted((x, y, ident) for ident, (x, y, _) in self.reg.items())
            d2, a, b = _par_rec(pts, 0, len(pts))
            if a > b:
                a, b = b, a
            t = isqrt(d2)
            if t * t < d2:
                t += 1
            self.par_cache = f"{a} {b} {t}"
        return self.par_cache


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
    (b) Lê o setup e as rotas (descartadas no E2), executa os lotes e registra
        cada período ao fim do seu lote. Escreve uma linha por REMOVER, PAR,
        MELHOR e PROSPERIDADE na saída padrão. DIST não é exercitado neste
        entregável: seu argumento é apenas consumido.
    (c) O(tamanho da entrada + soma dos custos das operações). Tratamento de
        cada comando (n = vivos no momento):
        - INSERIR: Rede.inserir_deposito, O(log n); as r rotas são puladas, O(1);
        - LUCRO: Rede.mudar_lucro, O(log n);
        - REMOVER: Rede.remover_abaixo, O((k+1) log n);
        - PAR: Rede.par, O(n log n), ou O(1) se o conjunto de vivos não mudou;
        - MELHOR: O(1); PROSPERIDADE: O(1);
        - registro de cada período: O(1) amortizado.
        Espaço: O(n + tamanho da entrada).
    """
    tokens = sys.stdin.read().split()
    n, m, T = int(tokens[0]), int(tokens[1]), int(tokens[2])
    pos = 3

    rede = Rede()
    for _ in range(n):
        ident, x, y, lucro = (int(t) for t in tokens[pos:pos + 4])
        rede.inserir_deposito(ident, x, y, lucro)
        pos += 4
    pos += 3 * m                     # rotas: lidas e descartadas no E2

    kadane = novo_kadane()
    pilha = []
    soma_pilha = 0
    saida = []

    k = 1                            # período 1: logo após o setup
    atualizar_kadane(kadane, k, rede.total)
    soma_pilha = atualizar_pilha(pilha, soma_pilha, k, rede.total)

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
                rede.inserir_deposito(ident, x, y, lucro)
            elif op == "LUCRO":
                ident, lucro = int(tokens[pos]), int(tokens[pos + 1])
                pos += 2
                rede.mudar_lucro(ident, lucro)
            elif op == "REMOVER":
                saida.append(str(rede.remover_abaixo(T)))
            elif op == "PAR":
                saida.append(rede.par())
            elif op == "MELHOR":
                saida.append(melhor(kadane))
            elif op == "PROSPERIDADE":
                saida.append(prosperidade(pilha, soma_pilha))
            elif op == "DIST":       # não aparece no E2; só consome o argumento
                pos += 1

        k += 1                       # fim do lote: registra L_k
        atualizar_kadane(kadane, k, rede.total)
        soma_pilha = atualizar_pilha(pilha, soma_pilha, k, rede.total)

    if saida:
        print("\n".join(saida))


if __name__ == "__main__":
    main()