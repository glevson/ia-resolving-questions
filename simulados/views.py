# simulados/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Assunto, Questao, RespostaUsuario
from .ml_service import gerar_relatorio_ml
import pandas as pd
import random # <--- Adicione se precisar, mas o order_by('?') do Django faz o trabalho
from .ml_service import prever_dica_assistente # Importe a nova função!
from django.contrib import messages # Importante para os alertas!


@login_required
def upload_csv(request):
    if request.method == 'POST' and request.FILES.get('arquivo_csv'):
        arquivo = request.FILES['arquivo_csv']
        
        # Validação simples de extensão
        if not arquivo.name.endswith('.csv'):
            messages.error(request, "Erro: O arquivo enviado não é um CSV válido. Verifique a extensão.")
            return redirect('upload_csv')

        try:
            # Tenta ler o CSV. Usamos sep=',' (ou ';' se for o caso do Excel no Brasil)
            df = pd.read_csv(arquivo, encoding='utf-8')
            
            # Limpa espaços em branco nos nomes das colunas
            df.columns = df.columns.str.strip().str.lower()
            
            # Valida se as colunas obrigatórias existem
            colunas_esperadas = ['assunto', 'enunciado', 'a', 'b', 'c', 'd', 'correta', 'justificativa']
            if not all(col in df.columns for col in colunas_esperadas):
                messages.error(request, "Erro: O CSV não possui o cabeçalho correto. Verifique o modelo.")
                return redirect('upload_csv')

            questoes_inseridas = 0
            questoes_ignoradas = 0

            # Itera pelas linhas do Pandas
            for index, row in df.iterrows():
                enunciado_limpo = str(row['enunciado']).strip()
                
                # PARSE: Verifica se já existe uma questão com ESSE enunciado exato
                if Questao.objects.filter(enunciado=enunciado_limpo).exists():
                    questoes_ignoradas += 1
                    continue # Pula para a próxima linha do CSV
                
                # Se não existe, cria a matéria (se não houver) e salva a questão
                assunto, _ = Assunto.objects.get_or_create(nome=str(row['assunto']).strip())
                
                Questao.objects.create(
                    assunto=assunto,
                    enunciado=enunciado_limpo,
                    opcao_a=str(row['a']).strip(),
                    opcao_b=str(row['b']).strip(),
                    opcao_c=str(row['c']).strip(),
                    opcao_d=str(row['d']).strip(),
                    resposta_correta=str(row['correta']).strip().upper(),
                    justificativa=str(row['justificativa']).strip() if pd.notna(row['justificativa']) else ""
                )
                questoes_inseridas += 1

            # Feedback de Sucesso Profissional
            if questoes_inseridas > 0:
                messages.success(request, f"Upload concluído! {questoes_inseridas} novas questões foram inseridas com sucesso.")
            
            if questoes_ignoradas > 0:
                messages.warning(request, f"Aviso: {questoes_ignoradas} questões foram ignoradas pois já existiam no banco de dados.")
                
            return redirect('upload_csv')

        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo: {str(e)}")
            return redirect('upload_csv')
            
    # Se for GET, apenas renderiza a página vazia
    return render(request, 'simulados/upload.html')


@login_required
def dashboard(request):
    # 1. Gera o relatório da IA
    relatorio = gerar_relatorio_ml(request.user)
    
    # 2. Lógica para buscar a próxima questão INÉDITA e ALEATÓRIA
    # Pega uma lista apenas com os números (IDs) das questões que o usuário já respondeu
    ids_respondidas = RespostaUsuario.objects.filter(usuario=request.user).values_list('questao_id', flat=True)
    
    # Busca todas as questões, EXCLUI as que estão na lista acima, ORDENA de forma aleatória ('?') e pega a primeira (.first())
    proxima_questao = Questao.objects.exclude(id__in=ids_respondidas).order_by('?').first()

    context = {
        'relatorio': relatorio,
        'proxima_questao': proxima_questao
    }
    return render(request, 'simulados/dashboard.html', context)


@login_required
def responder_questao(request, questao_id):
    questao = Questao.objects.get(id=questao_id)
    
    # Chama o robô da IA para dar a dica
    dica_ia = prever_dica_assistente(request.user, questao.assunto.id)
    
    if request.method == 'POST':
        escolha = request.POST.get('opcao')
        acertou = (escolha == questao.resposta_correta)
        
        # Salva a resposta
        RespostaUsuario.objects.create(
            usuario=request.user, questao=questao, opcao_escolhida=escolha, acertou=acertou
        )
        
        # Prepara a URL da PRÓXIMA questão para o botão "Avançar"
        ids_respondidas = RespostaUsuario.objects.filter(usuario=request.user).values_list('questao_id', flat=True)
        proxima = Questao.objects.exclude(id__in=ids_respondidas).order_by('?').first()
        
        # Manda as variáveis para a tela mostrar o RESULTADO, e não pular de vez.
        context = {
            'questao': questao, 'dica_ia': dica_ia,
            'respondido': True, 'acertou': acertou, 'escolha': escolha,
            'proxima_id': proxima.id if proxima else None
        }
        return render(request, 'simulados/responder.html', context)
        
    # Se for GET (Apenas abriu a página), mostra o formulário para responder
    return render(request, 'simulados/responder.html', {'questao': questao, 'dica_ia': dica_ia, 'respondido': False})