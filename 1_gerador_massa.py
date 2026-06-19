import os
import uuid
import random
import json
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from faker import Faker
from datetime import datetime, timedelta

# ---------------------------------------------------------
# SETUP E CONFIGURAÇÕES
# ---------------------------------------------------------
load_dotenv()
fake = Faker('pt_BR')

PARTIDOS = ["Partido Inovação (PI)", "Partido Conservador (PC)", "Partido Verde (PV)", "Partido Liberal (PL)"]
CARGOS = ["Vereador", "Deputado Estadual", "Deputado Federal"]
NIVEIS_POLITICOS = ["municipal", "estadual", "federal"]

SEMENTES_PROPOSTAS = [
    ("Implementação de Pedágio Urbano no Centro", "Criação de taxa para veículos circularem no centro.", "Mobilidade", ["transporte", "centro", "taxa"]),
    ("Tarifa Zero aos Domingos", "Gratuidade no transporte público municipal.", "Mobilidade", ["ônibus", "social", "domingo"]),
    ("Faixa Exclusiva para Motociclistas", "Criação de faixas azuis nas principais avenidas.", "Mobilidade", ["trânsito", "segurança", "motos"]),
    ("Integração Tarifária Regional", "Integração gratuita entre ônibus e trens.", "Mobilidade", ["trens", "integração", "metropolitana"]),
    ("Programa Bairro Iluminado", "Substituição de lâmpadas antigas por LED.", "Segurança", ["iluminação", "infraestrutura", "led"]),
    ("Câmeras Corporais na Guarda", "Uso obrigatório de bodycams por todos os agentes.", "Segurança", ["gcm", "tecnologia", "transparência"]),
    ("Drones para Monitoramento", "Uso de drones pela segurança pública.", "Segurança", ["inovação", "drones", "vigilância"]),
    ("Hospital Veterinário Público", "Atendimento gratuito para animais domésticos.", "Saúde", ["pets", "saúde", "animal"]),
    ("Telemedicina nos Postos", "Totens de atendimento virtual nas UBSs.", "Saúde", ["digital", "ubs", "inovação"]),
    ("Mutirão de Exames aos Finais de Semana", "Abertura das unidades aos sábados.", "Saúde", ["filas", "exames", "agilidade"]),
    ("Escola em Tempo Integral", "Ampliação da carga horária nas escolas.", "Educação", ["infância", "oficinas", "ensino"]),
    ("Vouchers para Creches Privadas", "Subsídio da prefeitura para zerar fila de creches.", "Educação", ["creche", "subsídio", "família"]),
    ("Kits de Robótica nas Escolas", "Laboratórios móveis para o ensino fundamental.", "Educação", ["tecnologia", "futuro", "robótica"]),
    ("Multa para Descarte Irregular", "Aumento de 500% na multa para descarte de entulho.", "Meio Ambiente", ["limpeza", "punição", "ecologia"]),
    ("Frota de Ônibus Elétricos", "Substituição de 30% da frota até 2028.", "Meio Ambiente", ["emissão zero", "elétricos", "clima"]),
    ("Criação do Parque Ecológico", "Construção de um grande parque de preservação.", "Meio Ambiente", ["parque", "verde", "lazer"]),
    ("Incentivo Fiscal para Startups", "Isenção de ISS por 5 anos para empresas de tech.", "Economia", ["startups", "impostos", "emprego"]),
    ("Feira Noturna Gastronômica", "Regulamentação de food trucks em praças.", "Economia", ["cultura", "gastronomia", "renda"]),
    ("Programa Jovem Aprendiz Municipal", "Cotas em empresas parceiras da prefeitura.", "Economia", ["juventude", "trabalho", "inclusão"]),
    ("Revitalização do Calçadão Comercial", "Reforma e acessibilidade das calçadas do centro.", "Infraestrutura", ["obras", "acessibilidade", "comércio"])
]

