import os
import uuid
import random
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from faker import Faker

# ---------------------------------------------------------
# SETUP E CONFIGURAÇÕES
# ---------------------------------------------------------
load_dotenv()
fake = Faker('pt_BR')

SEMENTES_PROPOSTAS = [
    # Mobilidade
    ("Implementação de Pedágio Urbano no Centro", "Criação de uma taxa de R$ 5,00 para veículos particulares circularem no centro em horário de pico.", "Mobilidade"),
    ("Tarifa Zero aos Domingos", "Gratuidade no transporte público municipal todos os domingos e feriados.", "Mobilidade"),
    ("Faixa Exclusiva para Motociclistas", "Criação de faixas azuis nas principais avenidas para reduzir acidentes de trânsito.", "Mobilidade"),
    ("Integração Tarifária Regional", "Integração gratuita entre ônibus municipais e malha de trens metropolitanos na primeira hora.", "Mobilidade"),

    # Segurança
    ("Programa Bairro Iluminado", "Substituição de 100% das lâmpadas antigas por LED em ruas de alto índice de criminalidade.", "Segurança"),
    ("Câmeras Corporais na Guarda Municipal", "Uso obrigatório de bodycams por todos os agentes da GCM durante patrulhamentos.", "Segurança"),
    ("Drones para Monitoramento Integrado", "Uso de drones pela defesa civil e segurança pública em áreas de risco e praças.", "Segurança"),

    # Saúde
    ("Hospital Veterinário Público", "Construção de uma unidade de atendimento gratuito para animais domésticos.", "Saúde"),
    ("Telemedicina nos Postos", "Implantação de totens de atendimento virtual e triagem remota nas UBSs.", "Saúde"),
    ("Mutirão de Exames aos Finais de Semana", "Abertura das unidades de saúde aos sábados para reduzir filas de espera.", "Saúde"),

    # Educação
    ("Escola em Tempo Integral", "Ampliação da carga horária nas escolas da rede municipal com oficinas culturais.", "Educação"),
    ("Vouchers para Creches Privadas", "Subsídio da prefeitura para zerar a fila de creches utilizando a rede privada.", "Educação"),
    ("Kits de Robótica nas Escolas", "Distribuição de laboratórios móveis de programação para o ensino fundamental.", "Educação"),

    # Meio Ambiente
    ("Multa para Descarte Irregular", "Aumento de 500% na multa para descarte de entulho em vias públicas e terrenos baldios.", "Meio Ambiente"),
    ("Frota de Ônibus Elétricos", "Substituição gradual de 30% da frota municipal por veículos emissão zero até 2028.", "Meio Ambiente"),
    ("Criação do Parque Ecológico Municipal", "Desapropriação de áreas ociosas para a construção de um grande parque de preservação.", "Meio Ambiente"),

    # Economia
    ("Incentivo Fiscal para Startups", "Isenção de ISS por 5 anos para empresas de tecnologia e inovação que se instalarem no município.", "Economia"),
    ("Feira Noturna Gastronômica", "Regulamentação de food trucks e feiras noturnas fixas nas principais praças da cidade.", "Economia"),
    ("Programa Jovem Aprendiz Municipal", "Cotas em empresas parceiras da prefeitura para incentivar o primeiro emprego.", "Economia"),

    # Infraestrutura
    ("Revitalização do Calçadão Comercial", "Reforma completa, padronização e acessibilidade das calçadas do centro.", "Infraestrutura")
]

