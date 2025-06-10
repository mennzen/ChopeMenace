import pygame
import random
import os
import tkinter as tk
from tkinter import messagebox
import json
from datetime import datetime

# --- Importações para reconhecimento de voz e fala ---
import speech_recognition as sr
import pyttsx3 # Reativado
import threading # Para rodar o reconhecimento de voz em segundo plano

# --- Funções de Banco de Dados ---
def inicializarBancoDeDados():
    if not os.path.exists("log.dat"):
        with open("log.dat", "w") as f:
            json.dump({}, f)

def escreverDados(nome, pontos):
    try:
        with open("log.dat", "r") as f:
            dados = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        dados = {}

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if nome not in dados:
        dados[nome] = []
    dados[nome].append({"pontos": pontos, "data_hora": data_hora})

    with open("log.dat", "w") as f:
        json.dump(dados, f, indent=4)

# --- Inicialização do Pygame e Configurações Globais ---
pygame.init()
inicializarBancoDeDados()

tamanho = (1000, 700)
relogio = pygame.time.Clock()
tela = pygame.display.set_mode(tamanho)
pygame.display.set_caption("Chope Menace")

icone = pygame.image.load("assets/icone.png")
pygame.display.set_icon(icone)

branco = (255, 255, 255)
preto = (0, 0, 0)
amarelo_claro = (255, 255, 200)

jogador_original = pygame.image.load("assets/jogador.png")
jogador = pygame.transform.scale(jogador_original, (190, 280))

fundoStart = pygame.image.load("assets/chopemenace.jpg")
fundoJogo = pygame.image.load("assets/fundoNuvens.jpg")
fundoDead = pygame.image.load("assets/teladead.jpg")
missel = pygame.transform.scale(pygame.image.load("assets/chopp.png"), (120, 150))
inimigo = pygame.image.load("assets/inimigo.png")

lobao_original = pygame.image.load("assets/lobao.png")
lobao_base_size = (200, 200)
lobao_min_scale = 0.95
lobao_max_scale = 1.05
lobao_scale_speed = 0.0015
lobao_current_scale = 1.0
lobao_scaling_up = True

missileSound = pygame.mixer.Sound("assets/laserBeam.mp3")
explosaoSound = pygame.mixer.Sound("assets/Chamber.mp3")

fonteMenu = pygame.font.SysFont("arialblack", 18)
fonteMorte = pygame.font.SysFont("arial", 120)
fontePause = pygame.font.SysFont("arialblack", 90)
fontePlacarTitulo = pygame.font.SysFont("arialblack", 30)
fontePlacarItem = pygame.font.SysFont("arialblack", 16)

try:
    fonteBotaoDead = pygame.font.SysFont("archivot", 28)
except:
    fonteBotaoDead = pygame.font.SysFont("arialblack", 28)

pygame.mixer.music.load("assets/fundomusica.mp3")

# --- Inicialização do Pyttsx3 (Global) ---
# Reativado: Inicializa o motor de fala
tts_engine = pyttsx3.init()
# Opcional: tentar configurar a voz para português
# voices = tts_engine.getProperty('voices')
# for voice in voices:
#    if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower():
#        tts_engine.setProperty('voice', voice.id)
#        break

# --- Variável global para armazenar o comando de voz reconhecido ---
comando_voz_global = None
# --- Lock para proteger o acesso à variável global ---
comando_lock = threading.Lock()

# --- Funções de Voz ---
def falar(texto):
    """
    Função para fazer o pyttsx3 falar um texto.
    Usado apenas para feedback de pausa/retoma.
    """
    tts_engine.say(texto)
    tts_engine.runAndWait()

