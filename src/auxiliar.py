import logging
import datetime
import csv
import nltk
import stemmer_porter


LEIA = 'LEIA'
ESCREVA = 'ESCREVA'
CONSULTAS = 'CONSULTAS'
RESULTADOS = 'RESULTADOS'
ESPERADOS = 'ESPERADOS'
STEMMER = 'STEMMER'
NOSTEMMER = 'NOSTEMMER'
RELATORIO = 'RELATORIO'
FINAL_ARQUIVO_STEMMER = '_stemmer.csv'
FINAL_ARQUIVO_NOSTEMMER = '_nostemmer.csv'

TAMANHO_MINIMO_PALAVRA = 2
CASAS_DECIMAIS = 3

caracteres_exclusao_termo = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', ',', '-', '+', '/', "'", '´', '`'}

usar_stemmer = True

# stemmer = nltk.PorterStemmer()
stemmer = stemmer_porter.PorterStemmer()

stopwords = nltk.corpus.stopwords.words('english')


def gerar_nome_arquivo (nome_referencia):
    if usar_stemmer:
        return nome_referencia.replace('.csv', FINAL_ARQUIVO_STEMMER) 
    else:
        return nome_referencia.replace('.csv', FINAL_ARQUIVO_NOSTEMMER) 

# -------------------------------------------------------------------


def configurar_uso_stemmer(comando):
    global usar_stemmer
    comando = comando.upper().strip()
    if comando == STEMMER:
        usar_stemmer = True
        print('Com stemmer')
        logging.info('Processamento com stemmer')
    elif comando == NOSTEMMER:
        usar_stemmer = False
        print('Sem stemmer')
        logging.info('Processamento sem stemmer')


# -------------------------------------------------------------------

def configurar_log(nome_arquivo):
    logging.basicConfig(filename='result/'+nome_arquivo,
                        encoding='utf-8',
                        level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        filemode='w')
# -------------------------------------------------------------------


def log_tempo (mensagem)    :
    logging.info(
        "\n"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" "+mensagem)

# -------------------------------------------------------------------

def termo_valido(termo):
    s = [l for l in termo if l in caracteres_exclusao_termo]
    return len(s) == 0

# -------------------------------------------------------------------


def gerar_arquico_cvs(nome_arquivo, dicionario):

    try:

        logging.info('Gerando arquivo cvs')

        with open(nome_arquivo, 'w') as arquivo_csv:
            writer = csv.writer(arquivo_csv, delimiter=';',
                                lineterminator='\n')
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
def processar_tokens(lista_tokens):
    tokens_pre_processados = []
    if usar_stemmer:
        # tokens_pre_processados = [stemmer.stem(t) for t in lista_tokens if t not in stopwords and len(t) > TAMANHO_MINIMO_PALAVRA and termo_valido(t)]
        tokens_pre_processados = [stemmer.stem(t, 0, len(t)-1) for t in lista_tokens if t not in stopwords and len(t) > TAMANHO_MINIMO_PALAVRA and termo_valido(t)]
    else:
        tokens_pre_processados = [t for t in lista_tokens if t not in stopwords and len(
            t) >= TAMANHO_MINIMO_PALAVRA and termo_valido(t)]
    return tokens_pre_processados
