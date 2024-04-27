import os
import datetime
import logging
import csv
import numpy
import matplotlib.pyplot as grafico
import auxiliar


RANKING_MAXIMO = 10
GERA_COMPLETO = True

class Avaliacao:
    
    def __init__(self, com_stemmer):
        self.com_stemmer = com_stemmer
        
        if com_stemmer:
            self.infixo_arquivo = "stemmer"
        else:
            self.infixo_arquivo = "nostemmer"
            
        self.precisoes_r_consultas = []
        self.recovacoes = []     
        self.matriz_precisoes = []
        
        self.matriz_precisoes_interpolacao_padrao = []
        self.precisao_revocacao = []
        self.precisao_5 = 0
        self.precisao_10 = 0
        self.precisao_r = 0.0
        self.f_1 = 0.0
        self.map = 0
        self.mrr = 0
        self.dcg = []
        self.ndcg = []

                
# DCG
pos_rank = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


nome_arquivo_relatorio = ''
nome_arquivo_esperados = ''
nome_arquivo_consulta_com_stemmer =''
nome_arquivo_consulta_sem_stemmer = ''

resultados_com_stemmer = {}
resultados_sem_stemmer = {}
resultados_esperados = {}

avaliacao_sem_stemmer = Avaliacao(False)
avaliacao_com_stemmer = Avaliacao(True)

# Definir os valores de recall desejados
recall_desejados = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]



def ler_configuracao():
    global nome_arquivo_relatorio
    global nome_arquivo_esperados
    global nome_arquivo_consulta_com_stemmer
    global nome_arquivo_consulta_sem_stemmer
    
    try:
        #auxiliar.log_tempo('Iniciando a leitura do arquivo de configuração gli.cfg')
   
        nome_arquivo_configuracao = os.getcwd() + '\\avaliacao.cfg'
    
        with open(nome_arquivo_configuracao, encoding="utf-8") as arquivo_configuracao:
            for linha in arquivo_configuracao:
                posicao_igual = linha.find('=')
                if posicao_igual > 0:
                    comando = linha[0:posicao_igual].upper()
                    nome_arquivo = linha[posicao_igual+1 : len(linha)-1]
                    if comando == auxiliar.ESPERADOS:
                        nome_arquivo_esperados = nome_arquivo
                    elif comando == auxiliar.RESULTADOS:
                        nome_arquivo_consulta_com_stemmer = nome_arquivo.replace('.csv', auxiliar.FINAL_ARQUIVO_STEMMER)    
                        nome_arquivo_consulta_sem_stemmer = nome_arquivo.replace('.csv', auxiliar.FINAL_ARQUIVO_NOSTEMMER)    
                    elif comando == auxiliar.RELATORIO:
                        nome_arquivo_relatorio = nome_arquivo
                            
        logging.info('Configuração lida')
    except:
        logging.info('Erro ao ler o arquivo de configuração')
        
# -----------------------------------------------------------------------------------------        

def abrir_resultados_consulta(nome_arquivo, resultado):
    try:
        logging.info('Lendo arquivo da resultados de consulta '+nome_arquivo)
        with open(nome_arquivo, 'r') as arquivo_csv:
            reader = csv.reader(arquivo_csv, delimiter=';')
            for row in reader:
                numero_consulta = int(row[0])
                codigos_documentos = row[1].lstrip('[').rstrip(']').replace("'", "").replace(" ","").split(',')
               
                if not numero_consulta in resultado:
                    resultado[numero_consulta] = []
               
                resultado[numero_consulta].append([int(codigos_documentos[0]),int(codigos_documentos[1]),float(codigos_documentos[2])])
                                                        
        logging.info('Fim da leitura do arquivo de consulta '+nome_arquivo)            
    except:        
        logging.info('Erro ao ler o arquivo consulta '+nome_arquivo)

# -----------------------------------------------------------------------------------------        

def abrir_resultados_esperados():
    global resultados_esperados
    
    try:
        logging.info('Lendo arquivo de resultados esperados')
        with open(nome_arquivo_esperados, 'r') as arquivo_csv:
            reader = csv.reader(arquivo_csv, delimiter=';')
            next(reader, None)  # O arquivo de consulta tem cabeçalho
            for linha in reader:
                numero_consulta = int(linha[0])
                #codigos_documentos = row[1].lstrip('[').rstrip(']').replace("'", "").split(',')
               
                if numero_consulta not in resultados_esperados:
                    resultados_esperados[numero_consulta] = []
               
                resultados_esperados[numero_consulta].append([int(linha[1]),int(linha[2])])
                
                                                        
        logging.info('Fim da leitura do arquivo de resultados esperados')            
    except:
        logging.info('Erro ao ler o arquivo de resultadis esperados')

# ------------------------------------------------------------------------------------------