SEMENTES_COMENTARIOS = [
    # Apoio
    "Apoio totalmente a ideia! Isso vai melhorar muito a nossa qualidade de vida.",
    "Excelente! Já passou da hora de termos medidas corajosas assim na cidade!",
    "Parabéns pela proposta. Tem o meu voto e da minha família.",
    "Perfeito, isso é exatamente o que a nossa região precisa há anos.",
    "Completamente a favor. Vai trazer desenvolvimento e organizar a casa.",
    # Alteração
    "Acho a iniciativa boa, mas o valor precisa ser revisto para não prejudicar trabalhadores.",
    "Excelente ideia, porém deveriam isentar moradores locais dessa regra.",
    "Sou a favor do projeto, mas o prazo de implementação é muito longo.",
    "A intenção é muito válida. Só precisa ajustar a redação para não criar brechas legais.",
    "Apoio a pauta, mas requer emendas. Da forma como está escrita, pode prejudicar a classe média.",
    # Neutro
    "Não tenho certeza se isso resolve o problema raiz, precisamos de mais estudos técnicos.",
    "Até que faz sentido, mas quero ver se o dinheiro vai mesmo para melhorias.",
    "Preciso ler o projeto de lei na íntegra para opinar. A descrição está muito vaga.",
    "Não sou nem contra nem a favor ainda. Faltam dados estatísticos justificando a medida.",
    "Pode ser que funcione, pode ser que não. Vamos acompanhar o debate na câmara.",
    # Oposição Parcial
    "A intenção do projeto é boa, mas o trecho que cria novos impostos deve ser removido.",
    "O projeto em si tem méritos, mas me oponho totalmente à cláusula de multas, isso tem que cair.",
    "Essa lei até pode seguir em frente, desde que removam a exigência de cobrança. Sem isso, eu aprovo.",
    "Entendo a necessidade, mas a parte punitiva do texto precisa ser totalmente excluída.",
    "Concordo com a criação do programa, mas sou terminantemente contra a taxa de adesão obrigatória.",
    # Rejeição
    "Sou contra. Isso é um absurdo e só serve para tirar dinheiro do cidadão.",
    "Isso vai destruir o comércio local. A lei deve ser rejeitada imediatamente e arquivada.",
    "Completamente inviável. Quem precisa trabalhar não tem outra opção. Voto não.",
    "Essa é a pior proposta que eu já vi. Um completo desrespeito com a população.",
    "Totalmente contrário. Medida elitista e desconectada da realidade das periferias."
]

def gerar_uuid():
    return str(uuid.uuid4())

def criar_conexao():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_NAME")
        )
    except Error as e:
        print(f"❌ Erro ao conectar: {e}")
        return None

# ---------------------------------------------------------
# INGESTÃO GEOGRÁFICA E METADADOS
# ---------------------------------------------------------
def limpar_banco(cursor):
    print("🧹 [1/8] Executando Truncate Cascata (limpeza profunda)...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tabelas = [
        "comment_vote", "proposal_vote", "comment_analysis", "attachment", 
        "vote", "parliamentary_activity", "proposal_share", "proposal_support", 
        "proposal_parliamentarian", "comment", "proposal", "community", 
        "parliamentarian", "category", "user_auth_provider", "app_user",
        "municipality", "state", "region", "country"
    ]
    for tab in tabelas:
        cursor.execute(f"TRUNCATE TABLE {tab};")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

def setup_geografia_categorias(cursor):
    print("🌍 [2/8] Mapeando Brasil (Norte a Sul), Estados e Partidos...")
    cursor.execute("INSERT INTO country (id, name) VALUES (1, 'Brasil')")
    
    # 5 Regiões do Brasil
    regioes = {1: "Sudeste", 2: "Sul", 3: "Nordeste", 4: "Norte", 5: "Centro-Oeste"}
    for r_id, nome in regioes.items():
        cursor.execute("INSERT INTO region (id, name) VALUES (%s, %s)", (r_id, nome))
        
    # Estados representativos
    estados = [
        (1, 'São Paulo', 'SP', 1), (2, 'Rio de Janeiro', 'RJ', 1), 
        (3, 'Paraná', 'PR', 2), (4, 'Bahia', 'BA', 3), 
        (5, 'Ceará', 'CE', 3), (6, 'Amazonas', 'AM', 4), 
        (7, 'Pará', 'PA', 4), (8, 'Goiás', 'GO', 5), 
        (9, 'Distrito Federal', 'DF', 5)
    ]
    cursor.executemany("INSERT INTO state (id, name, acronym, region_id, country_id) VALUES (%s, %s, %s, %s, 1)", estados)
    
    # Municípios principais
    municipios = [
        (1, 'São Paulo', 1), (2, 'Campinas', 1), (3, 'Rio de Janeiro', 2), 
        (4, 'Curitiba', 3), (5, 'Salvador', 4), (6, 'Fortaleza', 5), 
        (7, 'Manaus', 6), (8, 'Belém', 7), (9, 'Goiânia', 8), (10, 'Brasília', 9)
    ]
    cursor.executemany("INSERT INTO municipality (id, name, state_id) VALUES (%s, %s, %s)", municipios)
    
    categorias = ["Mobilidade", "Segurança", "Saúde", "Educação", "Meio Ambiente", "Economia", "Infraestrutura"]
    cat_ids = {nome: gerar_uuid() for nome in categorias}
    cursor.executemany("INSERT INTO category (id, name, description) VALUES (%s, %s, %s)", 
                       [(cat_ids[nome], nome, f"Área de {nome}") for nome in categorias])
    
    return cat_ids, list(regioes.keys()), [e[0] for e in estados], [m[0] for m in municipios]

