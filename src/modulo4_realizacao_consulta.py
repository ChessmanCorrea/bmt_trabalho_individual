import os
import logging
import datetime
import csv
import nltk
import numpy
import auxiliar


MODELO = 'MODELO'
RESULTADOS = 'RESULTADOS'
LISTA_INVERTIDA = 'LISTA_INVERTIDA'

nome_arquivo_modelo = ''
nome_arquivo_consultas = ''
nome_arquivo_saida = ''
nome_arquivo_lista_invertida = ''
modelo_vetorial = {}
dicionario_consultas = {}
dicionario_termos_binarios_consultas = {}
resultados_consultas = []

termos_lista_invertida = []

def criar_vetor_consulta(termos_consulta):    
    vetor_termos_consulta = []

    for token in termos_lista_invertida:
        if token in termos_consulta:
            vetor_termos_consulta.append(float(1))
        else:
            vetor_termos_consulta.append(float(0))
    return vetor_termos_consulta

# ---------------------------------------------------------------------------------------------
def ler_termos_lista_invertida():
    global termos_lista_invertida    
    try:
        logging.info('Lendo termos da lista invertida')
        with open(nome_arquivo_lista_invertida, encoding="utf-8",mode='r') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            termos_lista_invertida = []
            #next(reader, None)  # salta o cabeçalho. Vai precisar?
            for linha in reader:
                termos_lista_invertida.append(linha[0])
            logging.info('Termos da lista invertida carregados')
            #print ('quantidade de tokes'+str(len(termos_lista_invertida)))
    except:
        logging.info('Erro ao ler os termos da lista invertida')
            

# ---------------------------------------------------------------------------------------------

def ler_configuracao():
    global nome_arquivo_modelo
    global nome_arquivo_consultas
    global nome_arquivo_saida
    global nome_arquivo_lista_invertida

    try:
        logging.info('\n-----------------------------------------------------')
        #auxiliar.log_tempo('Iniciando a leitura do arquivo de configuração gli.cfg')
   
        nome_arquivo_configuracao = os.getcwd() + '\\busca.cfg' #precisa de duas barras porque \b é caractere especial
        #print ("nome do arquivo" + nome_arquivo_configuracao)
    
        with open(nome_arquivo_configuracao, encoding="utf-8") as arquivo_configuracao:
            for linha in arquivo_configuracao:
                posicao_igual = linha.find('=')
                if posicao_igual > 0:
                    comando = linha[0:posicao_igual]
                    nome_arquivo = linha[posicao_igual+1 : len(linha)-1]
                    if comando == MODELO:
                        nome_arquivo_modelo = nome_arquivo
                    elif comando == auxiliar.CONSULTAS:
                        nome_arquivo_consultas = nome_arquivo    
                    elif comando == RESULTADOS:
                        nome_arquivo_saida = nome_arquivo    
                    elif comando == LISTA_INVERTIDA:
                        nome_arquivo_lista_invertida = nome_arquivo    
   
        logging.info('\n\nFim da leitura do arquivo de configuração busca.cfg finalizada\n')
    except:
        logging.info('Erro ao ler o arquivo de configuração')

# ---------------------------------------------------------------------------------------------
def ler_modelo_vetorial():
    global modelo_vetorial
    try:
        logging.info('Lendo motero vetorial.')
        with open(nome_arquivo_modelo, encoding="utf-8", mode='r') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for linha in reader:
                codigo_documento = int(linha[0])
                vetor_valores = linha[1].lstrip('[').rstrip(']').split(',')
                modelo_vetorial[codigo_documento] = numpy.asarray(list(map(float, vetor_valores)))

        #print ('tamando do modelo vetorial: '+str(len(modelo_vetorial[codigo_documento])))
        logging.info('Modelo vetorial carregado.')        
    except:
        logging.info('Erro ao ler o modelo vetorial')
            