def contar_acertos (documentos_esperados, documentos_encontrados, ultimo_preciso = False):
    if ultimo_preciso and not (documentos_encontrados[-1] in documentos_esperados):
        return 0
    else:
        quantidade_acertos = 0
        for id_documento in documentos_encontrados:
            if id_documento in documentos_esperados:
                quantidade_acertos+=1
        return quantidade_acertos


# ------------------------------------------------------------------------------------------

def processar_consultas(resultados_consulta, avaliacao : Avaliacao):

    #DCG e NDCG
    processar_dcg_ndcg(resultados_consulta,avaliacao)

    #Precisão 5, Precisão 10 e Precisão R
    processar_precisao_ranking(resultados_consulta, avaliacao) # OK
    
    processar_11_pontos_revocacao_precisao(resultados_consulta, avaliacao)   
    
    processar_mrr(resultados_consulta, avaliacao) # ok
    
    processar_f1(resultados_consulta, avaliacao)
    
    processar_map(resultados_consulta, avaliacao)
    
# MRR (Mean Reciprocal Rank) ---------------------------------------------------------------
# Usado para avaliar a qualidade de um modelo de machile leraning que retornam 
# resultados relevantes.
# Está considernado apenas os 10 primeiros documentos de cada consulta de referência
# Pega sempre o ducumento melhor classificado no ranking retornado pelo algoritmo de busca....
# Testado e OK
def processar_mrr(resultados_consulta, avaliacao : Avaliacao):
    
    somatorio_mrr = 0.0
    
   
    ## resultados esperados lista todas as consultas
    for id_consulta, documentos_esperados in resultados_esperados.items():

        resultados = resultados_consulta[id_consulta]
    
        documentos_relevantes = []
        documentos_recuperados = []
        
        # Seleção dos documentos relevantes  (esperados) da consulta (tiveram votos)       
        for linha in documentos_esperados:
            # 0 = Número do documento
            # 1 = Quantidade de votos
            documentos_relevantes.append(linha[0])
        
        for linha in resultados:
            documentos_recuperados.append(linha[1]) # 1 = código do documento

        rank_documento = 0   

        # Os documentos recuperados já estão na ordem 
        # de classificação (ranking). 
        # É considerado o documento melhor classificado que que tenha sido definido
        # como relevante na consulta
        for id_documento in documentos_recuperados:
            rank_documento += 1   
            if rank_documento < RANKING_MAXIMO:
                if id_documento in documentos_relevantes:
                    rank_reciproco = 1 / rank_documento
                    somatorio_mrr += rank_reciproco
                    break
            else:
                break    
            
    avaliacao.mrr = somatorio_mrr / len(resultados_esperados)  # Valor médio do MRR = Mean Reciproval Rank



# ----------------------------------------------------------------------------------------- #        
# DCG = Discount Cumulative Gain
#  - Considera a posição do documento no ranking. Aplica um desconto (penalização) quando 
#    coloca documentos relevantes mais para o final da lista e um crédito (recompensa)
#    quando coloca documentos relevantes no topo da lista.
#  - CG (Cumulative Gain) é a soma dos scores (votos) de todos os itens importantes 
#  - D (discount) é o valor da penalização em função da posição do documento na busca
# NDCG = Normalied DCG
#  - Usa o iDCG para ajustar os valores do NDXF
#  - iDCG = DCG Ideal (representa o ranking ideal)
#  