def reconhecer_voz_thread(callback):
    """
    Função para rodar o reconhecimento de voz em uma thread separada.
    Chama o callback com o texto reconhecido.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            r.adjust_for_ambient_noise(source, duration=0.5) # Ajuste mais rápido
            print("Aguardando comando de voz...")
            audio = r.listen(source, timeout=3, phrase_time_limit=3)
            texto = r.recognize_google(audio, language="pt-BR")
            print(f"Comando reconhecido: {texto.lower()}")
            callback(texto.lower())
        except sr.WaitTimeoutError:
            # print("Nenhum comando de voz detectado.")
            callback(None) # Envia None se não houver fala
        except sr.UnknownValueError:
            # print("Não foi possível entender o áudio.")
            callback(None)
        except sr.RequestError as e:
            print(f"Erro no serviço de reconhecimento de voz; {e}")
            callback(None)
        except Exception as e:
            print(f"Erro inesperado no reconhecimento de voz: {e}")
            callback(None)


def set_comando_global(comando):
    """Callback para definir o comando global de forma segura."""
    global comando_voz_global
    with comando_lock:
        comando_voz_global = comando

# --- Funções do Jogo ---

def jogar():
    global comando_voz_global # Declara comando_voz_global como global dentro da função
    pygame.mixer.Sound.stop(explosaoSound)

    # --- Entrada de Nome do Jogador (Tkinter) ---
    largura_janela_tk = 300
    altura_janela_tk = 100

    def obter_nome():
        global nome
        nome = entry_nome.get()
        if not nome:
            messagebox.showwarning("Aviso", "Por favor, digite seu nome!")
        else:
            root.destroy()

    root = tk.Tk()
    largura_tela_monitor = root.winfo_screenwidth()
    altura_tela_monitor = root.winfo_screenheight()
    pos_x_tk = (largura_tela_monitor - largura_janela_tk) // 2
    pos_y_tk = (altura_tela_monitor - altura_janela_tk) // 2
    root.geometry(f"{largura_janela_tk}x{altura_janela_tk}+{pos_x_tk}+{pos_y_tk}")
    root.title("Informe seu nickname")
    root.protocol("WM_DELETE_WINDOW", lambda: None) # Impede que a janela seja fechada pelo 'X'

    label_nome = tk.Label(root, text="Digite seu nome para começar:")
    label_nome.pack(pady=5)

    entry_nome = tk.Entry(root)
    entry_nome.pack(pady=5)
    entry_nome.focus_set()

    botao = tk.Button(root, text="Enviar", command=obter_nome)
    botao.pack(pady=5)

    root.bind('<Return>', lambda event=None: botao.invoke()) # Permite enviar com a tecla Enter

    root.mainloop()

    # Se o Tkinter for fechado sem digitar o nome, encerra o jogo
    try:
        nome
    except NameError:
        quit()

    tela_boas_vindas(nome) # Não tem fala robótica aqui

    # --- Variáveis do Jogo ---
    posicaoXPersona = 400
    posicaoYPersona = (tamanho[1] / 2) - (jogador.get_height() / 2) + 150
    movimentoXPersona = 0

    larguraPersona = jogador.get_width()
    alturaPersona = jogador.get_height()

    inimigo_img = pygame.transform.scale(inimigo, (200, 200))
    larguraInimigo = inimigo_img.get_width()
    alturaInimigo = inimigo_img.get_height()
    posicaoXInimigo = 0
    posicaoYInimigo = 10
    movimentoXInimigo = 5

    larguaMissel = 120
    alturaMissel = 150
    posicaoXMissel = posicaoXInimigo + (larguraInimigo / 2) - (larguaMissel / 2)
    posicaoYMissel = alturaInimigo
    velocidadeMissel = 1

    pontos = 0
    paused = False

    global lobao_current_scale, lobao_scaling_up

    pygame.mixer.Sound.play(missileSound)
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(1.0)

    # Variáveis para controle do reconhecimento de voz em jogo
    ultima_tentativa_reconhecimento = pygame.time.get_ticks()
    intervalo_tentativa = 1500 # Tenta reconhecer a cada 1.5 segundos


    # --- Loop Principal do Jogo ---
    while True:
        # Lógica para reconhecimento de voz em segundo plano
        agora = pygame.time.get_ticks()
        if agora - ultima_tentativa_reconhecimento > intervalo_tentativa:
            ultima_tentativa_reconhecimento = agora
            # Inicia uma nova thread para reconhecimento de voz
            voice_thread = threading.Thread(target=reconhecer_voz_thread, args=(set_comando_global,))
            voice_thread.daemon = True # Permite que a thread seja encerrada com o programa principal
            voice_thread.start()

        # Processa o comando de voz reconhecido, se houver
        with comando_lock:
            comando = comando_voz_global
            comando_voz_global = None # Limpa o comando para evitar processamento duplicado

        if comando:
            if "pausar" in comando:
                if not paused:
                    paused = True
                    pygame.mixer.music.set_volume(0.2)
                    falar("Jogo pausado.") # Reativado
            elif "continuar" in comando or "retomar" in comando:
                if paused:
                    paused = False
                    pygame.mixer.music.set_volume(1.0)
                    falar("Jogo retomado.") # Reativado

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()

            # Lógica de pausa via tecla SPACE
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    paused = not paused
                    if paused:
                        pygame.mixer.music.set_volume(0.2)
                        falar("Jogo pausado.") # Reativado
                    else:
                        pygame.mixer.music.set_volume(1.0)
                        falar("Jogo retomado.") # Reativado

            if not paused:
                # Lógica de movimento do jogador (apenas eixo X)
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_RIGHT:
                        movimentoXPersona = 15
                    elif evento.key == pygame.K_LEFT:
                        movimentoXPersona = -15
                if evento.type == pygame.KEYUP:
                    if evento.key == pygame.K_RIGHT or evento.key == pygame.K_LEFT:
                        movimentoXPersona = 0

        if not paused:
            # --- Atualização de Posições e Lógica do Jogo ---
            posicaoXInimigo += movimentoXInimigo
            if posicaoXInimigo < 0 or posicaoXInimigo > tamanho[0] - larguraInimigo:
                movimentoXInimigo = -movimentoXInimigo

            posicaoXPersona += movimentoXPersona

            if posicaoXPersona < 0:
                posicaoXPersona = 0
            elif posicaoXPersona > tamanho[0] - larguraPersona:
                posicaoXPersona = tamanho[0] - larguraPersona

            posicaoYMissel += velocidadeMissel
            if posicaoYMissel > tamanho[1]:
                posicaoYMissel = alturaInimigo
                pontos += 1
                velocidadeMissel += 0.5
                posicaoXMissel = posicaoXInimigo + (larguraInimigo / 2) - (larguaMissel / 2)
                pygame.mixer.Sound.play(missileSound)
                # Removido: feedback de voz a cada 5 pontos
                # if pontos % 5 == 0 and pontos > 0:
                #    falar(f"Você tem {pontos} pontos!")

            persona_hitbox = pygame.Rect(posicaoXPersona + 50, posicaoYPersona + 40, larguraPersona - 100, alturaPersona - 60)
            missel_hitbox = pygame.Rect(posicaoXMissel + 45, posicaoYMissel + 50, larguaMissel - 90, alturaMissel - 85)

            if persona_hitbox.colliderect(missel_hitbox):
                escreverDados(nome, pontos)
                # Removido: falar("Game over!")
                dead()

            if lobao_scaling_up:
                lobao_current_scale += lobao_scale_speed
                if lobao_current_scale >= lobao_max_scale:
                    lobao_current_scale = lobao_max_scale
                    lobao_scaling_up = False
            else:
                lobao_current_scale -= lobao_scale_speed
                if lobao_current_scale <= lobao_min_scale:
                    lobao_current_scale = lobao_min_scale
                    lobao_scaling_up = True

        # --- Desenho na Tela ---
        tela.fill(branco)
        tela.blit(fundoJogo, (0,0))
        tela.blit(inimigo_img, (posicaoXInimigo, posicaoYInimigo))
        tela.blit(jogador, (posicaoXPersona, posicaoYPersona))
        tela.blit(missel, (posicaoXMissel, posicaoYMissel))

        texto = fonteMenu.render("Pontos: "+str(pontos), True, branco)
        tela.blit(texto, (15,15))

        texto_pause_msg = fonteMenu.render("• Pressione Espaço ou diga 'pausar' para Pausar o Jogo", True, branco)
        posicao_x_msg = 15 + texto.get_width() + 20
        tela.blit(texto_pause_msg, (posicao_x_msg, 15))

        current_lobao_width = int(lobao_base_size[0] * lobao_current_scale)
        current_lobao_height = int(lobao_base_size[1] * lobao_current_scale)
        lobao_scaled = pygame.transform.scale(lobao_original, (current_lobao_width, current_lobao_height))

        padding = 10
        lobao_pos_x = tamanho[0] - lobao_scaled.get_width() - padding
        lobao_pos_y = padding
        tela.blit(lobao_scaled, (lobao_pos_x, lobao_pos_y))

        if paused:
            overlay = pygame.Surface(tamanho, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            tela.blit(overlay, (0, 0))

            texto_pause = fontePause.render("PAUSE", True, branco)
            texto_rect = texto_pause.get_rect(center=(tamanho[0]/2, tamanho[1]/2))
            tela.blit(texto_pause, texto_rect)

        pygame.display.update()
        relogio.tick(60)

def start():
    larguraButtonStart = 220
    alturaButtonStart = 60
    larguraButtonQuit = 220
    alturaButtonQuit = 60

    fonteBotao = pygame.font.SysFont("arialblack", 28)

    # --- Loop da Tela Inicial ---
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if startButton.collidepoint(mouse_pos):
                    jogar() # Inicia o jogo
                if quitButton.collidepoint(mouse_pos):
                    quit() # Sai do jogo

        tela.fill(branco)
        tela.blit(fundoStart, (0, 0)) # Desenha o fundo da tela inicial

        centro_x = (tamanho[0] - larguraButtonStart) // 2
        start_y = (tamanho[1] // 2) - 80
        quit_y = start_y + 100

        # Botão "Iniciar Game"
        startButton = pygame.draw.rect(tela, branco, (centro_x, start_y, larguraButtonStart, alturaButtonStart), border_radius=20)
        textoStart = fonteBotao.render("Iniciar Game", True, preto)
        tela.blit(textoStart, textoStart.get_rect(center=startButton.center))

        # Botão "Sair do Game"
        quitButton = pygame.draw.rect(tela, branco, (centro_x, quit_y, larguraButtonQuit, alturaButtonQuit), border_radius=20)
        textoQuit = fonteBotao.render("Sair do Game", True, preto)
        tela.blit(textoQuit, textoQuit.get_rect(center=quitButton.center))

        pygame.display.update()
        relogio.tick(60)

def dead():
    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(explosaoSound)

    log_partidas_raw = []
    try:
        with open("log.dat", "r") as f:
            dados = json.load(f)
            for nickname, partidas_do_jogador in dados.items():
                if isinstance(partidas_do_jogador, list):
                    for partida in partidas_do_jogador:
                        if isinstance(partida, dict) and "pontos" in partida and "data_hora" in partida:
                            log_partidas_raw.append({
                                "nickname": nickname,
                                "pontos": partida["pontos"],
                                "data_hora": partida["data_hora"]
                            })
                        else:
                            print(f"Aviso: Item de partida inesperado para {nickname}: {partida}")
                else:
                    # Lida com o formato legado [pontos, data_hora_str]
                    if isinstance(partidas_do_jogador, list) and len(partidas_do_jogador) == 2 and isinstance(partidas_do_jogador[0], int) and isinstance(partidas_do_jogador[1], str):
                             log_partidas_raw.append({
                                "nickname": nickname,
                                "pontos": partidas_do_jogador[0],
                                "data_hora": partidas_do_jogador[1]
                             })
                    else:
                        print(f"Aviso: Formato de log inesperado para {nickname}: {partidas_do_jogador}")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    log_partidas_sorted = sorted(log_partidas_raw, key=lambda x: x["pontos"], reverse=True)
    ultimas_5_partidas = log_partidas_sorted[:5]


    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if startButton.collidepoint(mouse_pos):
                    jogar() # Inicia um novo jogo
                if quitButton.collidepoint(mouse_pos):
                    quit()

        tela.fill(branco)
        tela.blit(fundoDead, (0,0))

        larguraButton = 200
        alturaButton = 50

        centro_x = (tamanho[0] - larguraButton) // 2
        # Posições dos botões na tela de morte
        start_y = (tamanho[1] // 2) + 150
        quit_y = start_y + 70

        # Botão "Jogar Novamente"
        startButton = pygame.draw.rect(tela, branco, (centro_x, start_y, larguraButton, alturaButton), border_radius=15)
        startTexto = fonteBotaoDead.render("Jogar Novamente", True, preto)
        tela.blit(startTexto, startTexto.get_rect(center=startButton.center))

        # Botão "Sair do Game"
        quitButton = pygame.draw.rect(tela, branco, (centro_x, quit_y, larguraButton, alturaButton), border_radius=15)
        quitTexto = fonteBotaoDead.render("Sair do Game", True, preto)
        tela.blit(quitTexto, quitTexto.get_rect(center=quitButton.center))

        # --- Desenha o Placar no Pygame ---
        placar_bg_width = 250
        placar_bg_height = 130

        padding_right = 10
        padding_bottom = 10

        placar_bg_x = tamanho[0] - placar_bg_width - padding_right
        placar_bg_y = tamanho[1] - placar_bg_height - padding_bottom

        pygame.draw.rect(tela, branco, (placar_bg_x, placar_bg_y, placar_bg_width, placar_bg_height), border_radius=3)
        pygame.draw.rect(tela, preto, (placar_bg_x, placar_bg_y, placar_bg_width, placar_bg_height), 2, border_radius=3)

        item_y_offset = 0
        item_start_y_inside_box = placar_bg_y + 8

        for i, record in enumerate(ultimas_5_partidas):
            item_text = f"{i+1}. {record['nickname']:<10} - {record['pontos']:>5}"
            item_surface = fontePlacarItem.render(item_text, True, preto)
            item_rect = item_surface.get_rect(center=(placar_bg_x + placar_bg_width // 2, item_start_y_inside_box + item_y_offset))

            tela.blit(item_surface, item_rect)
            item_y_offset += 22

        if not ultimas_5_partidas:
            no_data_text = fontePlacarItem.render("Nenhuma pontuação registrada.", True, preto)
            no_data_rect = no_data_text.get_rect(center=(placar_bg_x + placar_bg_width // 2, placar_bg_y + placar_bg_height // 2))
            tela.blit(no_data_text, no_data_rect)

        pygame.display.update()
        relogio.tick(60)

def tela_boas_vindas(nome_jogador):
    larguraButtonStart = 200
    alturaButtonStart = 50
    fundoWelcome = pygame.image.load("assets/fundoNuvens.jpg")

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                quit()
            elif evento.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                if startButton.collidepoint(mouse_pos):
                    return

        tela.fill(branco)
        tela.blit(fundoWelcome, (0, 0))

        # Mensagens de boas-vindas e instruções
        texto_bem_vindo = fonteMenu.render(f"Olá, {nome_jogador}!", True, branco)
        texto_instrucoes1 = fonteMenu.render("Use as SETAS ESQUERDA e DIREITA para se mover.", True, branco)
        texto_instrucoes2 = fonteMenu.render("Desvie dos chopps envenenados do Evil Marcão.", True, branco)
        texto_instrucoes3 = fonteMenu.render("Pressione ESPAÇO ou diga 'pausar' para pausar/retomar o jogo.", True, branco) # Atualizado

        centro_tela_x = tamanho[0] / 2
        tela.blit(texto_bem_vindo, texto_bem_vindo.get_rect(center=(centro_tela_x, 250)))
        tela.blit(texto_instrucoes1, texto_instrucoes1.get_rect(center=(centro_tela_x, 300)))
        tela.blit(texto_instrucoes2, texto_instrucoes2.get_rect(center=(centro_tela_x, 330)))
        tela.blit(texto_instrucoes3, texto_instrucoes3.get_rect(center=(centro_tela_x, 360)))

        # Botão "Iniciar Partida"
        start_x = centro_tela_x - (larguraButtonStart / 2)
        startButton = pygame.draw.rect(tela, branco, (start_x, 450, larguraButtonStart, alturaButtonStart), border_radius=15)
        startTexto = fonteMenu.render("Iniciar Partida", True, preto)
        tela.blit(startTexto, startTexto.get_rect(center=startButton.center))

        pygame.display.update()
        relogio.tick(60)

# Inicia o jogo pela tela inicial
start()