# ---------------------------------------------------------
# SIMULADOR DEMOGRÁFICO E POLÍTICO
# ---------------------------------------------------------
def gerar_usuarios_e_politicos(cursor, regioes, estados, municipios, qtd_users, qtd_politicos):
    print(f"👥 [3/8] Injetando {qtd_users} cidadãos e {qtd_politicos} parlamentares VIPs...")
    users = []
    
    for _ in range(qtd_users):
        u_id = gerar_uuid()
        users.append((u_id, fake.unique.email(), fake.name(), fake.image_url(), fake.text(max_nb_chars=100), True))
    cursor.executemany("INSERT INTO app_user (id, email, name, avatar_url, bio, verified) VALUES (%s, %s, %s, %s, %s, %s)", users)
    
    usuarios_ids = [u[0] for u in users]
    politicos_ids = random.sample(usuarios_ids, qtd_politicos)
    dados_politicos = []
    
    for p_id in politicos_ids:
        dados_politicos.append((
            gerar_uuid(), p_id, fake.name(), random.choice(NIVEIS_POLITICOS), 
            random.choice(CARGOS), random.choice(PARTIDOS), random.choice(regioes), 
            random.choice(estados), random.choice(municipios), 
            datetime(2023, 1, 1), fake.url(), fake.unique.company_email()
        ))
        
    cursor.executemany("""
        INSERT INTO parliamentarian (id, user_id, name, political_level, position, party, 
        region_id, state_id, municipality_id, term_start, official_page_url, contact_email) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, dados_politicos)
    
    parlamentares_uuid = [p[0] for p in dados_politicos]
    return usuarios_ids, parlamentares_uuid

def gerar_propostas_complexas(cursor, cat_ids, usuarios_ids, municipios):
    print("📜 [4/8] Publicando propostas com Tags JSON, Comunidades e Metas...")
    
    com_id = gerar_uuid()
    cursor.execute("INSERT INTO community (id, user_id, name, description) VALUES (%s, %s, 'Fórum Nacional', 'Debates Cívicos')", (com_id, usuarios_ids[0]))
    
    propostas_ids = []
    dados_prop = []
    
    for i in range(50):
        prop_id = gerar_uuid()
        propostas_ids.append(prop_id)
        
        semente = SEMENTES_PROPOSTAS[i % len(SEMENTES_PROPOSTAS)]
        titulo, desc, cat_nome, tags = semente
        
        if i >= len(SEMENTES_PROPOSTAS):
            titulo = f"{titulo} ({fake.city()})"
            desc = f"{desc} {fake.sentence()}"
            
        dados_prop.append((
            prop_id, titulo, desc, cat_ids[cat_nome], random.choice(usuarios_ids), 
            random.choice(municipios), com_id, 'publicado', 'público', 
            json.dumps(tags), random.randint(500, 5000), random.randint(100, 10000)
        ))
        
    cursor.executemany("""
        INSERT INTO proposal (id, title, description, category_id, user_id, municipality_id, 
        community_id, status, visibility, tags, goal_supporters, views_count) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, dados_prop)
    
    return propostas_ids