def processar_dcg_ndcg(resultados_consulta, avaliacao : Avaliacao):
    ## resultados esperados lista todas as consultas
    matriz_dcg = []
    matriz_nDCG = []


    for id_consulta, esperados in resultados_esperados.items():

        resultados = resultados_consulta[id_consulta]
    
        votos_documentos_relevantes = {}
        
        

        # Seleção dos documentos relevantes da consulta (tiveram votos)     
        # OBS: Também poderia possível limitar a quantidade de documentos
        #      relevantes a serem considerados.  
        for linha in esperados:
          # 0 = Código do documento
          # 1 = Quantidade de votos
          votos_documentos_relevantes[linha[0]]=linha[1]
        
        # Seleciona os k primeiros documentos da busca
        quantidade_documentos = 0
        documentos_ranking_k = []
        ganho_ideal = []
        iDCG = []
        
        for linha in resultados: #resultados_bus
            quantidade_documentos+=1
            if quantidade_documentos <= RANKING_MAXIMO:
                documentos_ranking_k.append([linha[1],0]) # 1 = Código do documento)
                ganho_ideal.append((linha[1], votos_documentos_relevantes.get(linha[1],0))) 
            else:
                break    
          
        ganho_ideal.sort(key=lambda x: x[1],reverse=True)
        
        for par in ganho_ideal:
            iDCG.append([par[0],par[1]])
            


        # Calcula o CG (Cumulative Gain)
        # o CG de um documento é a sua quantidade de votos 
        # do documento anterior.  
        # Exemplo:
        #   CG =   < 4, 3,  4,  4,  0,  1,  2,  1,  3> 
        
        for i in range (len(documentos_ranking_k)):
            if i+1 > 1:
                # Recuperação do ganho (votos) do documento. O gaho é zero se o documento não for relevante
                ganho = votos_documentos_relevantes.get(documentos_ranking_k[i][0], 0) 
                # Cálculo do DCG
                documentos_ranking_k[i][1] = ganho / numpy.log2(i+1) # i começa em zero
                
            else:
                # O CG e o DCG é o mesmo para i = 1 (posição zero da matriz)
                documentos_ranking_k[i][1] = votos_documentos_relevantes.get(documentos_ranking_k[i][0], 0)
         

        matriz_dcg.append ([t[1] for t in documentos_ranking_k])
                        
        for i in range (len(iDCG)):
            if i+1 > 1:
                # Recuperação do ganho (votos) do documento. O gaho é zero se o documento não for relevante
                ganho = iDCG[i][0]
                # Cálculo do DCG
                iDCG[i][1] = ganho / numpy.log2(i+1) # i começa em zero

                
        nDCG = []
        for i in range (len(documentos_ranking_k)):
           nDCG.append(documentos_ranking_k[i][1] / max(iDCG[i][1],1)) 
            
        matriz_nDCG.append([t for t in nDCG])      
   
   
          
    matriz_dcg = numpy.array(matriz_dcg)
    matriz_ndcg = numpy.array(matriz_nDCG)
    
    avaliacao.dcg = numpy.mean(matriz_dcg, axis=0)       # DCG = Discounted Cumulative Gain
    avaliacao.ndcg = numpy.mean(matriz_ndcg, axis=0)         # NDCG = Normalized Discounted Cumulative Gain


# Considera o valor do DCG do elemento anterior
def processar_dcg_ndcg_acumulado(resultados_consulta, avaliacao : Avaliacao):
    ## resultados esperados lista todas as consultas
    matriz_dcg = []
    matriz_nDCG = []


    for id_consulta, esperados in resultados_esperados.items():

        resultados = resultados_consulta[id_consulta]
    
        votos_documentos_relevantes = {}
        
        

        # Seleção dos documentos relevantes da consulta (tiveram votos)     
        # OBS: Também poderia possível limitar a quantidade de documentos
        #      relevantes a serem considerados.  
        for linha in esperados:
          # 0 = Código do documento
          # 1 = Quantidade de votos
          votos_documentos_relevantes[linha[0]]=linha[1]
        
        # Seleciona os k primeiros documentos da busca
        quantidade_documentos = 0
        documentos_ranking_k = []
        ganho_ideal = []
        iDCG = []
        
        for linha in resultados: #resultados_bus
            quantidade_documentos+=1
            if quantidade_documentos <= RANKING_MAXIMO:
                documentos_ranking_k.append([linha[1],0]) # 1 = Código do documento)
                ganho_ideal.append((linha[1], votos_documentos_relevantes.get(linha[1],0))) 
            else:
                break    
          
        ganho_ideal.sort(key=lambda x: x[1],reverse=True)
        
        for par in ganho_ideal:
            iDCG.append([par[0],par[1]])
            


        # Calcula o CG (Cumulative Gain)
        # o CG de um documento é a sua quantidade de votos acumulada com o valor acumulado
        # do documento anterior.  
        # Exemplo:
        #   G =   < 4, 3,  4,  4,  0,  1,  2,  1,  3> 
        #   CG =  < 4  7, 11, 15, 15, 16, 18, 19, 22> 
        
        for i in range (len(documentos_ranking_k)):
            if i+1 > 1:
                # Recuperação do ganho (votos) do documento. O gaho é zero se o documento não for relevante
                ganho = votos_documentos_relevantes.get(documentos_ranking_k[i][0], 0) 
                # Cálculo do CG (Ganho Acumulado)
                documentos_ranking_k[i][1] = ganho + documentos_ranking_k[i-1][1]
                # Cálculo do DCG
                documentos_ranking_k[i][1] = documentos_ranking_k[i-1][1] + documentos_ranking_k[i][1] / numpy.log2(i+1) # i começa em zero
                
            else:
                # O CG e o DCG é o mesmo para i = 1 (posição zero da matriz)
                documentos_ranking_k[i][1] = votos_documentos_relevantes.get(documentos_ranking_k[i][0], 0)
         

        matriz_dcg.append ([t[1] for t in documentos_ranking_k])
                        
        for i in range (len(iDCG)):
            if i+1 > 1:
                # Recuperação do ganho (votos) do documento. O gaho é zero se o documento não for relevante
                ganho = iDCG[i][0]
                # Cálculo do CG (Ganho Acumulado)
                iDCG[i][1] = ganho + iDCG[i-1][1]
                # Cálculo do DCG
                iDCG[i][1] = iDCG[i-1][1] + iDCG[i][1] / numpy.log2(i+1) # i começa em zero

                
        nDCG = []
        for i in range (len(documentos_ranking_k)):
           nDCG.append(documentos_ranking_k[i][1] / max(iDCG[i][1],1)) 
            
        matriz_nDCG.append([t for t in nDCG])      
   
   
          
    matriz_dcg = numpy.array(matriz_dcg)
    matriz_ndcg = numpy.array(matriz_nDCG)
    
    avaliacao.dcg = numpy.mean(matriz_dcg, axis=0)       # DCG = Discounted Cumulative Gain
    avaliacao.ndcg = numpy.mean(matriz_ndcg, axis=0)         # NDCG = Normalized Discounted Cumulative Gain


