import requests
from time import sleep


def main():
    token = "8ae52a38e35c26c8e4cb6b1c33583fa1eadfb85fa53942763367da3c5d74a51be81a9a50"
    dataInicial = "23/04/2024"
    dataFinal = "25/04/2024"

    page = 1
    lista_produtos = []

    while True:

        url = f"https://bling.com.br/Api/v2/pedidos/page={page}/json/?apikey={token}&filters=dataEmissao[{dataInicial} TO {dataFinal}]; idSituacao[9]"

        response = requests.request("GET", url)

        if response.status_code != 200:
            break

        pedidos = response.json().get('retorno').get('pedidos')

        if not pedidos:
            break

        for pedido in pedidos:
            for item in pedido.get('pedido').get('itens'):

                quantidade = int(item.get('item').get('quantidade').split('.')[0])

                try:
                    precoCusto = float(item.get('item').get('precocusto'))
                except:
                    precoCusto = 0.0

                produto_novo = {
                    "nome": item.get('item').get('descricao'),
                    "codigo": item.get('item').get('codigo'),
                    "quantidade": quantidade,
                    "precocusto": precoCusto,
                    "valorTotal": quantidade * float(item.get('item').get('valorunidade'))
                }

                produto_encontrado = False
                for produto in lista_produtos:
                    if produto_novo.get('nome') == produto.get('nome'):
                        produto['quantidade'] += produto_novo['quantidade']
                        produto['valorTotal'] += produto_novo['valorTotal']
                        produto_encontrado = True
                        break

                if not produto_encontrado:
                    lista_produtos.append(produto_novo)

        page += 1

    lista_produtos = adicionar_estoque(lista_produtos, token)
    total_vendas = sum(produto['valorTotal'] for produto in lista_produtos)
    lista_ordenada_valorTotal = calcular_classificacao_vendas(lista_produtos, total_vendas)
    lista_ordenada_quantidadeVendida = sorted(lista_ordenada_valorTotal, key=lambda x: x['quantidade'], reverse=True)

    print("Total em vendas: ", total_vendas)
    print("Ordem Rendeu Mais")
    print(lista_ordenada_valorTotal)
    print("Ordem Vendeu Mais")
    print(lista_ordenada_quantidadeVendida)


def adicionar_estoque(lista_produtos, token):
    for produto in lista_produtos:
        url = f"https://bling.com.br/Api/v2/produto/{produto.get('codigo')}/json/?apikey={token}&estoque=S"

        requisicao = requests.request("GET", url)

        if requisicao.status_code == 200:
            try:
                response = requisicao.json().get('retorno').get('produtos')[0].get('produto')
                produto["fornecedor"] = response.get('nomeFornecedor')
                produto["marca"] = response.get('camposCustomizados').get('marca')
                produto["estoqueMin"] = int(str(response.get('estoqueMinimo')).split(".")[0])
                produto["estoqueMax"] = int(str(response.get('estoqueMaximo')).split(".")[0])
                produto["estoqueAtual"] = int(str(response.get('estoqueAtual')))
            except:
                continue
        else:
            sleep(10)

    return lista_produtos


def calcular_classificacao_vendas(lista_produtos, total_vendas):
    # fazer a subtracao do custo
    for produto in lista_produtos:
        print(produto)
        valorCustoTotal = produto.get('quantidade') * produto.get('precocusto')
        produto['valorTotal'] = produto['valorTotal'] - valorCustoTotal


    # Ordenar a lista de produtos com base no valor total em ordem decrescente
    lista_ordenada = sorted(lista_produtos, key=lambda x: x['valorTotal'], reverse=True)

    # Calcular os limites para as classes A, B e C
    limite_a = 0.8 * total_vendas
    limite_b = 0.95 * total_vendas  # 0.8 + 0.15 = 0.95
    # Restante pertence à classe C

    vendas_acumuladas = 0
    for produto in lista_ordenada:
        vendas_acumuladas += produto['valorTotal']
        if vendas_acumuladas <= limite_a:
            produto['classificacao'] = 'A'
        elif vendas_acumuladas <= limite_b:
            produto['classificacao'] = 'B'
        else:
            produto['classificacao'] = 'C'

    return lista_ordenada


if __name__ == "__main__":
    main()