def gerar_engajamento_organico(cursor, propostas_ids, usuarios_ids, parlamentares_uuid):
    print("🤝 [5/8] Simulando Atividades Parlamentares, Compartilhamentos e Apoios...")
    
    apoios, shares, activities, par_props = [], [], [], []
    
    for prop_id in propostas_ids:
        autores = random.sample(parlamentares_uuid, random.randint(1, 5))
        for aut in autores:
            par_props.append((prop_id, aut))
            
        apoiadores = random.sample(usuarios_ids, random.randint(5, 30))
        for u_id in apoiadores:
            apoios.append((gerar_uuid(), prop_id, u_id))
            if random.random() > 0.7:
                shares.append((gerar_uuid(), prop_id, u_id, 'whatsapp'))

    for p_id in parlamentares_uuid:
        activities.append((gerar_uuid(), p_id, 'Discurso', fake.sentence(), datetime.now() - timedelta(days=random.randint(1, 100))))

    cursor.executemany("INSERT INTO proposal_parliamentarian (proposal_id, parliamentarian_id) VALUES (%s, %s)", par_props)
    cursor.executemany("INSERT INTO proposal_support (id, proposal_id, user_id) VALUES (%s, %s, %s)", apoios)
    cursor.executemany("INSERT INTO proposal_share (id, proposal_id, shared_by, method) VALUES (%s, %s, %s, %s)", shares)
    cursor.executemany("INSERT INTO parliamentary_activity (id, representative_id, activity_type, description, date_occurred) VALUES (%s, %s, %s, %s, %s)", activities)

def injetar_comentarios(cursor, propostas_ids, usuarios_ids, qtd):
    print(f"💬 [6/8] Disparando {qtd} comentários semânticos para o motor de NLP...")
    dados_comentarios = []
    
    for _ in range(qtd):
        dados_comentarios.append((
            gerar_uuid(), random.choice(propostas_ids), 
            random.choice(usuarios_ids), random.choice(SEMENTES_COMENTARIOS)
        ))
        
    cursor.executemany("INSERT INTO comment (id, proposal_id, user_id, body) VALUES (%s, %s, %s, %s)", dados_comentarios)
    return [c[0] for c in dados_comentarios]

def gerar_votos_escala(cursor, propostas_ids, comentarios_ids, usuarios_ids):
    print("🔥 [7/8] Explodindo rede de Upvotes/Downvotes (Milhares de registros)...")
    votos_prop, votos_com = [], []
    
    for prop_id in propostas_ids:
        votantes = random.sample(usuarios_ids, random.randint(10, 150))
        for v in votantes:
            votos_prop.append((v, prop_id, random.choice([1, 1, 1, -1]))) 
            
    comentarios_amostra = random.sample(comentarios_ids, min(1000, len(comentarios_ids)))
    for com_id in comentarios_amostra:
        votantes = random.sample(usuarios_ids, random.randint(0, 20))
        for v in votantes:
            votos_com.append((v, com_id, random.choice([1, 1, -1])))

    cursor.executemany("INSERT IGNORE INTO proposal_vote (user_id, proposal_id, vote_value) VALUES (%s, %s, %s)", votos_prop)
    cursor.executemany("INSERT IGNORE INTO comment_vote (user_id, comment_id, vote_value) VALUES (%s, %s, %s)", votos_com)

# ---------------------------------------------------------
# MOTOR PRINCIPAL
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 INICIANDO SIMULADOR CÍVICO DE ALTA DENSIDADE...")
    conn = criar_conexao()
    if conn:
        try:
            cursor = conn.cursor()
            limpar_banco(cursor)
            conn.commit()
            
            cat_ids, regioes, estados, munics = setup_geografia_categorias(cursor)
            
            # Aqui definimos: 1000 usuários comuns e 40 políticos
            usuarios_ids, parl_ids = gerar_usuarios_e_politicos(cursor, regioes, estados, munics, qtd_users=1000, qtd_politicos=40)
            
            prop_ids = gerar_propostas_complexas(cursor, cat_ids, usuarios_ids, munics)
            gerar_engajamento_organico(cursor, prop_ids, usuarios_ids, parl_ids)
            
            # Aqui definimos: 3000 comentários a serem gerados
            comentarios_ids = injetar_comentarios(cursor, prop_ids, usuarios_ids, qtd=3000)
            
            gerar_votos_escala(cursor, prop_ids, comentarios_ids, usuarios_ids)
            
            conn.commit()
            print("✅ [8/8] FASE 1 CONCLUÍDA! Banco perfeitamente populado e pronto para BI e IA.")
            print("\n💡 Próximo Passo: Execute 'python 2_classificador_ia.py' para classificar os 3.000 novos comentários!")
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ ERRO CRÍTICO: {e}")
        finally:
            cursor.close()
            conn.close()