# ----------------------------------------------------------------------------------------- #        
# Precision_@_K 
#   - Indica precisão dos k primeiros documentos retornados pelo algoritmo de busca.
# R Precision
#   - Indica a precisão considerando todos os documentos retornados pelo algoritmo de busca
# OK.

def processar_precisao_ranking(resultados_consulta, avaliacao : Avaliacao):
    
    somatorio_precisao_5 = 0.0
    somatorio_precisao_10 = 0.0
    somatorio_precisao_r = 0.0
    ## resultados esperados lista todas as consultas
    for id_consulta, esperados in resultados_esperados.items():

        resultados = resultados_consulta[id_consulta]
    
        documentos_relevantes = {}
        documentos_recuperados = []
        lista_5 = []
        lista_10 = []
        lista_r =[]    #Corresponde a todos os documnentos relevantes (definidos na busca)

        
        # Seleção dos documentos relevantes da consulta (tiveram votos)       
        for linha in esperados:
          # 0 = Número do documento
          # 1 = Quantidade de votos
          documentos_relevantes[linha[0]]=linha[1]

        quantidade_documentos_relevantes = len(documentos_relevantes)

        # ----------------------------------------------------------------------#
        # Precisão 5, Precisão 10, Precisão R 
        # ----------------------------------------------------------------------#
        
        # Seleção dos documentos recuperados (reanqueados pelo valor do cosseno)
        # Seleciona também os top 5 e os top 10
        quantidade_documentos_recuperados = 0
        for linha in resultados:
            # [0 ,       1,         2            ] #
            # [ranking , documento, valor_cosseno] #
            quantidade_documentos_recuperados+=1
            numero_documento = linha[1]
            
            documentos_recuperados.append(numero_documento)
            
            if quantidade_documentos_recuperados <= 5:
                lista_5.append(numero_documento)
                
            if quantidade_documentos_recuperados <= 10:
                lista_10.append(numero_documento)

            # Para calcular o R-Precision, é necessário selecionar a quantidade de documentos
            # encontrados correspondente à quantidade de documentos que foram considerados
            # como relevantes. Por exemplo, se foram definidos 30 documentos relevantes,
            # então é necessário escolher os 30 primeiros documentos que foram selecionados
            # pelo algoritmo de busca
            if quantidade_documentos_recuperados <=  quantidade_documentos_relevantes:   
                lista_r.append(numero_documento)
        # Fim fo for
                        
        # Precisão top 5 e Precisão top 10
        # Proporção da quantidade de elementos dos n primeiros documentos encontrados
        # que estão dentro do conjunto de documentos relevantes
        # Precisao 5 = Proporção dos documentos 5 primeiros encontrados que estão
        # na lista de documentos relevantes.
        # Precisao 10 = Proporção dos documentos 10 primeiros encontrados que estão
        # na lista de documentos relevantes (Avaliação - SLIDE 44).
        # Importante: Pode ser qua a quantidade de documentos retornada pelo algoritmo de busca
        #             seja menor que 5 ou menor que 10. Nestes casos, dividir por 5 ou por 10 
        #             reduiria incorretamente a precisão.
        #somatorioPrecisao_5 += contar_acertos(documentos_relevantes, lista_5) / max (1,min(5, len(lista_5)))
        #somatorioPrecisao_10 += contar_acertos(documentos_relevantes, lista_10) / max (1,min(10, len(lista_10)))
        somatorio_precisao_5 += contar_acertos(documentos_relevantes, lista_5) / 5
        somatorio_precisao_10 += contar_acertos(documentos_relevantes, lista_10) / 10

        # Precisão R
        # É a proporção de documentos relevantes encontrados pela busca, correspondente à quantidade de documentos relevantes.
        # Por exemplo, se 10 documentos foram definidos como importantes, então são selecionados os 10 primeiros documentos
        # retornados pelo algoritmo de busca (Avaliação - SLIDE 45)
        # avaliacao.precisao_r.append(contar_acertos(documentos_relevantes,lista_r)
        precisao_r = contar_acertos(documentos_relevantes,lista_r) / quantidade_documentos_relevantes
        avaliacao.precisoes_r_consultas.append(precisao_r)#verificar
        somatorio_precisao_r += precisao_r
        #avaliacao.precisao_r.append(contar_acertos(documentos_relevantes,lista_r) / len(lista_r))  #vp/tot_selecionado (quantidade de verdadeiros positivos / total da busca)
        
    # Finalização dos cálculos das métricas. 
    quantidade_consultas = len(resultados_esperados)
    avaliacao.precisao_5 = somatorio_precisao_5 / quantidade_consultas    # Média da Precisão Top 5
    avaliacao.precisao_10 = somatorio_precisao_10 / quantidade_consultas  # Média da Precisão Top 10
    avaliacao.precisao_r = somatorio_precisao_r / quantidade_consultas  # Média da Precisão R

    

