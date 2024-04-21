'''
  - Este módulo tem como objetivo ler resumos de artigos contidos
    em arquivos xml e gerar uma "lista invertida". Cada linha 
    da lista mantém uma palavra (token) e um vetor contendo
    os códigos dos documentos onde a palavra foi encontrada. 
  
  - As stopwords, números, acentos e outros símbolos são removidos.
'''
import os
import logging
import datetime
import xml.etree.ElementTree as xml
import nltk
import auxiliar

CAMPO_ABSTRACT ='ABSTRACT'
CAMPO_EXTRACT ='EXTRACT'
CAMPO_REGISTRO ='RECORD'
CAMPO_NUMERO_REGISTRO ='RECORDNUM'

nomes_arquivos_entrada = []
nome_arquivo_saida = ''
dicionario_documentos = {}
dicionario_tokens = {}
documentos_tokens = {}



# ---------------------------------------------------------------------------------------------

def ler_configuracao():
    global nome_arquivo_saida

    try:
        #auxiliar.log_tempo('Iniciando a leitura do arquivo de configuração gli.cfg')
   
        nome_arquivo_configuracao = os.getcwd() + '\gli.cfg'
        #print ("nome do arquivo" + nome_arquivo_configuracao)
    
        with open(nome_arquivo_configuracao, encoding="utf-8") as arquivo_configuracao:
            for linha in arquivo_configuracao:
                posicao_igual = linha.find('=')
                if posicao_igual > 0:
                    comando = linha[0:posicao_igual]
                    nome_arquivo = linha[posicao_igual+1 : len(linha)-1]
                    if comando == auxiliar.LEIA:
                        nomes_arquivos_entrada.append(nome_arquivo)
                    elif comando == auxiliar.ESCREVA:
                        nome_arquivo_saida = nome_arquivo    
   
        logging.info('Arquivos de entrada: '+str(len(nomes_arquivos_entrada)))
        logging.info('Fim da leitura do arquivo de configuração gli.cfg finalizada')
    except:
        logging.info('Erro ao ler o arquivo de configuração')

# ---------------------------------------------------------------------------------------------
def ler_arvivos_xml():
    try:
        nome_arquivo = ''
        logging.info('Iniciando a leitura dos arquivos de entrada')
        diretorio = os.getcwd()
        for nome_arquivo in nomes_arquivos_entrada:
            arvore_xml = xml.parse(diretorio+'\\'+nome_arquivo)
            raiz_xml = arvore_xml.getroot()
            # O arquivo XML contém vários nós do tipo REGISTRO
            # Um nó do tipo registro representa um artigo, com número de registro e abstract
            resumo = ''
            for registro in raiz_xml.findall(CAMPO_REGISTRO):
                codigo_documento = registro.find(CAMPO_NUMERO_REGISTRO).text.strip()
                registro_dados = registro.find(CAMPO_ABSTRACT)
                if registro_dados is not None:
                    resumo = registro_dados.text
                else:    
                    registro_dados = registro.find(CAMPO_EXTRACT)
                    if registro_dados is not None:
                        resumo = registro_dados.text
            
                if len(resumo) > 0:
                    dicionario_documentos[codigo_documento] = resumo
                else:
                    logging.warning('Não foi possível extrair conteúdo do arquivo: '+codigo_documento)

        logging.info('Quantidade de arquivos lidos: '+str(len(dicionario_documentos)))
    
        logging.info('Fim da leitura dos arquivos de entrada')

    except:
        logging.info('Erro ao ler arquivos XML. Arquivo '+nome_arquivo)
                

            
# ---------------------------------------------------------------------------------------------
def pre_processar_dados():
    try:
        logging.info('Iniciando o pré-processamento dos dados')
    
        for codigo_documento, conteudo_documento in dicionario_documentos.items():
            # 1. Conversão para caracteres minísculos para a eliminação dos stopwords
            conteudo_documento = conteudo_documento.lower()
        
            # 2. Tokenização
            tokens= nltk.word_tokenize(conteudo_documento, 'english')
        
            # 3. Procesamento dos tokens
            dicionario_tokens[codigo_documento] = auxiliar.processar_tokens(tokens)

        logging.info('Quantidade de documentos pré-processados: '+str(len(dicionario_tokens)))
        logging.info('Fim do pré-processamento dos dados')

    except:    
        logging.info('Erro ao fazer o pro-processamento dos dados')
        

# ---------------------------------------------------------------------------------------------

def gerar_lista():
    try:
    
        logging.info('Gerando lista')
    
        for codigo_documento, tokens in dicionario_tokens.items():
            for token in tokens:
                palavra = token.upper()

                if not palavra in documentos_tokens.keys():
                    documentos_tokens[palavra] = []
 
                documentos_tokens[palavra]+=[codigo_documento] #mais rápido que o append?
                  
        logging.info('Quantidade de elementos da lista invertida: '+str(len(documentos_tokens)))
        
        logging.info('Fim da geração da lista')
    except:
        logging.info('Erro ao gerar a lista invertida')


# ---------------------------------------------------------------------------------------------
def executar():
    hora_inicio = datetime.datetime.now()
    auxiliar.configurar_log('modulo1_lista_invertida.log')
    
    logging.info("Geração da lista invertida iniciada em "+hora_inicio.strftime("%Y-%m-%d %H:%M:%S"))
    
    ler_configuracao()
    ler_arvivos_xml()
    pre_processar_dados()
    gerar_lista()
    auxiliar.gerar_arquico_cvs(nome_arquivo_saida,documentos_tokens)
    
    hora_fim = datetime.datetime.now()
    
    tempo = hora_fim - hora_inicio

    logging.info("Finalização da lista invertida em "+hora_fim.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("Tempo de processamento: "+ str(tempo.seconds) + " segundos ("+str(tempo.microseconds)+" microsegundos)")
    
    print ("fim do modulo 1")
        
# ---------------------------------------------------------------------------------------------
        
if __name__ == "__main__":
    executar()