SEMENTES_COMENTARIOS = [
    # Apoio Total
    "Apoio totalmente a ideia! Isso vai melhorar muito a nossa qualidade de vida.",
    "Excelente! Vai ajudar demais a população, já passou da hora de termos medidas corajosas assim na cidade!",
    "Parabéns pela proposta. Tem o meu voto e da minha família.",
    "Perfeito, isso é exatamente o que a nossa região precisa há anos.",
    "Projeto fantástico. Assino embaixo, podem aprovar sem mudar uma vírgula.",
    "Essa é a melhor lei que já propuseram por aqui recentemente. Concordo 100%.",
    "Gostei muito. Iniciativa brilhante que pensa no futuro do município.",
    "Completamente a favor. Vai trazer desenvolvimento e organizar a casa.",
    "Ótima ideia! Precisamos de mais políticos pensando de forma inovadora assim.",
    "Apoiadíssimo. Medida essencial para o progresso do nosso povo.",

    # Apoio com Alteração
    "Acho a iniciativa boa, mas o valor da taxa precisa ser revisto para não prejudicar os trabalhadores.",
    "Excelente ideia, porém deveriam isentar moradores locais dessa cobrança ou regra.",
    "Sou a favor do projeto, mas o prazo de implementação de 5 anos é muito longo. Precisamos disso para ontem.",
    "A proposta é ótima, contudo acho que falta detalhar melhor de onde vai sair o orçamento.",
    "Concordo com o objetivo principal, mas o artigo 3º precisa ser alterado para não punir os pequenos comerciantes.",
    "Tem o meu apoio em tese, mas sugiro que incluam um comitê de fiscalização popular no texto da lei.",
    "A intenção é muito válida. Só precisa ajustar a redação para não criar brechas legais.",
    "Gostei da proposta, no entanto, acho que a área de abrangência deveria ser ampliada para os bairros afastados.",
    "Iniciativa correta, mas com ressalvas. O financiamento não pode sair do fundo da educação.",
    "Apoio a pauta, mas requer emendas. Da forma como está escrita, pode prejudicar a classe média.",

    # Dúvida / Neutro
    "Não tenho certeza se isso resolve o problema raiz, precisamos de mais estudos técnicos.",
    "Até que faz sentido, mas quero ver se o dinheiro vai mesmo para melhorias públicas na prática.",
    "Preciso ler o projeto de lei na íntegra para opinar. A descrição está muito vaga.",
    "Será que a prefeitura tem estrutura para fiscalizar isso? Fica a dúvida.",
    "Parece interessante no papel, mas a execução no Brasil costuma ser diferente.",
    "Não sou nem contra nem a favor ainda. Faltam dados estatísticos justificando a medida.",
    "Gostaria de ver o impacto financeiro disso nos cofres públicos antes de me posicionar.",
    "A ideia não é ruim, mas também não é a prioridade da cidade no momento atual.",
    "Pode ser que funcione, pode ser que não. Vamos acompanhar o debate na câmara.",
    "Estou indeciso. Os argumentos de ambos os lados parecem fazer sentido.",

    # Oposição com Remoção
    "A intenção do projeto é boa, mas o trecho que cria novos impostos deve ser removido.",
    "Concordo que precisamos de segurança, mas sou contra a instalação dessas câmeras específicas, tirem essa parte.",
    "O projeto em si tem méritos de organização, mas me oponho totalmente à cláusula de multas absurdas, isso tem que cair.",
    "Apoio a ideia geral do texto, mas recuso veementemente o parágrafo que retira direitos adquiridos. Revoguem esse artigo.",
    "Essa lei até pode seguir em frente, desde que removam a exigência de cobrança de pedágio ou taxa. Sem isso, eu aprovo.",
    "A base da ideia é aceitável, contudo, a imposição de horários restritos é um erro. Apaguem essa restrição do projeto.",
    "Sou a favor da modernização, mas me oponho à privatização do serviço descrita no anexo. Removendo isso, fica bom.",
    "Entendo a necessidade, mas a parte punitiva do texto precisa ser totalmente excluída para ter meu apoio.",
    "O conceito é legal, só que o artigo que transfere a responsabilidade para o cidadão é inaceitável. Cortem isso.",
    "Concordo com a criação do programa, mas sou terminantemente contra a taxa de adesão obrigatória. Removam a taxa.",

    # Rejeição Total
    "Sou contra. Isso é um absurdo e só serve para tirar dinheiro do bolso do cidadão trabalhador.",
    "Isso vai destruir o comércio local. A lei deve ser rejeitada imediatamente e arquivada.",
    "Completamente inviável. Quem precisa trabalhar não tem outra opção. Voto não.",
    "Essa é a pior proposta que eu já vi. Um completo desrespeito com a população.",
    "Rejeito totalmente. Isso é apenas cabide de emprego e burocracia desnecessária.",
    "Sou 100% contra. Estão tentando empurrar guela abaixo algo que ninguém pediu.",
    "Péssima ideia. Não resolve nada e só cria mais problemas. Arquivem isso.",
    "Totalmente contrário. Medida elitista e desconectada da realidade das periferias.",
    "Isso beira o ridículo. A prefeitura deveria focar no que importa em vez de inventar lei inútil.",
    "Repúdio absoluto a esse projeto. Quem redigiu isso não anda de ônibus e não conhece a cidade."
]


def gerar_uuid():
    return str(uuid.uuid4())


def criar_conexao():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    except Error as e:
        print(f"❌ Erro ao conectar: {e}")
        return None