# O F1 é uma única meida para subsituir  a presião e revocação, dando o mesmo valor de importância para ambos
# Está usando apenas os 10 documentos (RANKING_MAXIMO) mais relevantes retornados pelo algoritmo de busca

def processar_f1(resultados_consulta, avaliacao : Avaliacao):
    
    somatorio_f1 = 0.0
    
    for id_consulta, documentos_esperados in resultados_esperados.items():

        resultados = resultados_consulta[id_consulta]
    
        documentos_relevantes =[]
        documentos_recuperados = []
        
        # Seleção dos documentos relevantes  (esperados) da consulta (tiveram votos)       
        for linha in documentos_esperados:
            documentos_relevantes.append(linha[0]) # 0 = código do documento
        
        for linha in resultados:
            documentos_recuperados.append(linha[1]) # 1 = código do documento
            
        verdadeiro_positivo = contar_acertos(documentos_relevantes, documentos_recuperados[:RANKING_MAXIMO])
        if verdadeiro_positivo > 0:
            precisao = verdadeiro_positivo / len(documentos_recuperados)
            revocacao = verdadeiro_positivo / len(documentos_relevantes)
            f1 =  2 * (precisao * revocacao)  / (precisao + revocacao)             
            somatorio_f1 += f1

    avaliacao.f_1 = somatorio_f1 / len(resultados_esperados)   # Média aritmética das médias armônicas. Slide 30
            

def processar_map(resultados_consulta, avaliacao : Avaliacao):
    
    somatorio_precisao_consultas_map = 0.0
    medias_precisao = []
    
    ## resultados esperados lista todas as consultas
    for id_consulta, documentos_esperados in resultados_esperados.items():

        resultados = resultados_consulta[id_consulta]
    
        documentos_relevantes = []
        documentos_recuperados = []
        
        # Seleção dos documentos relevantes  (esperados) da consulta (tiveram votos)       
        for linha in documentos_esperados:
            # 0 = Número do documento
            documentos_relevantes.append(linha[0])
        
        
        quantidade_documentos_relevantes = len(documentos_relevantes)
        

        for linha in resultados:
            documentos_recuperados.append(linha[1]) # 1 = código do documento

        soma_precisao_map = 0.0

       
        intervalo = 1
        while intervalo < len(documentos_recuperados):

            # Identifica os verdadeiros positivos dentro do intervalo, considerando se o último eelemento está no 
            # conjunto dos documentos relevantes. Retorna zero de o último elemento do intervalo não for relevante
            verdadeiro_positivo = contar_acertos(documentos_relevantes, documentos_recuperados[:intervalo], True)

            precisao = verdadeiro_positivo / intervalo
            
            soma_precisao_map += precisao
            
            intervalo += 1
            
        # O MAP mede a media de precisão do modelo
        # Cálculo do MAP     
        media_precisao = soma_precisao_map / quantidade_documentos_relevantes
        somatorio_precisao_consultas_map += media_precisao
    
    
    avaliacao.map = somatorio_precisao_consultas_map /  len(resultados_esperados)  # MAP = Mean Average Precision. É a média 

    
