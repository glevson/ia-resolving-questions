# simulados/ml_service.py
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from .models import RespostaUsuario, Assunto

def gerar_relatorio_ml(usuario):
    respostas = RespostaUsuario.objects.filter(usuario=usuario)
    total_respostas = respostas.count()
    
    if total_respostas < 10:
        faltam = 10 - total_respostas
        return {
            "erro": f"A Inteligência Artificial precisa de mais dados para analisar seu perfil. Responda mais {faltam} questões.",
            "total_respondidas": total_respostas
        }

    # 1. Preparar os dados para o Pandas
    dados = []
    for r in respostas:
        dados.append({
            'assunto_id': r.questao.assunto.id,
            'acertou': 1 if r.acertou else 0
        })
    
    df = pd.DataFrame(dados)

    # 2. Treinar a Árvore de Decisão
    X = df[['assunto_id']]
    y = df['acertou']

    arvore = DecisionTreeClassifier(random_state=42, max_depth=3) # max_depth=3 para regras não ficarem gigantes
    arvore.fit(X, y)

    # 3. EXTRAÇÃO DAS REGRAS DA ÁRVORE (NOVO!)
    # Pegamos os nomes reais dos assuntos para o texto fazer sentido
    nomes_assuntos = {assunto.id: assunto.nome for assunto in Assunto.objects.all()}
    
    # Exporta a árvore em formato de texto usando o nome da coluna ('assunto_id')
    regras_texto = export_text(arvore, feature_names=['assunto_id'])
    
    # Substitui os IDs numéricos (ex: assunto_id <= 2.50) pelos Nomes das Matérias para o usuário entender
    for assunto_id, nome in nomes_assuntos.items():
        regras_texto = regras_texto.replace(f"assunto_id <= {assunto_id}.50", f"Se a matéria for {nome} ou anterior...")
        regras_texto = regras_texto.replace(f"assunto_id >  {assunto_id}.50", f"Se a matéria for DEPOIS de {nome}...")
    
    # Substitui as classes de acerto/erro
    regras_texto = regras_texto.replace("class: 0", "➡ PREVISÃO: Você vai ERRAR ❌")
    regras_texto = regras_texto.replace("class: 1", "➡ PREVISÃO: Você vai ACERTAR ✅")

    # 4. Fazer previsões (Quais assuntos ele precisa melhorar?)
    todos_assuntos = Assunto.objects.all()
    pontos_a_melhorar = []
    pontos_fortes = []

    for assunto in todos_assuntos:
        # A IA prevê a probabilidade
        probabilidade = arvore.predict_proba([[assunto.id]])[0]
        prob_erro = probabilidade[0] * 100 
        
        if prob_erro >= 50:
            pontos_a_melhorar.append({
                "nome": assunto.nome, 
                "risco": f"{prob_erro:.1f}%",
                "cor": "danger"
            })
        else:
            pontos_fortes.append({
                "nome": assunto.nome, 
                "acerto": f"{probabilidade[1]*100:.1f}%",
                "cor": "success"
            })

    return {
        "pontos_a_melhorar": pontos_a_melhorar,
        "pontos_fortes": pontos_fortes,
        "total_respondidas": total_respostas,
        "regras_arvore": regras_texto # Enviando as regras para o HTML
    }

def prever_dica_assistente(usuario, assunto_id):
    respostas = RespostaUsuario.objects.filter(usuario=usuario)
    
    if respostas.count() < 10:
        return {
            "mensagem": "Ainda estou aprendendo seu estilo de estudo. Responda 10 questões para eu começar a te dar dicas precisas!",
            "cor": "secondary", "icone": "bi-robot"
        }

    # Treina a árvore rapidamente só para esta previsão
    import pandas as pd
    from sklearn.tree import DecisionTreeClassifier
    
    dados = [{'assunto_id': r.questao.assunto.id, 'acertou': 1 if r.acertou else 0} for r in respostas]
    df = pd.DataFrame(dados)
    X = df[['assunto_id']]
    y = df['acertou']
    
    arvore = DecisionTreeClassifier(random_state=42, max_depth=3)
    arvore.fit(X, y)
    
    # Prevê a chance de erro para ESTE assunto específico
    probabilidade = arvore.predict_proba([[assunto_id]])[0]
    prob_erro = probabilidade[0] * 100
    
    if prob_erro >= 50:
        return {
            "mensagem": f"⚠️ ALERTA DA IA: Seu histórico mostra {prob_erro:.0f}% de chance de erro neste assunto. Leia as alternativas com muita atenção, não tenha pressa!",
            "cor": "danger", "icone": "bi-exclamation-triangle-fill"
        }
    else:
        return {
            "mensagem": f"✅ IA ANALISOU: Você domina esse assunto! A probabilidade de você acertar é de {probabilidade[1]*100:.0f}%. Vai com confiança!",
            "cor": "success", "icone": "bi-check-circle-fill"
        }