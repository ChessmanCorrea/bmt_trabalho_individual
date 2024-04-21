import os
import datetime
import logging
import auxiliar
import csv
import math
nome_arquivo_entrada = ''
nome_arquivo_saida = ''
lista_invertida = {}
matriz_termo_documento = {}


# ---------------------------------------------------------------------------------------------

def ler_configuracao():
    global nome_arquivo_entrada
    global nome_arquivo_saida

    try:
        logging.info('Iniciando leitura do arquivo de configuração index.cfg')
   
        nome_arquivo_configuracao = os.getcwd() + '\index.cfg'
    
        with open(nome_arquivo_configuracao, encoding="utf-8") as arquivo_configuracao:
            for linha in arquivo_configuracao:
                posicao_igual = linha.find('=')
                if posicao_igual > 0:
                    comando = linha[0:posicao_igual]
                    nome_arquivo = linha[posicao_igual+1 : len(linha)-1]
                    if comando == auxiliar.LEIA:
                        nome_arquivo_entrada = nome_arquivo
                    elif comando == auxiliar.ESCREVA:
                        nome_arquivo_saida = nome_arquivo    
   
        logging.info('Fim da leitura do arquivo de configuração index.cfg finalizada')
    except:
        logging.info('Erro ao ler o arquivo de configuração')

# ---------------------------------------------------------------------------------------------

def ler_arquivo_lista_intertida():
    try:
        logging.info('Lendo arquivo da lista invertida')
        with open(nome_arquivo_entrada, 'r') as arquivo_csv:
            reader = csv.reader(arquivo_csv, delimiter=';')
            for row in reader:
                token = row[0]
                codigos_documentos = row[1].lstrip('[').rstrip(']').replace("'", "").split(',')
                lista_invertida[token] = codigos_documentos
        logging.info('Fim da leitura do arquivo da lista invertida')            
    except:        
        logging.info('Erro ao ler o arquivo de lista invertida')

# ---------------------------------------------------------------------------------------------

def gerar_modelo_vetorial():
    try:
        logging.info('Gerando modelo vetorial')
        lista_termos = lista_invertida.keys()
        frequencia_termos_documentos = {}
        idf_termos = {}
    
        # Gera uma lista de documentos não repetidos
        for termo, documentos_com_o_termo in lista_invertida.items():
            
            #Gera uma coleção de documentos com a frequência de cada termo
            for documento in documentos_com_o_termo:
                documento = documento.strip() #misteriosamente aparece um espaço no início do código do documento...
                if documento in frequencia_termos_documentos:
                    frequencia_termos_documentos[documento][termo]+=1
                else:    
                    frequencia_termos_documentos[documento]={}
                    #inclui todos os termos na lista de termos do documento
                    for termo_inclusao in lista_termos:
                        frequencia_termos_documentos[documento][termo_inclusao]=0
                    frequencia_termos_documentos[documento][termo]=1
                        
                        
    
        # Calcula o IDF (a frequência inversa dos termos (palavras)
        # IDF = log (quantidade_docummentos  / quantidade_documentos_com_o_termo)
        
        quantidade_documentos = len(frequencia_termos_documentos)
        
        # Contar quantos documentos possuem o termo 
        for termo, documentos_com_o_termo in lista_invertida.items():
            # O uso do set tem como finalidade eliminar documentos repetidos, retornando a quantidade de documentos com o termo
            quantidade_documentos_com_o_termo = len(set(documentos_com_o_termo));
            idf_termos[termo] = math.log(quantidade_documentos/quantidade_documentos_com_o_termo)
            
            

        #for i in range(len(lista_documentos)):
        #    codigo_documento = lista_documentos[i]
        for codigo_documento, frequencia_termos in frequencia_termos_documentos.items():

            pesos_palavra = []

            for termo in lista_termos:
                
                idf = idf_termos[termo]

                tf = frequencia_termos[termo]/len(frequencia_termos)

                tf_idf = round(tf * idf, auxiliar.CASAS_DECIMAIS)
                

                pesos_palavra.append(tf_idf)

            matriz_termo_documento[codigo_documento] = pesos_palavra
    
        logging.info('Fim da geração do modelo vetorial')
        
    except:
        logging.info('Erro ao gerar o modelo vetorial')



# ---------------------------------------------------------------------------------------------
def executar():
    print ("Inicio do modulo 2")

    hora_inicio = datetime.datetime.now()
    auxiliar.configurar_log('modulo2_indexador.log')
    
    logging.info("Geração da lista invertida iniciada em "+hora_inicio.strftime("%Y-%m-%d %H:%M:%S"))
    
    ler_configuracao()
    ler_arquivo_lista_intertida()
    gerar_modelo_vetorial()
    auxiliar.gerar_arquico_cvs(nome_arquivo_saida, matriz_termo_documento)

    hora_fim = datetime.datetime.now()
    
    tempo = hora_fim - hora_inicio

    logging.info("Finalização da lista invertida em "+hora_fim.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("Tempo de processamento: "+ str(tempo.seconds) + " segundos ("+str(tempo.microseconds)+" microsegundos)")
    
    print ("Fim do modulo 2")
                
            
# ---------------------------------------------------------------------------------------------

if __name__ == "__main__":
    executar()