def processar_11_pontos_revocacao_precisao(resultados_consulta, avaliacao : Avaliacao):
    
    medias_precisao = []
    
    ## resultados esperados lista todas as consultas
    for id_consulta, documentos_esperados in resultados_esperados.items():

        resultados = resultados_consulta[id_consulta]
    
        documentos_relevantes = {}
        documentos_recuperados = []
        ranking_documentos_recuperados = {}
        
        # Seleção dos documentos relevantes  (esperados) da consulta (tiveram votos)       
        for linha in documentos_esperados:
            # 0 = Número do documento
            # 1 = Quantidade de votos
            documentos_relevantes[linha[0]] = linha[1]
        
        for linha in resultados:
            documentos_recuperados.append(linha[1]) # 1 = código do documento
            ranking_documentos_recuperados[linha[1]]=linha[0]   # 0 = ranking do documento

        soma_precisao_map = 0.0

        precisoes = []
        precisoes_corrigidas_formula=[]
        revocacoes = []
        revocacoes_precisoes=[]
        
       
        intervalo = 1
        while intervalo < len(documentos_recuperados):

            #Identifica os verdadeiros positivos dentro do intervalo
            verdadeiro_positivo = contar_acertos(documentos_relevantes, documentos_recuperados[:intervalo])

            precisao = verdadeiro_positivo / intervalo
            revocacao = verdadeiro_positivo / len(documentos_relevantes)
            
            precisoes.append(precisao)
            revocacoes.append(revocacao);
            
            revocacoes_precisoes.append((revocacao,precisao))
            
            soma_precisao_map += precisao
            
            intervalo += 1
            
        # Seguindo a fórmula ------------------------------------------------------------------------
        # 1. Ordenação crescente das recovações
        # 2. Criação das listas de revocações e precisões correspondentes
        # 3. Interpolação para 11 pontos de revocação
        # 4. Ajuste das precisoes segundo a fórmula (consiserar a maior precisão à direita)
        revocacoes_precisoes.sort(key=lambda x: x[0])
        revocacoes_formula = [t[0] for t in revocacoes_precisoes]
        precisoes_formula = [t[1] for t in revocacoes_precisoes]
        precisoes_interpoladas = numpy.interp(recall_desejados, revocacoes_formula, precisoes_formula)

        for i in range(len(precisoes_interpoladas)):
            p = precisoes_interpoladas[i]
            for j in range(len(precisoes_interpoladas)-i):
               if precisoes_interpoladas[j+i] > p:
                   p = precisoes_interpoladas[j+i]
            precisoes_corrigidas_formula.append(p)
            
        avaliacao.matriz_precisoes_interpolacao_padrao.append(list(precisoes_corrigidas_formula))
            

        # Apenas ordenando as precisões, sem usar a fórmula ----------------------------------------
        revocacoes.sort()
        precisoes.sort(reverse=True)
        # Calcular a precisão interpolada para cada valor de recall desejado
        precisoes_interpoladas = numpy.interp(recall_desejados, revocacoes, precisoes)
        avaliacao.matriz_precisoes.append(list(precisoes_interpoladas))
    


# -----------------------------------------------------------------------------------------
def gerar_salvar_dados(resultados_consulta,avaliacao : Avaliacao):

    # 11 pontos de precisão e revocação
    matriz_precisoes = numpy.array(avaliacao.matriz_precisoes)
    media_colunas = numpy.mean(matriz_precisoes, axis=0)

    dados_precisao_revocacao = list(zip(recall_desejados, media_colunas))
    with open("avalia/11pontos-"+avaliacao.infixo_arquivo+"-1.csv", "w", newline="", encoding="utf-8") as pontos_11_nostemmer_csv:
        writer = csv.writer(pontos_11_nostemmer_csv, delimiter=";")
        writer.writerow(["Revocacao", "Precisao"])
        writer.writerows(dados_precisao_revocacao)

    # R-Precision
    consultas = resultados_consulta.keys()

    dados_precisao_r = list(zip(consultas, avaliacao.precisoes_r_consultas))
    with open("avalia/r-precision-"+avaliacao.infixo_arquivo+"-1.csv", "w", newline="", encoding="utf-8") as precisao_r_csv:
        writer = csv.writer(precisao_r_csv, delimiter=";")
        writer.writerow(["Consultas", "R-precision"])
        writer.writerows(dados_precisao_r)


    dados_dcg = list(zip(pos_rank, avaliacao.dcg))
    with open("avalia/dcg-"+avaliacao.infixo_arquivo+"-1.csv", "w", newline="", encoding="utf-8") as dcg_csv:
        writer = csv.writer(dcg_csv, delimiter=";")
        writer.writerow(["Posição", "DCG"])
        writer.writerows(dados_dcg)

    # NDCG
    dados_ndcg = list(zip(pos_rank, avaliacao.ndcg))
    with open("avalia/ndcg-"+avaliacao.infixo_arquivo+"-1.csv", "w", newline="", encoding="utf-8") as ndcg_csv:
        writer = csv.writer(ndcg_csv, delimiter=";")
        writer.writerow(["Posição", "NDCG"])
        writer.writerows(dados_ndcg)




