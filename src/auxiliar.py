import logging
import datetime
import csv
import nltk


LEIA ='LEIA'
ESCREVA = 'ESCREVA'
CONSULTAS = 'CONSULTAS'
RESULTADOS = 'RESULTADOS'
ESPERADOS = 'ESPERADOS'
TAMANHO_MINIMO_PALAVRA = 2
CASAS_DECIMAIS = 3

caracteres_exclusao_termo = {'0','1','2','3','4','5','6','7','8','9','.',',','-','+','/',"'", '´', '`'}

usar_stemmer = False

stemmer = nltk.PorterStemmer()
stopwords = nltk.corpus.stopwords.words('english')


# -------------------------------------------------------------------

def configurar_log(nome_arquivo):
    logging.basicConfig(filename='result/'+nome_arquivo, 
                        encoding='utf-8', 
                        level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        filemode='w')
# -------------------------------------------------------------------
def log_tempo (mensagem)    :
    logging.info("\n"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" "+mensagem)

# -------------------------------------------------------------------
def termo_valido(termo):
    s = [l for l in termo if l in caracteres_exclusao_termo]
    return len(s) == 0

# -------------------------------------------------------------------

def gerar_arquico_cvs(nome_arquivo, dicionario):
    
    try:
 
  
        logging.info('Gerando arquivo cvs')

        with open(nome_arquivo, 'w') as arquivo_csv:
            writer = csv.writer(arquivo_csv, delimiter=';', lineterminator='\n')
            if isinstance(dicionario, list):
                for item in dicionario:
                    writer.writerow(item)
            else:    
                for item in dicionario.items():
                    writer.writerow(item)

        logging.info('Fim da geração do arquivo cvs')
    except:
        logging.info('Erro ao gravar o arquivo cvs '+nome_arquivo)
        print('Erro ao gravar o arquivo cvs '+nome_arquivo)
    
    
# -------------------------------------------------------------------
def processar_tokens(lista_tokens) :
    tokens_pre_processados=[]
    if usar_stemmer:
        tokens_pre_processados = [stemmer.stem(t) for t in lista_tokens if t not in stopwords and len(t) > TAMANHO_MINIMO_PALAVRA and termo_valido(t)]
    else:
        tokens_pre_processados = [t for t in lista_tokens if t not in stopwords and len(t) >= TAMANHO_MINIMO_PALAVRA and termo_valido(t)]
    return tokens_pre_processados    
       