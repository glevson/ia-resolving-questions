from django.contrib import admin
from .models import Assunto, Questao, RespostaUsuario

# 1. Configuração do Assunto
@admin.register(Assunto)
class AssuntoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',) # Permite pesquisar pelo nome do assunto

# 2. Configuração das Questões (O mais importante)
@admin.register(Questao)
class QuestaoAdmin(admin.ModelAdmin):
    # Colunas que vão aparecer na lista
    list_display = ('id', 'assunto', 'resumo_enunciado', 'resposta_correta', 'justificativa')
    
    # Cria um menu lateral direito para filtrar as questões por assunto
    list_filter = ('assunto', 'resposta_correta')
    
    # Cria uma barra de pesquisa que busca palavras dentro do enunciado
    search_fields = ('enunciado',)

    # Função para não mostrar o enunciado inteiro na tabela (se for muito grande)
    def resumo_enunciado(self, obj):
        if len(obj.enunciado) > 75:
            return obj.enunciado[:75] + '...'
        return obj.enunciado
    
    resumo_enunciado.short_description = 'Enunciado' # Nome da coluna

# 3. Configuração do Histórico de Respostas (Para você ver como os alunos estão)
@admin.register(RespostaUsuario)
class RespostaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'questao', 'opcao_escolhida', 'acertou', 'data_resposta')
    
    # Filtros laterais fantásticos para ver quem acertou ou errou
    list_filter = ('acertou', 'usuario', 'data_resposta')
    
    # Permite pesquisar pelo nome do usuário ou pelo texto da questão
    search_fields = ('usuario__username', 'questao__enunciado')
    
    # Impede que as respostas sejam alteradas manualmente no admin (opcional, para manter integridade)
    readonly_fields = ('data_resposta',)