# ---------------------------------------------------------------------------------------------
def ler_consultas():
    global dicionario_consultas
    try:
        with open(nome_arquivo_consultas, encoding="utf-8", mode='r') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            next(reader, None)  # O arquivo de consulta tem cabeçalho
            for linha in reader:
                #codigo_consulta = int(linha[0]) # Pensar se realmente é necessário converter para inteiro. AUmenta o desempenho?
                codigo_consulta = int(linha[0]) # Pensar se realmente é necessário converter para inteiro. AUmenta o desempenho?
                vetor_valores = nltk.word_tokenize(linha[1],'english')
                dicionario_consultas[codigo_consulta] = vetor_valores

        #print(dicionario_consultas)
    except:
        #e = sys.exc_info()[0]
        logging.info('Erro ao carregar consulta.')
        print ('Erro ao ler consultas.')

# ---------------------------------------------------------------------------------------------

def gerar_lista_termos():
    global dicionario_termos_binarios_consultas
    try:
        for codigo_consulta, termos_consulta in dicionario_consultas.items():
            dicionario_termos_binarios_consultas[codigo_consulta] = criar_vetor_consulta(termos_consulta)
            #print('tamaho do vetor: '+str(len(dicionario_termos_binarios_consultas[codigo_consulta] )))
    except:
        logging.info('Erro ao gerar lista binária de termos.')
        
# ---------------------------------------------------------------------------------------------
            
def gerar_resultados_consultas():
    global resultados_consultas
    
    try:
    
        logging.info('Iniciando geração dos resultados das buscas')

        for codigo_consulta, vetor_valores_consulta in dicionario_termos_binarios_consultas.items(): #ok

            distancias_documento = []

            for codigo_documento, vetor_valores_documento in modelo_vetorial.items():

                distancia = nltk.cluster.cosine_distance(vetor_valores_consulta, vetor_valores_documento) 
                distancias_documento.append([codigo_documento, distancia])

            distancias_documento_ordenadas = sorted(distancias_documento, key=lambda elem: elem[1])

            for i, par_documento_distancia in enumerate(distancias_documento_ordenadas, start=1):
                codigo_documento = par_documento_distancia[0]
                distancia = par_documento_distancia[1]

                # 1-indexed
                posicao = i

                if (float(distancia) != 1.0):
                    resultados_consultas.append([ codigo_consulta, [posicao, codigo_documento, round(distancia, auxiliar.CASAS_DECIMAIS)]])

        logging.info('Fim da geração dos resultados das buscas')
    except:
        logging.info('Erro ao gerar os resultados das buscas')
            
# ---------------------------------------------------------------------------------------------

def executar():
    print ("Inicio do modulo 4")

    hora_inicio = datetime.datetime.now()
    auxiliar.configurar_log('modulo4_busca.log')
    
    logging.info("\nExecução de consulta iniciada em "+hora_inicio.strftime("%Y-%m-%d %H:%M:%S"))
    
    print('configuracao')
    ler_configuracao()
    
    print('leitura dos termos da lista investida')
    ler_termos_lista_invertida()
    
    print('leitura do modelo vetorial')
    ler_modelo_vetorial()
    
    print('leitura das consultas')
    ler_consultas()
    
    print('Geração da lista dos termos')
    gerar_lista_termos()
    
    print('Geração dos resultados')
    gerar_resultados_consultas()
    
    print('gravação do arquivo')
    auxiliar.gerar_arquico_cvs(nome_arquivo_saida, resultados_consultas)

    hora_fim = datetime.datetime.now()
    
    tempo = hora_fim - hora_inicio

    logging.info("\nFinalização da consulta em "+hora_fim.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("\nTempo de processamento: "+ str(tempo.seconds) + " segundos ("+str(tempo.microseconds)+" microsegundos)")
    
    print ("Fim do modulo 4")
    
# ---------------------------------------------------------------------------------------------

if __name__ == "__main__":
    executar()
