import os, re
import sqlite3

con = sqlite3.connect("legislativo.db")
cur = con.cursor()
cur.execute("CREATE TABLE norma(id  INTEGER PRIMARY KEY, tipo, data_publicacao, numero, ementa, preambulo)")
cur.execute("CREATE TABLE norma_texto(id  INTEGER PRIMARY KEY, texto, pai_id, ordem, tipo, norma_id)")

#percorrer diretorio extrair e listar todos os arquivos
def listar_arq_diretorio():
    lista_arquivos = []
    for root, dirs, files in os.walk("extrair"):
        for file in files:
            lista_arquivos.append(os.path.join(root, file))
    return lista_arquivos


#carregar o conteudo dos arquivos retornados na função extrator ()
def carregar_arquivos():
    lista_arquivos = listar_arq_diretorio()
    lista_conteudo = []
    for arquivo in lista_arquivos:
        with open(arquivo, 'r') as f:
            lista_conteudo.append(f.readlines())
    return lista_conteudo

def extrair_artigos(lista_conteudo):
    artigos = []
    for conteudo in lista_conteudo:
        for linha in conteudo:
            if linha.upper().startswith('ART'):
                numero_artigo = linha.split(' ')[1]
                inteiro = int(re.findall("\d+", numero_artigo)[0])
                artigos.append([inteiro , linha.strip()])
    return artigos

def extrair_numero_artigos(artigos_encontrados):
    return [int(artigo[0]) for artigo in artigos_encontrados]

def extrair_intervalo_entre_artigos(numero_artigos_encontrados):
    intervalo = []
    ultimo_artigo = numero_artigos_encontrados[-1]
    for artigo in numero_artigos_encontrados:
        if artigo == ultimo_artigo:
            return intervalo
        inicio = artigo
        final = inicio + 1
        while final not in numero_artigos_encontrados:
            final = final + 1
        intervalo.append([inicio, final])
    return intervalo

def inicia_com_numero_romano(conteudo):
    conteudo_split = conteudo.strip().split(' ')[0]
    return re.match(r'^[MDCLXVI]+',conteudo_split) is not None and len(conteudo_split) <= 3

def extrair_conteudo_entre_artigos(intervalo, lista_conteudo):
    paragrafros_incisos = []
    adicionar = False
    for inicio, final in intervalo:
        for conteudo in lista_conteudo[0]:
            if conteudo.upper().startswith('ART. ' + str(inicio)):
                adicionar = True
            if (conteudo.upper().startswith('PAR') 
                or conteudo.startswith('§')
                or inicia_com_numero_romano(conteudo) )and adicionar:
                paragrafros_incisos.append([inicio,conteudo.strip()])
            if conteudo.upper().startswith('ART. ' + str(final)):
                adicionar = False
                break

    return paragrafros_incisos


conteudo_norma = carregar_arquivos()
artigos_encontrados = extrair_artigos(conteudo_norma)
numero_artigos_encontrados = extrair_numero_artigos(artigos_encontrados)
intervalo = extrair_intervalo_entre_artigos(numero_artigos_encontrados) 
relacao_artigos_paragrafos_incisos = extrair_conteudo_entre_artigos(intervalo, conteudo_norma)

print("Fim --- primeira parte ")

#teste para banco de dados
# tipo, data_publicacao, numero, ementa, preambulo
cur.execute('''INSERT INTO norma
            (tipo, data_publicacao, numero, ementa, preambulo) 
            VALUES('RESOLUÇÃO NORMATIVA', '29 de julho de 2020', '117/2020',
            'Disciplina a gestão de patrimônio da Câmara Municipal de Teresina e dá outras providências.',
            'A MESA DIRETORA DA CÂMARA MUNICIPAL DE TERESINA, Estado do Piauí, em colegiado, no uso de suas atribuições legais e regimentais, com fulcro no art. 58, parágrafo único, alínea “a”, e 60 da Lei Orgânica do Município, e art. 36, VI, 163, V, do seu Regimento Interno, aprovou, em Plenário, e editou a seguinte Resolução Normativa:')
            ''')
con.commit() 

#id, texto, pai, ordem, tipo, , norma_id
artigos = []
for numero,  texto in artigos_encontrados:
    artigos.append([texto, 0, numero, 'artigo', '1'])
cur.executemany("INSERT INTO norma_texto(texto, pai_id, ordem, tipo, norma_id) VALUES(?, ?, ?,?,?)", artigos)
con.commit() 


#id, texto, pai, ordem, tipo, norma_id
paragrafos = []
for pai, texto in relacao_artigos_paragrafos_incisos:
    paragrafos.append([texto, pai, 0, 'paragrafo', '1'])

cur.executemany("INSERT INTO norma_texto(texto, pai_id, ordem, tipo, norma_id) VALUES(?, ?, ?,?,?)", paragrafos)
con.commit()