# ---------------------------------------------------------
# FUNÇÕES DE INGESTÃO MASSIVA
# ---------------------------------------------------------
def limpar_banco(cursor):
    print("🧹 Limpando dados antigos...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE comment_vote;")
    cursor.execute("TRUNCATE TABLE comment_analysis;")
    cursor.execute("TRUNCATE TABLE comment;")
    cursor.execute("TRUNCATE TABLE proposal;")
    cursor.execute("TRUNCATE TABLE category;")
    cursor.execute("TRUNCATE TABLE app_user;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    # TRUNCATE em InnoDB já dá commit implícito, mas mantemos o commit
    # explícito do chamador por clareza e por segurança em outros engines.


def criar_base_geografica_e_categorias(cursor):
    print("🌍 Injetando base geográfica e categorias diversificadas...")
    cursor.execute("INSERT IGNORE INTO country (id, name) VALUES (1, 'Brasil')")
    cursor.execute("INSERT IGNORE INTO region (id, name) VALUES (1, 'Sudeste')")
    cursor.execute("INSERT IGNORE INTO state (id, name, acronym, region_id, country_id) VALUES (1, 'São Paulo', 'SP', 1, 1)")
    cursor.execute("INSERT IGNORE INTO municipality (id, name, state_id) VALUES (1, 'São Paulo', 1)")

    categorias_nomes = ["Mobilidade", "Segurança", "Saúde", "Educação", "Meio Ambiente", "Economia", "Infraestrutura"]
    cat_ids = {nome: gerar_uuid() for nome in categorias_nomes}

    dados_categorias = [
        (cat_ids[nome], nome, f"Projetos e propostas para a área de {nome}")
        for nome in categorias_nomes
    ]
    cursor.executemany(
        "INSERT INTO category (id, name, description) VALUES (%s, %s, %s)",
        dados_categorias
    )
    return cat_ids


def gerar_usuarios_faker(cursor, quantidade=150):
    print(f"👥 Gerando {quantidade} cidadãos sintéticos...")
    usuarios_ids = []
    dados_usuarios = []

    for _ in range(quantidade):
        user_id = gerar_uuid()
        nome = fake.name()
        email = fake.unique.email()
        usuarios_ids.append(user_id)
        dados_usuarios.append((user_id, email, nome, True))

    # Bulk insert: uma única ida ao banco para todos os usuários, em vez de
    # uma chamada execute() por usuário.
    cursor.executemany(
        "INSERT INTO app_user (id, email, name, verified) VALUES (%s, %s, %s, %s)",
        dados_usuarios
    )
    return usuarios_ids


def gerar_propostas(cursor, cat_ids, usuarios_ids):
    print("📜 Distribuindo 20 propostas legislativas complexas...")
    propostas_ids = []
    dados_propostas = []

    for titulo, desc, cat_nome in SEMENTES_PROPOSTAS:
        prop_id = gerar_uuid()
        user_id = random.choice(usuarios_ids)
        cat_id = cat_ids[cat_nome]
        propostas_ids.append(prop_id)
        dados_propostas.append((prop_id, titulo, desc, cat_id, user_id))

    cursor.executemany(
        """
        INSERT INTO proposal (id, title, description, category_id, user_id, municipality_id, status)
        VALUES (%s, %s, %s, %s, %s, 1, 'publicado')
        """,
        dados_propostas
    )
    return propostas_ids


def gerar_interacoes_massa(cursor, propostas_ids, usuarios_ids, qtd_comentarios=1000):
    print(f"💬 Injetando {qtd_comentarios} comentários e explodindo a rede de votos...")

    dados_comentarios = []
    dados_votos = []

    for _ in range(qtd_comentarios):
        comment_id = gerar_uuid()
        prop_id = random.choice(propostas_ids)
        user_id = random.choice(usuarios_ids)
        texto = random.choice(SEMENTES_COMENTARIOS)
        dados_comentarios.append((comment_id, prop_id, user_id, texto))

        # Sorteia os votantes já excluindo o autor do comentário, em vez de
        # sortear e depois descartar quem coincidir com o autor — isso evita
        # que o número final de votos fique menor do que o sorteado.
        candidatos = [u for u in usuarios_ids if u != user_id]
        num_votos = random.randint(0, min(15, len(candidatos)))
        votantes = random.sample(candidatos, num_votos)

        for votante_id in votantes:
            voto_valor = random.choice([1, 1, 1, -1])  # Peso maior para upvotes
            dados_votos.append((votante_id, comment_id, voto_valor))

    # Bulk insert dos comentários (1 round-trip em vez de qtd_comentarios)
    cursor.executemany(
        "INSERT INTO comment (id, proposal_id, user_id, body) VALUES (%s, %s, %s, %s)",
        dados_comentarios
    )

    # Bulk insert dos votos (1 round-trip em vez de milhares). Esse é o
    # ganho de performance mais relevante do script, já que o volume de
    # votos costuma ser várias vezes maior que o de comentários.
    if dados_votos:
        cursor.executemany(
            "INSERT IGNORE INTO comment_vote (user_id, comment_id, vote_value) VALUES (%s, %s, %s)",
            dados_votos
        )


# ---------------------------------------------------------
# EXECUÇÃO DA FASE 1
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 INICIANDO FASE 1: GERAÇÃO DE MASSA DE DADOS (ESCALA MÁXIMA)...")
    conn = criar_conexao()
    cursor = None

    if conn:
        try:
            cursor = conn.cursor()

            limpar_banco(cursor)
            conn.commit()

            cat_ids = criar_base_geografica_e_categorias(cursor)
            conn.commit()

            usuarios_ids = gerar_usuarios_faker(cursor, quantidade=150)
            conn.commit()

            propostas_ids = gerar_propostas(cursor, cat_ids, usuarios_ids)
            conn.commit()

            gerar_interacoes_massa(cursor, propostas_ids, usuarios_ids, qtd_comentarios=1000)
            conn.commit()

            print("\n✅ FASE 1 CONCLUÍDA! Banco populado com sucesso.")
        except Exception as e:
            conn.rollback()
            print(f"\n❌ ERRO: {e}")
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()