def salvar_graficos(consultas, avaliacao1 : Avaliacao, avaliacao2 : Avaliacao):
    
    complemento_titulo = ''
    infixo_arquivo = 'comparacao'
    if avaliacao2 is  None:
        infixo_arquivo = avaliacao1.infixo_arquivo
        if avaliacao1.com_stemmer :
            complemento_titulo = ' (Com Stemmer)'
        else:
            complemento_titulo = ' (Sem Stemmer)'

    if GERA_COMPLETO:
        # 11 pontos de precisão e revocação, considerando apenas a reordenação das precisões#
        media_colunas1 = numpy.mean(avaliacao1.matriz_precisoes, axis=0)

        g1, ax1 = grafico.subplots()
        ax1.plot(recall_desejados, media_colunas1, marker='o', color ='blue', label = avaliacao1.infixo_arquivo)

        if avaliacao2 is not None:
            media_colunas2 = numpy.mean(avaliacao2.matriz_precisoes, axis=0)
            ax1.plot(recall_desejados, media_colunas2, marker='x', color = 'red', label = avaliacao2.infixo_arquivo)
            g1.legend()
    
        ax1.set_xlabel("Revocação")
        ax1.set_ylabel("Precisão")
        ax1.set_title("Gráfico de 11 Pontos de Precisão e Revocação "+complemento_titulo)
        g1.savefig('avalia/11pontos_apenas_ordenando-'+infixo_arquivo+'-1.pdf', format='pdf')
        #g1.show()
    
    
    # 11 pontos de precisão e revocação#
    media_colunas1b = numpy.mean(avaliacao1.matriz_precisoes_interpolacao_padrao, axis=0)


    g1, ax1 = grafico.subplots()
    ax1.plot(recall_desejados, media_colunas1b, marker='o', color ='blue', label = avaliacao1.infixo_arquivo)

    if avaliacao2 is not None:
        #media_colunas2b = numpy.mean(avaliacao2.matriz_precisoes, axis=0)
        media_colunas2b = numpy.mean(avaliacao2.matriz_precisoes_interpolacao_padrao, axis=0)
        ax1.plot(recall_desejados, media_colunas2b, marker='x', color = 'red', label = avaliacao2.infixo_arquivo)
        g1.legend()
    
    ax1.set_xlabel("Revocação")
    ax1.set_ylabel("Precisão")
    ax1.set_title("Gráfico de 11 Pontos de Precisão e Revocação "+complemento_titulo)
    g1.savefig('avalia/11pontos-'+infixo_arquivo+'-1.pdf', format='pdf')
    #g1.show()

    
    
    # R-Precision
    
    
    grafico.figure(figsize=(10,5))
    g2, ax2 = grafico.subplots()
    
    if avaliacao2 is None:
        largura_barra = 0.35
        ax2.bar(consultas, avaliacao1.precisoes_r_consultas, color='b', label = avaliacao1.infixo_arquivo,width=largura_barra)
    else:
        largura_barra = 0.25
        r1 = numpy.arange(len(consultas))
        r2 = [x + largura_barra for x in r1]
        ax2.bar(r1, avaliacao1.precisoes_r_consultas, color='b', label = avaliacao1.infixo_arquivo, width = largura_barra)
        ax2.bar(r2, avaliacao2.precisoes_r_consultas, color='r', label = avaliacao2.infixo_arquivo, width = largura_barra)
        grafico.rcParams['xtick.labelsize'] = 8
        #grafico.xticks([r + largura_barra for r in range(len(consultas))], consultas)
        g2.legend()
            

    
    ax2.set_xlabel("Consultas")
    ax2.set_ylabel("r-precision")
    ax2.set_title("Histograma de R-Precision "+complemento_titulo)
    g2.savefig('avalia/r-precision-'+infixo_arquivo+'-1.pdf', format='pdf')
    #g2.show()


   # DCG
    g3, ax3 = grafico.subplots()
    ax3.plot(pos_rank, avaliacao1.dcg, marker='o', label = avaliacao1.infixo_arquivo)

    if avaliacao2 is not None:
        ax3.plot(pos_rank, avaliacao2.dcg, marker='x', label = avaliacao2.infixo_arquivo)
        g3.legend()

    ax3.set_xlabel("Posição no ranking")
    ax3.set_ylabel("DCG")
    ax3.set_title("Discounted Cumulative Gain (DGG)"+complemento_titulo)
    g3.savefig('avalia/dcg-'+infixo_arquivo+'-1.pdf', format='pdf')
    #g3.show()

    # NDCG
    g4, ax4 = grafico.subplots()
    ax4.plot(pos_rank, avaliacao1.ndcg, marker='o', label = avaliacao1.infixo_arquivo)

    if avaliacao2 is not None:
        ax4.plot(pos_rank, avaliacao2.ndcg, marker='x', label = avaliacao2.infixo_arquivo)
        g4.legend()

    ax4.set_xlabel("Posição no ranking)")
    ax4.set_ylabel("NDCG")
    ax4.set_title("Normalized Discounted Cumulative Gain (NDCG) "+complemento_titulo)
    g4.savefig('avalia/ndcg-'+infixo_arquivo+'-1.pdf', format='pdf')
    #g4.show()



