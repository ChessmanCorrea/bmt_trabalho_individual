import os
import logging
import datetime
import auxiliar
import xml.etree.ElementTree as xml
import nltk
import csv

nome_arquivo_entrada = ''
nome_arquivo_consultas = ''
nome_arquivo_esperados = ''
dicionario_consultas = {}
lista_documentos_esperados =[]


# ---------------------------------------------------------------------------------------------

def ler_configuracao():
    global nome_arquivo_entrada
    global nome_arquivo_consultas
    global nome_arquivo_esperados

    try:
        auxiliar.log_tempo('Iniciando a leitura do arquivo de configuração pc.cfg')
   
        nome_arquivo_configuracao = os.getcwd() + '\pc.cfg' #precisa de duas barras porque \p é caractere especial
    
        with open(nome_arquivo_configuracao, encoding="utf-8") as arquivo_configuracao:
            for linha in arquivo_configuracao:
                posicao_igual = linha.find('=')
                if posicao_igual > 0:
                    comando = linha[0:posicao_igual]
                    nome_arquivo = linha[posicao_igual+1 : len(linha)-1]
                    if comando == auxiliar.LEIA:
                        nome_arquivo_entrada = nome_arquivo
                    elif comando == auxiliar.CONSULTAS:
                        nome_arquivo_consultas = nome_arquivo    
                    elif comando == auxiliar.ESPERADOS:
                        nome_arquivo_esperados = nome_arquivo    
                    
   
        logging.info('Fim da leitura do arquivo de configuração pc.cfg finalizada')
    except:
        logging.info('Erro ao ler o arquivo de configuração')

# ---------------------------------------------------------------------------------------------
def processar_consultas():
    global lista_documentos_esperados
    try:

        arvore_xml = xml.parse(nome_arquivo_entrada)
        raiz_xml = arvore_xml.getroot()

        lista_documentos_esperados+=[['QueryNumber','DocNumber','DocVotes']]

        for consulta in raiz_xml.findall('QUERY'):

            numero_consulta = consulta.find("QueryNumber").text.strip()
            texto_consulta = consulta.find("QueryText").text.strip()
            texto_consulta = texto_consulta.lower()
            tokens= nltk.word_tokenize(texto_consulta, 'english')

            dicionario_consultas['QueryNumber'] = 'QueryText' #títulos das colunas
            dicionario_consultas[numero_consulta] = ' '.join(auxiliar.processar_tokens(tokens)).upper() 

            
            for item in consulta.find("Records").findall('Item'):
                documento = item.text.strip()
                score = item.attrib['score'].strip()
                
                quantidade_votos = 0
                for caractere in score:
                    if caractere != "0":
                        quantidade_votos += 1
                
                lista_documentos_esperados+=[[numero_consulta,documento,quantidade_votos]]

        logging.info('Quantidade de consultas processadas '+str(len(dicionario_consultas)))
        logging.info('Quantidade de resultados esperados processados '+str(len(lista_documentos_esperados)))
    except:
        logging.info("Erro ao processar consultas")
        print('Erro ao processar as consultas')
        
# ---------------------------------------------------------------------------------------------
def executar():
    print ("Inicio do modulo 3")

    hora_inicio = datetime.datetime.now()
    auxiliar.configurar_log('modulo3_processamento_consulta.log')
    
    logging.info("Execução de consulta iniciada em "+hora_inicio.strftime("%Y-%m-%d %H:%M:%S"))
    
    ler_configuracao()
    processar_consultas()
    auxiliar.gerar_arquico_cvs(nome_arquivo_consultas,dicionario_consultas)
    auxiliar.gerar_arquico_cvs(nome_arquivo_esperados, lista_documentos_esperados)

    hora_fim = datetime.datetime.now()
    
    tempo = hora_fim - hora_inicio

    logging.info("Finalização da consulta em "+hora_fim.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("Tempo de processamento: "+ str(tempo.seconds) + " segundos ("+str(tempo.microseconds)+" microsegundos)")
    
    print ("Fim do modulo 3")

# ---------------------------------------------------------------------------------------------

if __name__ == "__main__":
    executar()
