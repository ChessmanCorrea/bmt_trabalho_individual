# bmt_projeto_individual
 Projeto de Busca e mineração de Texto

 Se desejado, o aequivo completo.py executa todos os módulos.

O programa também gera gráficos comparativos. 

As dependências estão listadas no arquivo dependencias.txt.

Passo 1. 
Criação de uma lista invertida. Esta lista contém uma coluna os termos e outra coluna que representa um vetor com os documentos que possuem or termos.

Para isso, são executados os seguintes passos:

   1.1. Remoção da pontuação.
   1.2. Remoção de palavras (termos) com 1 ou 2 caracteres.
   1.3. Uso do Stemmer para substituir as palavras pelos seus respectivos stemmers.
   1.4. Extração dos tokens dos textos.
   1.5. Criação de mapa associando os documentos com os respectivos tokens (a chave do mapa é o token)
   1.6. Geração do arquivo CSV a partir do mapa.

OBSERVAÇÃO: O uso de stemmer aumenta a precisão e revocação do modelo.   


Passo 2.
Geração do modelo vetorial a partir da lista invertida. O modelo contém duas colunas. A primeira coluna é o códgo do documento. 
A segunda coluna é um vetor contendo o TF_IDF de cada termo referente ao documento.

TF = Term Frequency
IDF = Inverse Term Frequency


Para isso, são executados os seguintes passos:
   
   2.1. Contagem da frequencia de cada termo em um documento.
   2.2. Cálculo do IDF dos termos, usando a seguinte fórmula:
        IDF - log (quantidade_documentos / quantidade_documentos_termo)
   2.3. Cálculo do TF do termo a partir da seguinte fórmula:
       TF = frequencia_termo / 
   2.4. Cálculo do TF-IDF (peso) do termo a partir da seguinte fórmula:
       TF_IDF  = TF * IDF.