# -----------------------------------------------------------------------------------------

def salvar_histograma_precisao(consultas):
    

    # Histograma comparativo de R-Precision
    diferenca_precisao_r = [a - b for a, b in zip(avaliacao_com_stemmer.precisoes_r_consultas, avaliacao_sem_stemmer.precisoes_r_consultas)]


    dados_diferenca = list(zip(consultas, diferenca_precisao_r))
    with open("avalia/r-precision-histograma-precisao-1.csv", "w", newline="", encoding="utf-8") as rprecision_csv:
        writer = csv.writer(rprecision_csv, delimiter=";")
        writer.writerow(["Consulta", "R_stemmer - R_nostemmer"])
        writer.writerows(dados_diferenca)


    grafico.figure(figsize=(10,5))
    grafico_histograma, eixo_grafico = grafico.subplots()

    eixo_grafico.bar(consultas, diferenca_precisao_r, color='b', width = 0.35)
    eixo_grafico.set_xlabel("Código da Consulta")
    eixo_grafico.set_ylabel("Diferença de R-Precision")
    eixo_grafico.set_title("Histograma Comparativo de R-Precision (C/ Stemmer - S/ Stemmer)")
    grafico_histograma.savefig('avalia/r-precision-histograma-precisao-1.pdf', format='pdf')
    

    #grafico_histograma.show()



def escrever_dados (arquivo, complemento_titulo, avaliacao):
    arquivo.write("## Resultados obtidos "+complemento_titulo+":\n\n")
    arquivo.write(f"- F1: {avaliacao.f_1}\n")
    arquivo.write(f"- R-Precision: {avaliacao.precisao_r}\n")
    arquivo.write(f"- Precision@5: {avaliacao.precisao_5}\n")
    arquivo.write(f"- Precision@10: {avaliacao.precisao_10}\n")
    arquivo.write(f"- MAP: {avaliacao.map}\n")
    arquivo.write(f"- MRR: {avaliacao.mrr}\n")
    arquivo.write(f"- DCG: {avaliacao.dcg}\n")
    arquivo.write(f"- NDCG: {avaliacao.ndcg}\n\n")
    arquivo.write("# ---------------------------------------------------------\n")
    


# -----------------------------------------------------------------------------------------

def gerar_arquivo_relatorio():
    # Salvando os resultados no arquivo RELATORIO.MD
    with open(nome_arquivo_relatorio, "w", encoding="utf-8") as arquivo:
        arquivo.write("# ---------------------------------------------------------\n")
        arquivo.write("# Relatório de Avaliação do Algoritmo de Busca \n")
        arquivo.write("# ---------------------------------------------------------\n")
        escrever_dados(arquivo, 'Sem Stemmer', avaliacao_sem_stemmer)
        escrever_dados(arquivo, 'Com Stemmer de Porter', avaliacao_com_stemmer)


# -----------------------------------------------------------------------------------------        
        
def executar():
    print ("Inicio do modulo 4")
    hora_inicio = datetime.datetime.now()
    auxiliar.configurar_log('modulo5_avaliacao.log')
    
    logging.info("\nExecução da avaliacao iniciada em "+hora_inicio.strftime("%Y-%m-%d %H:%M:%S"))
    
    print('configuracao')
    
    ler_configuracao()
   
    abrir_resultados_consulta(nome_arquivo_consulta_com_stemmer,resultados_com_stemmer)
    abrir_resultados_consulta(nome_arquivo_consulta_sem_stemmer,resultados_sem_stemmer)
    abrir_resultados_esperados()

    processar_consultas(resultados_sem_stemmer, avaliacao_sem_stemmer)
    processar_consultas(resultados_com_stemmer, avaliacao_com_stemmer)

    gerar_salvar_dados(resultados_sem_stemmer, avaliacao_sem_stemmer)
    gerar_salvar_dados(resultados_com_stemmer, avaliacao_com_stemmer)

    gerar_arquivo_relatorio()
    
    consultas = numpy.array([valor for valor in resultados_sem_stemmer.keys()])

    salvar_graficos(consultas, avaliacao_sem_stemmer, None)
    salvar_graficos(consultas, avaliacao_com_stemmer, None)

    salvar_histograma_precisao(consultas)
    
    salvar_graficos(resultados_com_stemmer, avaliacao_com_stemmer, avaliacao_sem_stemmer)
    
    hora_fim = datetime.datetime.now()
    tempo = hora_fim - hora_inicio
    print ('Tempo de execução: '+str(tempo.seconds))
    logging.info("\nExecução da avaliacao finalizada em "+hora_fim.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("\nTempo de processamento: "+ str(tempo.seconds) + " segundos ("+str(tempo.microseconds)+" microsegundos)")

    
if __name__ == "__main__":
    executar()
    
